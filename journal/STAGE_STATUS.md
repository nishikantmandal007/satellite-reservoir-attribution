# STAGE_STATUS.md — Pipeline Progress Tracker
## DVC Reservoir Attribution Project

> Claude Code updates this file at every session end.
> States: PENDING | IN PROGRESS | BLOCKED | COMPLETE | VERIFIED

| Stage | Name | Status | Last Updated | Key Output |
|-------|------|--------|-------------|------------|
| 1 | Multi-sensor storage reconstruction | COMPLETE (revised) → **REBUILD PENDING (B1 geometry)** | Session 016 | v1 series stands; CWC E-A-C rebuild gated on Track-B data (`data/raw/README.md` manifest) |
| 2 | Driver dataset construction | COMPLETE | Session 006 | X_climate_final.csv (264×8); raw inputs must be re-acquired (L1) before re-runs |
| 3 | XGBoost + SHAP attribution | **v2 CORRECTED** (leak-free) | Session 016 | De-leaked: pooled NSE=0.254, unclipped −0.251; persistence wins (0.589). Files: `xgb_cv_results_v2.csv`, `baseline_comparison_v2.csv`, `delta_S_anthro_v2.csv`, `shap_values_oos_v2.csv` |
| 4 | Causal inference (Granger + CCM) | **v2 CORRECTED** | Session 016 | CCM ns BOTH directions under matched per-L nulls; direction convention empirically pinned ('A:B'⇒B causes A). F-015 coupling DEAD. `ccm_results_v2.csv`; HMM refit pending |
| 5 | GRACE-FO reconciliation | **v2 CORRECTED** (units) | Session 016 | β₂ raw = +42.35 cm/BCM (seasonal) / +35.71 (deseasonalized) = 7–10× mass ceiling → association only. `grace_regression_results_v2.csv` |
| 6 | Operational fingerprint taxonomy | **SURVIVES audit** (method corrected) | Session 016 | k-medoids K=4 sil=0.5583, ARI stability 0.904; maithon-only control 0.4381 exact. `fingerprint_linkage_v2.csv` |

> **Session 016 note:** Phase-0 Track A (code corrections B2/B3/B4/D10/D12/R1)
> executed from surviving `data/processed/`. Track B (raw-data re-acquisition —
> `data/raw/` was lost from the machine) gates Stage-1 geometry rebuild and all
> PENDING re-runs listed in `journal/PHASE0_RESULTS.md`.

---

## Stage 2 Detail

| Sub-task | Status | File | Notes |
|----------|--------|------|-------|
| GEE driver extraction (6 exports) | COMPLETE | data/raw/DVC_drivers/ | chirps, era5, ndvi, aet, lulc, ntl_dmsp — all 264 rows ✓ |
| ERA5 band name fix | COMPLETE | gee_scripts/driver_extraction.js | potential_evapotranspiration → potential_evaporation_sum (D-014) |
| NDVI/AET null guards | COMPLETE | gee_scripts/driver_extraction.js | ee.Algorithms.If pattern for empty collections (D-015) |
| LULC null guard + ffill fix | COMPLETE | gee_scripts/driver_extraction.js + 02_feature_engineering.py | GEE null guard + Python zero-replace-then-ffill (D-019) |
| ENSO Nino34 download | COMPLETE | data/raw/nino34_monthly.csv | 276 rows 2002–2024; 2015 El Nino +2.53°C confirmed ✓ |
| IOD/DMI download | COMPLETE | data/raw/iod_dmi_monthly.csv | 276 rows 2002–2024; 2019 IOD Sep=0.893 confirmed ✓ |
| Deep physical validation (15 checks) | COMPLETE | — | 0 critical issues, 1 non-blocking warning (MO_anom only 3 values) |
| 02_feature_engineering.py | COMPLETE | src/02_feature_engineering.py | Sentinel masking, ERA5 column, LULC ffill all fixed |
| VIF check | COMPLETE | data/processed/vif_diagnostic.csv | 8/18 features retained (F-006 revised, D-016) |
| Final feature matrix | COMPLETE | data/processed/X_climate_final.csv | 264 rows x 8 features, 0 NaN in 6/8 features |
| API6 formula validation | COMPLETE | — | Lag-2 correlation r=0.859 confirms correct implementation (F-007, D-020) |

