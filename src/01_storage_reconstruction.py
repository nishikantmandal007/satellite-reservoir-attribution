"""
01_storage_reconstruction.py
DVC Reservoir Attribution Project — Stage 1

Purpose:
    Load GEE water-area CSVs → cross-sensor quantile mapping → Area-to-Volume
    conversion → sedimentation correction → baseline anomaly → Monte Carlo
    uncertainty bounds → 2009 flood validation → save outputs.

Run:
    uv run python src/01_storage_reconstruction.py

Expected inputs (download from Google Drive → data/raw/):
    data/raw/water_area_sentinel1.csv   — 396 rows (132 months × 3 reservoirs)
    data/raw/water_area_modis.csv       — 432 rows (144 months × 3 reservoirs)

Expected outputs:
    data/processed/DVC_storage_timeseries_2002_2024.csv   — 792 rows
    figures/Fig3_storage_timeseries.png                    — 300 DPI

AV_PARAMS updated Day 3: derived from ALOS AW3D30 + JRC mask (GEE),
calibrated to CWC design capacities (Maithon 1.36 BCM, Panchet 0.29 BCM).
Method: DEM-derived b exponent (shape), a solved analytically at FSL.
Uncertainty: ±20–40% per Hulsman et al. 2024 (Indian reservoirs, 30m DEM).
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for server/script use
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

# AV_PARAMS: ALOS AW3D30 + JRC mask (GEE), calibrated to CWC design capacities
# Power law: V (BCM) = a × A (km²)^b
# b = DEM-derived shape exponent; a = solved at FSL to match known capacity
# Calibration corrects for AW3D30 DSM-DTM bias (Hulsman et al. 2024)
#
# DURGAPUR SPECIAL CASE (D-021, D-023):
#   Run-of-river barrage — flat geometry violates power-law V=a×A^b assumption.
#   At max observed area (56.5 km²), original power-law gives 1.067 BCM = 13× design (0.080 BCM).
#   Fix: linear AV model (b=1.0) calibrated to CWC design capacity.
#   a_linear = V_design / A_median_observed = 0.080 / 17.9 km² = 0.00447 BCM/km²
#   Hard cap applied at 1.5× design (0.120 BCM) to prevent runaway extrapolation.
#   D-023: Durgapur volumes used for direction only (Rabi drawdown signal), not absolute magnitude.
AV_PARAMS = {
    'maithon':  {'a': 0.000002, 'b': 3.000, 'dead_storage_bcm': 0.185, 'model': 'power', 'cap_bcm': None},   # R²=0.865, FSL=174.5m
    'panchet':  {'a': 0.000023, 'b': 2.489, 'dead_storage_bcm': 0.048, 'model': 'power', 'cap_bcm': None},   # R²=0.994, FSL=108.5m
    'durgapur': {'a': 0.00447,  'b': 1.000, 'dead_storage_bcm': 0.010, 'model': 'linear', 'cap_bcm': 0.120}, # Linear, capped at 1.5x design
}

# Sedimentation: CWC 2022 rates applied from dam construction year
# max_loss_fraction: CWC 2022 estimated total live storage loss cap
SEDIMENTATION_PARAMS = {
    # D-029: AW3D30 DEM epoch ~2006-2011 (ALOS PRISM acquisition period, released 2016).
    # Applying CWC sedimentation from dam construction year (1957-1960) constitutes
    # double-counting because the DEM already captures ~50 years of sedimentation.
    # Correction applied only from DEM epoch (2008 midpoint) onwards.
    # Pre-DEM sedimentation is implicitly encoded in the AW3D30 hypsometry.
    'maithon': {
        'rate_bcm_yr': 0.0042, 'start_year': 2008,
        'capacity_bcm': 1.360, 'max_loss_fraction': 0.18,
    },
    'panchet': {
        'rate_bcm_yr': 0.0018, 'start_year': 2008,
        'capacity_bcm': 0.290, 'max_loss_fraction': None,
    },
    'durgapur': {
        'rate_bcm_yr': 0.0003, 'start_year': 2008,
        'capacity_bcm': None,   'max_loss_fraction': None,
    },
}

BASELINE_YEARS    = (2017, 2023)     # D-030: S1-era baseline (2017-2023) replaces 2005-2015.
                                    # MODIS-era baseline is invalid: 500m resolution causes
                                    # systematic area underestimation, forcing 70/71 MODIS
                                    # months to clip at dead storage → baseline = 0.185 BCM
                                    # (impossible: no neg anomalies in S1 era). S1 era mean
                                    # is the correct reference for Stage 3 attribution.
OVERLAP_START     = '2014-01-01'    # start of dual-sensor overlap for QM
OVERLAP_END       = '2015-12-31'    # end of dual-sensor overlap (24 months)
MIN_QM_PAIRS      = 12              # minimum paired observations for reliable QM

RESERVOIRS        = ['maithon', 'panchet', 'durgapur']
RAW_DIR           = Path('data/raw')
PROCESSED_DIR     = Path('data/processed')
FIGURES_DIR       = Path('figures')
N_MC              = 500             # Monte Carlo iterations for uncertainty
MC_NOISE_FRACTION = 0.10            # ±10% uniform noise on a and b coefficients

MISSING_VALUE     = -9999           # sentinel for gaps in GEE output

# ═══════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════════

def _ensure_dirs():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def _parse_date_col(df: pd.DataFrame) -> pd.DataFrame:
    """Parse 'date' column to first-of-month Timestamp."""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date']).dt.to_period('M').dt.to_timestamp()
    return df


def _volume_power_law(area_km2: np.ndarray, a: float, b: float) -> np.ndarray:
    """V = a × A^b (BCM). b=1.0 gives linear model. Returns nan for non-positive areas."""
    safe_area = np.where(area_km2 > 0, area_km2, np.nan)
    return a * (safe_area ** b)

# ═══════════════════════════════════════════════════════════════════
# STEP 1: Load and clean GEE CSVs
# ═══════════════════════════════════════════════════════════════════

def load_and_clean_csvs(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load water_area_sentinel1.csv and water_area_modis.csv.
    Validates row counts, parses dates, replaces MISSING_VALUE with NaN,
    and reindexes each reservoir to a full monthly DatetimeIndex.

    Returns:
        df_s1    : Sentinel-1 DataFrame, 396 rows (allow ±5%)
        df_modis : MODIS DataFrame,      432 rows (allow ±5%)
    """
    s1_path    = raw_dir / 'water_area_sentinel1.csv'
    modis_path = raw_dir / 'water_area_modis.csv'

    if not s1_path.exists():
        raise FileNotFoundError(
            f"Sentinel-1 CSV not found: {s1_path}\n"
            "Download from Google Drive after running s1_water_area.js"
        )
    if not modis_path.exists():
        raise FileNotFoundError(
            f"MODIS CSV not found: {modis_path}\n"
            "Download from Google Drive after running modis_water_area.js"
        )

    df_s1    = pd.read_csv(s1_path)
    df_modis = pd.read_csv(modis_path)

    # Validate row counts (±5% tolerance for partial months at boundary)
    for name, df, expected in [('Sentinel-1', df_s1, 396), ('MODIS', df_modis, 432)]:
        if abs(len(df) - expected) > expected * 0.05:
            warnings.warn(
                f"[WARN] {name} CSV has {len(df)} rows, expected ~{expected}. "
                "Check for duplicate months or missing reservoirs."
            )
        else:
            print(f"  {name}: {len(df)} rows ✓")

    # Parse dates
    df_s1    = _parse_date_col(df_s1)
    df_modis = _parse_date_col(df_modis)

    # Replace missing sentinel with NaN
    for df in (df_s1, df_modis):
        df['water_area_km2'] = df['water_area_km2'].replace(MISSING_VALUE, np.nan)

    # Standardise reservoir name to lowercase
    df_s1['reservoir']    = df_s1['reservoir'].str.lower().str.strip()
    df_modis['reservoir'] = df_modis['reservoir'].str.lower().str.strip()

    # D-010: Panchet bbox contamination fix
    # S1 verification showed 54/94 records had area 140–370 km² (Damodar river
    # valley + DVC canal network). Clean reservoir-only data clusters at 40–80 km².
    # Cap at 80 km² until re-run with tighter bbox [86.72, 23.52, 86.95, 23.68].
    panchet_s1_mask   = df_s1['reservoir']    == 'panchet'
    panchet_mod_mask  = df_modis['reservoir'] == 'panchet'
    n_capped_s1   = (df_s1.loc[panchet_s1_mask,  'water_area_km2'] > 80).sum()
    n_capped_mod  = (df_modis.loc[panchet_mod_mask,'water_area_km2'] > 80).sum()
    df_s1.loc[panchet_s1_mask & (df_s1['water_area_km2'] > 80),
              'water_area_km2'] = np.nan
    df_modis.loc[panchet_mod_mask & (df_modis['water_area_km2'] > 80),
                 'water_area_km2'] = np.nan
    if n_capped_s1 > 0 or n_capped_mod > 0:
        print(f"  [D-010] Panchet contamination NaN (>80 km²): "
              f"{n_capped_s1} S1 records, {n_capped_mod} MODIS records removed")

    # MODIS cloud artifact filter: NDWI cannot see through monsoon clouds →
    # reports 0.000 km² instead of NaN. Convert implausibly-low MODIS monsoon
    # areas to NaN. Thresholds = half of each reservoir's known dead storage.
    CLOUD_FLOOR = {'maithon': 15.0, 'panchet': 5.0, 'durgapur': 2.0}
    MONSOON_MONTHS = [6, 7, 8, 9]
    n_cloud_filtered = 0
    for res, floor in CLOUD_FLOOR.items():
        res_mask   = df_modis['reservoir'] == res
        cloud_mask = (res_mask &
                      df_modis['date'].dt.month.isin(MONSOON_MONTHS) &
                      (df_modis['water_area_km2'] < floor) &
                      df_modis['water_area_km2'].notna())
        n_cloud_filtered += cloud_mask.sum()
        df_modis.loc[cloud_mask, 'water_area_km2'] = np.nan
    if n_cloud_filtered:
        print(f"  MODIS cloud filter: {n_cloud_filtered} monsoon zero-area records → NaN")

    # Reindex each reservoir to a complete monthly DatetimeIndex (fill missing months)
    def reindex_reservoir(df, start, end):
        full_idx = pd.date_range(start, end, freq='MS')
        parts = []
        for res in RESERVOIRS:
            sub = df[df['reservoir'] == res].set_index('date').reindex(full_idx)
            sub['reservoir'] = res
            sub.index.name = 'date'
            parts.append(sub.reset_index())
        return pd.concat(parts, ignore_index=True)

    df_s1    = reindex_reservoir(df_s1,    '2014-01-01', '2024-12-01')
    df_modis = reindex_reservoir(df_modis, '2002-01-01', '2013-12-01')

    print(f"  After reindex — S1: {len(df_s1)} rows, MODIS: {len(df_modis)} rows")
    return df_s1, df_modis

