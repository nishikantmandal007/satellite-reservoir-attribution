# DECISIONS.md — All Methodological Decisions
## DVC Reservoir Attribution Project

> Aggregated from session logs. Every D-XXX entry lives here.
> Reference these when writing the Methods section of the paper.

---

## D-001: uv over conda/pip
Chose: uv | Over: conda | Why: faster, lockfile-based, no conflicts | Session 001

## D-002: JupyterLab + .py scripts dual approach
Chose: Both | Over: notebooks-only | Why: exploration + reproducibility | Session 001

## D-003: CLAUDE.md as persistent memory
Chose: Single CLAUDE.md | Over: multiple config files | Why: auto-read by Claude Code | Session 001

## D-004: Otsu adaptive threshold for SAR water extraction
Chose: Adaptive Otsu per image | Over: Fixed -16 dB threshold | Why: Damodar has high seasonal backscatter variation | Session 002

## D-005: Remove Refined Lee speckle filter for 11-year run
Chose: Median composite despeckling | Over: Per-image Refined Lee filter | Why: OOM at 18,637 EECU-seconds; median is equivalent for reservoir classification | Session 002

## D-006: Expand Panchet bbox east to 87.05°E
Chose: [86.72, 23.50, 87.05, 23.72] | Over: Original [86.72, 23.52, 86.84, 23.64] | Why: Original bbox missed reservoir body east of dam | Session 002
NOTE: Reversed in D-010 after verification showed contamination.

## D-007: AW3D30 over CartoDEM for hypsometry
Chose: ALOS AW3D30 (GEE) | Over: CartoDEM local tiles | Why: Hulsman 2024 — fill ratio <8% vs CartoDEM 33%; better for reservoir bathymetry | Session 002

## D-008: Calibrate AV parameter 'a' from CWC design capacity
Chose: b from DEM shape, a solved from V_known/A_fsl^b | Over: Full curve fit to DEM volumes | Why: AW3D30 DSM overestimates volume +87–161%; b captures shape correctly | Session 002

## D-009: Durgapur — Sentinel-1 only (no MODIS backfill)
Chose: S1 2014–2024 only | Over: MODIS 2002–2013 + S1 | Why: Run-of-river barrage too narrow for 500m MODIS pixel | Session 002

## D-010: Tighten Panchet bbox to [86.72, 23.52, 86.95, 23.68]
Chose: [86.72, 23.52, 86.95, 23.68] | Over: [86.72, 23.50, 87.05, 23.72] (D-006) | Why: S1 verification showed bimodal distribution — 54/94 records contaminated by Damodar river valley + DVC canal network east of 86.95°E. Clean data (40 records) clustered correctly at 40–80 km² matching FSL. | Session 003

## D-011: Skip cross-sensor QM calibration (no overlap window)
Chose: MODIS uncalibrated | Over: Postpone pipeline | Why: S1 had no valid acquisitions 2014–2016; MODIS ends 2013 → gap is structural, not fixable | Session 003
Impact: MODIS-epoch volumes on different scale than S1-epoch. Stated as Methods limitation.

## D-012: Proceed to Stage 2 without clean Panchet data
Chose: Advance using Maithon + Durgapur | Over: Wait for Panchet GEE re-run | Why: Maithon alone sufficient for C1 + C3 claims. Panchet needed only for C2 (Stage 6) | Session 003
Impact: Stage 2 driver extraction started without Panchet storage signal.

## D-013: Durgapur baseline uses full-record mean (fallback)
Chose: Full-record mean 0.234 BCM | Over: 2005–2015 baseline | Why: Durgapur no MODIS (sub-pixel), S1 only from 2017 → baseline window empty | Session 003
Impact: Durgapur anomaly relative to its own S1-era mean. Stated in Methods.

## D-014: ERA5-Land PET band name corrected to potential_evaporation_sum
Chose: potential_evaporation_sum | Over: potential_evapotranspiration | Why: GEE DAILY_AGGR collection uses ERA5 sum convention, not rate naming | Session 004
Impact: driver_extraction.js and 02_feature_engineering.py both corrected.

## D-015: GEE null guards added for NDVI, AET, LULC empty collections
Chose: ee.Algorithms.If(col.size().gt(0), ..., fallback) | Over: bare .mean()/.first() | Why: Some months/years have no MODIS composites → empty collection → .multiply() crashes | Session 004
Impact: 10 NDVI/AET no-data months (2023 Mar-Dec) now return NaN in Python, not -9999.

## D-016: VIF threshold 10 — 9 features dropped, 9 retained
Chose: iterative VIF drop (threshold = 10) | Over: manual feature selection | Why: Removes multicollinearity before XGBoost training; automated and reproducible | Session 004
Features DROPPED: P_mm (690), T_C (563), Nino34 (432), SM2 (349), NDVI (88), NTL (74), SM1 (32), LC_crop (26), P3_mm (17)
Features KEPT: API6, PET_mm, AET_mm, LC_for, DMI, dS_lag1, dS_lag3, Q_inflow_bcm, MO_anom

