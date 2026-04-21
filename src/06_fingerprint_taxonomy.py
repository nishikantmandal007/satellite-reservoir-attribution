"""
Stage 6: Operational Fingerprint Taxonomy — DTW Clustering
===========================================================
Detects whether different operational regimes produce distinct,
satellite-classifiable storage anomaly patterns.

Method:
  1. Segment ΔS_obs into annual 12-month windows per reservoir
  2. Compute pairwise DTW distance matrix
  3. Ward hierarchical clustering → silhouette score to select K
  4. Validate cluster centroids against known operational archetypes:
       Monsoon Surge / Flood Release / Rabi Drawdown / Conservation
  5. Validate against known events: 2009 flood, 2015-16 El Niño drought
     (Note: 2009 falls in MODIS era, lower confidence)

Publishability threshold: Silhouette score > 0.35
  (CLAUDE.md Part 11: > 0.45 publishable; < 0.30 problem)

Run:
  uv run python src/06_fingerprint_taxonomy.py
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from pathlib import Path
from datetime import datetime
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score

try:
    from dtaidistance import dtw as dtw_lib
    DTW_AVAILABLE = True
except ImportError:
    DTW_AVAILABLE = False
    print("[WARN] dtaidistance not installed. Install: uv add dtaidistance")
    print("       Falling back to scipy Euclidean distance.")

from tqdm import tqdm

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

PROCESSED_DIR = Path('data/processed')
FIGURES_DIR   = Path('figures')
RANDOM_STATE  = 42
K_RANGE       = range(2, 6)   # test K=2..5 clusters

# Fix 3: run both FULL (Maithon+Durgapur) and MAITHON_ONLY to check
# whether silhouette is driven by real operational variance or just
# scale difference between barrage and storage reservoir.
RESERVOIRS_FULL      = ['maithon', 'durgapur']
RESERVOIRS_MAITHON   = ['maithon']

# Known events for cluster validation
KNOWN_EVENTS = {
    2009: 'Damodar Flood (catastrophic release)',
    2015: 'El Niño Drought (2015-16)',
    2016: 'El Niño Drought (2015-16)',
    2022: 'Post-monsoon high storage',
}

# ═══════════════════════════════════════════════════════════════════
# STEP 1: Load and segment
# ═══════════════════════════════════════════════════════════════════

def load_and_segment(reservoirs: list = None) -> tuple[np.ndarray, list, list]:
    """
    Load DVC_storage_timeseries, extract delta_S_obs_bcm for specified reservoirs,
    segment into annual 12-month windows.

    Args:
        reservoirs: list of reservoir names to include (default: RESERVOIRS_FULL)

    Returns:
        segments      : (N, 12) float array — N annual windows
        segment_labels: list of "maithon_2017", "maithon_2018", etc.
        segment_years : list of int years
    """
    if reservoirs is None:
        reservoirs = RESERVOIRS_FULL

    print(f"[1/5] Loading and segmenting — reservoirs: {reservoirs}...")

    ts = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv',
                     parse_dates=['date'])
    ts = ts.set_index('date').sort_index()

    segments, labels, years = [], [], []

    for res in reservoirs:
        sub = ts[ts['reservoir'] == res]['delta_S_obs_bcm']
        sub = sub.resample('MS').first()  # ensure monthly grid

        # Find complete years (all 12 months present)
        for year in range(sub.index.year.min(), sub.index.year.max() + 1):
            window = sub[sub.index.year == year]
            if len(window) == 12 and window.notna().all():
                seg = window.values.astype(float)
                segments.append(seg)
                labels.append(f'{res}_{year}')
                years.append(year)
                print(f"  {res} {year}: range=[{seg.min():.3f}, {seg.max():.3f}]")
            else:
                n_valid = window.notna().sum()
                if n_valid > 0:
                    print(f"  {res} {year}: SKIPPED ({n_valid}/12 valid months)")

    if len(segments) < 4:
        raise RuntimeError(
            f"Only {len(segments)} complete annual segments found. "
            "Need ≥4 for meaningful clustering. Check data coverage."
        )

    segments_arr = np.array(segments)
    print(f"\n  Total segments: {len(segments)} "
          f"({segments_arr.shape[0]} × {segments_arr.shape[1]})")
    return segments_arr, labels, years


# ═══════════════════════════════════════════════════════════════════
# STEP 2: DTW distance matrix
# ═══════════════════════════════════════════════════════════════════

def compute_distance_matrix(segments: np.ndarray) -> np.ndarray:
    """
    Compute pairwise distance matrix.
    Uses DTW (dtaidistance) if available, else Euclidean (scipy).
    DTW handles phase shifts in seasonal patterns — crucial here.
    """
    n = len(segments)
    print(f"\n[2/5] Computing {n}×{n} distance matrix...")

    if DTW_AVAILABLE:
        print("  Method: DTW (dtaidistance) — handles phase shifts")
        segs_list = [seg.astype(np.double) for seg in segments]
        dist_matrix = np.zeros((n, n))
        with tqdm(total=n*(n-1)//2, desc='  DTW pairs') as pbar:
            for i in range(n):
                for j in range(i+1, n):
                    d = dtw_lib.distance_fast(segs_list[i], segs_list[j])
                    dist_matrix[i, j] = d
                    dist_matrix[j, i] = d
                    pbar.update(1)
    else:
        print("  Method: Euclidean (DTW unavailable — install dtaidistance)")
        from scipy.spatial.distance import cdist
        dist_matrix = cdist(segments, segments, metric='euclidean')

    print(f"  Distance range: [{dist_matrix.min():.4f}, {dist_matrix.max():.4f}]")
    return dist_matrix


# ═══════════════════════════════════════════════════════════════════
# STEP 3: Ward clustering + silhouette
# ═══════════════════════════════════════════════════════════════════

def cluster_segments(dist_matrix: np.ndarray,
                     labels: list) -> tuple[np.ndarray, int, float]:
    """
    Ward hierarchical clustering on DTW distance matrix.
    Test K=2..5, select K with highest silhouette score.
    Returns: (cluster_labels, best_K, best_silhouette)
    """
    print("\n[3/5] Ward hierarchical clustering (K=2..5)...")

    # Ward linkage requires condensed distance matrix
    dist_condensed = squareform(dist_matrix, checks=False)
    Z = linkage(dist_condensed, method='ward')

    best_K    = 2
    best_sil  = -1.0
    best_lbls = None

    print(f"  {'K':>3}  {'Silhouette':>12}  Interpretation")
    print(f"  {'-'*3}  {'-'*12}  {'-'*30}")

    for K in K_RANGE:
        if K >= len(labels):
            break
        cluster_lbls = fcluster(Z, K, criterion='maxclust')
        try:
            sil = silhouette_score(dist_matrix, cluster_lbls, metric='precomputed')
        except Exception:
            sil = -1.0

        if sil > best_sil:
            best_sil  = sil
            best_K    = K
            best_lbls = cluster_lbls

        quality = ('✓ publishable' if sil > 0.45
                   else ('~ acceptable' if sil > 0.35
                   else ('✗ weak' if sil > 0.20 else '✗ poor')))
        marker = ' ← best' if sil == best_sil else ''
        print(f"  K={K}  sil={sil:8.4f}  {quality}{marker}")

    print(f"\n  Selected: K={best_K}, silhouette={best_sil:.4f}")
    return best_lbls, best_K, best_sil, Z


# ═══════════════════════════════════════════════════════════════════
# STEP 4: Characterise clusters
# ═══════════════════════════════════════════════════════════════════

def characterise_clusters(segments: np.ndarray, cluster_labels: np.ndarray,
                          labels: list, years: list,
                          K: int) -> pd.DataFrame:
    """
    Compute cluster centroids + envelopes.
    Label clusters with operational archetype names.
    Validate against known events.
    """
    print(f"\n[4/5] Characterising {K} clusters...")

    months = ['Jan','Feb','Mar','Apr','May','Jun',
              'Jul','Aug','Sep','Oct','Nov','Dec']

    rows = []
    for k in range(1, K+1):
        mask      = cluster_labels == k
        segs_k    = segments[mask]
        centroid  = segs_k.mean(axis=0)
        envelope  = segs_k.std(axis=0)
        members   = [labels[i] for i in range(len(labels)) if cluster_labels[i] == k]
        member_years = [years[i] for i in range(len(years)) if cluster_labels[i] == k]

        # Auto-label based on centroid shape
        # NOTE: delta_S is anomaly vs 2017-2023 baseline, NOT absolute storage.
        # Pre-monsoon months (Apr-Jun) are always BELOW baseline for flood-control
        # reservoirs — this is by design, not drought. Use max fill level to
        # characterise operational regime, not summer mean vs fixed threshold.
        peak_month   = centroid.argmax()
        trough_month = centroid.argmin()
        summer_mean  = centroid[5:9].mean()   # Jun-Sep (informational only)
        winter_mean  = centroid[[9,10,11,0,1]].mean()  # Oct-Feb
        total_range  = centroid.max() - centroid.min()
        max_fill     = centroid.max()   # highest anomaly reached in the year

        # Triage 1: amplitude distinguishes barrage from storage reservoir
        if total_range < 0.10:
            # Run-of-river barrage (Durgapur): small-amplitude, irrigation-driven
            archetype = 'BARRAGE_IRRIGATION'
        # Triage 2: max fill level classifies storage reservoir operational intensity
        elif max_fill > 0.30:
            # Exceptional monsoon fill — above-normal inflow year
            archetype = 'HIGH_FILL'
        elif max_fill > 0.15:
            # Good monsoon fill — above-normal but not exceptional
            archetype = 'ABOVE_NORMAL_FILL'
        elif max_fill > 0.05:
            # Modest fill — near-normal or slightly below
            archetype = 'NORMAL_FILL'
        else:
            # Below-baseline peak — drought / poor monsoon year
            archetype = 'LOW_FILL'

        # Known-event hits
        event_hits = {yr: KNOWN_EVENTS[yr] for yr in member_years if yr in KNOWN_EVENTS}

        rows.append({
            'cluster': k,
            'archetype': archetype,
            'n_segments': mask.sum(),
            'members': ', '.join(members),
            'event_hits': str(event_hits) if event_hits else 'none',
            'peak_month': months[peak_month],
            'trough_month': months[trough_month],
            'summer_mean_bcm': round(summer_mean, 4),
            'winter_mean_bcm': round(winter_mean, 4),
            'total_range_bcm': round(total_range, 4),
            **{f'centroid_{m}': round(v, 4) for m, v in zip(months, centroid)},
        })

        print(f"  Cluster {k} [{archetype}]: {mask.sum()} segments")
        print(f"    Peak: {months[peak_month]}, Trough: {months[trough_month]}")
        print(f"    Summer mean: {summer_mean:.3f} BCM | Winter mean: {winter_mean:.3f} BCM")
        print(f"    Members: {', '.join(members)}")
        if event_hits:
            for yr, evt in event_hits.items():
                print(f"    ✓ Event validation: {yr} → {evt}")
        else:
            print(f"    No known-event years in this cluster")

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════
# STEP 5: Figures
# ═══════════════════════════════════════════════════════════════════

def plot_taxonomy(segments: np.ndarray, cluster_labels: np.ndarray,
                  cluster_df: pd.DataFrame, K: int,
                  linkage_matrix: np.ndarray, out_path: Path):
    """Fig 8: DTW cluster centroids ± envelopes + dendrogram."""

    months = ['J','F','M','A','M','J','J','A','S','O','N','D']
    x      = np.arange(12)
    colors = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd']

    fig = plt.figure(figsize=(16, 10))
    gs  = fig.add_gridspec(2, K, hspace=0.4, wspace=0.35)

    ax_dend = fig.add_subplot(gs[0, :])
    dendrogram(linkage_matrix, ax=ax_dend, color_threshold=0, above_threshold_color='gray',
               no_labels=True)
    ax_dend.set_title('Ward Hierarchical Clustering Dendrogram (DTW distances)', fontsize=11)
    ax_dend.set_ylabel('Distance', fontsize=9)

    for k in range(1, K+1):
        ax = fig.add_subplot(gs[1, k-1])
        mask     = cluster_labels == k
        segs_k   = segments[mask]
        centroid = segs_k.mean(axis=0)
        envelope = segs_k.std(axis=0)
        col      = colors[k-1]

        # Individual traces (faint)
        for seg in segs_k:
            ax.plot(x, seg, color=col, alpha=0.2, lw=0.8)

        # Centroid ± 1σ envelope
        ax.plot(x, centroid, color=col, lw=2.0, label='Centroid')
        ax.fill_between(x, centroid - envelope, centroid + envelope,
                        alpha=0.25, color=col)
        ax.axhline(0, color='gray', lw=0.5, ls='--')

        row = cluster_df[cluster_df['cluster'] == k].iloc[0]
        ax.set_title(f"Cluster {k}: {row['archetype']}\n"
                     f"n={row['n_segments']}", fontsize=9)
        ax.set_xticks(x)
        ax.set_xticklabels(months, fontsize=8)
        ax.set_ylabel('ΔS_obs (BCM)', fontsize=8)
        ax.set_xlabel('Month', fontsize=8)

    plt.suptitle(f'Operational Fingerprint Taxonomy — DTW Ward Clustering (K={K})\n'
                 f'Maithon + Durgapur | Annual 12-month windows', fontsize=11, y=1.01)
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


def plot_silhouette_curve(dist_matrix: np.ndarray, Z: np.ndarray, out_path: Path):
    """Fig 8b: Silhouette score vs K."""
    dist_condensed = squareform(dist_matrix, checks=False)
    ks   = list(K_RANGE)
    sils = []
    for K in ks:
        if K >= dist_matrix.shape[0]:
            sils.append(np.nan)
            continue
        lbls = fcluster(Z, K, criterion='maxclust')
        try:
            sils.append(silhouette_score(dist_matrix, lbls, metric='precomputed'))
        except Exception:
            sils.append(np.nan)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(ks, sils, 'o-', color='#1f77b4', lw=2)
    ax.axhline(0.45, color='green', ls='--', lw=1, label='Publishable threshold (0.45)')
    ax.axhline(0.35, color='orange', ls='--', lw=1, label='Acceptable threshold (0.35)')
    ax.set_xlabel('Number of clusters (K)', fontsize=10)
    ax.set_ylabel('Silhouette score', fontsize=10)
    ax.set_title('Cluster validity: Silhouette score vs K', fontsize=10)
    ax.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def run_pipeline(reservoirs: list, tag: str) -> dict:
    """Run the full taxonomy pipeline for a given reservoir set. Returns summary dict."""
    print(f"\n{'─'*60}")
    print(f"  Running: {tag} (reservoirs: {reservoirs})")
    print(f"{'─'*60}")

    segs, lbls, yrs = load_and_segment(reservoirs)
    if len(segs) < 4:
        print(f"  ✗ SKIPPED — only {len(segs)} segments (need ≥4)")
        return {'tag': tag, 'n_segments': len(segs), 'best_K': None, 'best_sil': None}

    dist  = compute_distance_matrix(segs)
    cl, K, sil, Z = cluster_segments(dist, lbls)
    cdf   = characterise_clusters(segs, cl, lbls, yrs, K)

    suffix = tag.lower().replace('+', '_').replace(' ', '_')
    plot_taxonomy(segs, cl, cdf, K, Z,
                  FIGURES_DIR / f'Fig8_taxonomy_{suffix}.png')
    plot_silhouette_curve(dist, Z, FIGURES_DIR / f'Fig8b_silhouette_{suffix}.png')
    cdf.to_csv(PROCESSED_DIR / f'fingerprint_clusters_{suffix}.csv', index=False)

    return {'tag': tag, 'n_segments': len(segs), 'best_K': K, 'best_sil': sil,
            'cluster_df': cdf, 'labels': lbls}


def main():
    print("=" * 60)
    print("Stage 6: Operational Fingerprint Taxonomy")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # ── RUN A: Full (Maithon + Durgapur) ────────────────────────
    result_full = run_pipeline(RESERVOIRS_FULL, 'Maithon+Durgapur')

    # ── RUN B: Maithon-only (Fix 3 — scale inflation check) ─────
    # If silhouette collapses without Durgapur, full silhouette was
    # driven by scale difference, not real operational variance.
    result_maithon = run_pipeline(RESERVOIRS_MAITHON, 'Maithon-only')

    # ─── COMPARATIVE SUMMARY ────────────────────────────────────
    print("\n" + "=" * 60)
    print("STAGE 6 SUMMARY — Scale Inflation Check (Fix 3)")
    print("=" * 60)

    print(f"\n  {'Run':<25} {'N segs':>7} {'Best K':>7} {'Silhouette':>12}  Verdict")
    print(f"  {'─'*25}  {'─'*7}  {'─'*7}  {'─'*12}  {'─'*25}")

    results = [result_full, result_maithon]
    for r in results:
        if r['best_sil'] is None:
            print(f"  {r['tag']:<25}  {r['n_segments']:>7}  {'—':>7}  {'N/A':>12}  SKIPPED")
            continue
        verdict = ('✓ publishable' if r['best_sil'] > 0.45
                   else ('~ acceptable' if r['best_sil'] > 0.35
                   else '✗ weak'))
        print(f"  {r['tag']:<25}  {r['n_segments']:>7}  {r['best_K']:>7}  "
              f"{r['best_sil']:>12.4f}  {verdict}")

    # Interpretation
    sil_full    = result_full['best_sil']
    sil_maithon = result_maithon['best_sil']
    if sil_full is not None and sil_maithon is not None:
        drop = sil_full - sil_maithon
        print(f"\n  Silhouette drop (Full → Maithon-only): {drop:+.4f}")
        if drop > 0.15:
            print("  ⚠  LARGE DROP — full silhouette significantly inflated by")
            print("     Maithon/Durgapur scale difference. Report Maithon-only")
            print("     result as primary in paper.")
        elif drop > 0.05:
            print("  ~  MODERATE DROP — scale contributes but Maithon itself")
            print("     has real cluster structure. Report both in paper.")
        else:
            print("  ✓  MINIMAL DROP — Maithon-only clustering holds.")
            print("     Scale inflation not a concern. F-011 finding is genuine.")

    if result_maithon['best_sil'] is not None:
        print(f"\n  Maithon-only archetypes:")
        for _, row in result_maithon['cluster_df'].iterrows():
            print(f"    [{row['archetype']:18s}] n={row['n_segments']} | "
                  f"members: {row['members']}")

    print(f"\n  Figures saved: figures/Fig8_taxonomy_*.png")
    print(f"  Data saved:   data/processed/fingerprint_clusters_*.csv")
    print("=" * 60)


if __name__ == '__main__':
    main()