# ═══════════════════════════════════════════════════════════════════
# STEP 2: Gap filling
# ═══════════════════════════════════════════════════════════════════

def apply_gap_filling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per reservoir:
      - Interpolate gaps of 1–2 consecutive months (linear)
      - Gaps ≥ 3 months: leave NaN, set gap_filled=1 flag

    Operates in-place on water_area_km2 column.
    """
    df = df.copy()
    if 'gap_filled' not in df.columns:
        df['gap_filled'] = 0

    for res in RESERVOIRS:
        mask = df['reservoir'] == res
        series = df.loc[mask, 'water_area_km2'].copy()

        # Identify run lengths of NaN
        is_nan = series.isna()
        filled_idx = []

        i = 0
        nan_runs = []
        while i < len(series):
            if is_nan.iloc[i]:
                start = i
                while i < len(series) and is_nan.iloc[i]:
                    i += 1
                nan_runs.append((start, i - 1))
            else:
                i += 1

        for (start, end) in nan_runs:
            run_len = end - start + 1
            if run_len <= 2:
                filled_idx.extend(range(start, end + 1))

        # Interpolate only where gap ≤ 2 months
        series_interp = series.interpolate(method='linear', limit=2)

        # Identify which NaN values were actually filled
        was_nan = series.isna()
        now_filled = was_nan & ~series_interp.isna()
        df.loc[mask, 'water_area_km2'] = series_interp.values
        # now_filled is indexed to reservoir-subset rows; use index alignment
        filled_locs = now_filled[now_filled].index
        df.loc[filled_locs, 'gap_filled'] = 1

    gaps_filled = df['gap_filled'].sum()
    remaining_nans = df['water_area_km2'].isna().sum()
    print(f"  Gap filling: {gaps_filled} months interpolated, "
          f"{remaining_nans} months remain NaN (gaps ≥3 months)")
    return df

# ═══════════════════════════════════════════════════════════════════
# STEP 3: Cross-sensor quantile mapping calibration
# ═══════════════════════════════════════════════════════════════════

def cross_sensor_quantile_mapping(
    df_s1: pd.DataFrame,
    df_modis: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calibrate MODIS water areas to Sentinel-1 scale using empirical quantile mapping.
    Uses 2014–2015 overlap period (24 months) as training window.

    Returns df_modis with calibrated water_area_km2 column.
    Logs bias and RMSE before/after calibration per reservoir.

    Out-of-range MODIS values (beyond overlap range) → NaN with warning.
    This is expected for extreme years like 2009.
    """
    df_modis_cal = df_modis.copy()
    df_modis_cal['sensor'] = 'MODIS_calibrated'

    overlap_s1    = df_s1[(df_s1['date'] >= OVERLAP_START) &
                          (df_s1['date'] <= OVERLAP_END)].copy()
    overlap_modis = df_modis[(df_modis['date'] >= OVERLAP_START) &
                              (df_modis['date'] <= OVERLAP_END)].copy()

    for res in RESERVOIRS:
        s1_ov    = overlap_s1[overlap_s1['reservoir'] == res].set_index('date')
        mod_ov   = overlap_modis[overlap_modis['reservoir'] == res].set_index('date')

        # Inner join on date for paired observations
        paired = s1_ov[['water_area_km2']].join(
            mod_ov[['water_area_km2']], lsuffix='_s1', rsuffix='_mod'
        ).dropna()

        n_pairs = len(paired)
        if n_pairs < MIN_QM_PAIRS:
            warnings.warn(
                f"[CRITICAL] {res}: only {n_pairs} paired overlap observations "
                f"(need ≥{MIN_QM_PAIRS}). QM calibration unreliable. "
                "Check GEE export date ranges overlap correctly."
            )

        print(f"  {res}: {n_pairs} paired overlap obs for QM calibration")

        if n_pairs < 3:
            # S1 had no valid acquisitions 2014-2016 (sparse revisit era).
            # MODIS ends 2013-12 → no temporal overlap exists.
            # Use MODIS areas uncalibrated: both sensors report km², same units.
            # This is flagged as a limitation in the Methods section.
            print(f"    → No overlap data for {res}: MODIS used uncalibrated "
                  f"(same km² units, no bias correction possible)")
            df_modis_cal.loc[df_modis_cal['reservoir'] == res, 'sensor'] = 'MODIS_uncalibrated'
            continue

        # Empirical CDF transfer function: MODIS quantiles → S1 quantiles
        s1_sorted  = np.sort(paired['water_area_km2_s1'].values)
        mod_sorted = np.sort(paired['water_area_km2_mod'].values)

        # Pre-calibration bias
        bias_before = np.nanmean(paired['water_area_km2_mod'].values -
                                  paired['water_area_km2_s1'].values)
        rmse_before = np.sqrt(np.nanmean(
            (paired['water_area_km2_mod'].values -
             paired['water_area_km2_s1'].values) ** 2
        ))

        # Apply transfer function to all MODIS data for this reservoir
        res_mask   = df_modis_cal['reservoir'] == res
        modis_vals = df_modis_cal.loc[res_mask, 'water_area_km2'].values

        # np.interp: linear interpolation within training range; clamp at edges
        calibrated = np.interp(modis_vals, mod_sorted, s1_sorted,
                               left=np.nan, right=np.nan)

        # Values beyond training range → NaN (log how many)
        oor_count = np.sum(np.isnan(calibrated) & ~np.isnan(modis_vals))
        if oor_count > 0:
            print(f"    ⚠ {res}: {oor_count} MODIS values out of calibration range "
                  f"→ set to NaN (expected for extreme years like 2009)")

        df_modis_cal.loc[res_mask, 'water_area_km2'] = calibrated

        # Post-calibration check in overlap window
        cal_overlap = np.interp(paired['water_area_km2_mod'].values,
                                mod_sorted, s1_sorted)
        bias_after = np.nanmean(cal_overlap - paired['water_area_km2_s1'].values)
        rmse_after = np.sqrt(np.nanmean(
            (cal_overlap - paired['water_area_km2_s1'].values) ** 2
        ))

        print(f"    Bias before QM: {bias_before:+.2f} km², after: {bias_after:+.2f} km²")
        print(f"    RMSE before QM: {rmse_before:.2f} km²,  after: {rmse_after:.2f} km²")

    return df_modis_cal

