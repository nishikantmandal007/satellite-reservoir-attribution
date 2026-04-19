"""
TASK A: Deseasonalized GRACE Regression
========================================
Tests whether the R²=0.869 in GRACE partial regression reflects genuine
anthropogenic signal or is inflated by shared monsoon seasonality.

Method:
  1. Load GRACE TWS and 4 predictors (dS_climate, dS_anthro, API6/SM, PET)
  2. Remove 12-month climatological mean from each variable
  3. Re-run partial OLS with HAC (Newey-West, maxlags=3)
  4. Compare original vs deseasonalized R², beta2, p-value

Nishi Kant Mandal | BIT Sindri | 2026
"""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson

PROJECT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT / 'data' / 'processed'


def deseasonalize(s: pd.Series) -> pd.Series:
    """Remove 12-month climatological mean (mean for each calendar month)."""
    monthly_clim = s.groupby(s.index.month).transform('mean')
    return s - monthly_clim


def main():
    print("=" * 70)
    print("TASK A: Deseasonalized GRACE Regression")
    print("=" * 70)

    # ── Load GRACE TWS ────────────────────────────────────────────────
    grace = pd.read_csv(PROCESSED / 'grace_tws_damodar.csv', parse_dates=['date'])
    grace = grace.set_index('date')
    grace.index = grace.index.to_period('M').to_timestamp()
    tws = grace['grace_tws_bcm'].rename('tws')

    # ── Load dS_anthro / dS_climate ───────────────────────────────────
    anthro = pd.read_csv(PROCESSED / 'delta_S_anthro.csv', index_col=0, parse_dates=True)
    anthro.index = anthro.index.to_period('M').to_timestamp()
    # Only maithon rows with actual climate/anthro values
    anthro = anthro[anthro['reservoir'] == 'maithon'].copy()
    anthro = anthro.dropna(subset=['delta_S_climate_bcm', 'delta_S_anthro_bcm'])

    dS_climate = anthro['delta_S_climate_bcm'].rename('dS_climate')
    dS_anthro = anthro['delta_S_anthro_bcm'].rename('dS_anthro')

    # ── Load SM (API6) and PET from feature matrix ────────────────────
    xf = pd.read_csv(PROCESSED / 'X_climate_final.csv', index_col=0, parse_dates=True)
    xf.index = xf.index.to_period('M').to_timestamp()
    api6 = xf['API6'].rename('SM') if 'API6' in xf.columns else None
    pet = xf['PET_mm'].rename('P_t') if 'PET_mm' in xf.columns else None

    # ── Align all series ──────────────────────────────────────────────
    df = pd.DataFrame({'tws': tws})
    df['dS_climate'] = dS_climate
    df['dS_anthro'] = dS_anthro
    if api6 is not None:
        df['SM'] = api6
    if pet is not None:
        df['P_t'] = pet
    df = df.dropna()

    feature_cols = [c for c in ['dS_climate', 'SM', 'P_t', 'dS_anthro'] if c in df.columns]
    # Ensure dS_anthro is last
    if 'dS_anthro' in feature_cols:
        feature_cols.remove('dS_anthro')
        feature_cols.append('dS_anthro')

    print(f"\n  Aligned months: {len(df)} ({df.index[0].date()} to {df.index[-1].date()})")
    print(f"  Features: {feature_cols}")

    if len(df) < 12:
        print("  ERROR: fewer than 12 aligned months. Cannot deseasonalize.")
        return

    # ══════════════════════════════════════════════════════════════════
    # A. Original (seasonal) regression — reproduce baseline
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "-" * 60)
    print("  A) ORIGINAL (seasonal) regression — baseline check")
    print("-" * 60)
    res_orig = _run_regression(df, feature_cols, label="Original")

    # ══════════════════════════════════════════════════════════════════
    # B. Deseasonalized regression — the real test
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "-" * 60)
    print("  B) DESEASONALIZED regression — monsoon signal removed")
    print("-" * 60)
    df_deseas = df.copy()
    for col in ['tws'] + feature_cols:
        df_deseas[col] = deseasonalize(df_deseas[col])

    # Verify deseasonalization worked
    for col in ['tws'] + feature_cols:
        month_means = df_deseas[col].groupby(df_deseas.index.month).mean()
        max_residual = month_means.abs().max()
        print(f"    {col}: max monthly-mean after deseas = {max_residual:.6f}")

    res_deseas = _run_regression(df_deseas, feature_cols, label="Deseasonalized")

    # ══════════════════════════════════════════════════════════════════
    # C. Summary comparison
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("  COMPARISON: Original vs Deseasonalized")
    print("=" * 70)
    print(f"  {'Metric':<25} {'Original':>12} {'Deseasonalized':>16}")
    print(f"  {'-'*25} {'-'*12} {'-'*16}")
    for key, fmt in [('r2', '.4f'), ('adj_r2', '.4f'), ('beta2', '+.4f'),
                     ('beta2_pval', '.6f'), ('beta2_ci_lo', '+.4f'),
                     ('beta2_ci_hi', '+.4f'), ('partial_r2', '.4f'),
                     ('durbin_watson', '.3f')]:
        v1 = res_orig.get(key, np.nan)
        v2 = res_deseas.get(key, np.nan)
        s1 = f"{v1:{fmt}}"
        s2 = f"{v2:{fmt}}"
        print(f"  {key:<25} {s1:>12} {s2:>16}")

    sig_orig = res_orig.get('beta2_pval', 1.0) < 0.05
    sig_deseas = res_deseas.get('beta2_pval', 1.0) < 0.05

    print()
    if sig_deseas:
        print("  >>> beta2 REMAINS SIGNIFICANT after deseasonalization <<<")
        print("  GRACE claim is STRENGTHENED: anthropogenic signal is NOT just shared seasonality.")
    else:
        if sig_orig:
            print("  >>> beta2 LOSES SIGNIFICANCE after deseasonalization <<<")
            print("  GRACE R²=0.869 was INFLATED by shared monsoon seasonality.")
            print("  Must disclose: C3 claim is driven by seasonal co-movement, not genuine attribution.")
        else:
            print("  beta2 was not significant in either model.")

    # ── Save results ──────────────────────────────────────────────────
    out = pd.DataFrame([
        {**{'model': 'original'}, **res_orig},
        {**{'model': 'deseasonalized'}, **res_deseas},
    ])
    out_path = PROCESSED / 'grace_deseasonalized_results.csv'
    out.to_csv(out_path, index=False)
    print(f"\n  Saved: {out_path}")


