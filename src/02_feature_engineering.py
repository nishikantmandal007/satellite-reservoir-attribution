"""
02_feature_engineering.py
DVC Reservoir Attribution Project — Stage 2

Purpose:
    Load GEE driver CSVs + external climate indices → compute derived features
    (API₆, P₃, SCS-CN inflow, monsoon onset anomaly, lagged storage) →
    merge into single feature matrix → VIF check → save.

Run:
    uv run python src/02_feature_engineering.py

Expected inputs (download from Google Drive DVC_drivers/ → data/raw/):
    data/raw/chirps_monthly.csv      — 264 rows: date, precipitation
    data/raw/era5_monthly.csv        — 264 rows: date, PET, SM1, SM2, T_K
    data/raw/ndvi_monthly.csv        — 264 rows: date, NDVI
    data/raw/aet_monthly.csv         — 264 rows: date, ET
    data/raw/lulc_annual.csv         — 22 rows:  year, LC_forest_frac, LC_crop_frac
    data/raw/ntl_dmsp_annual.csv     — 12 rows:  year, stable_lights
    data/raw/nino34_monthly.csv      — manual download from NOAA
    data/raw/iod_dmi_monthly.csv     — manual download from NOAA/JAMSTEC
    data/processed/DVC_storage_timeseries_2002_2024.csv — Stage 1 output

Expected outputs:
    data/processed/X_climate_final.csv     — 264 rows × ~18–22 features
    data/processed/vif_diagnostic.csv      — VIF scores per feature
    data/processed/enso_iod_merged.csv     — Niño3.4 + DMI reference series
    figures/Fig_feature_correlation.png    — 300 DPI heatmap
"""

import warnings
from pathlib import Path
from calendar import monthrange

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

RAW_DIR       = Path('data/raw')
PROCESSED_DIR = Path('data/processed')
FIGURES_DIR   = Path('figures')

DATE_START = '2002-01-01'
DATE_END   = '2023-12-01'   # 264 months

# SCS-CN defaults (CN=75: mixed land use, Class C soil, Jharkhand)
# Update with HWSD-derived values if available (Day 5 per sprint plan)
SCS_CN_DEFAULT        = 75
CATCHMENT_AREA_KM2    = 19600   # upper Damodar basin approx. catchment area

API6_DECAY = 0.85    # antecedent precipitation index decay factor (standard)

VIF_THRESHOLD = 10   # drop features with VIF > this iteratively

# ═══════════════════════════════════════════════════════════════════
# STEP 0: Setup
# ═══════════════════════════════════════════════════════════════════

def _ensure_dirs():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def build_date_index() -> pd.DatetimeIndex:
    """264 monthly timestamps: 2002-01-01 to 2023-12-01."""
    return pd.date_range(DATE_START, DATE_END, freq='MS')


# ═══════════════════════════════════════════════════════════════════
# STEP 1: Load GEE driver CSVs
# ═══════════════════════════════════════════════════════════════════

def _load_csv_with_date(path: Path, date_col: str = 'date') -> pd.DataFrame:
    df = pd.read_csv(path)
    df[date_col] = pd.to_datetime(df[date_col]).dt.to_period('M').dt.to_timestamp()
    return df.set_index(date_col).sort_index()