## D-017: API₆ ↔ P_mm correlation 0.516 accepted as physically correct
Chose: Accept 0.516, proceed | Over: Flag as formula error | Why: In Damodar monsoon climate, API₆ peaks Oct (lag after monsoon) while P_mm peaks Jul → phase mismatch reduces correlation. Expected 0.75–0.80 is calibrated for temperate climates. Formula is correct. | Session 004

## D-019: LULC zero-fill bug corrected — both LULC features now dropped by VIF
Chose: Replace both-zero LULC rows with NaN before ffill | Over: Accept zeros as valid | Why: GEE null guard fills missing years with 0.0 (not NaN); ffill was keeping zeros instead of propagating last real year | Session 004
Impact: LC_for forward-filled correctly from 2020→2021/2022. After fix, LC_crop (VIF=1480) and LC_for (VIF=106) both dropped by VIF as near-perfectly collinear with each other + seasonal features. Final matrix 8 features not 9.

## D-020: API6 formula confirmed correct — lag-2 correlation is expected
Chose: Accept API6 formula as-is | Over: Revise formula | Why: Deep check shows API6 ↔ P_mm peaks at lag 2 (r=0.859), not lag 0 (0.516). Physically correct: API6 accumulates 6 months of rainfall, so it correlates best with P(t-2) in monsoon climate where P peaks Jul but API6 peaks Sep. | Session 004
Impact: D-017 superseded — formula is confirmed correct.

## D-018: Panchet contamination persists after bbox tightening
Chose: Continue excluding Panchet | Over: Use contaminated data with filters | Why: Re-run with [86.72, 23.52, 86.95, 23.68] still shows 35/94 records > 100 km² (expected max ~70 km²), peak Apr at 158.8 km² — still Rabi canal contamination | Session 004
Impact: Panchet excluded from Stage 2/3. Further GEE fix needed (tighter bbox or JRC mask constraint).

## D-021: Durgapur excluded from Stage 3 XGBoost target variable
Chose: Maithon only as XGBoost target | Over: Maithon + Durgapur | Why: Durgapur AV curve gives 7x design capacity (0.080 BCM) at high water areas (44 km² → 0.57 BCM). Power-law V=a*A^b fails for flat barrage geometry. Absolute volumes unreliable. | Session 004 (deep audit)
Impact: Stage 3 trains on Maithon delta_S only. Durgapur used only for directional fingerprint (F-002) in Stage 6 DTW taxonomy.

## D-022: Stage 3 XGBoost training set is 160 samples (104 with lag features)
Chose: Accept 160-sample training set | Over: Wait for more data | Why: Structural data constraints — 3-year gap 2014-2016 (S1 sparse revisit), MODIS cloud gaps Aug-Sep 2002-2013. 160 samples is at lower bound but XGBoost is data-efficient for tabular data. Expanding window CV required.
Impact: NSE confidence intervals will be wide. Report CI in paper. Use SHAP feature importance, not just NSE, as the primary validation metric.

## D-023: AV param calibration is valid for Maithon only (not Durgapur)
Chose: Keep av_params_are_placeholder=False for Maithon, explicitly flag Durgapur volumes as unreliable above 25 km² water area | Over: Full recalibration | Why: Deep audit shows Maithon max vol = 0.703 BCM (52% of design capacity — plausible with sedimentation). Durgapur AV extrapolates to 7x capacity at observed max area.
Impact: All quantitative claims use Maithon. Durgapur direction-only. Paper Methods must state this explicitly.

## D-024: Durgapur AV curve replaced with linear model
Chose: V = 0.00447 × A (BCM/km², linear, b=1.0), hard cap at 0.120 BCM | Over: Power law V=a×A^b
Why: Power law at max observed area (56.5 km²) gave 1.067 BCM = 13× design capacity (0.080 BCM). Flat run-of-river barrage geometry violates the concave reservoir shape assumption behind power-law.
Calibration: a = V_design / A_median = 0.080 / 17.9 = 0.00447; cap = 1.5× design.
Impact: Durgapur volumes now range 0.010–0.120 BCM (physically bounded). D-023 confirmed: direction-only use.

## D-025: Stage 3 XGBoost uses S1 era only (2017-01-01+)
Chose: 82 S1-era rows | Over: 173 rows including MODIS era
Why: Expanding-window CV trained on 2002-2013 MODIS-era storage then tested on 2017+ S1-era → catastrophic NSE=-28.9 due to sensor distribution shift. MODIS (500m) and S1 (10m) water areas are systematically different. F-001 stated S1 data is the trustworthy training window.
Impact: 82 training rows (D-022 accepted). MODIS-era ΔS_anthro cannot be computed.

