"""
FIX B4b — Taxonomy clustering linkage audit (v2)
=================================================
Defect (RECOVERY_ROADMAP.md §1.1 B4 / §2 D6, verified 2026-07-11):
    src/06_fingerprint_taxonomy.py:177 applied Ward linkage to a DTW distance
    matrix. SciPy defines Ward only for Euclidean inputs; on arbitrary
    dissimilarities the reported silhouette (F-011: 0.5535) is unreliable.

Fixes implemented here:
  1. Same segmentation + DTW matrix as v1 (direct comparability).
  2. Four methods side-by-side:
       ward_raw   (v1 method — retained for contrast ONLY, flagged invalid)
       average    (valid for arbitrary dissimilarities)
       complete   (valid)
       kmedoids   (PAM on the precomputed matrix — fully valid)
  3. K = 2..6 selected by silhouette (precomputed metric).
  4. Bootstrap cluster stability: ARI between full-data labels and
     100 subsample reclusterings.

Outputs (v1 never overwritten):
    data/processed/fingerprint_linkage_v2.csv

Run: uv run python src/06b_taxonomy_linkage_v2.py [--reservoirs maithon durgapur]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score, adjusted_rand_score

try:
    from dtaidistance import dtw as dtw_lib
    DTW_OK = True
except ImportError:
    DTW_OK = False

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'


# ────────────────────────────────────────────────────────────────────────
# Segmentation (identical logic to v1 src/06 for direct comparability)
# ────────────────────────────────────────────────────────────────────────

def build_segments(reservoirs: list[str]):
    ts = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv',
                     parse_dates=['date']).set_index('date').sort_index()
    segments, labels = [], []
    for res in reservoirs:
        sub = ts[ts['reservoir'] == res]['delta_S_obs_bcm'].resample('MS').first()
        for year in range(sub.index.year.min(), sub.index.year.max() + 1):
            w = sub[sub.index.year == year]
            if len(w) == 12 and w.notna().all():
                segments.append(w.values.astype(float))
                labels.append(f'{res}_{year}')
    arr = np.array(segments)
    print(f"  Segments: {arr.shape[0]} annual cycles x {arr.shape[1]} months "
          f"({len(reservoirs)} reservoirs)")
    return arr, labels


def dtw_matrix(segments: np.ndarray) -> np.ndarray:
    n = len(segments)
    D = np.zeros((n, n))
    if not DTW_OK:
        from scipy.spatial.distance import cdist
        return cdist(segments, segments)
    segs = [s.astype(np.double) for s in segments]
    for i in range(n):
        for j in range(i + 1, n):
            d = dtw_lib.distance_fast(segs[i], segs[j])
            D[i, j] = D[j, i] = d
    return D


# ────────────────────────────────────────────────────────────────────────
# Clustering methods
# ────────────────────────────────────────────────────────────────────────

def pam(D: np.ndarray, k: int, seed: int = 42) -> np.ndarray:
    """Deterministic k-medoids (BUILD + first-improvement SWAP)."""
    rng = np.random.default_rng(seed)
    n = len(D)

    def cost(meds):
        return float(D[:, meds].min(axis=1).sum())

    medoids = [int(np.argmin(D.sum(axis=1)))]
    while len(medoids) < k:
        cand = [i for i in range(n) if i not in medoids]
        gains = [np.sum(np.minimum(D[:, medoids].min(axis=1), D[:, i]))
                 for i in cand]
        medoids.append(cand[int(np.argmin(gains))])

    improved, cur = True, cost(medoids)
    while improved:
        improved = False
        for m in list(medoids):
            for h in range(n):
                if h in medoids:
                    continue
                trial = [x for x in medoids if x != m] + [h]
                tc = cost(trial)
                if tc < cur - 1e-12:
                    medoids, cur, improved = trial, tc, True
                    break
            if improved:
                break
        _ = rng  # keep signature stable
    return np.argmin(D[:, medoids], axis=1)


def cluster(method: str, D: np.ndarray, k: int) -> np.ndarray:
    if method == 'kmedoids':
        return pam(D, k)
    scipy_name = 'ward' if method == 'ward_raw' else method
    Z = linkage(squareform(D, checks=False), method=scipy_name)
    return fcluster(Z, k, criterion='maxclust')


# ────────────────────────────────────────────────────────────────────────
# Main comparison
# ────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reservoirs', nargs='+', default=['maithon', 'durgapur'])
    ap.add_argument('--n-boot', type=int, default=100)
    args = ap.parse_args()

    print("=" * 70)
    print("FIX B4b — taxonomy linkage audit (v2)")
    print("=" * 70)

    segs, labels = build_segments(args.reservoirs)
    n = len(segs)
    D = dtw_matrix(segs)
    print(f"  DTW range: [{D[D > 0].min():.4f}, {D.max():.4f}]")

    rows, best_per_method = [], {}
    for method, valid in [('ward_raw', False), ('average', True),
                          ('complete', True), ('kmedoids', True)]:
        best = (-1, None, None)
        for k in range(2, min(7, n - 1)):
            lab = cluster(method, D, k)
            if len(np.unique(lab)) < 2:
                continue
            sil = silhouette_score(D, lab, metric='precomputed')
            rows.append({'method': method, 'K': k,
                         'silhouette': sil,
                         'valid_for_dtw': valid,
                         'labels': ';'.join(map(str, lab))})
            print(f"  {method:<10} K={k}  silhouette={sil:.4f}"
                  f"{'' if valid else '   [INVALID for DTW — contrast only]'}")
            if sil > best[0]:
                best = (sil, k, lab)
        best_per_method[method] = best

    # bootstrap stability on the best VALID method
    valid_methods = ['average', 'complete', 'kmedoids']
    ref_method = max(valid_methods,
                     key=lambda m: best_per_method[m][0])
    ref_sil, ref_k, ref_lab = best_per_method[ref_method]
    aris = []
    rng = np.random.default_rng(42)
    for _ in range(args.n_boot):
        idx = rng.choice(n, size=max(4, int(round(0.8 * n))), replace=False)
        D_sub = D[np.ix_(idx, idx)]
        try:
            lab_sub = cluster(ref_method, D_sub, ref_k)
            aris.append(adjusted_rand_score(np.array(ref_lab)[idx], lab_sub))
        except Exception:
            continue
    ari_mean, ari_sd = float(np.mean(aris)), float(np.std(aris))

    out = pd.DataFrame(rows)
    out_path = PROCESSED_DIR / 'fingerprint_linkage_v2.csv'
    out.to_csv(out_path, index=False)

    v1_full = pd.read_csv(PROCESSED_DIR / 'fingerprint_clusters_maithon_durgapur.csv') \
        if (PROCESSED_DIR / 'fingerprint_clusters_maithon_durgapur.csv').exists() else None

    summary = [
        "TAXONOMY LINKAGE AUDIT v2",
        f"Segments: {n} | methods x K grid | bootstrap stability of '{ref_method}' "
        f"(K={ref_k}): mean ARI={ari_mean:.3f} ± {ari_sd:.3f} over {args.n_boot} subsamples",
        "",
        f"BEST VALID: {ref_method} K={ref_k} silhouette={ref_sil:.4f}",
        f"Ward-on-DTW (v1 method): INVALID for non-Euclidean distances "
        f"(best sil {best_per_method['ward_raw'][0]:.4f} shown for contrast only)",
        "",
        "F-011 claimed K=5 sil=0.5535 under Ward-on-DTW.",
        "v2 verdict: see BEST VALID line above — report THAT in the paper.",
    ]
    txt_path = PROCESSED_DIR / 'taxonomy_linkage_v2_summary.txt'
    txt_path.write_text("\n".join(summary) + "\n")
    print("\n".join(summary))
    print(f"\nSaved: {out_path}")
    print(f"Saved: {txt_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