def load_gee_drivers(raw_dir: Path, date_idx: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Load all GEE-exported CSVs, apply unit conversions, align to date_idx.
    Returns DataFrame with columns: P_mm, PET_mm, SM1, SM2, T_C, NDVI, AET_mm.
    Missing files produce NaN columns with a warning (allows partial runs).
    """
    X = pd.DataFrame(index=date_idx)

    # ── CHIRPS precipitation (mm/month) ──────────────────────────────
    p = raw_dir / 'chirps_monthly.csv'
    if p.exists():
        df = _load_csv_with_date(p)
        X['P_mm'] = df['precipitation'].reindex(date_idx)
        print(f"  CHIRPS: {X['P_mm'].notna().sum()} valid rows")
    else:
        warnings.warn(f"[WARN] {p} not found — P_mm will be NaN")
        X['P_mm'] = np.nan

    # ── ERA5-Land (PET, SM, T) ────────────────────────────────────────
    p = raw_dir / 'era5_monthly.csv'
    if p.exists():
        df = _load_csv_with_date(p)
        df = df.reindex(date_idx)

        # PET: m/day mean → mm/month (multiply by days in month × 1000)
        days_in_month = pd.Series(
            [monthrange(d.year, d.month)[1] for d in date_idx],
            index=date_idx, dtype=float
        )
        X['PET_mm']  = df['potential_evaporation_sum'].abs() * days_in_month * 1000
        X['SM1']     = df['volumetric_soil_water_layer_1']   # m³/m³
        X['SM2']     = df['volumetric_soil_water_layer_2']   # m³/m³
        X['T_C']     = df['temperature_2m'] - 273.15         # K → °C
        print(f"  ERA5: {X['PET_mm'].notna().sum()} valid rows")
    else:
        warnings.warn(f"[WARN] {p} not found — ERA5 features will be NaN")
        for col in ['PET_mm', 'SM1', 'SM2', 'T_C']:
            X[col] = np.nan

    # ── MODIS NDVI ────────────────────────────────────────────────────
    p = raw_dir / 'ndvi_monthly.csv'
    if p.exists():
        df = _load_csv_with_date(p)
        ndvi = df['NDVI'].reindex(date_idx)
        ndvi = ndvi.where(ndvi > -100, np.nan)  # mask GEE sentinel -9999 values
        X['NDVI'] = ndvi
        print(f"  NDVI: {X['NDVI'].notna().sum()} valid rows")
    else:
        warnings.warn(f"[WARN] {p} not found — NDVI will be NaN")
        X['NDVI'] = np.nan

    # ── MODIS Actual ET (mm/month) ────────────────────────────────────
    p = raw_dir / 'aet_monthly.csv'
    if p.exists():
        df = _load_csv_with_date(p)
        et = df['ET'].reindex(date_idx)
        et = et.where(et > -100, np.nan)  # mask GEE sentinel -9999 values
        X['AET_mm'] = et
        print(f"  AET: {X['AET_mm'].notna().sum()} valid rows")
    else:
        warnings.warn(f"[WARN] {p} not found — AET_mm will be NaN")
        X['AET_mm'] = np.nan

    # ── MODIS LULC annual → forward-filled monthly ────────────────────
    p = raw_dir / 'lulc_annual.csv'
    if p.exists():
        lulc = pd.read_csv(p)
        # Create annual-to-monthly mapping
        lulc_monthly = pd.DataFrame(index=date_idx)
        lulc_monthly['year'] = date_idx.year
        lulc = lulc.set_index('year')
        for col in ['LC_forest_frac', 'LC_crop_frac']:
            lulc_monthly[col] = lulc_monthly['year'].map(lulc[col])
        # GEE null guard returns 0.0 for years with no MCD12Q1 data (e.g. 2021, 2022)
        # Replace rows where BOTH fractions are 0 with NaN so ffill propagates last valid year
        both_zero = (lulc_monthly['LC_forest_frac'] == 0) & (lulc_monthly['LC_crop_frac'] == 0)
        lulc_monthly.loc[both_zero, ['LC_forest_frac', 'LC_crop_frac']] = np.nan
        lulc_monthly.ffill(inplace=True)   # forward-fill missing years
        X['LC_for']  = lulc_monthly['LC_forest_frac']
        X['LC_crop'] = lulc_monthly['LC_crop_frac']
        print(f"  LULC: {X['LC_for'].notna().sum()} valid rows (annual forward-filled)")
    else:
        warnings.warn(f"[WARN] {p} not found — LULC features will be NaN")
        X['LC_for'] = np.nan
        X['LC_crop'] = np.nan

    return X


# ═══════════════════════════════════════════════════════════════════
# STEP 2: Derived rainfall features
# ═══════════════════════════════════════════════════════════════════

def compute_api6(P: pd.Series) -> pd.Series:
    """
    6-month Antecedent Precipitation Index.
    API₆(t) = Σ 0.85^i × P(t-i)  for i = 0..5

    Decay factor 0.85 = standard hydrological recession (CLAUDE.md Part 6).
    Returns NaN for first 5 months (insufficient history).
    """
    api6 = pd.Series(np.nan, index=P.index, name='API6')
    vals = P.values
    for i in range(5, len(vals)):
        api6.iloc[i] = sum(API6_DECAY**j * vals[i - j] for j in range(6))
    return api6


def compute_p3(P: pd.Series) -> pd.Series:
    """3-month cumulative precipitation P₃(t) = P(t) + P(t-1) + P(t-2)."""
    return P.rolling(3).sum().rename('P3_mm')


def compute_scs_cn_inflow(P: pd.Series,
                           CN: float = SCS_CN_DEFAULT,
                           catchment_area_km2: float = CATCHMENT_AREA_KM2) -> pd.Series:
    """
    Monthly inflow proxy using SCS Curve Number rainfall-runoff model.

    Q_mm = (P - Ia)² / (P - Ia + S)   if P > Ia, else 0
    S  = 25400/CN - 254   (maximum potential retention, mm)
    Ia = 0.2 × S          (initial abstraction)

    Returns runoff in BCM.
    CN=75 default: mixed land use, Class C soil (Jharkhand hillsides).
    Update after HWSD soil group download.
    """
    S  = 25400.0 / CN - 254.0
    Ia = 0.2 * S

    def _runoff(P_mm):
        if np.isnan(P_mm) or P_mm <= Ia:
            return np.nan if np.isnan(P_mm) else 0.0
        return (P_mm - Ia)**2 / (P_mm - Ia + S)

    Q_mm = P.map(_runoff)
    # Convert mm over catchment → BCM
    Q_bcm = Q_mm * catchment_area_km2 * 1e6 * 1e-3 * 1e-9
    return Q_bcm.rename('Q_inflow_bcm')


def compute_monsoon_onset_anomaly(P: pd.Series) -> pd.Series:
    """
    Per year: first month where P > 100 mm = monsoon onset proxy.
    Anomaly = onset_month - long-term median onset month.
    Returns annual value forward-filled to monthly.
    """
    years = P.index.year.unique()
    onset = {}
    for yr in years:
        yr_P = P[P.index.year == yr]
        candidates = yr_P[yr_P > 100]
        onset[yr] = candidates.index[0].month if len(candidates) > 0 else np.nan

    onset_series = pd.Series(onset)
    median_onset = onset_series.median()
    anom = onset_series - median_onset

    # Map annual anomaly to monthly index
    result = pd.Series(np.nan, index=P.index, name='MO_anom')
    for yr, val in anom.items():
        result[result.index.year == yr] = val
    return result


# ═══════════════════════════════════════════════════════════════════
# STEP 3: External climate indices (ENSO + IOD)
# ═══════════════════════════════════════════════════════════════════

def load_enso_iod(raw_dir: Path, date_idx: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Load Niño 3.4 and IOD/DMI monthly indices.
    Applies 3-month lag to Niño 3.4 (documented teleconnection delay to Damodar).

    Expected file formats (flexible parser handles common NOAA/JAMSTEC formats):
      nino34_monthly.csv  — columns: year, month, value  OR  date, value
      iod_dmi_monthly.csv — columns: year, month, value  OR  date, value
    """
    result = pd.DataFrame(index=date_idx)
    result['Nino34'] = np.nan
    result['DMI']    = np.nan

    def _parse_index_file(path: Path, value_col_hint: str) -> pd.Series:
        """Flexible parser for NOAA/JAMSTEC climate index files."""
        df = pd.read_csv(path, comment='#', skipinitialspace=True)
        df.columns = [c.strip().lower() for c in df.columns]

        # Case 1: has 'date' column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.to_period('M').dt.to_timestamp()
            val_col = [c for c in df.columns if c != 'date'][0]
            return df.set_index('date')[val_col]

        # Case 2: has 'year' and 'month' columns
        if 'year' in df.columns and 'month' in df.columns:
            df['date'] = pd.to_datetime(
                df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2) + '-01'
            )
            # Find value column (not year/month)
            val_cols = [c for c in df.columns if c not in ('year', 'month', 'date')]
            val_col  = val_cols[0] if val_cols else value_col_hint
            return df.set_index('date')[val_col]

        raise ValueError(f"Cannot parse {path}: expected 'date' or 'year'+'month' columns")

    # Niño 3.4 with 3-month lag
    p = raw_dir / 'nino34_monthly.csv'
    if p.exists():
        nino = _parse_index_file(p, 'nino34')
        nino_lagged = nino.shift(3)   # 3-month teleconnection lag
        result['Nino34'] = nino_lagged.reindex(date_idx)
        print(f"  Niño 3.4 (3-month lag): {result['Nino34'].notna().sum()} valid rows")
    else:
        warnings.warn(f"[WARN] {p} not found — Nino34 will be NaN. "
                      "Download from: https://psl.noaa.gov/data/climateindices/list/")

    # IOD / DMI (no lag needed)
    p = raw_dir / 'iod_dmi_monthly.csv'
    if p.exists():
        dmi = _parse_index_file(p, 'dmi')
        result['DMI'] = dmi.reindex(date_idx)
        print(f"  IOD/DMI: {result['DMI'].notna().sum()} valid rows")
    else:
        warnings.warn(f"[WARN] {p} not found — DMI will be NaN. "
                      "Download from: https://psl.noaa.gov/gcos_wgsp/Timeseries/DMI/")

    return result


