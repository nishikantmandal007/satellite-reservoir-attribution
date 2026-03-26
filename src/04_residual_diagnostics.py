"""
Tasks A, B, C: Residual Diagnostics + Fold-Level CV Metrics + Regime-Stratified NSE
==================================================================================
Run: cd /home/stark007/dvc-research && uv run python src/04_residual_diagnostics.py
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf, pacf

# ── Paths ──
PROCESSED = Path('data/processed')
FIGURES   = Path('figures')

# ── Metric functions (same as 03_xgboost_attribution.py) ──
def nse(obs, pred):
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    if len(o) < 3:
        return np.nan
    denom = np.sum((o - np.mean(o))**2)
    if denom < 1e-12:
        return np.nan
    return float(1.0 - np.sum((o - p)**2) / denom)

def kge(obs, pred):
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    if len(o) < 3:
        return np.nan
    if np.std(o) < 1e-12 or np.std(p) < 1e-12:
        return np.nan
    r = np.corrcoef(o, p)[0, 1]
    beta  = np.mean(p) / np.mean(o) if abs(np.mean(o)) > 1e-12 else np.nan
    gamma = (np.std(p)/np.mean(p)) / (np.std(o)/np.mean(o)) \
            if (abs(np.mean(p)) > 1e-12 and abs(np.mean(o)) > 1e-12) else np.nan
    if np.isnan(beta) or np.isnan(gamma):
        return np.nan
    return float(1 - np.sqrt((r-1)**2 + (beta-1)**2 + (gamma-1)**2))

def pbias(obs, pred):
    obs, pred = np.asarray(obs), np.asarray(pred)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    std_obs = np.std(o)
    return 100 * np.mean(np.abs(o - p)) / std_obs if std_obs > 1e-12 else np.nan


# ══════════════════════════════════════════════════════════════════════
# TASK A: Residual Diagnostics — ACF/PACF + Ljung-Box
# ══════════════════════════════════════════════════════════════════════
print("=" * 70)
print("TASK A: Residual Diagnostics (ACF/PACF + Ljung-Box)")
print("=" * 70)

df_anthro = pd.read_csv(PROCESSED / 'delta_S_anthro.csv', index_col=0, parse_dates=True)
df_anthro = df_anthro[df_anthro['reservoir'] == 'maithon']

# Get rows where delta_S_anthro_bcm is not NaN (i.e., where model produced predictions)
ds_anthro = df_anthro['delta_S_anthro_bcm'].dropna()
print(f"  delta_S_anthro series: {len(ds_anthro)} non-NaN values")
print(f"  Date range: {ds_anthro.index.min().date()} to {ds_anthro.index.max().date()}")
print(f"  Mean: {ds_anthro.mean():.4f} BCM | Std: {ds_anthro.std():.4f} BCM")

# ACF and PACF (up to lag 12)
n_lags = min(12, len(ds_anthro) // 2 - 1)
acf_vals, acf_ci = acf(ds_anthro.values, nlags=n_lags, alpha=0.05)
pacf_vals, pacf_ci = pacf(ds_anthro.values, nlags=n_lags, alpha=0.05)

# Ljung-Box test at lags 1, 3, 6, 12
test_lags = [l for l in [1, 3, 6, 12] if l <= n_lags]
lb_result = acorr_ljungbox(ds_anthro.values, lags=test_lags, return_df=True)
print(f"\n  Ljung-Box Test Results:")
print(f"  {'Lag':>4s}  {'LB Stat':>10s}  {'p-value':>10s}  {'Significant?':>14s}")
print(f"  {'----':>4s}  {'----------':>10s}  {'----------':>10s}  {'--------------':>14s}")

sig_lags = []
for lag_val in test_lags:
    row = lb_result.loc[lag_val]
    sig = row['lb_pvalue'] < 0.05
    if sig:
        sig_lags.append((lag_val, row['lb_pvalue']))
    print(f"  {lag_val:>4d}  {row['lb_stat']:>10.4f}  {row['lb_pvalue']:>10.4f}  {'*** YES ***' if sig else 'no':>14s}")

if sig_lags:
    for lag_val, pval in sig_lags:
        print(f"\n  >>> delta_S_anthro is autocorrelated at lag {lag_val} (p={pval:.4f})")
else:
    print(f"\n  >>> No significant autocorrelation detected at tested lags")

# Plot ACF and PACF
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
ci_level = 1.96 / np.sqrt(len(ds_anthro))

# ACF plot
ax = axes[0]
ax.bar(range(n_lags + 1), acf_vals, width=0.3, color='steelblue', edgecolor='navy', zorder=3)
ax.axhline(ci_level, ls='--', color='red', alpha=0.7, label=f'95% CI (±{ci_level:.3f})')
ax.axhline(-ci_level, ls='--', color='red', alpha=0.7)
ax.axhline(0, color='black', lw=0.5)
ax.set_xlabel('Lag (months)')
ax.set_ylabel('ACF')
ax.set_title('Autocorrelation Function — $\\Delta S_{anthro}$')
ax.set_xlim(-0.5, n_lags + 0.5)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3)

# PACF plot
ax = axes[1]
ax.bar(range(n_lags + 1), pacf_vals, width=0.3, color='darkorange', edgecolor='saddlebrown', zorder=3)
ax.axhline(ci_level, ls='--', color='red', alpha=0.7, label=f'95% CI (±{ci_level:.3f})')
ax.axhline(-ci_level, ls='--', color='red', alpha=0.7)
ax.axhline(0, color='black', lw=0.5)
ax.set_xlabel('Lag (months)')
ax.set_ylabel('PACF')
ax.set_title('Partial Autocorrelation Function — $\\Delta S_{anthro}$')
ax.set_xlim(-0.5, n_lags + 0.5)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3)

fig.suptitle('Residual (Anthropogenic) Signal Diagnostics — Maithon Reservoir', fontsize=13, y=1.02)
fig.tight_layout()
fig.savefig(FIGURES / 'FigS3_residual_acf.png', dpi=300, bbox_inches='tight')
print(f"\n  Figure saved: figures/FigS3_residual_acf.png")


# ══════════════════════════════════════════════════════════════════════
# TASK B: Fold-Level CV Metrics (re-derived from delta_S_anthro.csv)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TASK B: Fold-Level CV Metrics")
print("=" * 70)

# The existing xgb_cv_results.csv already has fold-level metrics.
# But we also re-derive from the delta_S_anthro data to cross-check.
# The CV structure: expanding window, min_train=24, step=12, S1 era (2017-03+)

# Load existing CV results for comparison
cv_existing = pd.read_csv(PROCESSED / 'xgb_cv_results.csv')
print(f"\n  Existing fold-level metrics from xgb_cv_results.csv:")
print(f"  {'Fold':>4s} | {'Train_n':>7s} | {'Test_n':>6s} | {'NSE_all':>8s} | {'NSE_unclip':>10s} | {'KGE':>8s} | {'PBIAS':>8s}")
print(f"  {'----':>4s} | {'-------':>7s} | {'------':>6s} | {'--------':>8s} | {'----------':>10s} | {'--------':>8s} | {'--------':>8s}")

for _, row in cv_existing.iterrows():
    print(f"  {int(row['fold']):>4d} | {int(row['train_months']):>7d} | {int(row['test_months']):>6d} | "
          f"{row['NSE']:>8.4f} | {row['NSE_unclipped']:>10.4f} | {row['KGE']:>8.4f} | {row['PBIAS']:>8.2f}")

# Compute aggregate stats
print(f"\n  Aggregate (mean +/- std across folds):")
print(f"    NSE (all):       {cv_existing['NSE'].mean():.4f} +/- {cv_existing['NSE'].std():.4f}")
print(f"    NSE (unclipped): {cv_existing['NSE_unclipped'].mean():.4f} +/- {cv_existing['NSE_unclipped'].std():.4f}")
print(f"    KGE (all):       {cv_existing['KGE'].mean():.4f} +/- {cv_existing['KGE'].std():.4f}")
print(f"    PBIAS (all):     {cv_existing['PBIAS'].mean():.2f} +/- {cv_existing['PBIAS'].std():.2f}")

# Now re-derive per-fold metrics from the actual predictions in delta_S_anthro.csv
# We know the fold boundaries from the CV results
print(f"\n  Re-deriving from delta_S_anthro.csv to cross-check...")

# Rows with predictions (delta_S_climate_bcm not NaN)
df_pred = df_anthro.dropna(subset=['delta_S_climate_bcm']).copy()
obs_vals = df_pred['delta_S_obs_bcm'].values
pred_vals = df_pred['delta_S_climate_bcm'].values
print(f"  Total rows with predictions: {len(df_pred)}")

# Reconstruct fold assignments from test_start/test_end in cv_existing
DEAD_FLOOR = -0.183
fold_records = []
for _, frow in cv_existing.iterrows():
    ts = pd.Timestamp(frow['test_start'])
    te = pd.Timestamp(frow['test_end'])
    fold_mask = (df_pred.index >= ts) & (df_pred.index <= te)
    fold_df = df_pred[fold_mask]

    o = fold_df['delta_S_obs_bcm'].values
    p = fold_df['delta_S_climate_bcm'].values

    # unclipped
    uc_mask = o > DEAD_FLOOR

    fold_records.append({
        'Fold': int(frow['fold']),
        'Train_n': int(frow['train_months']),
        'Test_n': len(fold_df),
        'NSE_all': nse(o, p),
        'NSE_unclipped': nse(o[uc_mask], p[uc_mask]) if uc_mask.sum() >= 3 else np.nan,
        'KGE': kge(o, p),
        'KGE_unclipped': kge(o[uc_mask], p[uc_mask]) if uc_mask.sum() >= 3 else np.nan,
        'PBIAS': pbias(o, p),
        'PBIAS_unclipped': pbias(o[uc_mask], p[uc_mask]) if uc_mask.sum() >= 3 else np.nan,
        'n_clipped': int((~uc_mask).sum()),
        'test_start': str(frow['test_start']),
        'test_end': str(frow['test_end']),
    })

fold_df_out = pd.DataFrame(fold_records)
fold_df_out.to_csv(PROCESSED / 'fold_level_metrics.csv', index=False)
print(f"\n  Re-derived fold metrics (from delta_S_anthro.csv):")
print(f"  {'Fold':>4s} | {'Train_n':>7s} | {'Test_n':>6s} | {'NSE_all':>8s} | {'NSE_unclip':>10s} | {'KGE':>8s} | {'PBIAS':>8s} | {'Clipped':>7s}")
print(f"  {'----':>4s} | {'-------':>7s} | {'------':>6s} | {'--------':>8s} | {'----------':>10s} | {'--------':>8s} | {'--------':>8s} | {'-------':>7s}")
for _, row in fold_df_out.iterrows():
    nse_uc_str = f"{row['NSE_unclipped']:>10.4f}" if not np.isnan(row['NSE_unclipped']) else '       N/A'
    print(f"  {int(row['Fold']):>4d} | {int(row['Train_n']):>7d} | {int(row['Test_n']):>6d} | "
          f"{row['NSE_all']:>8.4f} | {nse_uc_str} | {row['KGE']:>8.4f} | {row['PBIAS']:>8.2f} | {int(row['n_clipped']):>7d}")

print(f"\n  Saved: data/processed/fold_level_metrics.csv")


# ══════════════════════════════════════════════════════════════════════
# TASK C: Regime-Stratified NSE (Filling vs Drawdown)
# ══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("TASK C: Regime-Stratified NSE (Filling vs Drawdown)")
print("=" * 70)

# Use only test rows (rows with predictions) and unclipped only
uc_mask_all = obs_vals > DEAD_FLOOR
obs_uc = obs_vals[uc_mask_all]
pred_uc = pred_vals[uc_mask_all]

filling_mask = obs_uc > 0
drawdown_mask = obs_uc < 0

n_filling = filling_mask.sum()
n_drawdown = drawdown_mask.sum()
n_total = len(obs_uc)

print(f"\n  Using {n_total} unclipped test rows (dead-storage floor = {DEAD_FLOOR} BCM)")
print(f"    Filling months (dS_obs > 0):   {n_filling}")
print(f"    Drawdown months (dS_obs < 0):  {n_drawdown}")
print(f"    Near-zero (dS_obs == 0):       {n_total - n_filling - n_drawdown}")

nse_filling  = nse(obs_uc[filling_mask], pred_uc[filling_mask])
nse_drawdown = nse(obs_uc[drawdown_mask], pred_uc[drawdown_mask])
kge_filling  = kge(obs_uc[filling_mask], pred_uc[filling_mask])
kge_drawdown = kge(obs_uc[drawdown_mask], pred_uc[drawdown_mask])

print(f"\n  {'Regime':<15s} | {'N':>4s} | {'NSE':>8s} | {'KGE':>8s}")
print(f"  {'-'*15:<15s} | {'----':>4s} | {'--------':>8s} | {'--------':>8s}")
print(f"  {'Filling':<15s} | {n_filling:>4d} | {nse_filling:>8.4f} | {kge_filling:>8.4f}")
print(f"  {'Drawdown':<15s} | {n_drawdown:>4d} | {nse_drawdown:>8.4f} | {kge_drawdown:>8.4f}")
print(f"  {'All unclipped':<15s} | {n_total:>4d} | {nse(obs_uc, pred_uc):>8.4f} | {kge(obs_uc, pred_uc):>8.4f}")

# Interpretation
print(f"\n  Interpretation:")
if nse_filling > nse_drawdown:
    print(f"    Model performs BETTER during filling ({nse_filling:.3f}) than drawdown ({nse_drawdown:.3f}).")
    print(f"    Drawdown residuals are larger = anthropogenic signal stronger during releases.")
else:
    print(f"    Model performs BETTER during drawdown ({nse_drawdown:.3f}) than filling ({nse_filling:.3f}).")
    print(f"    Filling residuals are larger = anthropogenic signal stronger during storage buildup.")

print(f"\n  Done. All three tasks complete.")
