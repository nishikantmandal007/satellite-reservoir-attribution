# Satellite-based separation of hydroclimatic and operational storage signals in DVC reservoirs

> **STATUS (2026-08): Route-B rebuild in progress.** An independent audit
> (`journal/codex_review.md`, verified in `journal/RECOVERY_ROADMAP.md`) found four
> submission-blocking defects in the original pipeline (reservoir geometry, GRACE
> coefficient units, cross-validation leakage, CCM direction/linkage). **All headline
> numbers below come from the corrected v2 pipeline.** Legacy v1 outputs remain in
> `data/processed/` untouched for comparison; every `*_v2.csv` supersedes its v1 twin.
> Raw inputs are being re-acquired (see `data/raw/README.md` manifest) before Stage-1
> geometry is rebuilt on the official CWC area–elevation–capacity curve.

Code and data pipeline for the B.Tech project of Nishi Kant Mandal (BIT Sindri,
Civil Engineering), supervised by Dr. Maya Rajnarayan Ray.

## What this study does

GRACE/GRACE-FO satellite gravimetry monitors water storage across India's river basins,
but cannot distinguish climate-driven variability from storage change caused by dam
operations. This study reconstructs monthly storage for Damodar Valley Corporation
reservoirs from Sentinel-1 SAR imagery (2017–2024 primary window) and asks how much of
the observed variability hydroclimatic drivers can explain versus managed operations —
using expanding-window machine-learning attribution with leak-free evaluation, surrogate-
tested convergent cross-mapping, and partial regression against GRACE-FO mascons.

All data sources are open-access; the pipeline runs at zero cost.

## Headline results (corrected v2 pipeline)

### Climate model skill is weak once leakage is removed

De-leaked expanding-window CV (tuning confined to pre-CV data, early stopping on train
tails only, in-fold imputation, out-of-sample SHAP):

| Model | Pooled OOS NSE |
|---|---|
| Persistence ΔS(t−1) | **0.589** |
| XGBoost (all rows, n=48) | 0.254 |
| XGBoost (physically resolved rows, n=38) | −0.251 |
| Climatology | 0.123 |

Persistence beats the gradient-boosted climate model under honest evaluation. The
practical reading: sub-monthly Maithon storage variability is dominated by operational
memory, not by contemporaneous hydroclimate — and any residual-isolation framing that
treated model error as "anthropogenic signal" is retired. Files: `xgb_cv_results_v2.csv`,
`baseline_comparison_v2.csv`.

### GRACE-FO association is real but is not a mass-consistent fingerprint

Raw-unit partial regression (HAC Newey-West maxlags=3), response = mascon TWS [cm LWE]:

- Seasonal fit: β₂ = **+42.35 cm TWS per BCM** of ΔS_anthro, CI [+23.5, +61.2], p≈1e-5
- Deseasonalized fit: β₂ = **+35.71 cm/BCM**, CI [+16.5, +54.9], p≈0.0003
- Mass-only sensitivity: 4.28–5.10 cm/BCM (23,370–19,600 km²). Observed/theory ≈ **7–10×**.

The earlier claim that the coefficient matched theory within 10% was a units artifact
(standardized coefficients labelled cm/BCM). What survives is a statistically robust
association whose magnitude exceeds the mass-only ceiling several-fold — i.e. ΔS_anthro
covaries with basin-wide water variation rather than isolating reservoir mass.
Files: `grace_regression_results_v2.csv`, `grace_regression_summary_v2.txt`.

### Cross-mapping: no detectable coupling at available power

With the pyEDM convention pinned empirically on a synthetic unidirectional system and a
matched per-library-size surrogate null, neither Maithon↔Durgapur nor
ΔS_anthro↔ΔS_climate shows consistent exceedance at n=48 months. The earlier
"significant convergent Maithon→Durgapur link" does not survive the corrected protocol.
Files: `ccm_results_v2.csv`, `ccm_summary_v2.txt`.

### Operational signatures separate cleanly (survives audit)

DTW clustering of complete annual cycles (Maithon + Durgapur, 14 segments) under valid
linkages: k-medoids K=4 silhouette **0.558** (average linkage 0.554), subsample
stability mean ARI **0.90 ± 0.10** over 100 resamples. Durgapur barrage years remain
perfectly cohesive. The original Ward-on-DTW implementation was invalid (Ward requires
Euclidean input) but did not materially distort this result.
Files: `fingerprint_linkage_v2.csv`, `taxonomy_linkage_v2_summary.txt`.