# ═══════════════════════════════════════════════════════════════════
# STEP 4: Night lights (DMSP-OLS + Bhuvan crossover)
# ═══════════════════════════════════════════════════════════════════

def load_ntl(raw_dir: Path, date_idx: pd.DatetimeIndex) -> pd.Series:
    """
    Load DMSP-OLS annual night lights (2002–2013).
    If Bhuvan NTL CSV exists, crossover-calibrate at 2012–2013 overlap.
    Forward-fill annual values to monthly.
    Returns Series named 'NTL'.
    """
    result = pd.Series(np.nan, index=date_idx, name='NTL')

    p_dmsp = raw_dir / 'ntl_dmsp_annual.csv'
    if not p_dmsp.exists():
        warnings.warn(f"[WARN] {p_dmsp} not found — NTL will be NaN")
        return result

    dmsp = pd.read_csv(p_dmsp).set_index('year')['stable_lights']

    # Check for Bhuvan NTL (optional — download from bhuvan.nrsc.gov.in)
    p_bhuvan = raw_dir / 'ntl_bhuvan_annual.csv'
    if p_bhuvan.exists():
        bhuvan = pd.read_csv(p_bhuvan).set_index('year').iloc[:, 0]
        # Crossover calibration: linear regression DMSP → Bhuvan scale at 2012–2013
        overlap_years = dmsp.index.intersection(bhuvan.index)
        if len(overlap_years) >= 2:
            from numpy.polynomial import polynomial as P_poly
            coeffs = np.polyfit(dmsp[overlap_years], bhuvan[overlap_years], 1)
            scale, offset = coeffs
            # Apply crossover calibration to DMSP 2002–2011
            dmsp_cal = dmsp * scale + offset
            # Merge: calibrated DMSP (2002–2011) + Bhuvan (2012–2021)
            ntl_annual = pd.concat([
                dmsp_cal[dmsp_cal.index < 2012],
                bhuvan
            ]).sort_index()
            print(f"  NTL: DMSP crossover-calibrated to Bhuvan scale "
                  f"(slope={scale:.3f}, offset={offset:.2f})")
        else:
            ntl_annual = dmsp
            warnings.warn("[WARN] Insufficient overlap for DMSP-Bhuvan calibration")
    else:
        ntl_annual = dmsp
        warnings.warn(f"[WARN] Bhuvan NTL not found at {p_bhuvan}. "
                      "Using DMSP 2002–2013 only. Download from bhuvan.nrsc.gov.in")

    # Forward-fill annual → monthly
    for yr, val in ntl_annual.items():
        result[result.index.year == yr] = val
    result.ffill(inplace=True)

    print(f"  NTL: {result.notna().sum()} valid monthly rows")
    return result


