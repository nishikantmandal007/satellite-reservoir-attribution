"""
Integrity check: OLS vs HAC standard errors for GRACE regression.
Diagnoses whether "HAC correction STRENGTHENED the result" claim is valid.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import acf
from pathlib import Path
import xarray as xr

PROCESSED_DIR = Path('data/processed')

# === Reproduce the data loading exactly as 05_grace_reconciliation.py does ===
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

# Load GRACE TWS
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

# === Build regression dataframe ===
df = pd.DataFrame({'tws': tws})
for k, s in processed.items():
    df[k] = s
df = df.dropna()

y = df['tws'].values
feature_cols = ['dS_climate', 'SM', 'P_t', 'dS_anthro']
X_raw = df[feature_cols].values
X_std = (X_raw - X_raw.mean(axis=0)) / (X_raw.std(axis=0) + 1e-12)
X_sm = sm.add_constant(X_std)

# === Fit BOTH models ===
ols_model = sm.OLS(y, X_sm).fit()
hac_model = sm.OLS(y, X_sm).fit(cov_type='HAC', cov_kwds={'maxlags': 3})

coef_names = ['const'] + feature_cols
b2_idx = coef_names.index('dS_anthro')

print('=' * 70)
print('INTEGRITY CHECK: OLS vs HAC Standard Errors for beta2 (dS_anthro)')
print('=' * 70)

dw = durbin_watson(ols_model.resid)
print(f'\nN = {len(df)}, Durbin-Watson = {dw:.4f}')
print(f'  (DW < 2.0 means positive autocorrelation in residuals)')
print()

print('--- ALL COEFFICIENTS ---')
header = f'{"Coef":<15} {"beta":>10} {"OLS SE":>10} {"HAC SE":>10} {"OLS p":>10} {"HAC p":>10} {"SE ratio":>10}'
print(header)
for i, name in enumerate(coef_names):
    ols_se = ols_model.bse[i]
    hac_se = hac_model.bse[i]
    ratio = hac_se / ols_se
    print(f'{name:<15} {ols_model.params[i]:>+10.4f} {ols_se:>10.4f} {hac_se:>10.4f} '
          f'{ols_model.pvalues[i]:>10.4f} {hac_model.pvalues[i]:>10.4f} {ratio:>10.3f}')

print()
print('--- FOCUS: beta2 (dS_anthro) ---')
ols_ci = ols_model.conf_int()[b2_idx]
hac_ci = hac_model.conf_int()[b2_idx]

print(f'  OLS standard error:  {ols_model.bse[b2_idx]:.4f}')
print(f'  HAC standard error:  {hac_model.bse[b2_idx]:.4f}')
print(f'  SE ratio (HAC/OLS):  {hac_model.bse[b2_idx]/ols_model.bse[b2_idx]:.4f}')
print()
print(f'  OLS 95% CI:  [{ols_ci[0]:+.4f}, {ols_ci[1]:+.4f}]  width = {ols_ci[1]-ols_ci[0]:.4f}')
print(f'  HAC 95% CI:  [{hac_ci[0]:+.4f}, {hac_ci[1]:+.4f}]  width = {hac_ci[1]-hac_ci[0]:.4f}')
print(f'  CI width ratio (HAC/OLS): {(hac_ci[1]-hac_ci[0])/(ols_ci[1]-ols_ci[0]):.4f}')
print()

if hac_model.bse[b2_idx] < ols_model.bse[b2_idx]:
    print('  >>> ANOMALY: HAC SE < OLS SE <<<')
    print('  With DW=1.22 (positive autocorrelation), Newey-West HAC typically')
    print('  produces WIDER CIs. Narrower CIs suggest heteroscedasticity correction')
    print('  is dominating the autocorrelation correction, OR the autocorrelation')
    print('  structure at higher lags is negative (cancelling lag-1 positive).')
else:
    print('  HAC SE >= OLS SE -- EXPECTED with positive autocorrelation.')
    print('  If FINDINGS.md F-023 says CI narrowed, that claim is WRONG.')

# === Autocorrelation structure ===
resid = ols_model.resid
acf_vals = acf(resid, nlags=6, fft=True)
print()
print('--- RESIDUAL AUTOCORRELATION (OLS residuals) ---')
for lag in range(7):
    sig = ' *' if abs(acf_vals[lag]) > 1.96/np.sqrt(len(resid)) and lag > 0 else ''
    print(f'  Lag {lag}: ACF = {acf_vals[lag]:+.4f}{sig}')

# === HAC sensitivity to maxlags ===
print()
print('--- HAC SENSITIVITY TO MAXLAGS ---')
for nlags in [0, 1, 2, 3, 4, 5, 6]:
    m = sm.OLS(y, X_sm).fit(cov_type='HAC', cov_kwds={'maxlags': nlags})
    se = m.bse[b2_idx]
    ci = m.conf_int()[b2_idx]
    print(f'  maxlags={nlags}: SE={se:.4f}, CI=[{ci[0]:+.4f}, {ci[1]:+.4f}], '
          f'width={ci[1]-ci[0]:.4f}, p={m.pvalues[b2_idx]:.6f}')

# === Note about the script bug ===
print()
print('--- SCRIPT ANALYSIS ---')
print('The script at line 421 fits ONLY the HAC model:')
print('  full_model = sm.OLS(y, X_sm).fit(cov_type="HAC", cov_kwds={"maxlags": 3})')
print('It NEVER fits a plain OLS model for comparison.')
print('Therefore the claim "HAC correction STRENGTHENED the result" in F-023')
print('could not have been derived from this script -- it was either:')
print('  (a) stated without comparison data, or')
print('  (b) based on a separate ad-hoc analysis not preserved in the codebase.')
print()

# Also note: HAC uses z-distribution (normal), OLS uses t-distribution
# With N=48, k=5: t_{43} critical value = 2.017 vs z critical = 1.96
# This alone narrows the CI by ~3%
print('--- ADDITIONAL NOTE: z vs t distribution ---')
from scipy import stats
t_crit = stats.t.ppf(0.975, df=len(df)-5)
z_crit = stats.norm.ppf(0.975)
print(f'  OLS uses t-distribution: t_crit(df={len(df)-5}) = {t_crit:.4f}')
print(f'  HAC uses z-distribution: z_crit = {z_crit:.4f}')
print(f'  z/t ratio = {z_crit/t_crit:.4f} -- this alone narrows CI by {(1-z_crit/t_crit)*100:.1f}%')
print(f'  OLS CI width (using t): 2 * {t_crit:.4f} * OLS_SE')
print(f'  HAC CI width (using z): 2 * {z_crit:.4f} * HAC_SE')
print()

# True apples-to-apples: compare CI widths accounting for distribution difference
ols_ci_width = 2 * t_crit * ols_model.bse[b2_idx]
hac_ci_width = 2 * z_crit * hac_model.bse[b2_idx]
print(f'  OLS CI width (t-based): {ols_ci_width:.4f}')
print(f'  HAC CI width (z-based): {hac_ci_width:.4f}')
print(f'  Ratio: {hac_ci_width/ols_ci_width:.4f}')
if hac_ci_width < ols_ci_width:
    print(f'  >>> HAC CI appears narrower, but this conflates TWO effects:')
    print(f'      1. Switching from t to z distribution ({(1-z_crit/t_crit)*100:.1f}% narrower)')
    print(f'      2. HAC SE vs OLS SE change')
    # Apples-to-apples: same distribution
    ratio_se = hac_model.bse[b2_idx] / ols_model.bse[b2_idx]
    print(f'  Pure SE ratio (HAC/OLS): {ratio_se:.4f}')
    if ratio_se < 1.0:
        print(f'  HAC SE is genuinely smaller -- likely heteroscedasticity correction')
        print(f'  is reducing variance more than autocorrelation correction is adding.')
    else:
        print(f'  HAC SE is larger (as expected), but z-distribution masks this.')