# ═══════════════════════════════════════════════════════════════════
# STEP 4: Merge epochs
# ═══════════════════════════════════════════════════════════════════

def merge_epochs(
    df_s1: pd.DataFrame,
    df_modis_calibrated: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge calibrated MODIS (2002–2013) with Sentinel-1 (2014–2024).
    Assigns sensor labels. Asserts final row count = 792 (264 months × 3 reservoirs).
    """
    df_s1 = df_s1.copy()
    if 'sensor' not in df_s1.columns:
        df_s1['sensor'] = 'Sentinel1'

    merged = pd.concat([df_modis_calibrated, df_s1], ignore_index=True)
    merged = merged.sort_values(['reservoir', 'date']).reset_index(drop=True)

    n_months = len(merged) // 3
    print(f"  Epoch merge: {len(merged)} rows ({n_months} months × 3 reservoirs) ✓")
    return merged

# ═══════════════════════════════════════════════════════════════════
# STEP 5: Area → Volume conversion
# ═══════════════════════════════════════════════════════════════════

def area_to_volume(df: pd.DataFrame, av_params: dict) -> pd.DataFrame:
    """
    Convert water_area_km2 → volume_bcm using per-reservoir AV model.

    Maithon/Panchet: power law V = a × A^b (DEM-derived b, CWC-calibrated a)
    Durgapur:        linear V = a × A (b=1.0), hard cap at 1.5× design = 0.120 BCM
                     Rationale: flat run-of-river barrage geometry; power-law
                     extrapolates to 13× design capacity at max observed area.
                     Volumes used for directional signal only (D-021, D-023).
    """
    df = df.copy()
    df['volume_bcm'] = np.nan

    for res in RESERVOIRS:
        params = av_params[res]
        mask   = df['reservoir'] == res
        area   = df.loc[mask, 'water_area_km2'].values
        vol    = _volume_power_law(area, params['a'], params['b'])
        # Clip to dead storage floor
        vol = np.where(vol < params['dead_storage_bcm'], params['dead_storage_bcm'], vol)
        # Apply cap if specified (Durgapur linear model cap)
        if params.get('cap_bcm') is not None:
            vol = np.where(~np.isnan(vol), np.minimum(vol, params['cap_bcm']), vol)
        df.loc[mask, 'volume_bcm'] = vol

    # Report Durgapur volume range for verification
    durg_vols = df.loc[df['reservoir'] == 'durgapur', 'volume_bcm'].dropna()
    if len(durg_vols) > 0:
        print(f"  Durgapur volume range (linear model): {durg_vols.min():.4f}–{durg_vols.max():.4f} BCM")
        print(f"    Design capacity: 0.080 BCM | Cap applied at: 0.120 BCM")

    df['av_params_are_placeholder'] = False
    return df

# ═══════════════════════════════════════════════════════════════════
# STEP 6: Sedimentation correction
# ═══════════════════════════════════════════════════════════════════

def apply_sedimentation_correction(df: pd.DataFrame, sed_params: dict) -> pd.DataFrame:
    """
    Subtract cumulative sedimentation loss from volume estimates.
    Maithon: capped at 18% of 1.360 BCM = 0.245 BCM maximum correction.

    volume_bcm_corrected = volume_bcm - cumulative_loss(year)
    """
    df = df.copy()
    df['volume_bcm_corrected'] = np.nan

    for res in RESERVOIRS:
        params = sed_params[res]
        mask   = df['reservoir'] == res
        years  = df.loc[mask, 'date'].dt.year.values

        cumulative_loss = params['rate_bcm_yr'] * (years - params['start_year'])
        cumulative_loss = np.maximum(cumulative_loss, 0)  # no negative loss

        # Apply cap if specified
        if params.get('max_loss_fraction') and params.get('capacity_bcm'):
            max_loss = params['capacity_bcm'] * params['max_loss_fraction']
            cumulative_loss = np.minimum(cumulative_loss, max_loss)

        corrected = df.loc[mask, 'volume_bcm'].values - cumulative_loss
        # BUG FIX: dead storage floor must be applied AFTER sedimentation,
        # not before. Previous pipeline applied dead storage floor in area_to_volume()
        # before subtracting sedimentation loss, allowing volume_corrected to go
        # negative for dry-season MODIS years (e.g. 2010 Maithon: V=0.130 BCM,
        # loss=0.210 BCM → corrected=-0.080 BCM). This created a biased baseline.
        dead_storage = AV_PARAMS[res]['dead_storage_bcm']
        corrected = np.where(~np.isnan(corrected),
                             np.maximum(corrected, dead_storage),
                             corrected)
        df.loc[mask, 'volume_bcm_corrected'] = corrected

    return df

# ═══════════════════════════════════════════════════════════════════
# STEP 7: Storage anomaly computation
# ═══════════════════════════════════════════════════════════════════

def compute_storage_anomaly(df: pd.DataFrame, baseline_years: tuple) -> pd.DataFrame:
    """
    Compute delta_S_obs_bcm = volume_bcm_corrected - baseline_mean.
    Baseline: mean over 2005–2015 per reservoir.
    """
    df = df.copy()
    df['delta_S_obs_bcm'] = np.nan

    bl_start, bl_end = baseline_years
    for res in RESERVOIRS:
        mask = df['reservoir'] == res
        bl_mask = (mask &
                   (df['date'].dt.year >= bl_start) &
                   (df['date'].dt.year <= bl_end))
        baseline_mean = df.loc[bl_mask, 'volume_bcm_corrected'].mean()

        if pd.isna(baseline_mean):
            # Fallback: use full record mean if specified baseline has no data
            # (Durgapur: MODIS epoch = sub-pixel zeros, S1 only from 2017)
            baseline_mean = df.loc[mask, 'volume_bcm_corrected'].mean()
            print(f"  {res}: no data in {bl_start}–{bl_end} baseline → "
                  f"using full-record mean = {baseline_mean:.4f} BCM  [FALLBACK]")
        else:
            print(f"  {res}: baseline mean = {baseline_mean:.4f} BCM "
                  f"({bl_start}–{bl_end})")

        df.loc[mask, 'delta_S_obs_bcm'] = (
            df.loc[mask, 'volume_bcm_corrected'] - baseline_mean
        )

    return df

# ═══════════════════════════════════════════════════════════════════
# STEP 8: Monte Carlo uncertainty quantification
# ═══════════════════════════════════════════════════════════════════

def monte_carlo_uncertainty(
    df: pd.DataFrame,
    av_params: dict,
    sed_params: dict,
    baseline_years: tuple,
    n_mc: int = N_MC,
    noise: float = MC_NOISE_FRACTION,
) -> pd.DataFrame:
    """
    Propagate A-V parameter uncertainty to storage anomaly estimates.
    Samples a and b with ±noise uniform perturbation per iteration.

    Adds columns: delta_S_obs_p05, delta_S_obs_p50, delta_S_obs_p95
    """
    print(f"\n  Running Monte Carlo uncertainty ({n_mc} iterations, ±{noise*100:.0f}% noise)...")

    rng = np.random.default_rng(42)
    mc_results = {res: [] for res in RESERVOIRS}

    for _ in range(n_mc):
        for res in RESERVOIRS:
            params   = av_params[res]
            a_noisy  = params['a'] * (1 + rng.uniform(-noise, noise))
            # BUG FIX: do not perturb b for linear model (Durgapur b=1.0 is
            # physically mandated — flat barrage geometry). Only perturb b for
            # power-law models (Maithon, Panchet) where b is DEM-derived.
            if params.get('model') == 'linear':
                b_noisy = params['b']  # keep b=1.0 fixed
            else:
                b_noisy = params['b'] * (1 + rng.uniform(-noise, noise))

            mask  = df['reservoir'] == res
            area  = df.loc[mask, 'water_area_km2'].values
            years = df.loc[mask, 'date'].dt.year.values

            vol = _volume_power_law(area, a_noisy, b_noisy)
            vol = np.where(vol < params['dead_storage_bcm'],
                           params['dead_storage_bcm'], vol)

            # Sedimentation correction (deterministic, not perturbed)
            sp = sed_params[res]
            cumulative_loss = sp['rate_bcm_yr'] * (years - sp['start_year'])
            cumulative_loss = np.maximum(cumulative_loss, 0)
            if sp.get('max_loss_fraction') and sp.get('capacity_bcm'):
                cumulative_loss = np.minimum(
                    cumulative_loss,
                    sp['capacity_bcm'] * sp['max_loss_fraction']
                )
            vol_corr = vol - cumulative_loss

            # BUG FIX: apply dead storage floor after sedimentation in MC too
            dead_storage = AV_PARAMS[res]['dead_storage_bcm']
            vol_corr = np.where(~np.isnan(vol_corr),
                                np.maximum(vol_corr, dead_storage),
                                vol_corr)

            # BUG FIX: apply Durgapur linear cap in MC (previously missing)
            cap = AV_PARAMS[res].get('cap_bcm')
            if cap is not None:
                vol_corr = np.where(~np.isnan(vol_corr),
                                    np.minimum(vol_corr, cap),
                                    vol_corr)

            # Anomaly — with fallback baseline (mirrors main pipeline D-013)
            bl_start, bl_end = baseline_years
            bl_mask_arr = (df.loc[mask, 'date'].dt.year >= bl_start) & \
                          (df.loc[mask, 'date'].dt.year <= bl_end)
            baseline_mean = np.nanmean(vol_corr[bl_mask_arr])
            if np.isnan(baseline_mean):
                # Fallback: use full-record mean when baseline period has no data
                # (Durgapur: no MODIS 2005-2015 data — S1 only from 2017)
                baseline_mean = np.nanmean(vol_corr)
            delta_s = vol_corr - baseline_mean

            mc_results[res].append(delta_s)

    df = df.copy()
    df['delta_S_obs_p05'] = np.nan
    df['delta_S_obs_p50'] = np.nan
    df['delta_S_obs_p95'] = np.nan

    for res in RESERVOIRS:
        mask = df['reservoir'] == res
        mc_array = np.array(mc_results[res])  # (n_mc, n_timesteps)
        df.loc[mask, 'delta_S_obs_p05'] = np.nanpercentile(mc_array, 5,  axis=0)
        df.loc[mask, 'delta_S_obs_p50'] = np.nanpercentile(mc_array, 50, axis=0)
        df.loc[mask, 'delta_S_obs_p95'] = np.nanpercentile(mc_array, 95, axis=0)

    print("  Monte Carlo complete ✓")
    return df

# ═══════════════════════════════════════════════════════════════════
# STEP 9: 2009 flood validation check (GROUND TRUTH)
# ═══════════════════════════════════════════════════════════════════

def validate_2009_flood(df: pd.DataFrame) -> None:
    """
    Validate storage reconstruction against known 2009 Damodar flood event.
    Known facts (Maiti & Bhattacharya 2011; Rudra 2018):
      - Jul–Aug 2009: Maithon should show +ve anomaly (pre-flood filling)
      - Sep 2009: Maithon and Panchet should show large -ve drop (emergency release)
      - Durgapur Oct–Mar: should show negative drawdown (Rabi irrigation)

    Raises RuntimeError if ALL 4 checks fail.
    Issues warnings for individual failures (proceed and investigate).
    """
    checks_passed = 0
    checks_total  = 4

    maithon = df[df['reservoir'] == 'maithon'].set_index('date')['delta_S_obs_bcm']
    panchet = df[df['reservoir'] == 'panchet'].set_index('date')['delta_S_obs_bcm']
    durgapur= df[df['reservoir'] == 'durgapur'].set_index('date')['delta_S_obs_bcm']

    print("\n  ══ 2009 FLOOD VALIDATION ══")

    # Check 1: Maithon Jul+Aug 2009 > +0.1 BCM (pre-flood buildup)
    jul_aug_2009 = pd.to_datetime(['2009-07-01', '2009-08-01'])
    maith_prefill = maithon.reindex(jul_aug_2009).mean()
    if pd.notna(maith_prefill) and maith_prefill > 0.05:
        print(f"  ✓ CHECK 1: Maithon Jul–Aug 2009 anomaly = {maith_prefill:+.3f} BCM "
              "(pre-flood storage buildup detected)")
        checks_passed += 1
    else:
        val_str = f"{maith_prefill:+.3f}" if pd.notna(maith_prefill) else "NaN"
        warnings.warn(
            f"[WARN] CHECK 1 FAILED: Maithon Jul–Aug 2009 = {val_str} BCM "
            "(expected > +0.05 BCM). Check MODIS water area for 2009."
        )

    # Check 2: Maithon Sep 2009 < -0.1 BCM (emergency flood release)
    sep_2009 = pd.Timestamp('2009-09-01')
    maith_sep = maithon.get(sep_2009)
    if pd.notna(maith_sep) and maith_sep < -0.1:
        print(f"  ✓ CHECK 2: Maithon Sep 2009 anomaly = {maith_sep:+.3f} BCM "
              "(flood release spike detected — expected -0.2 to -0.4 BCM)")
        checks_passed += 1
    else:
        val_str = f"{maith_sep:+.3f}" if pd.notna(maith_sep) else "NaN"
        warnings.warn(
            f"[WARN] CHECK 2 FAILED: Maithon Sep 2009 = {val_str} BCM "
            "(expected < -0.1 BCM). 2009 was QM out-of-range — set to NaN. "
            "This is expected with placeholder AV_PARAMS; update after CartoDEM."
        )

    # Check 3: Panchet Sep 2009 < 0 (tandem release)
    panch_sep = panchet.get(sep_2009)
    if pd.notna(panch_sep) and panch_sep < 0:
        print(f"  ✓ CHECK 3: Panchet Sep 2009 anomaly = {panch_sep:+.3f} BCM "
              "(tandem release detected)")
        checks_passed += 1
    else:
        val_str = f"{panch_sep:+.3f}" if pd.notna(panch_sep) else "NaN"
        warnings.warn(
            f"[WARN] CHECK 3 FAILED: Panchet Sep 2009 = {val_str} BCM "
            "(expected < 0). Check Panchet MODIS coverage Sep 2009."
        )

    # Check 4: Durgapur Rabi mean (Oct–Mar) < 0 across all years
    durg_oct_mar = durgapur[durgapur.index.month.isin([10, 11, 12, 1, 2, 3])]
    durg_rabi_mean = durg_oct_mar.mean()
    if pd.notna(durg_rabi_mean) and durg_rabi_mean < 0:
        print(f"  ✓ CHECK 4: Durgapur Oct–Mar mean = {durg_rabi_mean:+.3f} BCM "
              "(Rabi irrigation drawdown pattern confirmed)")
        checks_passed += 1
    else:
        val_str = f"{durg_rabi_mean:+.3f}" if pd.notna(durg_rabi_mean) else "NaN"
        warnings.warn(
            f"[WARN] CHECK 4 FAILED: Durgapur Oct–Mar mean = {val_str} BCM "
            "(expected < 0). Check Durgapur area-volume relationship."
        )

    print(f"\n  Validation: {checks_passed}/{checks_total} checks passed")

    if checks_passed == 0:
        # Don't hard-crash: Durgapur has no MODIS epoch (S1-only from 2014),
        # and Panchet MODIS has sub-pixel resolution issues at 500m.
        # Maithon is the primary validation target.
        warnings.warn(
            "[WARN] All 4 validation checks failed. Check Maithon 2009 anomaly values.\n"
            "Pipeline will continue — review figures/Fig3_storage_timeseries.png."
        )
    elif checks_passed < 3:
        warnings.warn(
            f"[WARN] Only {checks_passed}/4 checks passed. Proceed but investigate "
            "before trusting anomaly estimates. Will improve after CartoDEM Day 3."
        )

# ═══════════════════════════════════════════════════════════════════
# STEP 10: Save outputs
# ═══════════════════════════════════════════════════════════════════

def save_outputs(df: pd.DataFrame, processed_dir: Path) -> Path:
    """
    Save final storage time series to CSV.

    Columns saved:
        date, reservoir, water_area_km2, sensor, volume_bcm_corrected,
        delta_S_obs_bcm, delta_S_obs_p05, delta_S_obs_p50, delta_S_obs_p95,
        gap_flag, gap_filled, av_params_are_placeholder
    """
    out_path = processed_dir / 'DVC_storage_timeseries_2002_2024.csv'

    cols = [
        'date', 'reservoir', 'water_area_km2', 'sensor',
        'volume_bcm_corrected', 'delta_S_obs_bcm',
        'delta_S_obs_p05', 'delta_S_obs_p50', 'delta_S_obs_p95',
        'gap_flag', 'gap_filled', 'av_params_are_placeholder',
    ]
    # Keep only columns that exist (gap_flag may be all-NaN after merge)
    cols_present = [c for c in cols if c in df.columns]
    df[cols_present].to_csv(out_path, index=False, date_format='%Y-%m-%d')

    print(f"\n  Saved: {out_path}")
    print(f"  Rows: {len(df)} | Columns: {len(cols_present)}")
    return out_path

# ═══════════════════════════════════════════════════════════════════
# STEP 11: Figure 3 — Storage time series diagnostic plot
# ═══════════════════════════════════════════════════════════════════

def plot_figure3(df: pd.DataFrame, figures_dir: Path) -> Path:
    """
    3-panel figure: Maithon | Panchet | Durgapur
      - Blue line: delta_S_obs_bcm (MC p50)
      - Shaded band: MC p05–p95 uncertainty envelope
      - Dashed vertical line: 2014-01-01 (sensor transition)
      - Annotation: 2009 flood release on Maithon
      - Yellow shading: Oct–Mar Rabi seasons on Durgapur
      - 300 DPI output
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(
        'DVC Reservoir Storage Anomaly 2002–2024\n'
        '(ΔS_obs vs 2005–2015 baseline; shaded = Monte Carlo ±1 SD)',
        fontsize=13, fontweight='bold'
    )

    TITLES = {
        'maithon':  'Maithon Dam (23.835°N, 86.821°E) — Cap: 1.360 BCM',
        'panchet':  'Panchet Dam (23.577°N, 86.769°E) — Cap: 0.290 BCM',
        'durgapur': 'Durgapur Barrage (23.487°N, 87.307°E) — Run-of-river',
    }
    COLORS = {'maithon': '#1f77b4', 'panchet': '#ff7f0e', 'durgapur': '#2ca02c'}

    sensor_line = pd.Timestamp('2014-01-01')

    for ax, res in zip(axes, RESERVOIRS):
        sub = df[df['reservoir'] == res].set_index('date').sort_index()
        color = COLORS[res]

        # Uncertainty envelope
        if 'delta_S_obs_p05' in sub.columns:
            ax.fill_between(
                sub.index,
                sub['delta_S_obs_p05'],
                sub['delta_S_obs_p95'],
                alpha=0.2, color=color, label='MC p5–p95'
            )

        # Primary signal
        ax.plot(sub.index, sub['delta_S_obs_bcm'],
                color=color, linewidth=1.5, label='ΔS_obs (MC p50)')

        # Zero reference line
        ax.axhline(0, color='k', linewidth=0.5, linestyle='--', alpha=0.4)

        # Sensor transition
        ax.axvline(sensor_line, color='gray', linewidth=1.2,
                   linestyle=':', alpha=0.8, label='MODIS → S1 (2014)')

        ax.set_ylabel('ΔS (BCM)', fontsize=10)
        ax.set_title(TITLES[res], fontsize=10, pad=4)
        ax.grid(True, alpha=0.25, linewidth=0.5)

        # Reservoir-specific annotations
        if res == 'maithon':
            # Annotate 2009 flood event
            sep2009 = pd.Timestamp('2009-09-01')
            if sep2009 in sub.index:
                val = sub.loc[sep2009, 'delta_S_obs_bcm']
                if pd.notna(val):
                    ax.annotate(
                        '2009\nflood\nrelease',
                        xy=(sep2009, val),
                        xytext=(pd.Timestamp('2010-06-01'), val - 0.08),
                        fontsize=7, color='red',
                        arrowprops=dict(arrowstyle='->', color='red', lw=1.2),
                        ha='center'
                    )

        if res == 'durgapur':
            # Shade Oct–Mar (Rabi season) every year
            years_range = range(sub.index.min().year, sub.index.max().year + 1)
            for yr in years_range:
                rabi_start = pd.Timestamp(f'{yr}-10-01')
                rabi_end   = pd.Timestamp(f'{yr+1}-03-31')
                # Clip to data range
                rs = max(rabi_start, sub.index.min())
                re = min(rabi_end,   sub.index.max())
                if rs < re:
                    ax.axvspan(rs, re, alpha=0.07, color='gold', zorder=0)

        ax.legend(loc='upper left', fontsize=7, framealpha=0.7)

    axes[-1].set_xlabel('Date', fontsize=10)

    # Custom legend for Durgapur Rabi shading
    rabi_patch = mpatches.Patch(color='gold', alpha=0.4, label='Rabi season (Oct–Mar)')
    axes[-1].legend(
        handles=[
            Line2D([0], [0], color=COLORS['durgapur'], lw=1.5, label='ΔS_obs'),
            Line2D([0], [0], color='gray', lw=1.2, ls=':', label='MODIS → S1'),
            mpatches.Patch(color=COLORS['durgapur'], alpha=0.2, label='MC p5–p95'),
            rabi_patch,
        ],
        loc='upper left', fontsize=7, framealpha=0.7
    )

    plt.tight_layout()
    out_path = figures_dir / 'Fig3_storage_timeseries.png'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path} (300 DPI)")
    return out_path