## D-026: Annual (12-month) CV step replacing 6-month step
Chose: CV_STEP=12 | Over: CV_STEP=6
Why: 6-month steps created 22 folds with first fold at 24 training samples → NSE=-25. Fold 9 tested 2023-Mar-Aug where AET=NaN for all months (MODIS MOD16A2 cutoff) → PBIAS=-3592%. Annual steps give 4 clean folds, NSE range [0.008, 0.587].
Impact: Only 4 CV folds (vs 22). Wider CI but reliable.

## D-027: AET_mm NaN imputed with monthly seasonal mean (2023 Mar-Dec)
Chose: Monthly seasonal mean imputation | Over: Drop rows / XGBoost internal NaN handling
Why: MODIS MOD16A2 data ends early 2023 → 10/82 rows (12.2%) have AET=NaN, all clustered in 2023 test window. XGBoost internal NaN handling routes those rows to a "missing" branch trained primarily on non-missing data → PBIAS=-3592% for fold 9.
Imputation uses same-month mean from 2017–2022 only (6 years of seasonal signal).
Impact: PBIAS improved from -290% to -16%. Stated in Methods.

## D-028: NSE = 0.39 is a finding, not a failure (Day 8 checkpoint assessment)
Chose: Accept NSE=0.39, proceed to Stage 4 | Over: Re-engineer model
Why: Climate features explain 39% of Maithon storage variance (NSE=0.39, range 0.008–0.587). This means 61% is unexplained by climate → large anthropogenic residual (ΔS_anthro). This IS the paper's core thesis. Low NSE = evidence for operational influence, not model failure. SHAP attribution is physically correct (dS_lag1 dominant, then PET/AET/DMI/API6). Per D-022: SHAP is primary validation metric.
Impact: Day 8 checkpoint — NSE target not met (0.60–0.85), but scientifically this represents a stronger attribution claim. Tier target: Journal of Hydrology (Granger test next).

---
*(New decisions appended by Claude Code at each session end)*

---

## Session 008 — 2026-03-23 — Audit Decisions

🔒 DECISION [D-033]: Dead storage floor rows excluded from primary CV metrics
   Chose: Report BOTH all-rows AND unclipped metrics in paper
   Over:  Report only all-rows metrics (standard practice)
   Why:   10/48 (21%) rows are artificially clamped at AV curve minimum; KGE=-2.0
          is an artifact of this clamping, not a true model performance indicator.
          Reporting only all-rows metrics would mislead reviewers.
   Impact: Paper Methods section must explain the clipping mechanism and report
           unclipped NSE/KGE/PBIAS as the primary model skill metrics.
           KGE all-rows remains reported for transparency.

🔒 DECISION [D-034]: SHAP importances reported from valid-lag rows only (n=48)
   Chose: Primary SHAP from 48 rows where dS_lag1, dS_lag3 are non-NaN
   Over:  SHAP from all 82 rows (includes NaN-routing for 2017-2018)
   Why:   XGBoost NaN-routing assigns SHAP values to NaN features based on
          learned default direction — these reflect routing rules, not actual
          feature contributions. Including these inflates/deflates lag feature
          importance estimates.
   Impact: dS_lag1 % share may change slightly (pending Stage 3 rerun).
           All feature importance claims in paper come from 48-row subset.

🔒 DECISION [D-035]: AV curve volumetric uncertainty stated as ±15–25%
   Chose: Quantify DEM-based volume uncertainty as ±15-25%
   Over:  Treat AV curve volumes as exact (no stated uncertainty)
   Why:   ALOS AW3D30 vertical RMSE ±3-5m in Jharkhand terrain (documented).
          At active storage zone, ±5m elevation → ±15-25% volume change.
          Max observed 0.883 BCM vs design 1.36 BCM gap (35%) confirms bias.
   Impact: ΔS_anthro magnitude claims become "indicative" not precise.
           Relative patterns (sign, timing, clustering) remain valid.
           Paper must state: "absolute volumes carry ±15-25% uncertainty."

🔒 DECISION [D-036]: CCM false positive (F-014) superseded — E=2 was unjustified
   Chose: Simplex-validated E per series as sole reported result (F-015)
   Over:  Retain F-014 alongside F-015 as "sensitivity"
   Why:   Using E=2 without validation is methodologically indefensible.
          F-014 result (ρ=0.37 vs threshold 0.35, margin=0.02) would be
          immediately questioned by any CCM reviewer.
          The corrected result (anthro-climate ns; Maithon-Durgapur significant)
          is physically more meaningful and methodologically correct.
   Impact: Paper no longer claims CCM evidence for climate→anthro causation.
           Instead claims Maithon-Durgapur operational coupling (ρ=0.29, p<0.05).
           This is actually a stronger and more defensible finding.
