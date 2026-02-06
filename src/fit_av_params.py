"""
fit_av_params.py
DVC Reservoir Attribution Project — Stage 1 (Day 3)

Purpose:
    Read GEE-exported av_hypsometry.csv (ALOS AW3D30 + JRC mask) →
    compute trapezoidal volume integration → fit V = a × A^b power law
    per reservoir → print updated AV_PARAMS → save A-V figure.

Run:
    uv run python src/fit_av_params.py

Input:  data/raw/av_hypsometry.csv  (from av_hypsometry.js GEE export)
Output:
    Prints AV_PARAMS dict → copy into src/01_storage_reconstruction.py
    data/processed/av_hypsometry_with_volume.csv
    figures/FigS1_AV_curves.png
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from pathlib import Path

RAW_DIR       = Path('data/raw')
PROCESSED_DIR = Path('data/processed')
FIGURES_DIR   = Path('figures')
PROCESSED_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

RESERVOIRS = ['maithon', 'panchet', 'durgapur']

# Known design Full Supply Levels (FSL) in metres above MSL — CWC records
# Used to identify the physically meaningful range of the A-V curve
FSL = {
    'maithon':  174.5,
    'panchet':  108.5,
    'durgapur':  58.0,
}

# Known design capacities (BCM) — validation target
KNOWN_CAPACITY = {
    'maithon':  1.360,
    'panchet':  0.290,
    'durgapur': None,
}

# Dead storage (BCM) — minimum operational volume
DEAD_STORAGE = {
    'maithon':  0.185,
    'panchet':  0.048,
    'durgapur': 0.010,
}


def trapezoidal_volume(elev: np.ndarray, area_km2: np.ndarray) -> np.ndarray:
    """
    Cumulative volume (BCM) by trapezoidal integration of area-elevation curve.
    V(h) = ∫ A(z) dz  [km² × m × 1e-3 = BCM]
    """
    volumes = np.zeros(len(elev))
    for i in range(1, len(elev)):
        dh = elev[i] - elev[i-1]
        volumes[i] = volumes[i-1] + (area_km2[i] + area_km2[i-1]) / 2.0 * dh * 1e-3
    return volumes


def power_law(A, a, b):
    return a * (A ** b)


def fit_reservoir(df_res: pd.DataFrame, name: str):
    """
    Integrate volume and fit V = a × A^b for one reservoir.

    Fits on data up to FSL + 5m buffer only — terrain above the dam crest
    distorts the power law relationship for storage estimation.

    Returns (a, b, r2, df_with_volume).
    """
    df = df_res.sort_values('elevation_m').copy()

    # Compute cumulative volume by trapezoidal integration
    df['volume_bcm'] = trapezoidal_volume(
        df['elevation_m'].values,
        df['area_km2'].values
    )

    # Restrict fit to elevation ≤ FSL + 5m (physically meaningful range)
    fsl  = FSL.get(name, df['elevation_m'].max())
    df_fit = df[(df['elevation_m'] <= fsl + 5) & (df['area_km2'] > 0.05)].copy()

    if len(df_fit) < 10:
        print(f"  {name}: only {len(df_fit)} valid points below FSL — skipping fit")
        return None, None, None, df

    # Fit power law
    try:
        popt, pcov = curve_fit(
            power_law,
            df_fit['area_km2'].values,
            df_fit['volume_bcm'].values,
            p0=[0.05, 1.3],
            bounds=([1e-6, 0.5], [10.0, 3.0]),
            maxfev=10000
        )
        a, b = popt

        predicted = power_law(df_fit['area_km2'].values, a, b)
        ss_res = np.sum((df_fit['volume_bcm'].values - predicted) ** 2)
        ss_tot = np.sum((df_fit['volume_bcm'].values - df_fit['volume_bcm'].mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # Volume at FSL from DEM integration (physical validation)
        vol_at_fsl = df[df['elevation_m'] <= fsl]['volume_bcm'].max()
        area_at_fsl = df[df['elevation_m'] <= fsl]['area_km2'].max()
        known = KNOWN_CAPACITY.get(name)

        print(f"  {name.upper()}:")
        print(f"    Fit:        V = {a:.4f} × A^{b:.3f}  |  R² = {r2:.3f}")
        print(f"    At FSL ({fsl}m): area = {area_at_fsl:.1f} km², "
              f"volume = {vol_at_fsl:.3f} BCM")
        if known:
            pct = (vol_at_fsl - known) / known * 100
            print(f"    Known cap:  {known:.3f} BCM  →  DEM diff: {pct:+.1f}%")
            if abs(pct) > 40:
                print(f"    ⚠ Large diff — AW3D30 measures canopy surface, not "
                      f"reservoir bed. Uncertainty ±20–40% expected (Hulsman 2024).")
        return a, b, r2, df

    except RuntimeError as exc:
        print(f"  {name}: curve_fit failed — {exc}")
        return None, None, None, df


def main():
    print("=" * 60)
    print("A-V Hypsometry Fitting — ALOS AW3D30 + JRC (GEE)")
    print("=" * 60)

    hyps_path = RAW_DIR / 'av_hypsometry.csv'
    if not hyps_path.exists():
        raise FileNotFoundError(
            f"Not found: {hyps_path}\n"
            "Run av_hypsometry.js in GEE first → download → data/raw/"
        )

    df = pd.read_csv(hyps_path)
    # Replace GEE placeholder
    df['volume_bcm'] = df['volume_bcm'].replace(-9999, np.nan)

    print(f"\nLoaded: {len(df)} rows | "
          f"Reservoirs: {list(df['reservoir'].unique())}\n")

    fit_results = {}
    all_dfs = []

    print("── Fitting V = a × A^b (up to FSL) ──\n")
    for res in RESERVOIRS:
        df_res = df[df['reservoir'] == res].copy()
        if len(df_res) == 0:
            print(f"  {res}: no data")
            continue
        a, b, r2, df_out = fit_reservoir(df_res, res)
        fit_results[res] = {'a': a, 'b': b, 'r2': r2}
        all_dfs.append(df_out)
        print()

    # Save enriched table
    df_out_all = pd.concat(all_dfs, ignore_index=True)
    out_csv = PROCESSED_DIR / 'av_hypsometry_with_volume.csv'
    df_out_all.to_csv(out_csv, index=False, float_format='%.4f')
    print(f"Saved: {out_csv}")

    # Calibrate 'a' using known design capacities
    # Keep DEM-derived 'b' (shape correct), solve a = V_known / A_at_fsl^b
    # This corrects for AW3D30 DSM-DTM bias (Hulsman et al. 2024)
    print("\n── Calibrating 'a' against known design capacities ──\n")
    calibrated = {}
    for res in RESERVOIRS:
        r = fit_results.get(res, {})
        a, b = r.get('a'), r.get('b')
        if a is None:
            calibrated[res] = {'a': None, 'b': None}
            continue

        known  = KNOWN_CAPACITY.get(res)
        df_res = next(d for d in all_dfs if (d['reservoir'] == res).any())
        fsl    = FSL.get(res)
        area_at_fsl = df_res[df_res['elevation_m'] <= fsl]['area_km2'].max()

        if known and area_at_fsl > 0:
            # Solve: V_known = a_cal × A_at_fsl^b  →  a_cal = V_known / A_at_fsl^b
            a_cal = known / (area_at_fsl ** b)
            scale = known / (a * (area_at_fsl ** b)) if a > 0 else float('inf')
            print(f"  {res.upper()}: b={b:.3f}, A_at_FSL={area_at_fsl:.1f} km²")
            print(f"    DEM volume at FSL: {a * area_at_fsl**b:.3f} BCM")
            print(f"    Known capacity:    {known:.3f} BCM")
            print(f"    Scale factor:      {1/scale:.3f} (DSM-DTM correction)")
            print(f"    Calibrated a:      {a_cal:.6f}")
            calibrated[res] = {'a': a_cal, 'b': b, 'r2': r.get('r2')}
        else:
            # No known capacity (Durgapur) — use DEM-derived a as-is
            print(f"  {res.upper()}: no known capacity — using DEM-derived a={a:.6f}")
            calibrated[res] = {'a': a, 'b': b, 'r2': r.get('r2')}
        print()

    # Print AV_PARAMS block
    print("=" * 60)
    print("COPY THIS INTO src/01_storage_reconstruction.py")
    print("Replace the entire AV_PARAMS = { ... } block:")
    print("=" * 60)
    print("AV_PARAMS = {")
    for res in RESERVOIRS:
        r   = calibrated.get(res, {})
        a   = r.get('a')
        b   = r.get('b')
        r2  = r.get('r2', 0)
        ds  = DEAD_STORAGE[res]
        if a is not None:
            print(f"    '{res}':  {{'a': {a:.6f}, 'b': {b:.3f}, "
                  f"'dead_storage_bcm': {ds}}},  "
                  f"# AW3D30+JRC calibrated to CWC capacity, R²={r2:.3f}")
        else:
            print(f"    '{res}':  # FIT FAILED — keep placeholder value")
    print("}")
    print("=" * 60)

    # Figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        'Area–Volume Hypsometric Curves — ALOS AW3D30 v2.2 + JRC Water Mask\n'
        'DVC Reservoir Attribution Project (fitted up to FSL)',
        fontsize=12, fontweight='bold'
    )
    colors = {'maithon': '#1f77b4', 'panchet': '#ff7f0e', 'durgapur': '#2ca02c'}

    for ax, res in zip(axes, RESERVOIRS):
        r   = fit_results.get(res, {})
        a, b, r2 = r.get('a'), r.get('b'), r.get('r2')
        df_r = next((d for d in all_dfs if (d['reservoir'] == res).any()), None)
        color = colors[res]

        if df_r is None:
            continue

        fsl = FSL.get(res, df_r['elevation_m'].max())

        # All data (grey)
        df_all_plot = df_r[df_r['area_km2'] > 0.05]
        ax.scatter(df_all_plot['area_km2'], df_all_plot['volume_bcm'],
                   s=4, alpha=0.2, color='grey', label='All DEM data')

        # Data up to FSL (coloured)
        df_fsl = df_r[(df_r['elevation_m'] <= fsl + 5) & (df_r['area_km2'] > 0.05)]
        ax.scatter(df_fsl['area_km2'], df_fsl['volume_bcm'],
                   s=8, alpha=0.6, color=color, label=f'≤ FSL+5m ({fsl}m)')

        if a is not None:
            A_fit = np.linspace(df_fsl['area_km2'].min(),
                                df_fsl['area_km2'].max(), 300)
            ax.plot(A_fit, power_law(A_fit, a, b), 'k-', lw=2,
                    label=f'V={a:.4f}·A^{b:.3f}\nR²={r2:.3f}')

        known = KNOWN_CAPACITY.get(res)
        if known:
            ax.axhline(known, color='red', ls='--', lw=1.2,
                       label=f'Design cap: {known} BCM')

        ax.set_xlabel('Water Area (km²)', fontsize=10)
        ax.set_ylabel('Volume (BCM)', fontsize=10)
        ax.set_title(res.capitalize(), fontsize=11)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_fig = FIGURES_DIR / 'FigS1_AV_curves.png'
    plt.savefig(out_fig, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"\nSaved: {out_fig}")
    print("\nNext: copy AV_PARAMS above → "
          "uv run python src/01_storage_reconstruction.py")


if __name__ == '__main__':
    main()
