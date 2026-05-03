"""
Critical Checks for DVC Reservoir Attribution Paper
=====================================================
TASK A: Residual Contamination Check
  - Do VIF-dropped climate features correlate with ΔS_anthro?
  - If yes, the "anthropogenic" residual may contain unexplained climate signal.

TASK B: Naive Baseline Comparison
  - Is XGBoost (NSE=0.208 pooled OOS) better than trivial baselines?
  - Persistence, climatological mean, zero model.

Run: cd /home/stark007/dvc-research && uv run python src/critical_checks.py
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

PROCESSED_DIR = Path('data/processed')
S1_ERA_START = '2017-01-01'
DEAD_STORAGE_FLOOR_BCM = -0.183

# ═══════════════════════════════════════════════════════════════════
# TASK A: Residual Contamination Check
# ═══════════════════════════════════════════════════════════════════

def task_a_residual_contamination():
    print("=" * 70)
    print("TASK A: RESIDUAL CONTAMINATION CHECK")
    print("  Does ΔS_anthro correlate with VIF-dropped climate features?")
    print("=" * 70)

    # Load ΔS_anthro
    anthro = pd.read_csv(PROCESSED_DIR / 'delta_S_anthro.csv', index_col=0, parse_dates=True)
    anthro = anthro[anthro['reservoir'] == 'maithon'].copy()
    # Keep only rows where delta_S_anthro_bcm is not NaN (i.e., test rows with predictions)
    anthro_valid = anthro.dropna(subset=['delta_S_anthro_bcm'])
    print(f"\n  ΔS_anthro rows with valid values: {len(anthro_valid)}")
    print(f"  Date range: {anthro_valid.index.min()} to {anthro_valid.index.max()}")

    # Now build the FULL 18-feature matrix from raw data (before VIF filtering)
    # We need to reconstruct this from the raw files used by 02_feature_engineering.py
    from calendar import monthrange

    RAW_DIR = Path('data/raw')
    date_idx = pd.date_range('2002-01-01', '2023-12-01', freq='MS')

    X_all = pd.DataFrame(index=date_idx)

    # CHIRPS precipitation
    p = RAW_DIR / 'chirps_monthly.csv'
    if p.exists():
        df = pd.read_csv(p)
        df['date'] = pd.to_datetime(df['date']).dt.to_period('M').dt.to_timestamp()
        df = df.set_index('date').sort_index()
        X_all['P_mm'] = df['precipitation'].reindex(date_idx)

    # ERA5-Land
    p = RAW_DIR / 'era5_monthly.csv'
    if p.exists():
        df = pd.read_csv(p)
        df['date'] = pd.to_datetime(df['date']).dt.to_period('M').dt.to_timestamp()
        df = df.set_index('date').sort_index()
        df = df.reindex(date_idx)
        days_in_month = pd.Series(
            [monthrange(d.year, d.month)[1] for d in date_idx],
            index=date_idx, dtype=float
        )
        X_all['PET_mm'] = df['potential_evaporation_sum'].abs() * days_in_month * 1000
        X_all['SM1'] = df['volumetric_soil_water_layer_1']
        X_all['SM2'] = df['volumetric_soil_water_layer_2']
        X_all['T_C'] = df['temperature_2m'] - 273.15

    # NDVI
    p = RAW_DIR / 'ndvi_monthly.csv'
    if p.exists():
        df = pd.read_csv(p)
        df['date'] = pd.to_datetime(df['date']).dt.to_period('M').dt.to_timestamp()
        df = df.set_index('date').sort_index()
        ndvi = df['NDVI'].reindex(date_idx)
        ndvi = ndvi.where(ndvi > -100, np.nan)
        X_all['NDVI'] = ndvi

    # AET
    p = RAW_DIR / 'aet_monthly.csv'
    if p.exists():
        df = pd.read_csv(p)
        df['date'] = pd.to_datetime(df['date']).dt.to_period('M').dt.to_timestamp()
        df = df.set_index('date').sort_index()
        et = df['ET'].reindex(date_idx)
        et = et.where(et > -100, np.nan)
        X_all['AET_mm'] = et

    # LULC annual -> monthly
    p = RAW_DIR / 'lulc_annual.csv'
    if p.exists():
        lulc = pd.read_csv(p)
        lulc_monthly = pd.DataFrame(index=date_idx)
        lulc_monthly['year'] = date_idx.year
        lulc = lulc.set_index('year')
        for col in ['LC_forest_frac', 'LC_crop_frac']:
            if col in lulc.columns:
                lulc_monthly[col] = lulc_monthly['year'].map(lulc[col])
        X_all['LC_crop'] = lulc_monthly.get('LC_crop_frac', np.nan)
        X_all['LC_for'] = lulc_monthly.get('LC_forest_frac', np.nan)

    # NTL annual -> monthly
    p = RAW_DIR / 'ntl_dmsp_annual.csv'
    if p.exists():
        ntl = pd.read_csv(p)
        ntl_monthly = pd.DataFrame(index=date_idx)
        ntl_monthly['year'] = date_idx.year
        if 'year' in ntl.columns:
            ntl = ntl.set_index('year')
        # Try to find the lights column
        for col in ntl.columns:
            if 'light' in col.lower() or 'ntl' in col.lower() or 'avg' in col.lower():
                ntl_monthly['NTL'] = ntl_monthly['year'].map(ntl[col])
                X_all['NTL'] = ntl_monthly['NTL']
                break

    # Nino34 (year, month columns, not date)
    p = RAW_DIR / 'nino34_monthly.csv'
    if p.exists():
        df = pd.read_csv(p)
        df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        df = df.set_index('date').sort_index()
        nino_col = [c for c in df.columns if 'nino' in c.lower() and 'anom' in c.lower()]
        if nino_col:
            X_all['Nino34'] = df[nino_col[0]].reindex(date_idx)
        else:
            nino_col = [c for c in df.columns if 'nino' in c.lower()]
            if nino_col:
                X_all['Nino34'] = df[nino_col[0]].reindex(date_idx)

    # IOD/DMI (year, month columns, not date)
    p = RAW_DIR / 'iod_dmi_monthly.csv'
    if p.exists():
        df = pd.read_csv(p)
        df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        df = df.set_index('date').sort_index()
        dmi_col = [c for c in df.columns if 'dmi' in c.lower()]
        if dmi_col:
            X_all['DMI'] = df[dmi_col[0]].reindex(date_idx)
        elif len(df.columns) == 1:
            X_all['DMI'] = df.iloc[:, 0].reindex(date_idx)

    # Derived: P3_cumul (3-month cumulative rainfall)
    if 'P_mm' in X_all.columns:
        X_all['P3_mm'] = X_all['P_mm'].rolling(3).sum()

    # Derived: API6
    if 'P_mm' in X_all.columns:
        api6 = pd.Series(0.0, index=date_idx)
        decay = 0.85
        p_vals = X_all['P_mm'].fillna(0).values
        for i in range(len(p_vals)):
            val = 0
            for lag in range(6):
                if i - lag >= 0:
                    val += (decay ** lag) * p_vals[i - lag]
            api6.iloc[i] = val
        X_all['API6'] = api6

    # Storage lags from the timeseries
    ts = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv', parse_dates=['date'])
    ts_m = ts[ts['reservoir'] == 'maithon'][['date', 'delta_S_obs_bcm']].copy()
    ts_m = ts_m.set_index('date').sort_index()
    ts_m.index = pd.to_datetime(ts_m.index).to_period('M').to_timestamp()
    X_all['dS_lag1'] = ts_m['delta_S_obs_bcm'].reindex(date_idx).shift(1)
    X_all['dS_lag3'] = ts_m['delta_S_obs_bcm'].reindex(date_idx).shift(3)

    print(f"\n  Reconstructed feature matrix: {X_all.shape}")
    print(f"  Columns: {list(X_all.columns)}")

    # The 10 VIF-dropped features (from vif_diagnostic.csv)
    vif_dropped = ['P_mm', 'P3_mm', 'SM1', 'SM2', 'T_C', 'NDVI', 'LC_crop', 'LC_for', 'Nino34', 'NTL']

    # Align with ΔS_anthro valid dates
    common_idx = anthro_valid.index.intersection(X_all.index)
    print(f"  Common date range for correlation: {len(common_idx)} rows")

    ds_anthro = anthro_valid.loc[common_idx, 'delta_S_anthro_bcm']

    results = []
    print(f"\n  {'Feature':<12} {'Spearman r':>10} {'p-value':>10} {'n':>5} {'FLAG':>10}")
    print("  " + "-" * 52)

    for feat in vif_dropped:
        if feat not in X_all.columns:
            print(f"  {feat:<12} {'MISSING':>10}")
            results.append({'feature': feat, 'spearman_r': np.nan, 'p_value': np.nan,
                            'n': 0, 'flag': 'MISSING'})
            continue

        x = X_all.loc[common_idx, feat]
        # Drop NaN pairs
        mask = x.notna() & ds_anthro.notna()
        if mask.sum() < 5:
            print(f"  {feat:<12} {'<5 obs':>10}")
            results.append({'feature': feat, 'spearman_r': np.nan, 'p_value': np.nan,
                            'n': int(mask.sum()), 'flag': 'INSUFFICIENT'})
            continue

        r, p = stats.spearmanr(x[mask], ds_anthro[mask])
        flag = 'DANGEROUS' if abs(r) > 0.3 else 'OK'
        symbol = '***' if abs(r) > 0.3 else ''
        print(f"  {feat:<12} {r:>10.4f} {p:>10.4f} {mask.sum():>5d} {flag:>10} {symbol}")
        results.append({'feature': feat, 'spearman_r': r, 'p_value': p,
                        'n': int(mask.sum()), 'flag': flag})

    # Also check the 8 KEPT features for completeness
    kept_features = ['API6', 'PET_mm', 'AET_mm', 'DMI', 'dS_lag1', 'dS_lag3']
    print(f"\n  --- Kept features (for reference) ---")
    for feat in kept_features:
        if feat not in X_all.columns:
            continue
        x = X_all.loc[common_idx, feat]
        mask = x.notna() & ds_anthro.notna()
        if mask.sum() < 5:
            continue
        r, p = stats.spearmanr(x[mask], ds_anthro[mask])
        print(f"  {feat:<12} {r:>10.4f} {p:>10.4f} {mask.sum():>5d}")

    # Sort results by |r|
    results_df = pd.DataFrame(results)
    results_df['abs_r'] = results_df['spearman_r'].abs()
    results_df = results_df.sort_values('abs_r', ascending=False)
    results_df.to_csv(PROCESSED_DIR / 'residual_contamination.csv', index=False)
    print(f"\n  Saved: data/processed/residual_contamination.csv")

    # Summary
    dangerous = results_df[results_df['flag'] == 'DANGEROUS']
    if len(dangerous) > 0:
        print(f"\n  *** DANGEROUS: {len(dangerous)} VIF-dropped features correlate with ΔS_anthro at |r|>0.3:")
        for _, row in dangerous.iterrows():
            print(f"      {row['feature']}: r={row['spearman_r']:.4f}, p={row['p_value']:.4f}")
        print("  >>> The anthropogenic residual may contain unexplained climate signal!")
    else:
        print(f"\n  CLEAR: No VIF-dropped features correlate with ΔS_anthro at |r|>0.3")

    return results_df


# ═══════════════════════════════════════════════════════════════════
# TASK B: Naive Baseline Comparison
# ═══════════════════════════════════════════════════════════════════

def nse(obs, pred):
    """Nash-Sutcliffe Efficiency."""
    obs, pred = np.asarray(obs, dtype=float), np.asarray(pred, dtype=float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    if len(o) < 3:
        return np.nan
    denom = np.sum((o - np.mean(o))**2)
    if denom < 1e-12:
        return np.nan
    return float(1.0 - np.sum((o - p)**2) / denom)


def task_b_baseline_comparison():
    print("\n" + "=" * 70)
    print("TASK B: NAIVE BASELINE COMPARISON")
    print("  Is XGBoost better than persistence, climatology, and zero models?")
    print("=" * 70)

    # Load ΔS_anthro to get OOS predictions and observations
    anthro = pd.read_csv(PROCESSED_DIR / 'delta_S_anthro.csv', index_col=0, parse_dates=True)
    anthro = anthro[anthro['reservoir'] == 'maithon'].copy()

    # Test rows = rows where delta_S_climate_bcm is not NaN
    test_rows = anthro.dropna(subset=['delta_S_climate_bcm']).copy()
    print(f"\n  Total test rows (OOS with XGBoost predictions): {len(test_rows)}")

    obs = test_rows['delta_S_obs_bcm'].values
    xgb_pred = test_rows['delta_S_climate_bcm'].values  # XGBoost predicted climate component

    # Identify physically-resolved rows (not at dead storage floor)
    phys_mask = obs > DEAD_STORAGE_FLOOR_BCM
    n_phys = phys_mask.sum()
    n_floor = (~phys_mask).sum()
    print(f"  Physically-resolved rows: {n_phys}")
    print(f"  Dead-storage-floor rows: {n_floor}")

    # XGBoost NSE on ALL test rows
    xgb_nse_all = nse(obs, xgb_pred)
    # XGBoost NSE on physically-resolved rows only
    xgb_nse_phys = nse(obs[phys_mask], xgb_pred[phys_mask])

    print(f"\n  XGBoost NSE (all test rows): {xgb_nse_all:.4f}")
    print(f"  XGBoost NSE (physical rows): {xgb_nse_phys:.4f}")

    # Load the full storage timeseries for lag/climatology reference
    ts = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv', parse_dates=['date'])
    ts_m = ts[ts['reservoir'] == 'maithon'][['date', 'delta_S_obs_bcm']].copy()
    ts_m = ts_m.set_index('date').sort_index()
    ts_m.index = pd.to_datetime(ts_m.index)

    # --- Baseline 1: Persistence model: predict dS(t) = dS(t-1) ---
    persist_pred = []
    for date in test_rows.index:
        prev_month = date - pd.DateOffset(months=1)
        if prev_month in ts_m.index:
            persist_pred.append(ts_m.loc[prev_month, 'delta_S_obs_bcm'])
        else:
            persist_pred.append(np.nan)
    persist_pred = np.array(persist_pred, dtype=float)

    persist_nse_all = nse(obs, persist_pred)
    valid_persist = ~np.isnan(persist_pred)
    persist_nse_phys = nse(obs[phys_mask & valid_persist], persist_pred[phys_mask & valid_persist])

    # --- Baseline 2: Climatological mean (per calendar month) ---
    # Compute monthly climatology from TRAINING data only (pre-test period)
    first_test_date = test_rows.index.min()
    train_ts = ts_m.loc[:first_test_date - pd.DateOffset(months=1)]
    monthly_clim = train_ts.groupby(train_ts.index.month)['delta_S_obs_bcm'].mean()

    clim_pred = np.array([monthly_clim.get(d.month, np.nan) for d in test_rows.index])
    clim_nse_all = nse(obs, clim_pred)
    valid_clim = ~np.isnan(clim_pred)
    clim_nse_phys = nse(obs[phys_mask & valid_clim], clim_pred[phys_mask & valid_clim])

    # --- Baseline 3: Zero model (predict dS = 0 always) ---
    zero_pred = np.zeros(len(obs))
    zero_nse_all = nse(obs, zero_pred)
    zero_nse_phys = nse(obs[phys_mask], zero_pred[phys_mask])

    # --- Baseline 4: Mean model (predict dS = training mean always) ---
    train_mean = train_ts['delta_S_obs_bcm'].mean()
    mean_pred = np.full(len(obs), train_mean)
    mean_nse_all = nse(obs, mean_pred)
    mean_nse_phys = nse(obs[phys_mask], mean_pred[phys_mask])

    print(f"\n  Training mean: {train_mean:.4f} BCM")
    print(f"  Monthly climatology computed from {len(train_ts)} training months")

    # Build results table
    results = pd.DataFrame([
        {'model': 'XGBoost (climate)', 'NSE_all_test': xgb_nse_all, 'NSE_physical': xgb_nse_phys},
        {'model': 'Persistence dS(t-1)', 'NSE_all_test': persist_nse_all, 'NSE_physical': persist_nse_phys},
        {'model': 'Climatological mean', 'NSE_all_test': clim_nse_all, 'NSE_physical': clim_nse_phys},
        {'model': 'Zero (dS=0)', 'NSE_all_test': zero_nse_all, 'NSE_physical': zero_nse_phys},
        {'model': 'Training mean', 'NSE_all_test': mean_nse_all, 'NSE_physical': mean_nse_phys},
    ])

    print(f"\n  {'Model':<25} {'NSE (all test)':>15} {'NSE (physical)':>15}")
    print("  " + "-" * 57)
    for _, row in results.iterrows():
        flag = ''
        if row['model'] != 'XGBoost (climate)':
            if row['NSE_all_test'] > xgb_nse_all:
                flag = ' *** BEATS XGBOOST'
        print(f"  {row['model']:<25} {row['NSE_all_test']:>15.4f} {row['NSE_physical']:>15.4f}{flag}")

    # Flag critical issues
    print("\n  --- VERDICT ---")
    beaten_by = [r['model'] for _, r in results.iterrows()
                 if r['model'] != 'XGBoost (climate)' and r['NSE_all_test'] > xgb_nse_all]
    if beaten_by:
        print(f"  CRITICAL: XGBoost is WORSE than: {', '.join(beaten_by)}")
        print(f"  The climate model adds NEGATIVE value compared to naive baselines.")
    else:
        print(f"  OK: XGBoost beats all naive baselines.")

    beaten_phys = [r['model'] for _, r in results.iterrows()
                   if r['model'] != 'XGBoost (climate)' and not np.isnan(r['NSE_physical'])
                   and r['NSE_physical'] > xgb_nse_phys]
    if beaten_phys:
        print(f"  CRITICAL (physical rows): XGBoost is WORSE than: {', '.join(beaten_phys)}")

    results.to_csv(PROCESSED_DIR / 'baseline_comparison.csv', index=False)
    print(f"\n  Saved: data/processed/baseline_comparison.csv")

    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("\n" + "#" * 70)
    print("# CRITICAL CHECKS — DVC RESERVOIR ATTRIBUTION PAPER")
    print("#" * 70)

    contam = task_a_residual_contamination()
    baselines = task_b_baseline_comparison()

    print("\n" + "#" * 70)
    print("# DONE — Review results above carefully.")
    print("#" * 70)