# ═══════════════════════════════════════════════════════════════════
# STEP 5: Lagged storage features from Stage 1
# ═══════════════════════════════════════════════════════════════════

def load_lagged_storage(processed_dir: Path,
                         date_idx: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Load Maithon delta_S_obs_bcm from Stage 1 output.
    Compute 1-month and 3-month lags.
    Panchet excluded (D-012) — Maithon is primary.
    """
    result = pd.DataFrame(index=date_idx)
    result['dS_lag1'] = np.nan
    result['dS_lag3'] = np.nan

    p = processed_dir / 'DVC_storage_timeseries_2002_2024.csv'
    if not p.exists():
        warnings.warn(f"[WARN] Stage 1 output not found: {p} — lag features will be NaN")
        return result

    df = pd.read_csv(p, parse_dates=['date'])
    df['date'] = df['date'].dt.to_period('M').dt.to_timestamp()
    maithon = df[df['reservoir'] == 'maithon'].set_index('date')['delta_S_obs_bcm']

    result['dS_lag1'] = maithon.shift(1).reindex(date_idx)
    result['dS_lag3'] = maithon.shift(3).reindex(date_idx)

    print(f"  Storage lags (Maithon): "
          f"lag1={result['dS_lag1'].notna().sum()} valid, "
          f"lag3={result['dS_lag3'].notna().sum()} valid")
    return result


# ═══════════════════════════════════════════════════════════════════
# STEP 6: VIF check — iteratively drop features with VIF > threshold
# ═══════════════════════════════════════════════════════════════════

def vif_check(X_clean: pd.DataFrame, threshold: float = VIF_THRESHOLD) -> pd.DataFrame:
    """
    Compute Variance Inflation Factor for all numeric features.
    Iteratively drop the feature with highest VIF if > threshold.
    Log each dropped feature.
    Returns filtered DataFrame and saves vif_diagnostic.csv.
    """
    cols = X_clean.columns.tolist()
    dropped = []

    while True:
        vif_df = pd.DataFrame({
            'feature': cols,
            'VIF': [variance_inflation_factor(X_clean[cols].values, i)
                    for i in range(len(cols))]
        }).set_index('feature').sort_values('VIF', ascending=False)

        max_vif  = vif_df['VIF'].max()
        max_feat = vif_df['VIF'].idxmax()

        if max_vif <= threshold:
            break

        print(f"  [VIF] Dropping '{max_feat}' (VIF={max_vif:.1f} > {threshold})")
        dropped.append({'feature': max_feat, 'VIF': max_vif})
        cols.remove(max_feat)

    # Save full VIF diagnostics (including dropped)
    all_vif = pd.DataFrame({
        'feature': X_clean.columns,
        'VIF': [variance_inflation_factor(X_clean.values, i)
                for i in range(X_clean.shape[1])]
    })
    all_vif['dropped'] = all_vif['feature'].isin([d['feature'] for d in dropped])
    all_vif.to_csv(PROCESSED_DIR / 'vif_diagnostic.csv', index=False)
    print(f"  VIF diagnostic saved → data/processed/vif_diagnostic.csv")

    if dropped:
        print(f"  Dropped {len(dropped)} features: {[d['feature'] for d in dropped]}")
    else:
        print("  All features passed VIF < 10 ✓")

    return X_clean[cols]


# ═══════════════════════════════════════════════════════════════════
# STEP 7: Correlation heatmap
# ═══════════════════════════════════════════════════════════════════

def plot_correlation_heatmap(X: pd.DataFrame) -> None:
    """Save feature correlation matrix as Fig_feature_correlation.png."""
    corr = X.corr()

    fig, ax = plt.subplots(figsize=(14, 12), facecolor='#0d1117')
    ax.set_facecolor('#161b22')

    mask = np.zeros_like(corr, dtype=bool)
    mask[np.triu_indices_from(mask)] = True

    sns.heatmap(
        corr, mask=mask, ax=ax,
        cmap='RdBu_r', center=0, vmin=-1, vmax=1,
        annot=True, fmt='.2f', annot_kws={'size': 7},
        linewidths=0.3, linecolor='#30363d',
        cbar_kws={'shrink': 0.8}
    )

    ax.set_title('Feature Correlation Matrix — Stage 2\n'
                 'Flag: |r| > 0.75 pairs require PCA-SHAP treatment (SERIOUS-2)',
                 color='#e6edf3', fontsize=11, pad=12)
    ax.tick_params(colors='#8b949e', labelsize=8)

    # Highlight r > 0.75 pairs
    n = len(corr)
    for i in range(n):
        for j in range(i):
            if abs(corr.iloc[i, j]) > 0.75:
                ax.add_patch(plt.Rectangle((j, i), 1, 1,
                             fill=False, edgecolor='#d29922', linewidth=2))

    fig.text(0.5, 0.01,
             'Orange boxes: |r| > 0.75 — PCA-SHAP grouping required in Stage 3',
             ha='center', color='#d29922', fontsize=8)

    out = FIGURES_DIR / 'Fig_feature_correlation.png'
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#0d1117')
    plt.close()
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════

def main():
    _ensure_dirs()
    print('=' * 60)
    print('STAGE 2: Driver Dataset Construction')
    print('DVC Reservoir Attribution Project')
    print('=' * 60)

    date_idx = build_date_index()
    print(f"\nDate range: {date_idx[0].date()} to {date_idx[-1].date()} "
          f"({len(date_idx)} months)\n")

    # ── [1] GEE drivers ──────────────────────────────────────────────
    print('[1/7] Loading GEE driver CSVs...')
    X = load_gee_drivers(RAW_DIR, date_idx)

    # ── [2] Derived rainfall features ────────────────────────────────
    print('\n[2/7] Computing derived rainfall features...')
    if X['P_mm'].notna().any():
        X['P3_mm']  = compute_p3(X['P_mm'])
        X['API6']   = compute_api6(X['P_mm'])
        X['Q_inflow_bcm'] = compute_scs_cn_inflow(X['P_mm'])
        X['MO_anom']      = compute_monsoon_onset_anomaly(X['P_mm'])
        print(f"  API₆: {X['API6'].notna().sum()} valid (NaN for first 5 months expected)")
        print(f"  SCS-CN inflow: {X['Q_inflow_bcm'].notna().sum()} valid (CN={SCS_CN_DEFAULT})")
    else:
        warnings.warn("[WARN] P_mm all NaN — cannot compute derived rainfall features")
        for col in ['P3_mm', 'API6', 'Q_inflow_bcm', 'MO_anom']:
            X[col] = np.nan

    # ── [3] External climate indices ─────────────────────────────────
    print('\n[3/7] Loading ENSO / IOD indices...')
    enso_iod = load_enso_iod(RAW_DIR, date_idx)
    X['Nino34'] = enso_iod['Nino34']
    X['DMI']    = enso_iod['DMI']

    # Save merged ENSO/IOD for reference
    enso_iod.to_csv(PROCESSED_DIR / 'enso_iod_merged.csv')

    # ── [4] Night lights ─────────────────────────────────────────────
    print('\n[4/7] Loading night lights...')
    X['NTL'] = load_ntl(RAW_DIR, date_idx)

    # ── [5] Lagged storage from Stage 1 ──────────────────────────────
    print('\n[5/7] Loading lagged storage features (Stage 1 output)...')
    lags = load_lagged_storage(PROCESSED_DIR, date_idx)
    X['dS_lag1'] = lags['dS_lag1']
    X['dS_lag3'] = lags['dS_lag3']

    # ── [6] Feature matrix assembly ──────────────────────────────────
    print('\n[6/7] Assembling feature matrix...')

    # Ordered as per CLAUDE.md Part 6
    FEATURE_ORDER = [
        'P_mm', 'P3_mm', 'API6',
        'PET_mm', 'AET_mm', 'SM1', 'SM2', 'T_C',
        'NDVI', 'LC_crop', 'LC_for',
        'Nino34', 'DMI', 'NTL',
        'dS_lag1', 'dS_lag3',
        'Q_inflow_bcm', 'MO_anom'
    ]
    X = X[[c for c in FEATURE_ORDER if c in X.columns]]

    print(f"\n  Feature matrix shape: {X.shape} ({X.shape[0]} months × {X.shape[1]} features)")
    print(f"\n  NaN count per feature:")
    nan_counts = X.isna().sum()
    for feat, n in nan_counts.items():
        flag = ' ⚠' if n / len(X) > 0.10 else ''
        print(f"    {feat:20s}: {n:3d} NaN ({n/len(X)*100:.1f}%){flag}")

    # ── [7] VIF check ─────────────────────────────────────────────────
    print('\n[7/7] Running VIF check (drop features with VIF > 10)...')
    # Only run VIF on rows with no NaN
    X_complete = X.dropna()
    if len(X_complete) < 50:
        warnings.warn(f"[WARN] Only {len(X_complete)} complete rows for VIF — "
                      "run again after all GEE data downloaded")
        X_vif = X
    else:
        X_vif_filtered = vif_check(X_complete)
        # Apply dropped columns to full X
        X_vif = X[X_vif_filtered.columns]

    # ── Save outputs ──────────────────────────────────────────────────
    out_csv = PROCESSED_DIR / 'X_climate_final.csv'
    X_vif.to_csv(out_csv)
    print(f"\n  Saved: {out_csv}")
    print(f"  Shape: {X_vif.shape}")

    # ── Correlation heatmap ───────────────────────────────────────────
    X_for_plot = X_vif.dropna()
    if len(X_for_plot) >= 12:
        plot_correlation_heatmap(X_for_plot)

    # ── Validation summary ────────────────────────────────────────────
    print('\n' + '=' * 60)
    print('STAGE 2 SUMMARY')
    print('=' * 60)
    print(f"  Rows:     {len(X_vif)} (need 264)")
    print(f"  Features: {X_vif.shape[1]} (after VIF filtering)")

    if X_vif.shape[0] != 264:
        warnings.warn(f"[WARN] Expected 264 rows, got {X_vif.shape[0]}. "
                      "Check date alignment.")
    else:
        print("  Row count: 264 ✓")

    # Key validation: API₆ ↔ P_mm correlation (use pre-VIF X if P_mm was dropped)
    if 'API6' in X_vif.columns and 'P_mm' in X_vif.columns:
        api_corr = X_vif[['P_mm', 'API6']].dropna().corr().iloc[0, 1]
        flag = '✓' if 0.6 < api_corr < 0.90 else '⚠ (check API₆ formula)'
        print(f"  API₆ ↔ P_mm correlation: {api_corr:.3f} {flag}")
    elif 'API6' in X_vif.columns:
        # P_mm was dropped by VIF — compute correlation from raw X before VIF
        api_corr = X[['P_mm', 'API6']].dropna().corr().iloc[0, 1]
        flag = '✓' if 0.6 < api_corr < 0.90 else '⚠ (check API₆ formula)'
        print(f"  API₆ ↔ P_mm correlation (pre-VIF): {api_corr:.3f} {flag}")

    p_source = X_vif if 'P_mm' in X_vif.columns else X
    if 'P_mm' in p_source.columns:
        monsoon_mean = p_source.loc[p_source.index.month.isin([7, 8]), 'P_mm'].mean()
        flag = '✓' if monsoon_mean > 150 else '⚠ check CHIRPS units'
        print(f"  Jul-Aug P_mm mean: {monsoon_mean:.1f} mm {flag}")

    print('\n  Next: uv run python src/03_xgboost_attribution.py')
    print('  (After all GEE CSVs downloaded and ENSO/IOD indices saved)')
    print('=' * 60)


if __name__ == '__main__':
    main()
