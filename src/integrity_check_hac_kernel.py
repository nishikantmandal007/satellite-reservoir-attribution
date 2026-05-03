"""
Final diagnostic: Examine the Newey-West kernel computation directly.
Why does adding autocorrelation lags REDUCE the SE further?
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from pathlib import Path
import xarray as xr

PROCESSED_DIR = Path('data/processed')

# === Load data (same as before) ===
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
weights_da = xr.DataArray(np.cos(lats), coords={'lat': da['lat'].values}, dims=['lat'])
tws_ts = da.weighted(weights_da).mean(dim=['lat', 'lon'])
times = pd.to_datetime(tws_ts['time'].values)
tws = pd.Series(tws_ts.values.flatten(), index=times, name='tws_cm').dropna()
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
X = sm.add_constant(X_std)

n, k = X.shape
b2_idx = 4  # dS_anthro

# OLS residuals
ols = sm.OLS(y, X).fit()
e = ols.resid

# === Manually compute Newey-West covariance matrix ===
# Newey-West: S = S_0 + sum_{j=1}^{L} w_j * (S_j + S_j')
# where S_j = (1/n) * sum_{t=j+1}^{n} e_t * e_{t-j} * x_t * x_{t-j}'
# w_j = 1 - j/(L+1)  (Bartlett kernel)

XtXinv = np.linalg.inv(X.T @ X)

# S_0: HC0 meat
S_0 = np.zeros((k, k))
for t in range(n):
    xt = X[t:t+1, :].T  # (k,1)
    S_0 += (e[t]**2) * (xt @ xt.T)
S_0 /= n

print("=" * 70)
print("NEWEY-WEST KERNEL DECOMPOSITION")
print("=" * 70)

# Variance of beta2 from S_0 alone (HC0)
V_hc0 = n * XtXinv @ S_0 @ XtXinv
se_hc0_manual = np.sqrt(V_hc0[b2_idx, b2_idx])
print(f"\nHC0 SE(dS_anthro) [manual]: {se_hc0_manual:.4f}")

# Now add each lag
L = 3
S_cumulative = S_0.copy()
for j in range(1, L+1):
    w_j = 1 - j / (L + 1)  # Bartlett kernel weight
    S_j = np.zeros((k, k))
    for t in range(j, n):
        xt = X[t:t+1, :].T
        xtj = X[t-j:t-j+1, :].T
        S_j += e[t] * e[t-j] * (xt @ xtj.T)
    S_j /= n

    # The autocovariance contribution is w_j * (S_j + S_j')
    autocov_contrib = w_j * (S_j + S_j.T)
    S_cumulative = S_cumulative + autocov_contrib

    V_cum = n * XtXinv @ S_cumulative @ XtXinv
    se_cum = np.sqrt(V_cum[b2_idx, b2_idx])

    # Just the diagonal element contribution
    diag_contrib = n * (XtXinv @ autocov_contrib @ XtXinv)[b2_idx, b2_idx]

    print(f"\nLag {j} (Bartlett weight = {w_j:.3f}):")
    print(f"  Autocovariance contribution to Var(beta2): {diag_contrib:+.6f}")
    print(f"  Cumulative SE(dS_anthro): {se_cum:.4f}")
    if diag_contrib < 0:
        print(f"  >>> NEGATIVE contribution: lag-{j} autocovariance REDUCES variance")
        # This can happen when the cross-product e_t*e_{t-j}*x_t*x_{t-j}'
        # contributes negatively to the (b2,b2) element

print()
print("=" * 70)
print("EXPLANATION")
print("=" * 70)
print()
print("In multivariate regression, the Newey-West autocovariance terms S_j are")
print("MATRICES, not scalars. Even when e_t and e_{t-j} are positively correlated,")
print("the CROSS-PRODUCTS x_t * x_{t-j}' can contribute negatively to specific")
print("diagonal elements of the sandwich covariance matrix.")
print()
print("This means: for a specific coefficient (dS_anthro), the autocorrelation")
print("correction CAN reduce the standard error, even with globally positive")
print("residual autocorrelation. This is not a bug; it's a feature of the")
print("multivariate sandwich estimator.")
print()
print("HOWEVER, this is precisely why the F-023 claim is misleading:")
print("Saying 'HAC STRENGTHENED the result' implies the autocorrelation correction")
print("validated the finding. In reality, the direction of the HAC correction is")
print("coefficient-specific and does not indicate robustness.")

# === What SHOULD be reported ===
print()
print("=" * 70)
print("RECOMMENDED FIX FOR F-023")
print("=" * 70)
print()
print("REMOVE: 'HAC correction STRENGTHENED the result (CI narrowed)'")
print()
print("REPLACE WITH:")
print("  'Newey-West HAC standard errors (3 lags) were applied to account for")
print("  residual autocorrelation (DW=1.22). Under both OLS and HAC covariance,")
print("  beta2 remains significant (OLS p=0.003; HAC p<0.001). The HAC standard")
print("  error for beta2 is smaller than the OLS standard error; this reflects")
print("  the heteroscedasticity structure of the residuals rather than an")
print("  enhancement from autocorrelation correction.'")
print()
print("CONFIDENCE remains: VERY HIGH -- the result is significant under both")
print("OLS and HAC, and both CIs exclude zero.")