### Stage 2 Final Feature Set (8 features)
| Feature | VIF (initial) | Physical meaning |
|---------|--------------|-----------------|
| API6 | 50.9 (kept) | 6-month antecedent rainfall (key hydrological memory) |
| PET_mm | 237.5 (kept) | Evaporative demand (ERA5) |
| AET_mm | 12.6 (kept) | Actual ET (MODIS MOD16A2) |
| DMI | 2.1 (kept) | Indian Ocean Dipole — dominant teleconnection |
| dS_lag1 | 4.4 (kept) | Maithon storage anomaly t-1 (35% NaN, XGBoost handles) |
| dS_lag3 | 4.9 (kept) | Maithon storage anomaly t-3 (36% NaN, XGBoost handles) |
| Q_inflow_bcm | 453 (kept) | SCS-CN inflow proxy (CN=75, 19600 km²) |
| MO_anom | 4.1 (kept) | Monsoon onset anomaly (3 distinct values: -2,-1,0) |

### Stage 2 Known Limitations (for Methods section)
- AET (MOD16A2) annual mean ~260 mm/yr is low vs expected 400–900 mm/yr — known underestimation bias in South Asian monsoon regions (cite Miralles et al. 2011)
- LULC forest fraction very low (0.3–0.8%) — IGBP classes 1–5 miss Jharkhand's woody savanna/dry deciduous forest; use as relative trend only
- NTL DMSP 2002→2003 dip (-1.76 DN) is known satellite-switch artifact, not real darkening
- MO_anom has only 3 distinct values (limited discriminating power)
- dS_lag features have 35% NaN due to MODIS-era cloud gaps and S1 sparse revisit 2014–2016
- Panchet excluded (D-018)

---

## Stage 1 Detail

| Sub-task | Status | File | Notes |
|----------|--------|------|-------|
| GEE S1 water area extraction | COMPLETE (provisional) | data/raw/water_area_sentinel1.csv | 396 rows; Maithon ✓, Durgapur ✓, Panchet ✗ (needs bbox re-run) |
| GEE MODIS backfill 2002–2013 | COMPLETE (limited) | data/raw/water_area_modis.csv | 432 rows; cloud gaps Jun–Sep every year; Durgapur sub-pixel (unusable) |
| CartoDEM download | COMPLETE | data/raw/cartoDEM/ | 4 tiles: N23E086/87, N24E086/87 |
| A-V hypsometry curves (GEE) | COMPLETE (provisional) | data/raw/av_hypsometry.csv | From ALOS AW3D30; Panchet params contaminated by old bbox |
| fit_av_params.py | COMPLETE (provisional) | data/processed/av_hypsometry_with_volume.csv | a calibrated to CWC capacities; Panchet needs redo after S1 re-run |
| Cross-sensor QM calibration | SKIPPED | — | No overlap window: MODIS ends 2013, S1 valid only from 2017-03. MODIS used uncalibrated. |
| Sedimentation correction | COMPLETE | embedded in pipeline | CWC 2022 rates applied |
| Final storage time series | PROVISIONAL | data/processed/DVC_storage_timeseries_2002_2024.csv | 828 rows; Maithon + Durgapur usable; Panchet pending |
| 2009 flood validation check | FAILED (expected) | — | Sep 2009 in MODIS cloud-gap window; cannot validate from optical sensor |

### Stage 1 Blockers
- **BLOCKER (non-critical):** Panchet S1 needs GEE re-run with bbox [86.72, 23.52, 86.95, 23.68]. GEE script already updated. Can proceed to Stage 2 without Panchet.
- **KNOWN LIMITATION:** No cross-sensor QM calibration possible (4-year gap 2014–2016). Stated as Methods caveat.
- **KNOWN LIMITATION:** 2009 flood unvalidatable from MODIS (cloud gap). Will use post-2017 S1 era operational events instead.

---

## Day 8 Checkpoint (CRITICAL GATE)

| Question | Answer | Status |
|----------|--------|--------|
| ΔS_anthro clean for all 3 reservoirs? | Maithon only (Panchet excluded D-021) | PARTIAL |
| XGBoost NSE 0.60–0.85 for ≥2 reservoirs? | NSE=0.572 Maithon (marginal miss); 2/4 folds above 0.60 | MARGINAL |
| Granger p < 0.10 for Maithon–Durgapur? | p=0.44 (ns) — Panchet excluded (invalid data) | DONE (ns) |

**Checkpoint result: 1.5/3 — MARGINAL**
**Scope decision: LOCKED → Remote Sensing / JHRS. Granger not significant.**
**Key findings locked:**
- ΔS_anthro robust to lag specification (±0.016 BCM, no-lag vs lag model)
- Null checks pass: anthro⊄climate (p=0.41), climate⊄anthro (p=0.57) → attribution is clean
- HMM: DRAWDOWN state mean=-0.168 BCM (25% months), NORMAL=+0.033 BCM (75%)
- Granger ns (n=48 rows; test severely underpowered — stated as Methods caveat)
- Panchet confirmed invalid: inverted seasonal cycle, AV overestimate 34× design capacity