### Pilot level validation

Sentinel-1 area-derived elevations were compared to CWC bulletin and DVC report levels
(n=9 points; RMSE 0.23 m, or 0.07 m excluding one temporal-mismatch point). This is a
pilot consistency check, not formal validation — the clean subset shares repeated weekly
readings against two distinct monthly satellite values. Exact-date multi-season
validation is scheduled in the rebuild (roadmap task D7).

## Repository structure

```
src/
  canonical pipeline (v1 lineage):
    01_storage_reconstruction.py     # area -> volume via AV curves (geometry rebuild pending)
    02_feature_engineering.py        # driver matrix + VIF filtering
    03_xgboost_attribution.py        # legacy CV (LEAKY — kept for provenance)
    04_causal_inference.py           # Granger/HMM/CCM legacy (direction bug fixed in 04b)
    05_grace_reconciliation.py       # legacy units bug fixed in fix_b2 script
    06_fingerprint_taxonomy.py       # Ward-on-DTW legacy (superseded by 06b)
    07_cwc_validation.py             # CWC/DVC level comparison
  corrected v2 scripts (Phase-0 fixes):
    03b_xgboost_deleak.py            # leak-free CV + baselines + OOS-SHAP
    04b_ccm_direction_check.py       # synthetic-convention-pinned CCM, matched nulls
    06b_taxonomy_linkage_v2.py       # valid linkages + k-medoids + bootstrap stability
    fix_b2_grace_raw_units.py        # raw-unit GRACE regressions, side-by-side std
    critical_checks.py               # FAIL-CLOSED read-only diagnostics
gee_scripts/                          # Google Earth Engine exports (S1/MODIS/drivers/hypsometry)
tests/                                # metric fixtures, fail-closed tripwire
data/processed/                       # pipeline outputs (v1 + *_v2 corrected twins)
journal/                              # research log: findings, decisions, roadmap, playbook
reservoir_watch/                      # Streamlit dashboard (research demonstrator)
```

## Reproducing the analysis

1. Re-acquire raw inputs per `data/raw/README.md` (GEE exports, climate indices).
   GEE scripts run in [code.earthengine.google.com](https://code.earthengine.google.com).
2. Environment:

```bash
pip install uv && uv sync
uv run python tests/test_units.py          # metric definitions + conversions
uv run python tests/test_failclosed.py     # diagnostics fail-closed tripwire
uv run python src/01_storage_reconstruction.py   # after geometry rebuild lands
uv run python src/02_feature_engineering.py
uv run python src/03b_xgboost_deleak.py          # canonical attribution CV
uv run python src/04_causal_inference.py         # Granger/HMM
uv run python src/04b_ccm_direction_check.py     # canonical CCM
uv run python src/05_grace_reconciliation.py     # download+extract
uv run python src/fix_b2_grace_raw_units.py      # canonical GRACE regression
uv run python src/06b_taxonomy_linkage_v2.py     # canonical clustering
```

## Requirements

Python ≥3.11 via [uv](https://docs.astral.sh/uv/). Main dependencies: xgboost, shap,
optuna, statsmodels, hmmlearn, dtaidistance, pyEDM, scikit-learn, pandas, matplotlib.
A Google Earth Engine account is required for the export scripts; NASA Earthdata
credentials for GRACE-FO.

## Citation

```bibtex
@bachelorsthesis{mandal2026dvc,
  author  = {Mandal, Nishi Kant},
  title   = {Satellite-Based Attribution of Anthropogenic Storage Signals
             in {Damodar Valley Corporation} Reservoirs Using Explainable
             Machine Learning and Causal Inference},
  school  = {{BIT} Sindri},
  year    = {2026},
  type    = {{B.Tech} Project Report},
  address = {Dhanbad, Jharkhand, India},
  note    = {Department of Civil Engineering.
             Supervised by Dr. Maya Rajnarayan Ray}
}
```

## Contact

Nishi Kant Mandal -- nishim.ce22.063@bitsindri.ac.in
Department of Civil Engineering, BIT Sindri, Dhanbad 828123

## License

Code: MIT (`LICENSE`). A CC-BY-4.0 license for processed data ships with the archival
release (roadmap Phase 5).
