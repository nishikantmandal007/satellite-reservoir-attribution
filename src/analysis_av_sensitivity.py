"""
TASK B: AV Curve Sensitivity Analysis
=======================================
Tests whether dS_anthro changes sign or becomes negligible under
+/-20% perturbation of AV power-law coefficients (a, b).

This is the paper's biggest weakness: if ±20% AV uncertainty flips
the sign of the anthropogenic signal, the attribution is unreliable.

Method:
  1. Load original water area timeseries (Maithon S1 era)
  2. Perturb 'a' by -20%, -10%, 0%, +10%, +20%
  3. Perturb 'b' by -20%, -10%, 0%, +10%, +20% (separately)
  4. For each perturbation, recompute V -> dS_obs -> dS_anthro
     (using saved XGBoost climate predictions as fixed reference)
  5. Report: range, mean, sign stability of dS_anthro

Nishi Kant Mandal | BIT Sindri | 2026
"""

from pathlib import Path
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT / 'data' / 'processed'
RAW = PROJECT / 'data' / 'raw'

# Original AV params from 01_storage_reconstruction.py
AV_PARAMS = {
    'maithon': {'a': 0.000002, 'b': 3.000, 'dead_storage_bcm': 0.185, 'cap_bcm': None},
}

# Sedimentation params
SED_PARAMS = {
    'maithon': {
        'rate_bcm_yr': 0.0042, 'start_year': 2008,
        'capacity_bcm': 1.360, 'max_loss_fraction': 0.18,
    },
}

BASELINE_YEARS = (2017, 2023)
PERTURBATIONS = [-0.20, -0.10, 0.0, +0.10, +0.20]


def volume_power_law(area_km2, a, b, dead_storage, cap=None):
    """V = a * A^b, floored at dead storage, optionally capped."""
    safe = np.where(area_km2 > 0, area_km2, np.nan)
    vol = a * (safe ** b)
    vol = np.where(vol < dead_storage, dead_storage, vol)
    if cap is not None:
        vol = np.where(~np.isnan(vol), np.minimum(vol, cap), vol)
    return vol


def apply_sedimentation(vol, years, params):
    """Subtract cumulative sedimentation loss."""
    loss = params['rate_bcm_yr'] * (years - params['start_year'])
    loss = np.maximum(loss, 0)
    if params.get('max_loss_fraction') and params.get('capacity_bcm'):
        max_loss = params['capacity_bcm'] * params['max_loss_fraction']
        loss = np.minimum(loss, max_loss)
    corrected = vol - loss
    return corrected


def compute_anomaly(vol_corrected, dates, baseline_years, dead_storage):
    """Compute storage anomaly relative to baseline period mean."""
    # Floor at dead storage after sedimentation
    vol_corrected = np.where(~np.isnan(vol_corrected),
                             np.maximum(vol_corrected, dead_storage),
                             vol_corrected)
    years = pd.to_datetime(dates).year
    bl_mask = (years >= baseline_years[0]) & (years <= baseline_years[1])
    bl_vals = vol_corrected[bl_mask]
    bl_mean = np.nanmean(bl_vals)
    if np.isnan(bl_mean):
        bl_mean = np.nanmean(vol_corrected)
    return vol_corrected - bl_mean


