"""
FIX B2 — GRACE regression refit in RAW units (+ standardized side-by-side)
==========================================================================
Defect (RECOVERY_ROADMAP.md §1.1 B2, verified 2026-07-11):
    src/05_grace_reconciliation.py:418 z-standardized predictors before OLS,
    so beta2 = 3.8424 was cm TWS per 1 SD of dS_anthro — NOT cm per BCM.
    analysis_grace_deseasonalized.py additionally used a BCM response
    (grace_tws_bcm), so its beta2 = 0.7531 was BCM per SD. The manuscript
    compared both to a mass-only theoretical sensitivity (~4.28 cm/BCM),
    an accidental comparison of incompatible quantities.

This script refits every variant in RAW units with explicit unit chains,
reports standardized coefficients side-by-side, and verifies the exact
back-transformation identity on the fitted models:

    beta_raw[j] = beta_std[j] / sd(x_j)
    b0_raw      = b0_std - sum_j beta_std[j] * mu_j / sd_j

Outputs (v1 files are NEVER overwritten):
    data/processed/grace_regression_results_v2.csv
    data/processed/grace_regression_summary_v2.txt

Run: uv run python src/fix_b2_grace_raw_units.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'

# Basin-area candidates for the theoretical mass-only sensitivity.
# ONE authoritative value will come from a HydroBASINS Lv8 polygon (Phase 3);
# until then both published figures are shown, explicitly labelled.
AREA_BASIN_KM2     = 23370.0   # Damodar basin, full extent (FINDINGS F-023)
AREA_CATCHMENT_KM2 = 19600.0   # upper-basin constant used by src/05 v1


def cm_per_bcm(area_km2: float) -> float:
    """Mass-only conversion: 1 BCM spread over area_km2 -> cm LWE."""
    return 1e5 / area_km2          # 1e9 m3 / (area*1e6 m2) * 100 cm/m


def load_aligned_frame() -> pd.DataFrame:
    """Rebuild the v1 aligned design frame from surviving processed CSVs."""
    grace = pd.read_csv(PROCESSED_DIR / 'grace_tws_damodar.csv', parse_dates=['date'])
    grace = grace.set_index('date')
    grace.index = grace.index.to_period('M').to_timestamp()
    tws_cm = grace['grace_tws_cm'].rename('tws_cm')

    anthro = pd.read_csv(PROCESSED_DIR / 'delta_S_anthro.csv',
                         index_col=0, parse_dates=True)
    anthro.index = anthro.index.to_period('M').to_timestamp()
    anthro = anthro[anthro['reservoir'] == 'maithon'].copy()
    anthro = anthro.dropna(subset=['delta_S_climate_bcm', 'delta_S_anthro_bcm'])

    xf = pd.read_csv(PROCESSED_DIR / 'X_climate_final.csv',
                     index_col=0, parse_dates=True)
    xf.index = xf.index.to_period('M').to_timestamp()

    df = pd.DataFrame({'tws_cm': tws_cm})
    df['dS_climate'] = anthro['delta_S_climate_bcm']       # BCM
    df['dS_anthro']  = anthro['delta_S_anthro_bcm']        # BCM
    df['SM']         = xf['API6'] if 'API6' in xf.columns else np.nan    # mm (moisture proxy, v1 logic)
    df['PET']        = xf['PET_mm'] if 'PET_mm' in xf.columns else np.nan  # mm
    df = df.dropna()
    return df


def deseasonalize(s: pd.Series) -> pd.Series:
    """Remove 12-month climatological mean (same method as v1 Task A)."""
    return s - s.groupby(s.index.month).transform('mean')


def fit_ols_pair(df: pd.DataFrame, feature_cols: list[str]) -> dict:
    """
    Fit the SAME model twice: raw-unit X and standardized-X.
    Returns both coefficient sets plus the back-transformation audit.
    Response is always tws_cm; predictors dS_* are BCM, SM/PET are mm.
    """
    y = df['tws_cm'].values
    X_raw = df[feature_cols].values
    mu, sd = X_raw.mean(axis=0), X_raw.std(axis=0)

    # --- raw-unit fit (HAC Newey-West maxlags=3, identical to v1 spec) ---
    m_raw = sm.OLS(y, sm.add_constant(X_raw)).fit(cov_type='HAC',
                                                  cov_kwds={'maxlags': 3})
    # --- standardized-X fit (replicates v1 exactly; y NOT standardized) ---
    X_std = (X_raw - mu) / (sd + 1e-12)
    m_std = sm.OLS(y, sm.add_constant(X_std)).fit(cov_type='HAC',
                                                  cov_kwds={'maxlags': 3})

    names = ['const'] + feature_cols
    i_ant = names.index('dS_anthro')

    ci_r = np.array(m_raw.conf_int()); ci_s = np.array(m_std.conf_int())

    # --- back-transformation audit on ALL coefficients ---
    b_std = m_std.params[1:]
    b0_back = m_std.params[0] - np.sum(b_std * mu / sd)
    b_back  = b_std / sd
    dev_coef = np.max(np.abs(m_raw.params[1:] - b_back))
    dev_int  = abs(m_raw.params[0] - b0_back)

    # --- partial R^2 for dS_anthro (restricted model without it) ---
    restr_cols = [c for c in feature_cols if c != 'dS_anthro']
    partial_r2_raw = partial_r2_std = np.nan
    if restr_cols:
        r_raw = sm.OLS(y, sm.add_constant(df[restr_cols].values)).fit()
        r_std = sm.OLS(y, sm.add_constant((df[restr_cols].values - df[restr_cols].values.mean(0)) /
                                          (df[restr_cols].values.std(0) + 1e-12))).fit()
        if r_raw.ssr > 1e-10:
            partial_r2_raw = (r_raw.ssr - m_raw.ssr) / r_raw.ssr
            partial_r2_std = (r_std.ssr - m_std.ssr) / r_std.ssr

    return {
        'n': len(df),
        'feature_cols': feature_cols,
        'names': names,
        'raw': {
            'model': m_raw, 'params': dict(zip(names, m_raw.params)),
            'pvals': dict(zip(names, m_raw.pvalues)),
            'ci': {n_: (ci_r[k, 0], ci_r[k, 1]) for k, n_ in enumerate(names)},
            'r2': m_raw.rsquared, 'adj_r2': m_raw.rsquared_adj,
            'dw': durbin_watson(m_raw.resid), 'partial_r2': partial_r2_raw,
        },
        'std': {
            'model': m_std, 'params': dict(zip(names, m_std.params)),
            'pvals': dict(zip(names, m_std.pvalues)),
            'ci': {n_: (ci_s[k, 0], ci_s[k, 1]) for k, n_ in enumerate(names)},
            'r2': m_std.rsquared, 'adj_r2': m_std.rsquared_adj,
            'dw': durbin_watson(m_std.resid), 'partial_r2': partial_r2_std,
        },
        'audit': {
            'max_abs_dev_coef': float(dev_coef),
            'abs_dev_intercept': float(dev_int),
            'partial_r2_param_invariance_dev':
                float(abs(partial_r2_raw - partial_r2_std))
                if np.isfinite(partial_r2_raw) else np.nan,
        },
        'sd': dict(zip(feature_cols, sd)),
        'mean': dict(zip(feature_cols, mu)),
    }


def report(label: str, res: dict, lines: list[str]) -> None:
    """Human-readable report block with explicit unit chains."""
    raw, std, aud = res['raw'], res['std'], res['audit']
    b2_raw, b2_std = raw['params']['dS_anthro'], std['params']['dS_anthro']
    p_raw = raw['pvals']['dS_anthro']
    ci_raw = raw['ci']['dS_anthro']

    out = []
    out.append(f"\n{'=' * 72}")
    out.append(f"MODEL: {label}")
    out.append(f"{'=' * 72}")
    out.append(f"Unit chain: y = GRACE TWS [cm LWE]; dS_climate/dS_anthro [BCM];")
    out.append(f"            SM = API6 antecedent rainfall [mm]; PET [mm]")
    out.append(f"N = {res['n']} months | R2(raw) = {raw['r2']:.4f} | adj-R2 = {raw['adj_r2']:.4f}"
               f" | DW = {raw['dw']:.3f}")
    out.append("")
    out.append(f"  {'term':<14} {'beta_raw':>12} {'p(HAC)':>9}   {'beta_std':>12}")
    for n_ in res['names']:
        br = raw['params'][n_]; pr = raw['pvals'][n_]; bs = std['params'][n_]
        flag = ' ***' if pr < 0.001 else (' **' if pr < 0.01 else (' *' if pr < 0.05 else ''))
        out.append(f"  {n_:<14} {br:+12.4f} {pr:9.4f}{flag:<4} {bs:+12.4f}")
    out.append("")
    out.append(f"  beta2 (RAW units)  = {b2_raw:+.4f}  cm TWS per BCM of dS_anthro")
    out.append(f"    95% CI (HAC)     = [{ci_raw[0]:+.4f}, {ci_raw[1]:+.4f}] cm/BCM")
    out.append(f"    p-value          = {p_raw:.6f}")
    out.append(f"  beta2 (STD units)  = {b2_std:+.4f}  cm TWS per 1 SD of dS_anthro"
               f"   [SD = {res['sd']['dS_anthro']:.4f} BCM]")
    out.append(f"  Partial R2 (anthro) = {raw['partial_r2']:.4f}")

    th_basin, th_catch = cm_per_bcm(AREA_BASIN_KM2), cm_per_bcm(AREA_CATCHMENT_KM2)
    out.append("")
    out.append(f"  Mass-only theoretical sensitivity:")
    out.append(f"    Damodar basin polygon figure ({AREA_BASIN_KM2:,.0f} km2): "
               f"{th_basin:.3f} cm/BCM  ->  observed/theory = {b2_raw / th_basin:5.2f}x")
    out.append(f"    Upper-catchment constant    ({AREA_CATCHMENT_KM2:,.0f} km2): "
               f"{th_catch:.3f} cm/BCM  ->  observed/theory = {b2_raw / th_catch:5.2f}x")
    out.append(f"    NOTE: authoritative area awaits HydroBASINS Lv8 polygon (Phase 3).")
    if abs(b2_raw) > 2 * th_catch:
        out.append(f"    INTERPRETATION: |beta2| exceeds 2x the mass-only ceiling -> the")
        out.append(f"    coefficient cannot represent reservoir mass alone; it absorbs")
        out.append(f"    basin-wide water variations correlated with operations.")
    out.append("")
    out.append(f"  Back-transform audit (identity must hold for OLS point estimates):")
    out.append(f"    max |beta_raw - beta_std/sd| = {aud['max_abs_dev_coef']:.3e}")
    out.append(f"    |b0_raw - back-transformed|  = {aud['abs_dev_intercept']:.3e}")
    ok = aud['max_abs_dev_coef'] < 1e-8 and aud['abs_dev_intercept'] < 1e-8
    out.append(f"    ACCEPT (<1e-8): {'PASS ✓' if ok else 'FAIL ✗'}")

    text = "\n".join(out)
    print(text)
    lines.append(text)


def main() -> int:
    print("=" * 72)
    print("FIX B2 — GRACE regressions in RAW units (v2)")
    print("=" * 72)

    df = load_aligned_frame()
    print(f"\nAligned months: {len(df)} ({df.index[0].date()} to {df.index[-1].date()})")
    if len(df) < 24:
        print("ERROR: <24 aligned months — cannot fit.")
        return 1

    feature_cols = ['dS_climate', 'SM', 'PET', 'dS_anthro']
    lines: list[str] = []

    results = {}

    # ── Variant 1: seasonal (replicates v1 main regression sample) ────────
    results['seasonal'] = fit_ols_pair(df, feature_cols)
    report("SEASONAL (as-published sample)", results['seasonal'], lines)

    # ── Variant 2: deseasonalized (mirrors analysis_grace_deseasonalized) ─
    df_d = df.copy()
    for col in ['tws_cm'] + feature_cols:
        df_d[col] = deseasonalize(df_d[col])
    max_resid = max(abs(df_d[c].groupby(df_d.index.month).mean()).max()
                    for c in ['tws_cm'] + feature_cols)
    print(f"\n[deseasonalization check] max |monthly-mean| after removal = {max_resid:.2e}")
    results['deseasonalized'] = fit_ols_pair(df_d, feature_cols)
    report("DESEASONALIZED (12-month climatology removed)", results['deseasonalized'], lines)

    # ── Save v2 outputs (never overwrite v1) ──────────────────────────────
    rows = []
    for variant, res in results.items():
        for kind in ('raw', 'std'):
            side = res[kind]
            rows.append({
                'model': f'{variant}_{kind}',
                'coefficient_units': ('cm_TWS_per_BCM_dSanthro' if kind == 'raw'
                                      else 'cm_TWS_per_SD_dSanthro'),
                'n': res['n'],
                'r2': side['r2'], 'adj_r2': side['adj_r2'],
                'durbin_watson': side['dw'],
                'beta1_dSclimate': side['params']['dS_climate'],
                'beta1_pval': side['pvals']['dS_climate'],
                'beta2_dSanthro': side['params']['dS_anthro'],
                'beta2_pval': side['pvals']['dS_anthro'],
                'beta2_ci_lo': side['ci']['dS_anthro'][0],
                'beta2_ci_hi': side['ci']['dS_anthro'][1],
                'partial_r2_anthro': side['partial_r2'],
                'sd_dSanthro_bcm': res['sd']['dS_anthro'],
                'theory_cmPerBCM_basin23370': cm_per_bcm(AREA_BASIN_KM2),
                'observed_over_theory_basin': side['params']['dS_anthro'] / cm_per_bcm(AREA_BASIN_KM2),
                'backtransform_max_dev': res['audit']['max_abs_dev_coef'],
            })
    out_csv = PROCESSED_DIR / 'grace_regression_results_v2.csv'
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    header = (
        "GRACE partial regression — CORRECTED UNITS (v2)\n"
        "Generated by src/fix_b2_grace_raw_units.py\n"
        "Response: GRACE-FO RL06.3 V4 mascon TWS anomaly [cm LWE],\n"
        "Damodar bounding box mean (85.5–87.5E, 23.0–24.5N).\n"
        "Predictors: dS_climate, dS_anthro [BCM]; SM=API6 [mm]; PET [mm].\n"
        "Covariance: HAC Newey-West maxlags=3.\n"
    )
    out_txt = PROCESSED_DIR / 'grace_regression_summary_v2.txt'
    out_txt.write_text(header + "\n" + "\n".join(lines) + "\n")
    print(f"Saved: {out_txt}")

    all_ok = all(r['audit']['max_abs_dev_coef'] < 1e-8 and
                 r['audit']['abs_dev_intercept'] < 1e-8 for r in results.values())
    print("\nFIX B2 STATUS:", "PASS ✓ — identities hold; v2 files written" if all_ok
          else "FAIL ✗ — investigate before proceeding")
    return 0 if all_ok else 2


if __name__ == '__main__':
    sys.exit(main())
