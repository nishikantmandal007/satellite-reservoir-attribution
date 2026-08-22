"""
Critical Checks — FAIL-CLOSED diagnostics (D12 fix, v2)
========================================================
Defect fixed (RECOVERY_ROADMAP.md §2 D12): v1 used `if p.exists()` fallbacks,
inserted MISSING rows into output tables, and printed a CLEAR verdict even when
inputs were absent — silently invalidating previously-good CSVs.

v2 contract:
  * READ-ONLY: writes nothing, ever. Diagnostics only.
  * FAIL-CLOSED: every task's required inputs are verified BEFORE anything
    runs. Any missing input => full listing on stderr => exit(1).
  * CLEAR is printed only if every check actually executed.

Tasks:
  A  Residual contamination: Spearman |r| between ΔS_anthro (de-leaked v2) and
     each VIF-dropped climate feature reconstructed from raw drivers.
     NOTE: requires data/raw/DVC_drivers/* — currently absent from this
     machine (raw re-acquisition pending, Track B). The script will therefore
     exit(1) listing them until re-acquisition lands.
  B  Baseline comparison: pooled OOS NSE of XGBoost vs persistence /
     climatology / zero under the de-leak framework.

Run: uv run python src/critical_checks.py [--allow-partial]
Exit codes: 0 all checks ran | 1 missing inputs | 2 runtime failure
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
RAW_DIR       = PROJECT_ROOT / 'data' / 'raw'

DEAD_STORAGE_FLOOR_BCM = -0.183

TASK_INPUTS: dict[str, list[Path]] = {
    'A_residual_contamination': [
        PROCESSED_DIR / 'delta_S_anthro_v2.csv',
        PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv',
        RAW_DIR / 'DVC_drivers' / 'chirps_monthly.csv',
        RAW_DIR / 'DVC_drivers' / 'era5_monthly.csv',
        RAW_DIR / 'DVC_drivers' / 'ndvi_monthly.csv',
        RAW_DIR / 'DVC_drivers' / 'aet_monthly.csv',
        RAW_DIR / 'nino34_monthly.csv',
        RAW_DIR / 'iod_dmi_monthly.csv',
    ],
    'B_baseline_comparison': [
        PROCESSED_DIR / 'delta_S_anthro_v2.csv',
        PROCESSED_DIR / 'baseline_comparison_v2.csv',
    ],
}

VIF_DROPPED = ['P_mm', 'P3_mm', 'SM1', 'SM2', 'T_C', 'NDVI', 'LC_crop',
               'LC_for', 'Nino34', 'NTL']


def preflight() -> None:
    missing_all: list[tuple[str, Path]] = []
    for task, paths in TASK_INPUTS.items():
        for p in paths:
            if not p.exists():
                missing_all.append((task, p))
    if missing_all:
        print("FAIL-CLOSED: missing required inputs — nothing was executed, "
              "no files were touched.\n", file=sys.stderr)
        for task, p in missing_all:
            rel = p.relative_to(PROJECT_ROOT)
            print(f"  [{task}]  {rel}", file=sys.stderr)
        print("\nRe-acquire the inputs (see journal/RECOVERY_ROADMAP.md Track B), "
              "then rerun.", file=sys.stderr)
        sys.exit(1)


def nse(obs, pred) -> float:
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    if len(o) < 3:
        return np.nan
    denom = np.sum((o - o.mean()) ** 2)
    return np.nan if denom < 1e-12 else float(1 - np.sum((o - p) ** 2) / denom)


def load_anthro_v2() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / 'delta_S_anthro_v2.csv',
                     index_col=0, parse_dates=True)
    return df.dropna(subset=['delta_S_anthro_bcm'])


def task_a_residual_contamination() -> bool:
    """Returns True if the DANGEROUS flag fired."""
    anthro = load_anthro_v2()
    date_idx = anthro.index

    X_all = pd.DataFrame(index=date_idx)

    chirps = pd.read_csv(RAW_DIR / 'DVC_drivers' / 'chirps_monthly.csv')
    chirps['date'] = pd.to_datetime(chirps['date']).dt.to_period('M').dt.to_timestamp()
    X_all['P_mm'] = chirps.set_index('date')['precipitation'].reindex(date_idx)

    era5 = pd.read_csv(RAW_DIR / 'DVC_drivers' / 'era5_monthly.csv')
    era5['date'] = pd.to_datetime(era5['date']).dt.to_period('M').dt.to_timestamp()
    era5 = era5.set_index('date').reindex(date_idx)
    days = pd.Series([pd.Timestamp(d).days_in_month for d in date_idx], index=date_idx)
    X_all['PET_raw'] = era5['potential_evaporation_sum'].abs() * days * 1000
    X_all['SM1'] = era5['volumetric_soil_water_layer_1']
    X_all['SM2'] = era5['volumetric_soil_water_layer_2']
    X_all['T_C'] = era5['temperature_2m'] - 273.15

    ndvi = pd.read_csv(RAW_DIR / 'DVC_drivers' / 'ndvi_monthly.csv')
    ndvi['date'] = pd.to_datetime(ndvi['date']).dt.to_period('M').dt.to_timestamp()
    nv = ndvi.set_index('date')['NDVI'].reindex(date_idx)
    X_all['NDVI'] = nv.where(nv > -100)

    aet = pd.read_csv(RAW_DIR / 'DVC_drivers' / 'aet_monthly.csv')
    aet['date'] = pd.to_datetime(aet['date']).dt.to_period('M').dt.to_timestamp()
    et = aet.set_index('date')['ET'].reindex(date_idx)
    X_all['AET_mm'] = et.where(et > -100)

    nino = pd.read_csv(RAW_DIR / 'nino34_monthly.csv')
    nino['date'] = pd.to_datetime(nino[['year', 'month']].assign(day=1))
    ncol = [c for c in nino.columns if 'nino' in c.lower()]
    X_all['Nino34'] = nino.set_index('date')[ncol[0]].reindex(date_idx)

    iod = pd.read_csv(RAW_DIR / 'iod_dmi_monthly.csv')
    iod['date'] = pd.to_datetime(iod[['year', 'month']].assign(day=1))
    dcol = [c for c in iod.columns if 'dmi' in c.lower()] or [iod.columns[-1]]
    X_all['DMI'] = iod.set_index('date')[dcol[0]].reindex(date_idx)

    X_all['P3_mm'] = X_all['P_mm'].rolling(3).sum()

    ds_anthro = anthro['delta_S_anthro_bcm']

    print("=" * 70)
    print("TASK A: RESIDUAL CONTAMINATION (de-leaked ΔS_anthro v2)")
    print("=" * 70)
    dangerous = []
    print(f"  {'feature':<10} {'Spearman r':>11} {'p':>9} {'n':>5}")
    for feat in VIF_DROPPED:
        x = X_all[feat]
        mask = x.notna() & ds_anthro.notna()
        if mask.sum() < 5:
            print(f"  {feat:<10} {'<5 obs':>20}")
            continue
        r, p = stats.spearmanr(x[mask], ds_anthro[mask])
        flag = ' <<< DANGEROUS' if abs(r) > 0.3 else ''
        if abs(r) > 0.3:
            dangerous.append(feat)
        print(f"  {feat:<10} {r:>11.4f} {p:>9.4f} {int(mask.sum()):>5d}{flag}")

    if dangerous:
        print(f"\n  *** DANGEROUS: {', '.join(dangerous)} correlate with ΔS_anthro "
              f"at |r|>0.3 — residual may contain omitted climate signal.")
    else:
        print("\n  CLEAR: no VIF-dropped feature correlates with ΔS_anthro at |r|>0.3.")
    return bool(dangerous)


def task_b_baseline_comparison() -> bool:
    """Returns True if any naive baseline beats XGBoost."""
    base = pd.read_csv(PROCESSED_DIR / 'baseline_comparison_v2.csv')
    xgb_row = base[base['model'].str.contains('xgboost', case=False)].iloc[0]

    print("=" * 70)
    print("TASK B: BASELINE COMPARISON (de-leaked framework)")
    print("=" * 70)
    print(f"  {'model':<26} {'NSE':>9} {'KGE':>9} {'PBIAS':>10} {'nMAE_std':>9}")
    beaten = False
    for _, row in base.iterrows():
        is_xgb = 'xgboost' in str(row['model']).lower()
        mark = '' if is_xgb else (
            '  *** BEATS XGB' if row['NSE'] > xgb_row['NSE'] else '')
        if mark:
            beaten = True
        fmt = lambda v: f"{v:>9.4f}" if pd.notna(v) else f"{'nan':>9}"
        pb = f"{row.get('PBIAS', float('nan')):>10.1f}" if 'PBIAS' in row else f"{'—':>10}"
        nm = f"{row['nMAE_std']:>9.4f}" if 'nMAE_std' in row else f"{'—':>9}"
        print(f"  {row['model']:<26} {fmt(row['NSE'])} {fmt(row.get('KGE'))} {pb} {nm}{mark}")

    if beaten:
        print("\n  CRITICAL: at least one naive baseline beats de-leaked XGBoost — "
              "residual framing must NOT treat ΔS_anthro as model-isolated signal.")
    else:
        print("\n  OK: XGBoost beats all naive baselines.")
    return beaten


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--allow-partial', action='store_true',
                    help='run tasks whose inputs exist; still exits 1 listing gaps')
    args = ap.parse_args()

    missing = [(t, p) for t, paths in TASK_INPUTS.items() for p in paths
               if not p.exists()]
    runnable = ({t for t in TASK_INPUTS}
                - {t for t, _ in missing}) if args.allow_partial else set()
    if missing and not args.allow_partial:
        preflight()  # exits 1

    results = {}
    if 'A_residual_contamination' in runnable or not missing:
        results['A_dangerous'] = task_a_residual_contamination()
    if 'B_baseline_comparison' in runnable or not missing:
        results['B_beaten'] = task_b_baseline_comparison()

    ran = len(results)
    expected = len(TASK_INPUTS) if not args.allow_partial else max(runnable and 1, ran)
    print("\n" + "#" * 70)
    if ran == len(TASK_INPUTS):
        verdict = ("VERDICT: " +
                   ("ATTENTION REQUIRED — see flags above"
                    if any(results.values()) else "ALL CLEAR"))
        print(f"# DONE — all {ran}/{len(TASK_INPUTS)} checks executed.")
        print(f"# {verdict}")
        sys.exit(0)
    else:
        print(f"# INCOMPLETE — only {ran} check(s) executed "
              f"({len(missing)} input gap(s)).")
        sys.exit(1)


if __name__ == '__main__':
    main()