def main():
    print("=" * 70)
    print("TASK B: AV Curve Sensitivity Analysis")
    print("=" * 70)

    # ── Load storage timeseries (water area) ──────────────────────────
    ts_path = PROCESSED / 'DVC_storage_timeseries_2002_2024.csv'
    df_ts = pd.read_csv(ts_path, parse_dates=['date'])
    df_m = df_ts[df_ts['reservoir'] == 'maithon'].copy()
    df_m = df_m.sort_values('date').reset_index(drop=True)
    print(f"  Maithon timeseries: {len(df_m)} months")

    # ── Load XGBoost climate predictions (fixed reference) ────────────
    anthro_path = PROCESSED / 'delta_S_anthro.csv'
    df_a = pd.read_csv(anthro_path, index_col=0, parse_dates=True)
    df_a.index = df_a.index.to_period('M').to_timestamp()
    df_a = df_a[df_a['reservoir'] == 'maithon'].copy()
    df_a = df_a.dropna(subset=['delta_S_climate_bcm'])

    dS_climate = df_a['delta_S_climate_bcm']
    print(f"  XGBoost climate predictions: {len(dS_climate)} months")
    print(f"  Climate pred range: [{dS_climate.min():.4f}, {dS_climate.max():.4f}] BCM")

    # ── Align water area with prediction period ───────────────────────
    df_m['date_key'] = df_m['date'].dt.to_period('M').dt.to_timestamp()
    df_m = df_m.set_index('date_key')
    common_idx = df_m.index.intersection(dS_climate.index)
    print(f"  Overlapping months: {len(common_idx)}")

    if len(common_idx) < 12:
        print("  ERROR: too few overlapping months.")
        return

    area = df_m.loc[common_idx, 'water_area_km2'].values
    dates = common_idx
    years = dates.year.values
    climate_pred = dS_climate.loc[common_idx].values

    orig_a = AV_PARAMS['maithon']['a']
    orig_b = AV_PARAMS['maithon']['b']
    dead_storage = AV_PARAMS['maithon']['dead_storage_bcm']
    cap = AV_PARAMS['maithon']['cap_bcm']

    # Compute original dS_anthro as reference for correlation
    vol_orig = volume_power_law(area, orig_a, orig_b, dead_storage, cap)
    vol_corr_orig = apply_sedimentation(vol_orig, years, SED_PARAMS['maithon'])
    dS_obs_orig = compute_anomaly(vol_corr_orig, dates, BASELINE_YEARS, dead_storage)
    dS_anthro_orig = dS_obs_orig - climate_pred

    results = []

    # ══════════════════════════════════════════════════════════════════
    # Perturbation sweep: coefficient 'a'
    # ══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print(f"  Perturbing coefficient 'a' (original = {orig_a:.8f})")
    print(f"{'─'*60}")

    for pct in PERTURBATIONS:
        a_new = orig_a * (1 + pct)
        vol = volume_power_law(area, a_new, orig_b, dead_storage, cap)
        vol_corr = apply_sedimentation(vol, years, SED_PARAMS['maithon'])
        dS_obs = compute_anomaly(vol_corr, dates, BASELINE_YEARS, dead_storage)
        dS_anthro = dS_obs - climate_pred

        valid = ~np.isnan(dS_anthro)
        ds_valid = dS_anthro[valid]

        n_pos = (ds_valid > 0).sum()
        n_neg = (ds_valid < 0).sum()
        sign_stable = (n_pos == 0 or n_neg == 0)  # all same sign?
        mean_sign = '+' if np.mean(ds_valid) >= 0 else '-'

        # Correlation with original dS_anthro (temporal pattern stability)
        orig_valid = dS_anthro_orig[valid]
        corr_with_orig = np.corrcoef(ds_valid, orig_valid)[0, 1] if len(ds_valid) > 2 else np.nan

        # Sign flips: how many months change sign vs original
        sign_flips = int(np.sum(np.sign(ds_valid) != np.sign(orig_valid)))

        row = {
            'perturbed_param': 'a',
            'perturbation_pct': pct * 100,
            'param_value': a_new,
            'dS_anthro_mean': np.nanmean(ds_valid),
            'dS_anthro_std': np.nanstd(ds_valid),
            'dS_anthro_min': np.nanmin(ds_valid),
            'dS_anthro_max': np.nanmax(ds_valid),
            'dS_anthro_median': np.nanmedian(ds_valid),
            'n_positive': int(n_pos),
            'n_negative': int(n_neg),
            'n_total': int(len(ds_valid)),
            'mean_sign': mean_sign,
            'all_same_sign': sign_stable,
            'corr_with_original': corr_with_orig,
            'n_sign_flips': sign_flips,
        }
        results.append(row)

        print(f"  a={a_new:.10f} ({pct*100:+.0f}%): "
              f"mean={row['dS_anthro_mean']:+.4f}, std={row['dS_anthro_std']:.4f}, "
              f"range=[{row['dS_anthro_min']:+.4f}, {row['dS_anthro_max']:+.4f}], "
              f"r_orig={corr_with_orig:.3f}, sign_flips={sign_flips}/{len(ds_valid)}")

    # ══════════════════════════════════════════════════════════════════
    # Perturbation sweep: coefficient 'b'
    # ══════════════════════════════════════════════════════════════════
    print(f"\n{'─'*60}")
    print(f"  Perturbing coefficient 'b' (original = {orig_b:.4f})")
    print(f"{'─'*60}")

    for pct in PERTURBATIONS:
        b_new = orig_b * (1 + pct)
        vol = volume_power_law(area, orig_a, b_new, dead_storage, cap)
        vol_corr = apply_sedimentation(vol, years, SED_PARAMS['maithon'])
        dS_obs = compute_anomaly(vol_corr, dates, BASELINE_YEARS, dead_storage)
        dS_anthro = dS_obs - climate_pred

        valid = ~np.isnan(dS_anthro)
        ds_valid = dS_anthro[valid]

        n_pos = (ds_valid > 0).sum()
        n_neg = (ds_valid < 0).sum()
        sign_stable = (n_pos == 0 or n_neg == 0)
        mean_sign = '+' if np.mean(ds_valid) >= 0 else '-'

        # Correlation with original dS_anthro
        orig_valid = dS_anthro_orig[valid]
        corr_with_orig = np.corrcoef(ds_valid, orig_valid)[0, 1] if len(ds_valid) > 2 else np.nan
        sign_flips = int(np.sum(np.sign(ds_valid) != np.sign(orig_valid)))

        row = {
            'perturbed_param': 'b',
            'perturbation_pct': pct * 100,
            'param_value': b_new,
            'dS_anthro_mean': np.nanmean(ds_valid),
            'dS_anthro_std': np.nanstd(ds_valid),
            'dS_anthro_min': np.nanmin(ds_valid),
            'dS_anthro_max': np.nanmax(ds_valid),
            'dS_anthro_median': np.nanmedian(ds_valid),
            'n_positive': int(n_pos),
            'n_negative': int(n_neg),
            'n_total': int(len(ds_valid)),
            'mean_sign': mean_sign,
            'all_same_sign': sign_stable,
            'corr_with_original': corr_with_orig,
            'n_sign_flips': sign_flips,
        }
        results.append(row)

        print(f"  b={b_new:.4f} ({pct*100:+.0f}%): "
              f"mean={row['dS_anthro_mean']:+.4f}, std={row['dS_anthro_std']:.4f}, "
              f"range=[{row['dS_anthro_min']:+.4f}, {row['dS_anthro_max']:+.4f}], "
              f"r_orig={corr_with_orig:.3f}, sign_flips={sign_flips}/{len(ds_valid)}")

    # ══════════════════════════════════════════════════════════════════
    # Summary
    # ══════════════════════════════════════════════════════════════════
    df_res = pd.DataFrame(results)

    print(f"\n{'='*70}")
    print("  SENSITIVITY SUMMARY")
    print(f"{'='*70}")

    # Original baseline
    baseline_row = df_res[(df_res['perturbed_param'] == 'a') & (df_res['perturbation_pct'] == 0)].iloc[0]
    print(f"\n  Original dS_anthro: mean = {baseline_row['dS_anthro_mean']:+.4f} BCM")
    print(f"    range = [{baseline_row['dS_anthro_min']:+.4f}, {baseline_row['dS_anthro_max']:+.4f}]")

    # Sign stability check across all perturbations
    all_means = df_res['dS_anthro_mean'].values
    all_positive = (all_means > 0).all()
    all_negative = (all_means < 0).all()
    mixed = not (all_positive or all_negative)

    print(f"\n  Mean dS_anthro sign across all perturbations:")
    print(f"    Min mean: {all_means.min():+.4f} BCM")
    print(f"    Max mean: {all_means.max():+.4f} BCM")

    if mixed:
        print("\n  WARNING: dS_anthro MEAN CHANGES SIGN under perturbation.")
        print("  The anthropogenic signal direction is SENSITIVE to AV uncertainty.")
        print("  This must be disclosed as a major limitation.")
    else:
        sign_word = "positive" if all_positive else "negative"
        print(f"\n  Mean dS_anthro remains {sign_word} across ALL perturbations.")
        print("  Sign stability: PASSED. AV uncertainty does NOT flip the signal.")

    # Variance sensitivity
    a_rows = df_res[df_res['perturbed_param'] == 'a']
    b_rows = df_res[df_res['perturbed_param'] == 'b']

    print(f"\n  Std deviation of dS_anthro across perturbations:")
    print(f"    'a' perturbations: std range = [{a_rows['dS_anthro_std'].min():.4f}, {a_rows['dS_anthro_std'].max():.4f}] BCM")
    print(f"    'b' perturbations: std range = [{b_rows['dS_anthro_std'].min():.4f}, {b_rows['dS_anthro_std'].max():.4f}] BCM")

    # Correlation stability
    print(f"\n  Temporal pattern correlation with original dS_anthro:")
    print(f"    'a' perturbations: r range = [{a_rows['corr_with_original'].min():.3f}, {a_rows['corr_with_original'].max():.3f}]")
    print(f"    'b' perturbations: r range = [{b_rows['corr_with_original'].min():.3f}, {b_rows['corr_with_original'].max():.3f}]")

    # Sign flip summary
    print(f"\n  Sign flip counts (out of {baseline_row['n_total']} months):")
    for _, r in df_res.iterrows():
        print(f"    {r['perturbed_param']}={r['param_value']:.8f} ({r['perturbation_pct']:+.0f}%): "
              f"{r['n_sign_flips']} sign flips")

    min_corr = df_res['corr_with_original'].min()
    if min_corr > 0.9:
        print(f"\n  STRONG RESULT: minimum correlation with original = {min_corr:.3f}")
        print("  Temporal pattern of dS_anthro is ROBUST to AV uncertainty.")
    elif min_corr > 0.7:
        print(f"\n  MODERATE: minimum correlation = {min_corr:.3f}")
        print("  Pattern mostly preserved but 'b' perturbation causes notable changes.")
    else:
        print(f"\n  WEAK: minimum correlation = {min_corr:.3f}")
        print("  AV uncertainty substantially changes the temporal pattern of dS_anthro.")

    # Save
    out_path = PROCESSED / 'av_sensitivity_results.csv'
    df_res.to_csv(out_path, index=False)
    print(f"\n  Saved: {out_path}")


if __name__ == '__main__':
    main()