def _run_regression(df, feature_cols, label=""):
    """Run OLS with HAC and report results."""
    y = df['tws'].values
    X_raw = df[feature_cols].values
    X_std = (X_raw - X_raw.mean(axis=0)) / (X_raw.std(axis=0) + 1e-12)
    X = sm.add_constant(X_std)

    model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 3})

    coef_names = ['const'] + feature_cols
    b2_idx = coef_names.index('dS_anthro') if 'dS_anthro' in coef_names else None

    b2 = model.params[b2_idx] if b2_idx is not None else np.nan
    b2_pval = model.pvalues[b2_idx] if b2_idx is not None else np.nan
    ci = np.array(model.conf_int())
    b2_ci = (ci[b2_idx, 0], ci[b2_idx, 1]) if b2_idx is not None else (np.nan, np.nan)
    dw = durbin_watson(model.resid)

    # Partial R2
    restr_cols = [c for c in feature_cols if c != 'dS_anthro']
    partial_r2 = np.nan
    if restr_cols:
        X_r = df[restr_cols].values
        X_r = (X_r - X_r.mean(axis=0)) / (X_r.std(axis=0) + 1e-12)
        X_r = sm.add_constant(X_r)
        restr = sm.OLS(y, X_r).fit()
        if restr.ssr > 1e-10:
            partial_r2 = (restr.ssr - model.ssr) / restr.ssr

    print(f"\n  {label}: N={len(df)} | R2={model.rsquared:.4f} | adj-R2={model.rsquared_adj:.4f}")
    print(f"  Durbin-Watson: {dw:.3f}")
    for name, coef, pval in zip(coef_names, model.params, model.pvalues):
        flag = ' ***' if pval < 0.001 else (' **' if pval < 0.01 else (' *' if pval < 0.05 else ''))
        print(f"    {name:<15} beta={coef:+.4f}  p={pval:.4f}{flag}")
    print(f"  beta2 (dS_anthro) = {b2:+.4f}, p = {b2_pval:.6f}, 95% CI [{b2_ci[0]:+.4f}, {b2_ci[1]:+.4f}]")
    print(f"  Partial R2 (anthro) = {partial_r2:.4f}")

    return {
        'n': len(df), 'r2': model.rsquared, 'adj_r2': model.rsquared_adj,
        'beta2': b2, 'beta2_pval': b2_pval,
        'beta2_ci_lo': b2_ci[0], 'beta2_ci_hi': b2_ci[1],
        'partial_r2': partial_r2, 'durbin_watson': dw,
    }


if __name__ == '__main__':
    main()
