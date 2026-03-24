"""
Stage 4: Causal Inference — Granger VAR + STL Decomposition
=============================================================
Tests whether ΔS_anthro causally influences downstream proxies
and whether anthropogenic/climate signals are statistically separable.

Tests:
  A) Granger causality on STL remainders (Maithon → Panchet → Durgapur)
  B) Granger causality: ΔS_anthro → climate residual (bidirectional)
  C) HMM 3-state operational regime detection on ΔS_anthro

Critical rule: STL decompose ALL series BEFORE Granger test.
Reason: all three reservoirs share monsoon seasonal driver →
raw series will always show spurious causality (FATAL-5 in CLAUDE.md).

Pass criterion: p < 0.05 on at least one Granger test → Journal of Hydrology target
                p < 0.10 → Remote Sensing of Environment target

Run:
  uv run python src/04_causal_inference.py
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from datetime import datetime

from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from statsmodels.tsa.api import VAR

try:
    from hmmlearn import hmm
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False
    print("  [WARN] hmmlearn not installed — HMM step will be skipped")

try:
    import pyEDM
    CCM_AVAILABLE = True
except ImportError:
    CCM_AVAILABLE = False
    print("  [WARN] pyEDM not installed — CCM step will be skipped")

from tqdm import tqdm

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

PROCESSED_DIR = Path('data/processed')
FIGURES_DIR   = Path('figures')
RANDOM_STATE  = 42
STL_PERIOD    = 12       # monthly → annual seasonality
MAX_LAG       = 4        # Granger max lag (months)
HMM_STATES    = 2        # DRAWDOWN vs NORMAL — 3-state was unjustified:
                          # CONSERVATION mean=+0.015 and FILLING mean=+0.035
                          # differ by only 0.020 BCM < model RMSE (0.097 BCM),
                          # meaning they were statistically indistinguishable.
N_SURROGATES  = 999      # phase-randomised surrogates for Granger p-value check
CCM_LIB_SIZES = list(range(10, 49, 4))  # library sizes for CCM convergence test

# ═══════════════════════════════════════════════════════════════════
# STEP 0: Helper functions
# ═══════════════════════════════════════════════════════════════════

def stl_remainder(series: pd.Series, period: int = STL_PERIOD) -> pd.Series:
    """
    STL decompose and return remainder (trend + seasonal removed).
    Requires ≥2 full periods of non-NaN data.
    Uses robust=True to downweight outliers (flood events).
    """
    s = series.dropna()
    if len(s) < 2 * period:
        raise ValueError(f"Series too short for STL: {len(s)} < {2*period}")
    result = STL(s, period=period, robust=True).fit()
    return pd.Series(result.resid, index=s.index, name=series.name + '_stl_resid')


def adf_test(series: pd.Series) -> dict:
    """Augmented Dickey-Fuller stationarity test."""
    s = series.dropna()
    stat, p, _, _, crit, _ = adfuller(s, autolag='AIC')
    return {'stat': stat, 'p': p, 'crit_5pct': crit['5%'],
            'stationary': p < 0.05}


def granger_test(cause: pd.Series, effect: pd.Series,
                 maxlag: int = MAX_LAG) -> pd.DataFrame:
    """
    Test whether 'cause' Granger-causes 'effect'.
    Returns DataFrame with p-values per lag.
    Uses F-test (ssr_ftest) — most reliable for small samples.
    """
    df_test = pd.concat([effect, cause], axis=1).dropna()
    if len(df_test) < 3 * maxlag + 10:
        return pd.DataFrame({'lag': range(1, maxlag+1),
                             'p_value': [np.nan]*maxlag,
                             'F_stat':  [np.nan]*maxlag})
    results = grangercausalitytests(df_test.values, maxlag=maxlag, verbose=False)
    records = []
    for lag in range(1, maxlag + 1):
        f_stat = results[lag][0]['ssr_ftest'][0]
        p_val  = results[lag][0]['ssr_ftest'][1]
        records.append({'lag': lag, 'p_value': p_val, 'F_stat': f_stat})
    return pd.DataFrame(records)


def phase_randomise(series: np.ndarray, n: int = N_SURROGATES,
                    rng: np.random.Generator = None) -> np.ndarray:
    """
    Generate n phase-randomised surrogates (Theiler et al. 1992).
    Preserves amplitude spectrum, randomises phases.
    Used to validate Granger p-values against chance.
    """
    if rng is None:
        rng = np.random.default_rng(RANDOM_STATE)
    ft = np.fft.rfft(series)
    magnitudes = np.abs(ft)
    surrogates = np.zeros((n, len(series)))
    for i in range(n):
        phases = rng.uniform(0, 2 * np.pi, len(ft))
        ft_surr = magnitudes * np.exp(1j * phases)
        surrogates[i] = np.fft.irfft(ft_surr, n=len(series))
    return surrogates


# ═══════════════════════════════════════════════════════════════════
# STEP 1: Load data
# ═══════════════════════════════════════════════════════════════════

def load_series() -> dict:
    """
    Load Maithon, Panchet, Durgapur delta_S and ΔS_anthro.
    Returns dict of named Series, S1 era only.
    """
    print("[1/5] Loading series...")

    ts = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv',
                     parse_dates=['date'])
    ts = ts.set_index('date').sort_index()

    series = {}
    for res in ['maithon', 'panchet', 'durgapur']:
        sub = ts[ts['reservoir'] == res]['delta_S_obs_bcm']
        sub = sub[sub.index >= '2017-01-01'].dropna()
        series[res] = sub
        print(f"  {res}: {len(sub)} rows "
              f"[{sub.index[0].date()} → {sub.index[-1].date()}]"
              f"  range=[{sub.min():.3f}, {sub.max():.3f}]")

    # ΔS_anthro — prefer no-lag version (clean, no circular lag dependency)
    nolags_path = PROCESSED_DIR / 'delta_S_anthro_nolags.csv'
    anthro_path = PROCESSED_DIR / 'delta_S_anthro.csv'
    if nolags_path.exists():
        anthro = pd.read_csv(nolags_path, index_col=0, parse_dates=True)
        print("  [INFO] Using no-lag ΔS_anthro (clean, no circular dependency)")
    else:
        anthro = pd.read_csv(anthro_path, index_col=0, parse_dates=True)
        print("  [WARN] Using lag-contaminated ΔS_anthro — run Stage 3 sensitivity first")
    anthro_series = anthro['delta_S_anthro_bcm'].dropna()
    series['anthro'] = anthro_series
    print(f"  anthro: {len(anthro_series)} rows "
          f"[{anthro_series.index[0].date()} → {anthro_series.index[-1].date()}]"
          f"  range=[{anthro_series.min():.3f}, {anthro_series.max():.3f}]")

    # Climate predicted
    climate_series = anthro['delta_S_climate_bcm'].dropna()
    series['climate'] = climate_series
    print(f"  climate: {len(climate_series)} rows")

    return series


# ═══════════════════════════════════════════════════════════════════
# STEP 2: STL decompose all series
# ═══════════════════════════════════════════════════════════════════

def decompose_all(series: dict) -> dict:
    """
    Apply STL to each series. Return dict of STL remainder series.
    Only decompose series with ≥24 non-NaN rows.
    """
    print("\n[2/5] STL decomposition (removing seasonal + trend)...")
    remainders = {}
    for name, s in series.items():
        try:
            r = stl_remainder(s)
            remainders[name] = r
            adf = adf_test(r)
            print(f"  {name:12s}: {len(r)} rows | "
                  f"ADF p={adf['p']:.4f} ({'STATIONARY ✓' if adf['stationary'] else 'NON-STATIONARY ✗'})")
        except Exception as e:
            print(f"  {name:12s}: SKIPPED — {e}")
    return remainders


# ═══════════════════════════════════════════════════════════════════
# STEP 3: Granger causality tests
# ═══════════════════════════════════════════════════════════════════

def run_granger_tests(remainders: dict) -> pd.DataFrame:
    """
    Run Granger causality on STL remainders.
    Tests:
      1. maithon → panchet  (tandem operation signal)
      2. maithon → durgapur (upstream → downstream)
      3. anthro  → climate  (residual → climate prediction, should be ZERO)
      4. climate → anthro   (spurious climate → anthro, should be ZERO)
    Test 3 & 4 are null checks: if significant, attribution is contaminated.
    """
    print("\n[3/5] Granger causality tests (STL remainders, max lag=4)...")
    print("  ⚠ POWER WARNING: S1 era = ~82 months → ~70 after STL → ~42 effective df")
    print("    at lag=4. Severely underpowered (ideal n≥100). p<0.10 = 'suggestive'")
    print("    only. Report in Methods: 'Granger tests are indicative, not conclusive,")
    print("    owing to the 82-month S1 observation window.'")

    # NOTE: Panchet EXCLUDED — data is physically invalid (inverted seasonal cycle:
    # peak Apr, trough Aug-Sep, opposite of monsoon reservoir; AV model gives 34×
    # design capacity at max area). Including Panchet would invalidate this test.
    # D-021 confirmed: Panchet excluded from all quantitative claims.
    tests = [
        ('maithon',  'durgapur', 'Maithon → Durgapur (upstream→downstream ops)'),
        ('anthro',   'climate',  'ΔS_anthro → ΔS_climate (NULL CHECK — should be p>0.05)'),
        ('climate',  'anthro',   'ΔS_climate → ΔS_anthro (NULL CHECK — should be p>0.05)'),
    ]

    all_results = []
    for cause_name, effect_name, label in tests:
        if cause_name not in remainders or effect_name not in remainders:
            print(f"  SKIP: {label} — series not available")
            continue
        cause  = remainders[cause_name]
        effect = remainders[effect_name]
        result = granger_test(cause, effect, maxlag=MAX_LAG)
        result['cause']  = cause_name
        result['effect'] = effect_name
        result['label']  = label
        all_results.append(result)

        # Report min p-value across lags
        min_p  = result['p_value'].min()
        best_lag = result.loc[result['p_value'].idxmin(), 'lag']
        sig    = '✓ SIGNIFICANT' if min_p < 0.05 else ('~ MARGINAL' if min_p < 0.10 else '✗ ns')
        print(f"\n  {label}")
        print(f"    Best p={min_p:.4f} at lag={best_lag}  [{sig}]")
        for _, row in result.iterrows():
            bar = '█' * int((1 - row.p_value) * 20) if not np.isnan(row.p_value) else ''
            print(f"    lag={int(row.lag)}: p={row.p_value:.4f}  F={row.F_stat:.2f}  {bar}")

    return pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════
# STEP 4: HMM operational regime detection
# ═══════════════════════════════════════════════════════════════════

def fit_hmm(anthro_series: pd.Series) -> pd.DataFrame:
    """
    Fit 2-state Gaussian HMM to ΔS_anthro.
    States: DRAWDOWN (negative anomaly — releases, irrigation) vs
            NORMAL (near-zero or positive — conservation / monsoon filling).
    3-state was rejected: CONSERVATION (+0.015 BCM) and FILLING (+0.035 BCM)
    differ by only 0.020 BCM < model RMSE (0.097 BCM) → indistinguishable.
    Returns DataFrame with state assignments.
    """
    print(f"\n[4/5] HMM regime detection (n_states={HMM_STATES})...")

    if not HMM_AVAILABLE:
        print("  SKIPPED — hmmlearn not installed.")
        print("  Install: uv add hmmlearn")
        return pd.DataFrame()

    s = anthro_series.dropna().values.reshape(-1, 1)
    if len(s) < HMM_STATES * 5:
        print(f"  SKIPPED — too few rows ({len(s)} < {HMM_STATES*5})")
        return pd.DataFrame()

    model = hmm.GaussianHMM(n_components=HMM_STATES,
                             covariance_type='full',
                             n_iter=1000,
                             random_state=RANDOM_STATE)
    model.fit(s)
    states = model.predict(s)

    # Label states by emission mean (2-state: DRAWDOWN vs NORMAL)
    means = model.means_.flatten()
    order = np.argsort(means)  # ascending: most-negative → most-positive
    label_map = {order[0]: 'DRAWDOWN',  # most negative = drawdown / release
                 order[1]: 'NORMAL'}    # most positive = conservation / filling

    df = pd.DataFrame({
        'date':         anthro_series.dropna().index,
        'delta_S_anthro': s.flatten(),
        'state_id':     states,
        'state_label':  [label_map[s] for s in states],
    }).set_index('date')

    print(f"  HMM converged: {model.monitor_.converged}")
    print(f"  State means: {sorted(means)}")
    for lbl in ['DRAWDOWN', 'NORMAL']:
        n = (df.state_label == lbl).sum()
        pct = 100 * n / len(df)
        print(f"    {lbl:12s}: {n:3d} months ({pct:.1f}%)")

    return df


# ═══════════════════════════════════════════════════════════════════
# STEP 5: Figures
# ═══════════════════════════════════════════════════════════════════

def plot_stl_decompositions(series: dict, remainders: dict, out_path: Path):
    """Fig 6a: STL decomposition for Maithon + Panchet."""
    res_list = [r for r in ['maithon', 'panchet', 'durgapur'] if r in series]
    fig, axes = plt.subplots(len(res_list), 2, figsize=(14, 4*len(res_list)))
    if len(res_list) == 1:
        axes = axes.reshape(1, -1)

    colors = {'maithon': '#1f77b4', 'panchet': '#ff7f0e', 'durgapur': '#2ca02c'}

    for i, res in enumerate(res_list):
        c = colors.get(res, 'gray')
        # Raw
        axes[i, 0].plot(series[res].index, series[res].values, color=c, lw=1.2)
        axes[i, 0].axhline(0, color='gray', lw=0.5, ls='--')
        axes[i, 0].set_title(f'{res.capitalize()} — raw ΔS', fontsize=10)
        axes[i, 0].set_ylabel('BCM', fontsize=9)

        # STL remainder
        if res in remainders:
            axes[i, 1].plot(remainders[res].index, remainders[res].values,
                            color=c, lw=1.0, alpha=0.8)
            axes[i, 1].axhline(0, color='gray', lw=0.5, ls='--')
            axes[i, 1].set_title(f'{res.capitalize()} — STL remainder', fontsize=10)
            axes[i, 1].set_ylabel('BCM', fontsize=9)

    plt.suptitle('STL Decomposition — Seasonal + Trend Removed\n'
                 'Remainders used for Granger causality tests', fontsize=11, y=1.01)
    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


def plot_granger_pvalues(granger_df: pd.DataFrame, out_path: Path):
    """Fig 6b: Granger p-values across lags as heatmap."""
    if granger_df.empty:
        return

    pivot_labels = granger_df['label'].unique()
    fig, ax = plt.subplots(figsize=(10, len(pivot_labels) * 1.2 + 1))

    pv_matrix = granger_df.pivot_table(index='label', columns='lag', values='p_value')
    pv_matrix = pv_matrix.fillna(1.0)

    im = ax.imshow(pv_matrix.values, aspect='auto', cmap='RdYlGn_r',
                   vmin=0, vmax=0.2)
    ax.set_xticks(range(MAX_LAG))
    ax.set_xticklabels([f'Lag {i+1}' for i in range(MAX_LAG)], fontsize=9)
    ax.set_yticks(range(len(pivot_labels)))
    ax.set_yticklabels([l[:45] for l in pv_matrix.index], fontsize=8)

    for i in range(len(pv_matrix.index)):
        for j in range(MAX_LAG):
            v = pv_matrix.values[i, j]
            txt = f'{v:.3f}'
            color = 'white' if v < 0.08 else 'black'
            ax.text(j, i, txt, ha='center', va='center', fontsize=8, color=color)

    plt.colorbar(im, ax=ax, label='p-value (green=significant)')
    ax.axhline(1.5, color='black', lw=1.5, ls='--')  # separator after operational tests
    ax.set_title('Granger Causality p-values (STL remainders)\n'
                 'Green = significant (p<0.05), Red = not significant', fontsize=10)
    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


def plot_hmm_states(hmm_df: pd.DataFrame, out_path: Path):
    """Fig 7: HMM state sequence over time."""
    if hmm_df.empty:
        print(f"  SKIPPED (HMM not run): {out_path}")
        return

    color_map = {'DRAWDOWN': '#d62728', 'NORMAL': '#2ca02c'}
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 6), sharex=True)

    # ΔS_anthro
    ax1.plot(hmm_df.index, hmm_df.delta_S_anthro, color='black', lw=1.0, label='ΔS_anthro')
    ax1.axhline(0, color='gray', lw=0.5)
    ax1.set_ylabel('ΔS_anthro (BCM)', fontsize=10)
    ax1.set_title('Anthropogenic Storage Anomaly with HMM Operational Regimes', fontsize=11)
    ax1.legend(fontsize=9)

    # State colours
    for lbl, col in color_map.items():
        mask = hmm_df.state_label == lbl
        ax2.bar(hmm_df.index[mask], np.ones(mask.sum()),
                color=col, alpha=0.7, width=25, label=lbl)
    ax2.set_ylabel('Operational State', fontsize=10)
    ax2.set_yticks([])
    ax2.legend(fontsize=9)
    ax2.set_xlabel('Date', fontsize=10)

    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


# ═══════════════════════════════════════════════════════════════════
# STEP 4b: CCM — Convergent Cross Mapping (Fix 2 + Simplex E)
# ═══════════════════════════════════════════════════════════════════

def find_optimal_E(series: np.ndarray, name: str,
                   max_E: int = 8, Tp: int = 1) -> int:
    """
    Simplex projection to find optimal embedding dimension E.
    Standard practice: run pyEDM.EmbedDimension before CCM.
    Without this, any E choice is arbitrary and methodologically indefensible.

    Returns the E that maximises leave-one-out prediction skill (rho).
    Falls back to E=2 if pyEDM fails (logged as warning).
    """
    if not CCM_AVAILABLE:
        return 2

    n = len(series)
    df = pd.DataFrame({'time': range(1, n + 1), 'x': series})
    try:
        out = pyEDM.EmbedDimension(
            dataFrame=df,
            columns='x',
            target='x',
            maxE=max_E,
            Tp=Tp,
            lib=f'1 {n//2}',      # train on first half
            pred=f'{n//2+1} {n}',  # predict second half
            showPlot=False
        )
        best_E = int(out.loc[out['rho'].idxmax(), 'E'])
        best_rho = out['rho'].max()
        print(f"    Simplex E [{name}]: optimal E={best_E} (ρ={best_rho:.3f})")
        return best_E
    except Exception as e:
        print(f"    Simplex E [{name}]: FAILED ({e}) — defaulting to E=2")
        return 2

def run_ccm(remainders: dict) -> pd.DataFrame:
    """
    Fix 2: Convergent Cross Mapping (Sugihara et al. 2012, Science).
    Tests nonlinear causality between ΔS_anthro and ΔS_climate remainders.

    Critical rule (FATAL-5 in CLAUDE.md): ALL series must be STL-decomposed
    first to remove seasonal common driver. We receive remainders already decomposed.

    Surrogate validation (Theiler et al. 1992): real CCM rho must exceed
    95th percentile of 199 phase-randomised surrogates to be significant.

    n=48 rows → max library size = 48. CCM needs convergence (rho increasing
    with library size L) to claim causality. Power is low — results are
    indicative, not conclusive.
    """
    if not CCM_AVAILABLE:
        print("  [SKIP] pyEDM not installed")
        return pd.DataFrame()

    print(f"\n[3b/5] CCM causality tests (Fix 2 — Sugihara 2012)...")
    print(f"  ⚠ POWER WARNING: n=48, library sizes {min(CCM_LIB_SIZES)}–{max(CCM_LIB_SIZES)}")
    print(f"    Convergence with n<50 is unreliable. Results are indicative only.")

    ccm_pairs = [
        ('anthro',  'climate',  'ΔS_anthro xmap ΔS_climate (anthro causes climate?)'),
        ('climate', 'anthro',   'ΔS_climate xmap ΔS_anthro (climate causes anthro?)'),
        ('maithon', 'durgapur', 'Maithon xmap Durgapur (upstream → downstream?)'),
    ]

    results = []
    rng = np.random.default_rng(RANDOM_STATE)

    for cause_name, effect_name, label in ccm_pairs:
        if cause_name not in remainders or effect_name not in remainders:
            print(f"  SKIP: {label} — series not available")
            continue

        cause  = remainders[cause_name].dropna().values
        effect = remainders[effect_name].dropna().values

        # Align lengths
        min_len = min(len(cause), len(effect))
        cause   = cause[:min_len]
        effect  = effect[:min_len]

        if min_len < 20:
            print(f"  SKIP: {label} — n={min_len} < 20")
            continue

        lib_sizes = [s for s in CCM_LIB_SIZES if s <= min_len - 2]
        if not lib_sizes:
            print(f"  SKIP: {label} — not enough data for CCM")
            continue

        # Build pyEDM dataframe (indexed 1..n)
        df_ccm = pd.DataFrame({'time': range(1, min_len+1),
                               'cause': cause, 'effect': effect})

        # Simplex projection to find optimal E for CAUSE series (Sugihara best practice)
        print(f"\n  {label}")
        opt_E = find_optimal_E(cause, cause_name, max_E=min(8, min_len // 5))

        # Real CCM rho at each library size using validated E
        rhos_real = []
        for L in lib_sizes:
            try:
                out = pyEDM.CCM(dataFrame=df_ccm,
                                E=opt_E, tau=-1,
                                columns='cause', target='effect',
                                libSizes=f'{L} {L} 1',
                                sample=100, seed=RANDOM_STATE,
                                showPlot=False)
                rho_val = out['cause:effect'].mean() if 'cause:effect' in out.columns else np.nan
                rhos_real.append(rho_val)
            except Exception:
                rhos_real.append(np.nan)

        rhos_real = np.array(rhos_real)
        max_rho = np.nanmax(rhos_real) if not np.all(np.isnan(rhos_real)) else np.nan

        # Surrogate test at max library size
        max_L   = lib_sizes[-1]
        surr    = phase_randomise(cause, n=N_SURROGATES, rng=rng)
        surr_rhos = []
        for s in surr:
            df_s = pd.DataFrame({'time': range(1, min_len+1),
                                 'cause': s, 'effect': effect})
            try:
                out_s = pyEDM.CCM(dataFrame=df_s,
                                  E=opt_E, tau=-1,
                                  columns='cause', target='effect',
                                  libSizes=f'{max_L} {max_L} 1',
                                  sample=50, seed=RANDOM_STATE,
                                  showPlot=False)
                rho_s = out_s['cause:effect'].mean() if 'cause:effect' in out_s.columns else np.nan
                surr_rhos.append(rho_s)
            except Exception:
                surr_rhos.append(np.nan)

        surr_rhos  = np.array(surr_rhos)
        valid_surr = surr_rhos[~np.isnan(surr_rhos)]
        pct95      = np.percentile(valid_surr, 95) if len(valid_surr) > 10 else np.nan

        # Convergence: slope of rho vs library size (positive = converging)
        valid_mask = ~np.isnan(rhos_real)
        if valid_mask.sum() >= 3:
            slope = np.polyfit(np.array(lib_sizes)[valid_mask],
                               rhos_real[valid_mask], 1)[0]
        else:
            slope = np.nan

        sig   = 'SIGNIFICANT ✓' if (not np.isnan(max_rho) and not np.isnan(pct95)
                                     and max_rho > pct95) else 'ns'
        conv  = 'CONVERGING ✓' if (not np.isnan(slope) and slope > 0.002) else 'flat/diverging'

        print(f"\n  {label}")
        print(f"    Max rho={max_rho:.4f} at L={max_L} | 95th surr pct={pct95:.4f}")
        print(f"    Convergence slope: {slope:+.5f}  [{conv}]")
        print(f"    Surrogate test: {sig}")

        results.append({
            'pair': label,
            'cause': cause_name, 'effect': effect_name,
            'opt_E': opt_E,
            'max_rho': max_rho,
            'surr_pct95': pct95,
            'sig': sig,
            'conv_slope': slope,
            'converging': conv,
            'n': min_len,
        })

    if not results:
        return pd.DataFrame()

    ccm_df = pd.DataFrame(results)
    return ccm_df


def plot_ccm_convergence(remainders: dict, ccm_df: pd.DataFrame, out_path: Path):
    """Fig 6c: CCM convergence curves (rho vs library size)."""
    if not CCM_AVAILABLE or ccm_df.empty:
        return

    pairs = [('anthro', 'climate'), ('maithon', 'durgapur')]
    fig, axes = plt.subplots(1, len(pairs), figsize=(12, 4))
    if len(pairs) == 1:
        axes = [axes]

    rng = np.random.default_rng(RANDOM_STATE)
    colors = {'real': '#1f77b4', 'surr_median': '#ff7f0e'}

    for ax, (cause_name, effect_name) in zip(axes, pairs):
        if cause_name not in remainders or effect_name not in remainders:
            ax.set_visible(False)
            continue

        cause  = remainders[cause_name].dropna().values
        effect = remainders[effect_name].dropna().values
        min_len = min(len(cause), len(effect))
        cause   = cause[:min_len]
        effect  = effect[:min_len]

        lib_sizes = [s for s in CCM_LIB_SIZES if s <= min_len - 2]
        if not lib_sizes:
            ax.set_visible(False)
            continue

        df_ccm = pd.DataFrame({'time': range(1, min_len+1),
                               'cause': cause, 'effect': effect})

        # Look up validated optimal E from run_ccm results
        row = ccm_df[(ccm_df['cause'] == cause_name) & (ccm_df['effect'] == effect_name)]
        plot_E = int(row['opt_E'].iloc[0]) if not row.empty else 2

        rhos_real = []
        for L in lib_sizes:
            try:
                out = pyEDM.CCM(dataFrame=df_ccm, E=plot_E, tau=-1,
                                columns='cause', target='effect',
                                libSizes=f'{L} {L} 1',
                                sample=100, seed=RANDOM_STATE,
                                showPlot=False)
                rhos_real.append(out['cause:effect'].mean()
                                 if 'cause:effect' in out.columns else np.nan)
            except Exception:
                rhos_real.append(np.nan)

        # 3 representative surrogates for background
        for i in range(3):
            s = phase_randomise(cause, n=1, rng=rng)[0]
            df_s = pd.DataFrame({'time': range(1, min_len+1),
                                 'cause': s, 'effect': effect})
            rhos_s = []
            for L in lib_sizes:
                try:
                    out_s = pyEDM.CCM(dataFrame=df_s, E=plot_E, tau=-1,
                                      columns='cause', target='effect',
                                      libSizes=f'{L} {L} 1',
                                      sample=50, seed=RANDOM_STATE,
                                      showPlot=False)
                    rhos_s.append(out_s['cause:effect'].mean()
                                  if 'cause:effect' in out_s.columns else np.nan)
                except Exception:
                    rhos_s.append(np.nan)
            ax.plot(lib_sizes, rhos_s, color='gray', alpha=0.3, lw=0.7)

        ax.plot(lib_sizes, rhos_real, 'o-', color=colors['real'], lw=2,
                label='Real data', markersize=5)
        ax.axhline(0, color='black', lw=0.5, ls='--')
        ax.set_xlabel('Library size (L)', fontsize=9)
        ax.set_ylabel('CCM ρ', fontsize=9)
        ax.set_title(f'{cause_name} → {effect_name}\n(gray = surrogates)', fontsize=9)
        ax.legend(fontsize=8)
        ax.set_ylim(-0.5, 1.0)

    plt.suptitle('CCM Convergence Test (Sugihara 2012)\n'
                 'Converging ρ > surrogate 95th pct = causal signal', fontsize=10)
    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Stage 4: Causal Inference")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load
    series = load_series()

    # 2. STL decompose
    remainders = decompose_all(series)

    # 3. Granger tests
    granger_df = run_granger_tests(remainders)

    # 3b. CCM (Fix 2)
    ccm_df = run_ccm(remainders)

    # 4. HMM
    hmm_df = fit_hmm(series['anthro'])

    # 5. Figures
    print("\n[5/5] Generating figures...")
    plot_stl_decompositions(series, remainders, FIGURES_DIR / 'Fig6a_STL_decomp.png')
    if not granger_df.empty:
        plot_granger_pvalues(granger_df, FIGURES_DIR / 'Fig6b_Granger_pvalues.png')
    if CCM_AVAILABLE and not ccm_df.empty:
        plot_ccm_convergence(remainders, ccm_df, FIGURES_DIR / 'Fig6c_CCM_convergence.png')
    plot_hmm_states(hmm_df, FIGURES_DIR / 'Fig7_HMM_states.png')

    # Save results
    if not granger_df.empty:
        granger_df.to_csv(PROCESSED_DIR / 'granger_results.csv', index=False)
    if not ccm_df.empty:
        ccm_df.to_csv(PROCESSED_DIR / 'ccm_results.csv', index=False)
    if not hmm_df.empty:
        hmm_df.to_csv(PROCESSED_DIR / 'hmm_states.csv')

    # ─── SUMMARY ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STAGE 4 SUMMARY")
    print("=" * 60)

    if not granger_df.empty:
        print("\n  Granger results (minimum p-value per test):")
        for label in granger_df['label'].unique():
            sub = granger_df[granger_df['label'] == label]
            min_p = sub['p_value'].min()
            best_lag = sub.loc[sub['p_value'].idxmin(), 'lag']
            sig = '✓ p<0.05' if min_p < 0.05 else ('~ p<0.10' if min_p < 0.10 else '✗ ns')
            print(f"    [{sig}] {label[:50]}: p={min_p:.4f} (lag {int(best_lag)})")

        # Paper scope decision
        op_tests = granger_df[granger_df['cause'] == 'maithon']
        any_sig  = (op_tests['p_value'] < 0.05).any()
        any_marg = (op_tests['p_value'] < 0.10).any()
        null_ok  = (granger_df[granger_df['cause'] == 'anthro']['p_value'] > 0.05).all()

        print(f"\n  Operational Granger significant (p<0.05): {'YES ✓' if any_sig else 'NO'}")
        print(f"  Operational Granger marginal  (p<0.10): {'YES ~' if any_marg else 'NO'}")
        print(f"  Null checks pass (anthro⊄climate): {'YES ✓' if null_ok else 'NO ✗ — check attribution'}")

        print("\n  ── Paper Scope Decision ────────────────────────────")
        if any_sig and null_ok:
            print("  → Granger SIGNIFICANT. Target: Journal of Hydrology (Q1, IF 6.7)")
        elif any_marg and null_ok:
            print("  → Granger MARGINAL. Target: Remote Sensing of Environment (Q1)")
        else:
            print("  → Granger not significant. Target: Remote Sensing / JHRS")
            print("     Report as: 'No Granger causality detected — supports climate attribution'")

    if not ccm_df.empty:
        print("\n  CCM results (Fix 2 — nonlinear causality test):")
        for _, row in ccm_df.iterrows():
            print(f"    {row['pair'][:50]}")
            print(f"      ρ_max={row['max_rho']:.4f} | surr_95th={row['surr_pct95']:.4f}"
                  f" | {row['sig']} | {row['converging']}")
        any_ccm_sig = (ccm_df['sig'].str.contains('SIGNIFICANT')).any()
        if any_ccm_sig:
            print("\n  → CCM SIGNIFICANT — causal evidence found!")
            print("     Upgrade paper scope: Journal of Hydrology possible.")
        else:
            print("\n  → CCM not significant (expected with n=48).")
            print("     State as: 'CCM convergence test inconclusive owing to")
            print("     limited S1 observation window (n=48 months).'")

    print("\n  Figures:")
    for f in ['Fig6a_STL_decomp.png', 'Fig6b_Granger_pvalues.png',
              'Fig6c_CCM_convergence.png', 'Fig7_HMM_states.png']:
        print(f"    {'✓' if (FIGURES_DIR/f).exists() else '✗'} figures/{f}")

    print("\n  Saved: data/processed/granger_results.csv")
    print("  Next: uv run python src/06_fingerprint_taxonomy.py")
    print("=" * 60)


if __name__ == '__main__':
    main()