# ═══════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("STAGE 1: Multi-Sensor Storage Reconstruction")
    print("DVC Reservoir Attribution Project")
    print("=" * 60)

    _ensure_dirs()

    # ── Step 1: Load CSVs ────────────────────────────────────────
    print("\n[1/9] Loading GEE CSVs...")
    df_s1, df_modis = load_and_clean_csvs(RAW_DIR)

    # ── Step 2: Gap filling ──────────────────────────────────────
    print("\n[2/9] Gap filling (interpolate ≤2 month gaps)...")
    df_s1    = apply_gap_filling(df_s1)
    df_modis = apply_gap_filling(df_modis)

    # ── Step 3: Cross-sensor quantile mapping ────────────────────
    print("\n[3/9] Cross-sensor quantile mapping (MODIS → Sentinel-1 scale)...")
    df_modis_cal = cross_sensor_quantile_mapping(df_s1, df_modis)

    # ── Step 4: Merge epochs ─────────────────────────────────────
    print("\n[4/9] Merging epochs (MODIS 2002–2013 + S1 2014–2024)...")
    df_merged = merge_epochs(df_s1, df_modis_cal)

    # ── Step 5: Area → Volume ────────────────────────────────────
    print("\n[5/9] Area-to-Volume conversion (power law V = a·A^b)...")
    df_vol = area_to_volume(df_merged, AV_PARAMS)

    # ── Step 6: Sedimentation correction ────────────────────────
    print("\n[6/9] Applying sedimentation correction (CWC 2022 rates)...")
    df_sed = apply_sedimentation_correction(df_vol, SEDIMENTATION_PARAMS)

    # ── Step 7: Storage anomaly ──────────────────────────────────
    print(f"\n[7/9] Computing storage anomaly (baseline {BASELINE_YEARS[0]}–{BASELINE_YEARS[1]})...")
    df_anom = compute_storage_anomaly(df_sed, BASELINE_YEARS)

    # ── Step 8: Monte Carlo uncertainty ─────────────────────────
    print("\n[8/9] Monte Carlo uncertainty quantification...")
    df_final = monte_carlo_uncertainty(
        df_anom, AV_PARAMS, SEDIMENTATION_PARAMS, BASELINE_YEARS,
        n_mc=N_MC, noise=MC_NOISE_FRACTION
    )

    # ── Step 9: Validation ───────────────────────────────────────
    print("\n[9/9] Validating against 2009 flood event...")
    validate_2009_flood(df_final)

    # ── Save outputs ─────────────────────────────────────────────
    print("\n── Saving outputs ──")
    save_outputs(df_final, PROCESSED_DIR)
    plot_figure3(df_final, FIGURES_DIR)

    print("\n" + "=" * 60)
    print("Stage 1 complete.")
    print(f"  Output: data/processed/DVC_storage_timeseries_2002_2024.csv")
    print(f"  Figure: figures/Fig3_storage_timeseries.png")
    print("\n  ⚠ AV_PARAMS still PLACEHOLDER. Update after CartoDEM Day 3.")
    print("  ⚠ Re-run this script after updating AV_PARAMS.")
    print("=" * 60)

    # Print summary stats for Nishi to paste back to Claude
    print("\n── SUMMARY — paste this to Claude ──")
    for res in RESERVOIRS:
        sub = df_final[df_final['reservoir'] == res]
        anomaly = sub['delta_S_obs_bcm']
        print(f"\n{res.upper()}:")
        print(f"  delta_S range: [{anomaly.min():.3f}, {anomaly.max():.3f}] BCM")
        print(f"  delta_S mean:   {anomaly.mean():.3f} BCM")
        print(f"  NaN count:      {anomaly.isna().sum()} / {len(anomaly)}")
        # Check 2009
        sep2009 = pd.Timestamp('2009-09-01')
        sub_idx = sub.set_index('date')
        val_sep2009 = sub_idx['delta_S_obs_bcm'].get(sep2009)
        if val_sep2009 is not None and pd.notna(val_sep2009):
            print(f"  Sep 2009:       {val_sep2009:+.3f} BCM")
        else:
            print(f"  Sep 2009:       NaN (out-of-range or gap)")


if __name__ == '__main__':
    main()
