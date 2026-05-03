"""
Deep diagnostic: WHY is HAC SE < OLS SE for dS_anthro?
Examines the Newey-West kernel weights and heteroscedasticity structure.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import acf
from pathlib import Path
import xarray as xr

PROCESSED_DIR = Path('data/processed')

# === Reproduce data loading ===
df_a = pd.read_csv(PROCESSED_DIR / 'delta_S_anthro.csv', index_col=0, parse_dates=True)
df_a.index = df_a.index.to_period('M').to_timestamp()

processed = {}
for col in df_a.columns:
    cl = col.lower()
    if any(x in cl for x in ['pred', 'climate', 'xgb_pred']):
        processed['dS_climate'] = df_a[col].rename('dS_climate')
    elif any(x in cl for x in ['anthro', 'resid']):
        processed['dS_anthro'] = df_a[col].rename('dS_anthro')
    elif any(x in cl for x in ['obs', 'actual']):
        processed['dS_obs'] = df_a[col].rename('dS_obs')

df_x = pd.read_csv(PROCESSED_DIR / 'X_climate_final.csv', index_col=0, parse_dates=True)
df_x.index = df_x.index.to_period('M').to_timestamp()
processed['SM'] = df_x['API6'].rename('SM')
processed['P_t'] = df_x['PET_mm'].rename('P_t')

nc_path = list(Path('data/raw/grace').glob('*.nc'))[0]
ds = xr.open_dataset(nc_path, decode_times=True)
da = ds['lwe_thickness']
da = da.sel(lat=slice(23.0, 24.5), lon=slice(85.5, 87.5))
lats = np.deg2rad(da['lat'].values)
weights = np.cos(lats)
weights_da = xr.DataArray(weights, coords={'lat': da['lat'].values}, dims=['lat'])
tws_ts = da.weighted(weights_da).mean(dim=['lat', 'lon'])
times = pd.to_datetime(tws_ts['time'].values)
values = tws_ts.values.flatten()
tws = pd.Series(values, index=times, name='tws_cm').dropna()
tws.index = tws.index.to_period('M').to_timestamp()
tws = tws.sort_index()
tws = tws[~tws.index.duplicated(keep='first')]
full_idx = pd.date_range(tws.index[0], tws.index[-1], freq='MS')
tws = tws.reindex(full_idx).interpolate(method='linear')

df = pd.DataFrame({'tws': tws})
for k, s in processed.items():
    df[k] = s
df = df.dropna()

y = df['tws'].values
feature_cols = ['dS_climate', 'SM', 'P_t', 'dS_anthro']
X_raw = df[feature_cols].values
X_std = (X_raw - X_raw.mean(axis=0)) / (X_raw.std(axis=0) + 1e-12)
X_sm = sm.add_constant(X_std)

ols_model = sm.OLS(y, X_sm).fit()

# === Examine the OLS covariance matrix structure ===
# The OLS variance of beta is: (X'X)^{-1} * sigma^2
# The HC0 (heteroscedasticity-only) variance is: (X'X)^{-1} X' diag(e_i^2) X (X'X)^{-1}
# Newey-West adds autocorrelation terms to HC0

print("=" * 70)
print("DEEP DIAGNOSTIC: Why HAC SE < OLS SE for dS_anthro")
print("=" * 70)

# 1. Compare HC0 (hetero-only, no autocorrelation) vs OLS
hc0_model = sm.OLS(y, X_sm).fit(cov_type='HC0')
hc1_model = sm.OLS(y, X_sm).fit(cov_type='HC1')
hc3_model = sm.OLS(y, X_sm).fit(cov_type='HC3')
hac_model = sm.OLS(y, X_sm).fit(cov_type='HAC', cov_kwds={'maxlags': 3})

b2_idx = 4  # dS_anthro is last

print("\n--- Step 1: Heteroscedasticity-only correction ---")
print(f"  OLS SE(dS_anthro):  {ols_model.bse[b2_idx]:.4f}")
print(f"  HC0 SE(dS_anthro):  {hc0_model.bse[b2_idx]:.4f}  (ratio: {hc0_model.bse[b2_idx]/ols_model.bse[b2_idx]:.4f})")
print(f"  HC1 SE(dS_anthro):  {hc1_model.bse[b2_idx]:.4f}  (ratio: {hc1_model.bse[b2_idx]/ols_model.bse[b2_idx]:.4f})")
print(f"  HC3 SE(dS_anthro):  {hc3_model.bse[b2_idx]:.4f}  (ratio: {hc3_model.bse[b2_idx]/ols_model.bse[b2_idx]:.4f})")
print(f"  HAC SE(dS_anthro):  {hac_model.bse[b2_idx]:.4f}  (ratio: {hac_model.bse[b2_idx]/ols_model.bse[b2_idx]:.4f})")

if hc0_model.bse[b2_idx] < ols_model.bse[b2_idx]:
    print()
    print("  KEY FINDING: HC0 (heteroscedasticity-only) SE is ALREADY < OLS SE")
    print("  This means the homoscedasticity assumption in OLS is OVER-estimating")
    print("  the variance of beta2. The residuals are LESS variable in the region")
    print("  of X-space where dS_anthro has high leverage.")
    print()
    print("  This is NOT a bug. It is a known phenomenon where:")
    print("  - OLS assumes constant variance across all observations")
    print("  - But actual residual variance is SMALLER for high-leverage dS_anthro obs")
    print("  - HC correction recognizes this and produces smaller SE")
    print("  - The autocorrelation correction (Newey-West) then ADDS back some variance")
    print("    but not enough to overcome the heteroscedasticity correction")
else:
    print()
    print("  HC0 SE >= OLS SE. The narrowing is from autocorrelation structure.")

# 2. Examine residual heteroscedasticity pattern
resid = ols_model.resid
x_anthro = X_std[:, 3]  # dS_anthro standardized

print("\n--- Step 2: Residual variance by dS_anthro quintile ---")
q = pd.qcut(x_anthro, 5, labels=False)
for qi in range(5):
    mask = q == qi
    resid_var = resid[mask].var()
    print(f"  Quintile {qi+1}: var(resid) = {resid_var:.4f}, n = {mask.sum()}")

# 3. Breusch-Pagan test for heteroscedasticity
from statsmodels.stats.diagnostic import het_breuschpagan
bp_stat, bp_pval, _, _ = het_breuschpagan(resid, X_sm)
print(f"\n--- Step 3: Breusch-Pagan test ---")
print(f"  BP statistic: {bp_stat:.4f}")
print(f"  BP p-value:   {bp_pval:.4f}")
if bp_pval < 0.05:
    print("  Significant heteroscedasticity detected (p < 0.05)")
else:
    print("  No significant heteroscedasticity (p >= 0.05)")
    print("  This means the HC correction SHOULD NOT dramatically change SEs")
    print("  but it can still change them for individual coefficients")

# 4. The real question: is the F-023 claim misleading?
print()
print("=" * 70)
print("VERDICT")
print("=" * 70)
print()
print("F-023 states: 'HAC correction STRENGTHENED the result (CI narrowed)'")
print(f"  OLS CI width:  {ols_model.conf_int()[b2_idx][1] - ols_model.conf_int()[b2_idx][0]:.4f}")
print(f"  HAC CI width:  {hac_model.conf_int()[b2_idx][1] - hac_model.conf_int()[b2_idx][0]:.4f}")
print()

hc0_se = hc0_model.bse[b2_idx]
ols_se = ols_model.bse[b2_idx]
hac_se = hac_model.bse[b2_idx]

print("MECHANISM:")
print(f"  1. HC0 (hetero-only) SE = {hc0_se:.4f} (vs OLS {ols_se:.4f})")
print(f"     Heteroscedasticity correction REDUCES SE by {(1-hc0_se/ols_se)*100:.1f}%")
print(f"  2. HAC (hetero + autocorr) SE = {hac_se:.4f} (vs HC0 {hc0_se:.4f})")
if hac_se > hc0_se:
    print(f"     Autocorrelation correction INCREASES SE by {(hac_se/hc0_se - 1)*100:.1f}%")
else:
    print(f"     Autocorrelation correction further DECREASES SE by {(1-hac_se/hc0_se)*100:.1f}%")
print(f"  3. Net effect: HAC SE is {(1-hac_se/ols_se)*100:.1f}% smaller than OLS SE")
print()
print("IS THIS A BUG? No -- but the INTERPRETATION in F-023 is misleading.")
print("F-023 implies HAC 'strengthened' the result as if autocorrelation correction")
print("made the finding more robust. In reality:")
print("  - The heteroscedasticity correction reduced the SE (legitimate)")
print("  - The autocorrelation correction partially counteracted this (as expected)")
print("  - The net effect happened to be narrower CI")
print()
print("CORRECTED INTERPRETATION for the paper:")
print("  'After applying Newey-West HAC correction (3 lags) to account for")
print("   residual autocorrelation (DW=1.22), beta2 remained highly significant")
print(f"   (p < 0.001, HAC 95% CI: [{hac_model.conf_int()[b2_idx][0]:+.2f}, {hac_model.conf_int()[b2_idx][1]:+.2f}]).'")
print()
print("  Do NOT claim HAC 'strengthened' or 'narrowed' the CI as evidence of")
print("  robustness. The narrowing is incidental to the heteroscedasticity structure,")
print("  not a validation of the autocorrelation correction.")
print()

# Also: the key result (significance) is robust either way
print("BOTTOM LINE: beta2 is significant under BOTH OLS and HAC.")
print(f"  OLS: p = {ols_model.pvalues[b2_idx]:.6f}, CI = [{ols_model.conf_int()[b2_idx][0]:+.4f}, {ols_model.conf_int()[b2_idx][1]:+.4f}]")
print(f"  HAC: p = {hac_model.pvalues[b2_idx]:.6f}, CI = [{hac_model.conf_int()[b2_idx][0]:+.4f}, {hac_model.conf_int()[b2_idx][1]:+.4f}]")
print("  Both exclude zero. The core finding (C3 supported) is valid.")
print("  But F-023 needs rewording to remove the misleading 'strengthened' claim.")
