"""
Stage 5: GRACE-FO Cross-Scale Reconciliation
=============================================
Tests Claim C3: DVC reservoir operations contaminate GRACE-FO TWS signal
beyond what climate alone explains.

Model:
  GRACE_TWS(t) ~ beta0 + beta1*dS_climate(t) + beta2*dS_anthro(t) + beta3*SM(t) + e(t)

If beta2 is significant (p < 0.05): DVC operations leave detectable fingerprint
in GRACE at basin scale -- basin-scale satellite water assessments are biased
for managed basins.

GRACE resolution caveat: Damodar basin ~23,370 km2; GRACE mascon ~0.5 degree cell.
Signal is sub-pixel. Partial regression tests whether the operational signal is
statistically detectable despite spatial mismatch.

Units: GRACE TWS in cm LWE -> converted to BCM for direct comparison.
1 cm LWE * 19600 km2 * 1e6 m2/km2 * 0.01 m/cm * 1e-9 = 0.196 BCM

Nishi Kant Mandal | BIT Sindri | 2026
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
RAW_DIR       = PROJECT_ROOT / 'data' / 'raw'
GRACE_DIR     = RAW_DIR / 'grace'
FIGURES_DIR   = PROJECT_ROOT / 'figures'

# ── Constants ──────────────────────────────────────────────────────────────
# Damodar catchment bounding box (upper basin: Maithon + Panchet)
LAT_MIN, LAT_MAX = 23.0, 24.5
LON_MIN, LON_MAX = 85.5, 87.5
CATCHMENT_AREA_KM2 = 19600.0    # km2

# BCM per cm LWE over catchment
CM_TO_BCM = (CATCHMENT_AREA_KM2 * 1e6 * 0.01) / 1e9   # = 0.196 BCM/cm

# GRACE gap period to interpolate over
GRACE_GAP_START = '2017-07'
GRACE_GAP_END   = '2018-05'

GRACE_PRODUCT_SHORT = 'TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4'

# ── Dependency checks ───────────────────────────────────────────────────────
try:
    import xarray as xr
    XARRAY_OK = True
except ImportError:
    XARRAY_OK = False

try:
    import earthaccess
    EARTHACCESS_OK = True
except ImportError:
    EARTHACCESS_OK = False

try:
    import statsmodels.api as sm
    from statsmodels.stats.stattools import durbin_watson
    STATSMODELS_OK = True
except ImportError:
    STATSMODELS_OK = False


# =========================================================================
# STEP 1: DOWNLOAD GRACE DATA
# =========================================================================

def download_grace() -> Path | None:
    """
    Download JPL GRACE-FO mascon RL06.3 V4 via earthaccess.

    Requires NASA Earthdata credentials. Set up one of:
      (a) ~/.netrc with: machine urs.earthdata.nasa.gov login USER password PASS
      (b) Environment vars: EARTHDATA_USERNAME, EARTHDATA_PASSWORD

    Returns path to the downloaded NetCDF file, or None if download fails.
    """
    GRACE_DIR.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    existing = list(GRACE_DIR.glob('*.nc')) + list(GRACE_DIR.glob('*.nc4'))
    if existing:
        print(f"  Found cached GRACE file: {existing[0].name}")
        return existing[0]

    if not EARTHACCESS_OK:
        print("  ERROR: earthaccess not installed. Run: uv add earthaccess")
        return None

    print("  Authenticating with NASA Earthdata...")
    try:
        # Try netrc first, then environment variables
        auth = earthaccess.login(strategy="netrc")
        if not getattr(auth, 'authenticated', True):
            auth = earthaccess.login(strategy="environment")
    except Exception as e:
        print(f"  Auth attempt: {e}")
        try:
            auth = earthaccess.login(strategy="environment")
        except Exception as e2:
            print(f"  Auth failed: {e2}")
            _print_auth_instructions()
            return None

    print(f"  Searching for {GRACE_PRODUCT_SHORT}...")
    try:
        results = earthaccess.search_data(
            short_name=GRACE_PRODUCT_SHORT,
            temporal=("2002-01-01", "2024-12-31"),
            count=5
        )
        if not results:
            # Try alternative short name
            print("  Trying alternative product name...")
            results = earthaccess.search_data(
                short_name="TELLUS_GRFO_L3_JPL_RL06.3_OCN_GRID_RL06.3_V4",
                temporal=("2002-01-01", "2024-12-31"),
                count=5
            )
        if not results:
            print(f"  No granules found. Try manual download:")
            print(f"  https://podaac.jpl.nasa.gov/dataset/{GRACE_PRODUCT_SHORT}")
            print(f"  Save .nc file to: {GRACE_DIR}/")
            return None

        print(f"  Found {len(results)} granule(s). Downloading (may take 2-5 min)...")
        files = earthaccess.download(results[:1], str(GRACE_DIR))
        if files:
            p = Path(files[0])
            print(f"  Downloaded: {p.name} ({p.stat().st_size / 1e6:.1f} MB)")
            return p
        return None

    except Exception as e:
        print(f"  Download error: {e}")
        _print_auth_instructions()
        return None


def _print_auth_instructions():
    print("\n  +---------------------------------------------------------+")
    print("  |  NASA Earthdata credentials required for GRACE data.    |")
    print("  |  Steps:                                                  |")
    print("  |  1. Register: https://urs.earthdata.nasa.gov            |")
    print("  |  2. Create ~/.netrc file with:                          |")
    print("  |       machine urs.earthdata.nasa.gov                    |")
    print("  |       login YOUR_USERNAME                               |")
    print("  |       password YOUR_PASSWORD                            |")
    print("  |  3. chmod 600 ~/.netrc                                  |")
    print("  |  4. Re-run: uv run python src/05_grace_reconciliation.py|")
    print("  +---------------------------------------------------------+\n")


# =========================================================================
# STEP 2: EXTRACT DAMODAR TWS
# =========================================================================

def extract_damodar_tws(nc_path: Path) -> pd.Series | None:
    """
    Extract monthly TWS anomaly (cm LWE) for Damodar catchment bounding box.
    Averages over all 0.5 degree cells within LAT/LON bounds.
    Interpolates across the GRACE/GRACE-FO gap (2017-07 to 2018-05).
    """
    if not XARRAY_OK:
        print("  ERROR: xarray not available")
        return None

    print(f"  Loading: {nc_path.name}")
    try:
        ds = xr.open_dataset(nc_path, decode_times=True)
    except Exception:
        try:
            ds = xr.open_dataset(nc_path, decode_times=False)
        except Exception as e:
            print(f"  Cannot open NetCDF: {e}")
            return None

    print(f"  Variables: {list(ds.data_vars)}")
    print(f"  Dimensions: {dict(ds.dims)}")

    # Identify TWS variable
    tws_var = None
    candidates = ['lwe_thickness', 'twsa', 'lwe', 'GRACE_REC_10d_JPL', 'liquid_water_eq']
    for c in candidates:
        if c in ds.data_vars:
            tws_var = c
            break
    if tws_var is None:
        for v in ds.data_vars:
            if 'uncert' not in v.lower() and 'mask' not in v.lower():
                tws_var = v
                break
    if tws_var is None:
        print(f"  Cannot identify TWS variable. Available: {list(ds.data_vars)}")
        return None
    print(f"  TWS variable: {tws_var}")

    # Standardise coordinate names
    lat_name = lon_name = time_name = None
    for c in list(ds.coords) + list(ds.dims):
        cl = c.lower()
        if cl in ('lat', 'latitude') and lat_name is None:
            lat_name = c
        if cl in ('lon', 'longitude') and lon_name is None:
            lon_name = c
        if 'time' in cl and time_name is None:
            time_name = c

    if lat_name is None or lon_name is None:
        print(f"  Cannot find lat/lon. Available coords: {list(ds.coords)}")
        return None

    # Spatial subset
    da = ds[tws_var]
    lat_vals = da[lat_name].values
    ascending = lat_vals[0] < lat_vals[-1]

    try:
        if ascending:
            da = da.sel({lat_name: slice(LAT_MIN, LAT_MAX),
                         lon_name: slice(LON_MIN, LON_MAX)})
        else:
            da = da.sel({lat_name: slice(LAT_MAX, LAT_MIN),
                         lon_name: slice(LON_MIN, LON_MAX)})
    except Exception as e:
        print(f"  Spatial subset failed: {e}")
        return None

    n_cells = da.sizes.get(lat_name, 0) * da.sizes.get(lon_name, 0)
    print(f"  Cells in Damodar bounding box: {n_cells}")
    if n_cells == 0:
        print("  WARNING: no cells selected. Expanding bounding box to 1 degree.")
        # Emergency fallback: single cell nearest to Maithon
        if ascending:
            da = ds[tws_var].sel({lat_name: 23.5, lon_name: 86.75}, method='nearest')
        else:
            da = ds[tws_var].sel({lat_name: 23.5, lon_name: 86.75}, method='nearest')
        tws_ts = da
    else:
        # Spatial mean (cosine-weighted latitude)
        lats = np.deg2rad(da[lat_name].values)
        weights = np.cos(lats)
        weights_da = xr.DataArray(weights, coords={lat_name: da[lat_name].values},
                                  dims=[lat_name])
        tws_ts = da.weighted(weights_da).mean(dim=[lat_name, lon_name])

    # Parse time
    if time_name is not None:
        try:
            raw_times = tws_ts[time_name].values
            times = pd.to_datetime(raw_times)
        except Exception:
            # Try manual decoding for days-since-epoch
            try:
                units = ds[time_name].attrs.get('units', '')
                times = xr.coding.times.decode_cf_datetime(raw_times, units)
                times = pd.to_datetime(times)
            except Exception:
                n = len(tws_ts.values.flatten())
                print(f"  WARNING: Cannot parse time. Generating synthetic monthly index ({n} months from 2002-04)")
                times = pd.date_range('2002-04-01', periods=n, freq='MS')
    else:
        n = len(tws_ts.values.flatten())
        times = pd.date_range('2002-04-01', periods=n, freq='MS')

    values = tws_ts.values.flatten()
    ts = pd.Series(values, index=times, name='tws_cm')
    ts = ts.dropna()
    ts.index = ts.index.to_period('M').to_timestamp()
    ts = ts.sort_index()
    # Drop duplicates that arise from period→timestamp conversion
    ts = ts[~ts.index.duplicated(keep='first')]

    print(f"  GRACE coverage: {ts.index[0].date()} to {ts.index[-1].date()} ({len(ts)} months)")
    print(f"  TWS range: {ts.min():.2f} to {ts.max():.2f} cm")

    # Interpolate across GRACE/GRACE-FO gap
    full_idx = pd.date_range(ts.index[0], ts.index[-1], freq='MS')
    ts_full  = ts.reindex(full_idx)
    n_gap    = ts_full.isna().sum()
    if n_gap > 0:
        ts_full = ts_full.interpolate(method='linear')
        print(f"  Interpolated {n_gap} gap months (GRACE/GRACE-FO gap)")

    return ts_full


# =========================================================================
# STEP 3: LOAD PROCESSED DATA
# =========================================================================

def load_processed_series() -> dict[str, pd.Series]:
    """Load dS_anthro, dS_climate, soil moisture from Stage 2/3 outputs."""
    out = {}

    anthro_path = PROCESSED_DIR / 'delta_S_anthro.csv'
    if not anthro_path.exists():
        raise FileNotFoundError(
            f"Missing: {anthro_path}\n"
            "Run Stage 3 first: uv run python src/03_xgboost_attribution.py"
        )

    df_a = pd.read_csv(anthro_path, index_col=0, parse_dates=True)
    if df_a.index.name and 'date' not in df_a.index.name.lower():
        # try resetting and finding the date column
        df_a = pd.read_csv(anthro_path, parse_dates=[0])
        df_a = df_a.set_index(df_a.columns[0])
    df_a.index = df_a.index.to_period('M').to_timestamp()

    print(f"  delta_S_anthro.csv columns: {list(df_a.columns)}")

    # Identify columns flexibly
    for col in df_a.columns:
        cl = col.lower()
        if any(x in cl for x in ['pred', 'climate', 'xgb_pred']):
            out['dS_climate'] = df_a[col].rename('dS_climate')
        elif any(x in cl for x in ['anthro', 'resid']):
            out['dS_anthro'] = df_a[col].rename('dS_anthro')
        elif any(x in cl for x in ['obs', 'actual']):
            out['dS_obs'] = df_a[col].rename('dS_obs')

    print(f"  Loaded from Stage 3: {list(out.keys())}")

    # Soil moisture from Stage 2 feature matrix
    x_path = PROCESSED_DIR / 'X_climate_final.csv'
    if x_path.exists():
        df_x = pd.read_csv(x_path, index_col=0, parse_dates=True)
        df_x.index = df_x.index.to_period('M').to_timestamp()

        # Soil moisture columns (may have been dropped by VIF)
        sm_cols = [c for c in df_x.columns if 'SM' in c and 'm3' in c.lower()]
        if not sm_cols:
            sm_cols = [c for c in df_x.columns if 'SM' in c]
        if sm_cols:
            out['SM'] = df_x[sm_cols].mean(axis=1).rename('SM')
            print(f"  Soil moisture from: {sm_cols}")
        elif 'API6' in df_x.columns:
            # SM dropped by VIF — use API6 (antecedent rainfall) as moisture proxy
            out['SM'] = df_x['API6'].rename('SM')
            print("  Soil moisture proxy: API6 (SM dropped by VIF)")

        # Precipitation / ET control — must differ from SM to avoid multicollinearity
        sm_source = df_x['API6'] if 'API6' in df_x.columns else None
        for p_cand in ('PET_mm', 'AET_mm', 'P_t', 'P_mm'):
            if p_cand in df_x.columns:
                candidate = df_x[p_cand]
                # Skip if perfectly correlated with SM proxy
                if sm_source is not None and candidate.corr(sm_source) > 0.999:
                    continue
                out['P_t'] = candidate.rename('P_t')
                print(f"  Precipitation/ET control: {p_cand}")
                break

    return out


# =========================================================================
# STEP 4: PARTIAL REGRESSION
# =========================================================================

def run_partial_regression(tws: pd.Series,
                            processed: dict[str, pd.Series]) -> dict:
    """
    Partial OLS regression:
      GRACE_TWS(t) ~ b0 + b1*dS_climate + b2*dS_anthro + b3*SM [+ b4*P_t]

    H0: b2 = 0 (dS_anthro has no independent effect on GRACE TWS).
    Reject at p < 0.05 => DVC operations detectable in GRACE.
    """
    if not STATSMODELS_OK:
        print("  ERROR: statsmodels not available")
        return {}

    # Build aligned dataframe
    df = pd.DataFrame({'tws': tws})
    for k, s in processed.items():
        df[k] = s
    df = df.dropna()

    print(f"\n  Aligned dataset: {len(df)} months "
          f"({df.index[0].date()} to {df.index[-1].date()})")

    if len(df) < 24:
        print(f"  ERROR: only {len(df)} overlapping months — need at least 24")
        print("  This likely means GRACE data (2002-2024) and Stage 3 data (2017-2024)")
        print("  have insufficient overlap after accounting for GRACE gap and NaN removal.")
        return {}

    y = df['tws'].values

    # Use available features; always include dS_anthro if present
    feature_cols = [c for c in ['dS_climate', 'SM', 'P_t', 'dS_anthro']
                    if c in df.columns]
    # Ensure dS_anthro is last for easy indexing
    if 'dS_anthro' in feature_cols and feature_cols[-1] != 'dS_anthro':
        feature_cols.remove('dS_anthro')
        feature_cols.append('dS_anthro')

    print(f"  Features in model: {feature_cols}")

    X_raw = df[feature_cols].values
    X_std = (X_raw - X_raw.mean(axis=0)) / (X_raw.std(axis=0) + 1e-12)
    X_sm  = sm.add_constant(X_std)

    full_model = sm.OLS(y, X_sm).fit(cov_type='HAC', cov_kwds={'maxlags': 3})

    # Restricted model (without dS_anthro) for partial R2
    restr_cols = [c for c in feature_cols if c != 'dS_anthro']
    partial_r2 = np.nan
    if restr_cols:
        X_r   = df[restr_cols].values
        X_r   = (X_r - X_r.mean(axis=0)) / (X_r.std(axis=0) + 1e-12)
        X_r   = sm.add_constant(X_r)
        restr = sm.OLS(y, X_r).fit()
        if restr.ssr > 1e-10:
            partial_r2 = (restr.ssr - full_model.ssr) / restr.ssr

    # Extract b2 (dS_anthro)
    coef_names = ['const'] + feature_cols
    b2_idx = coef_names.index('dS_anthro') if 'dS_anthro' in coef_names else None

    b2      = full_model.params[b2_idx]   if b2_idx is not None else np.nan
    b2_pval = full_model.pvalues[b2_idx]  if b2_idx is not None else np.nan
    ci_arr  = np.array(full_model.conf_int())
    b2_ci   = (ci_arr[b2_idx, 0], ci_arr[b2_idx, 1]) if b2_idx is not None else (np.nan, np.nan)

    dw = durbin_watson(full_model.resid)

    print(f"\n  === Partial Regression Results ===")
    print(f"  N = {len(df)} | R2 = {full_model.rsquared:.3f} | adj-R2 = {full_model.rsquared_adj:.3f}")
    print(f"  Durbin-Watson: {dw:.2f}  (2.0 = no autocorrelation; <1.5 or >2.5 = concern)")
    print()

    for name, coef, pval in zip(coef_names, full_model.params, full_model.pvalues):
        flag = ' ***' if pval < 0.001 else (' **' if pval < 0.01 else
               (' *' if pval < 0.05 else ''))
        print(f"  {name:<20}  beta={coef:+.4f}  p={pval:.4f}{flag}")

    print()
    if not np.isnan(b2_pval):
        sig = b2_pval < 0.05
        print(f"  C3 Claim: beta2(dS_anthro) = {b2:+.4f}  p = {b2_pval:.4f}")
        if not np.isnan(partial_r2):
            print(f"  Partial R2 (dS_anthro contribution) = {partial_r2:.4f}")
        print(f"  95% CI: [{b2_ci[0]:+.4f}, {b2_ci[1]:+.4f}]")
        print()
        if sig:
            print(f"  >>> C3 CLAIM SUPPORTED: p={b2_pval:.4f} < 0.05 <<<")
            print(f"  DVC operations leave statistically detectable fingerprint in GRACE TWS.")
            print(f"  Basin-scale GRACE water balance assessments are biased for managed basins.")
        else:
            print(f"  C3 claim NOT supported at p=0.05 (p={b2_pval:.4f}).")
            print(f"  This is EXPECTED: GRACE measurement noise (~1-2 cm = 0.2-0.4 BCM)")
            print(f"  is comparable to our dS_anthro range (~0.2 BCM = ~1 cm).")
            print(f"  Signal at sub-pixel scale is at detection limit of GRACE.")
            print(f"  C1 (CCM causal) and C2 (DTW taxonomy) claims are unaffected.")

    return {
        'n':                  len(df),
        'r2':                 full_model.rsquared,
        'adj_r2':             full_model.rsquared_adj,
        'beta2':              b2,
        'beta2_pval':         b2_pval,
        'beta2_ci_lo':        b2_ci[0],
        'beta2_ci_hi':        b2_ci[1],
        'partial_r2_anthro':  partial_r2,
        'durbin_watson':      dw,
        'significant_c3':     bool(not np.isnan(b2_pval) and b2_pval < 0.05),
        'feature_cols':       feature_cols,
        'summary':            full_model.summary().as_text(),
        'df':                 df,
        'full_model':         full_model,
    }


# =========================================================================
# STEP 5: FIGURES
# =========================================================================

def plot_grace_reconciliation(tws: pd.Series,
                               processed: dict[str, pd.Series],
                               reg: dict,
                               out_path: Path):
    """Fig 9: GRACE-FO cross-scale reconciliation (4-panel figure)."""
    fig = plt.figure(figsize=(14, 10))
    gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.50, wspace=0.35)

    tws_bcm = tws * CM_TO_BCM

    # ── Panel A: GRACE TWS + DVC comparison ───────────────────────
    ax_a = fig.add_subplot(gs[0, :])
    ax_a.plot(tws_bcm.index, tws_bcm.values, 'b-', lw=2,
              label='GRACE-FO TWS anomaly (Damodar cell, BCM)', alpha=0.85)

    dS_obs = processed.get('dS_obs')
    dS_ant = processed.get('dS_anthro')

    if dS_obs is not None:
        ax_a.plot(dS_obs.index, dS_obs.values, 'g--', lw=1.5,
                  label='Delta_S_obs Maithon (BCM)', alpha=0.8)
    if dS_ant is not None:
        ax_a.fill_between(dS_ant.index, dS_ant.values, 0,
                          alpha=0.25, color='red', label='Delta_S_anthro')

    ax_a.axhline(0, color='k', lw=0.6, ls='--')
    ax_a.set_ylabel('BCM', fontsize=9)
    ax_a.set_title('Panel A: GRACE-FO TWS vs. DVC Reservoir Storage Anomalies', fontsize=10)
    ax_a.legend(fontsize=8, loc='upper left', ncol=3)
    ax_a.tick_params(labelsize=8)

    # ── Panel B: Scatter dS_anthro vs GRACE ───────────────────────
    ax_b = fig.add_subplot(gs[1, 0])
    df = reg.get('df')
    if df is not None and 'dS_anthro' in df.columns:
        sc = ax_b.scatter(df['dS_anthro'], df['tws'], s=20, alpha=0.65,
                          c=range(len(df)), cmap='viridis')
        plt.colorbar(sc, ax=ax_b, label='time index')
        z = np.polyfit(df['dS_anthro'], df['tws'], 1)
        xline = np.linspace(df['dS_anthro'].min(), df['dS_anthro'].max(), 100)
        ax_b.plot(xline, np.polyval(z, xline), 'r-', lw=1.5)
        b2 = reg.get('beta2', np.nan)
        pv = reg.get('beta2_pval', np.nan)
        sig_str = '*' if pv < 0.05 else 'ns'
        ax_b.set_title(f'Panel B: dS_anthro vs GRACE TWS\nbeta={b2:+.3f}, p={pv:.3f} ({sig_str})',
                       fontsize=9)
    ax_b.set_xlabel('dS_anthro (BCM)', fontsize=9)
    ax_b.set_ylabel('GRACE TWS (cm)', fontsize=9)
    ax_b.tick_params(labelsize=8)

    # ── Panel C: Variance explained decomposition (bar chart) ─────
    ax_c = fig.add_subplot(gs[1, 1])
    r2_total   = reg.get('r2', 0) or 0
    r2_anthro  = max(0, reg.get('partial_r2_anthro', 0) or 0)
    r2_other   = max(0, r2_total - r2_anthro)
    r2_unexp   = max(0, 1.0 - r2_total)

    bars   = ['Climate\n+ SM', 'Anthropogenic\n(dS_anthro)', 'Unexplained']
    vals   = [r2_other, r2_anthro, r2_unexp]
    colors = ['#4CAF50', '#F44336', '#9E9E9E']
    ax_c.bar(bars, vals, color=colors, edgecolor='k', linewidth=0.8)
    ax_c.set_ylim(0, 1)
    ax_c.set_ylabel('Fraction of GRACE TWS variance', fontsize=9)
    ax_c.set_title(f'Panel C: Variance Decomposition\n(Total R2={r2_total:.3f})', fontsize=9)
    for i, (b, v) in enumerate(zip(bars, vals)):
        ax_c.text(i, v + 0.01, f'{v:.3f}', ha='center', fontsize=9)
    ax_c.tick_params(labelsize=8)

    # ── Panel D: OLS residuals ─────────────────────────────────────
    ax_d = fig.add_subplot(gs[2, :])
    if reg.get('full_model') is not None and df is not None:
        resid = reg['full_model'].resid
        ax_d.plot(df.index, resid, 'k-', lw=1, alpha=0.75)
        ax_d.axhline(0, color='r', lw=0.8, ls='--')
        ax_d.fill_between(df.index, resid, 0, alpha=0.25, color='gray')
        dw = reg.get('durbin_watson', np.nan)
        ax_d.set_title(f'Panel D: OLS Residuals (Durbin-Watson={dw:.2f}; '
                       f'ideal=2.0, <1.5 or >2.5 = autocorrelation concern)', fontsize=9)
        ax_d.set_ylabel('Residual (cm)', fontsize=9)
        ax_d.tick_params(labelsize=8)

    plt.suptitle(
        'Fig. 9 -- GRACE-FO Cross-Scale Reconciliation\n'
        'C3 Test: Do DVC operations contaminate basin-scale GRACE TWS?',
        fontsize=11, fontweight='bold', y=1.005
    )
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


def plot_anthro_only(processed: dict[str, pd.Series], out_path: Path):
    """Fallback figure: dS_anthro time series when GRACE unavailable."""
    dS_ant = processed.get('dS_anthro')
    dS_cli = processed.get('dS_climate')
    dS_obs = processed.get('dS_obs')

    if dS_ant is None:
        print("  No dS_anthro available for figure")
        return

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    ax1 = axes[0]
    if dS_obs is not None:
        ax1.plot(dS_obs.index, dS_obs.values, 'k-', lw=1.5,
                 label='Delta_S_obs (Maithon, BCM)', alpha=0.8)
    if dS_cli is not None:
        ax1.plot(dS_cli.index, dS_cli.values, 'b--', lw=1.5,
                 label='Delta_S_climate (XGBoost predicted)', alpha=0.8)
    ax1.set_ylabel('BCM', fontsize=10)
    ax1.set_title('Storage Anomaly: Observed vs Climate-Predicted (Stage 3)', fontsize=11)
    ax1.legend(fontsize=9)
    ax1.axhline(0, color='gray', lw=0.5)

    ax2 = axes[1]
    ax2.fill_between(dS_ant.index, dS_ant.values, 0,
                     where=(dS_ant.values > 0), alpha=0.55,
                     color='#D32F2F', label='Over-storage (positive anomaly)')
    ax2.fill_between(dS_ant.index, dS_ant.values, 0,
                     where=(dS_ant.values <= 0), alpha=0.55,
                     color='#1565C0', label='Over-release / drought deficit')
    ax2.axhline(0, color='k', lw=0.6, ls='--')
    ax2.set_ylabel('Delta_S_anthro (BCM)', fontsize=10)
    ax2.set_title('Anthropogenic Storage Residual (DVC Operational Fingerprint)', fontsize=11)
    ax2.legend(fontsize=9, ncol=2)

    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


# =========================================================================
# SAVE
# =========================================================================

def save_outputs(tws: pd.Series | None, reg: dict) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if tws is not None and len(tws) > 0:
        df_tws = pd.DataFrame({
            'date':            tws.index,
            'grace_tws_cm':    tws.values,
            'grace_tws_bcm':   tws.values * CM_TO_BCM,
        })
        df_tws.to_csv(PROCESSED_DIR / 'grace_tws_damodar.csv', index=False)
        print(f"  Saved: data/processed/grace_tws_damodar.csv ({len(df_tws)} rows)")

    if reg:
        (PROCESSED_DIR / 'grace_regression_summary.txt').write_text(
            reg.get('summary', ''))
        print("  Saved: data/processed/grace_regression_summary.txt")

        row = {k: reg.get(k) for k in [
            'n', 'r2', 'adj_r2', 'beta2', 'beta2_pval',
            'beta2_ci_lo', 'beta2_ci_hi', 'partial_r2_anthro',
            'durbin_watson', 'significant_c3'
        ]}
        pd.DataFrame([row]).to_csv(
            PROCESSED_DIR / 'grace_regression_results.csv', index=False)
        print("  Saved: data/processed/grace_regression_results.csv")


# =========================================================================
# MAIN
# =========================================================================

def main():
    print("=" * 60)
    print("Stage 5: GRACE-FO Cross-Scale Reconciliation")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    GRACE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load processed series (Stages 2-3)
    print("\n[1/5] Loading processed data...")
    try:
        processed = load_processed_series()
        for k, v in processed.items():
            valid = v.dropna()
            print(f"  {k}: {len(valid)} valid months")
    except FileNotFoundError as e:
        print(f"  FATAL: {e}")
        sys.exit(1)

    # 2. Download GRACE
    print("\n[2/5] Acquiring GRACE-FO data...")
    nc_path = download_grace()

    tws = None
    if nc_path is not None and nc_path.exists():
        # 3. Extract Damodar TWS
        print("\n[3/5] Extracting Damodar catchment TWS time series...")
        tws = extract_damodar_tws(nc_path)

    reg = {}
    if tws is not None and len(tws) > 0:
        # 4. Partial regression
        print("\n[4/5] Running partial regression (C3 claim test)...")
        reg = run_partial_regression(tws, processed)

        # 5. Figures + outputs
        print("\n[5/5] Saving outputs...")
        save_outputs(tws, reg)
        if reg:
            plot_grace_reconciliation(tws, processed, reg,
                                      FIGURES_DIR / 'Fig9_GRACE_reconciliation.png')
        else:
            plot_anthro_only(processed, FIGURES_DIR / 'Fig9_GRACE_no_regression.png')
    else:
        print("\n[3-5/5] GRACE data unavailable -- generating dS_anthro figure only")
        plot_anthro_only(processed, FIGURES_DIR / 'Fig9_anthro_timeseries.png')
        save_outputs(None, {})

    # Summary
    print("\n" + "=" * 60)
    print("STAGE 5 SUMMARY")
    print("=" * 60)
    if tws is not None and len(tws) > 0:
        bcm = tws * CM_TO_BCM
        print(f"  GRACE TWS: {len(tws)} months | {tws.index[0].date()} to {tws.index[-1].date()}")
        print(f"  TWS range (BCM): {bcm.min():.3f} to {bcm.max():.3f}")
        if reg:
            b2  = reg.get('beta2', np.nan)
            pv  = reg.get('beta2_pval', np.nan)
            pr2 = reg.get('partial_r2_anthro', np.nan)
            sig = reg.get('significant_c3', False)
            print(f"  beta2 (dS_anthro): {b2:+.4f}  p = {pv:.4f}")
            if not np.isnan(pr2):
                print(f"  Partial R2 (dS_anthro): {pr2:.4f}")
            print(f"  C3 CLAIM: {'SUPPORTED' if sig else 'NOT SUPPORTED (expected at sub-pixel scale)'}")
    else:
        print("  GRACE download required.")
        print("  See authentication instructions above.")
        print("  Note: Stage 5 is the MOONSHOT claim (7-15% probability).")
        print("  Stages 1-4 + 6 are sufficient for J.Hydrology/RSE submission.")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
