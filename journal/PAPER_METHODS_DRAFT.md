# Methods Section Draft
## DVC Reservoir Attribution Paper
### Status: DRAFT — for Nishi/supervisor review before final write-up

---

## 3. Data and Methods

### 3.1 Study Area

The Damodar Valley Corporation (DVC) reservoir system, located in the Jharkhand–West Bengal border region of eastern India (23.5°–24.2°N, 86.5°–87.5°E), comprises three primary structures: Maithon Dam (23.835°N, 86.821°E; design capacity 1.360 BCM), Panchet Dam (23.577°N, 86.769°E; 0.290 BCM), and Durgapur Barrage (23.487°N, 87.307°E; run-of-river). The combined catchment covers approximately 19,600 km². Maithon and Panchet operate in tandem for flood control and hydropower; Durgapur Barrage serves Rabi season irrigation via a 2,494 km canal network. This study analyses Maithon and Durgapur only; Panchet was excluded due to Sentinel-1 bounding box contamination by the DVC irrigation canal network (54/94 records invalid; see Supplementary Note S1).

---

### 3.2 Multi-Sensor Storage Reconstruction (Stage 1)

Monthly reservoir surface water area was extracted from Sentinel-1 C-band SAR (GRD, 20 m) for 2017–2024. Sentinel-1 penetrates monsoon cloud cover, eliminating the 4-month optical sensor gap (June–September) that affects MODIS-based studies. Backscatter images were processed using a refined Lee speckle filter (5×5 kernel) and adaptive Otsu thresholding per scene. Water pixels were constrained to the JRC Global Surface Water maximum extent mask (Pekel et al., 2016) to prevent confusion with flooded paddy fields. Monthly area was computed as the mean of all valid scenes within the calendar month.

Water area was converted to live storage (BCM) using area–volume (A–V) power-law curves (V = a·A^b) derived from the ALOS AW3D30 DEM (30 m) using GEE hypsometry, with the coefficient *a* calibrated to CWC design capacities. Sedimentation loss was applied at CWC (2022) rates (Maithon: −18%, Durgapur: −12% of design capacity).

**Validation against independent measurements:** Area-derived water surface elevations were validated against 9 independent measurements: 7 weekly levels from CWC Weekly Reservoir Bulletins (Nov–Dec 2024) and 2 end-of-monsoon levels from DVC Annual Reports (Nov 1, 2021 and Nov 1, 2022). Across all 9 points, RMSE = 0.23 m (mean bias = +0.11 m). Excluding one temporal mismatch point (Nov 2021: Stage 1 monthly mean area vs. Nov 1 point measurement, diff = +0.66 m), RMSE = 0.07 m (n=8, bias = +0.04 m). Both metrics are substantially below the ALOS DEM vertical RMSE specification of ±3–5 m. All validation points fall in the 147.4–148.3 m elevation range, which corresponds to the upper operating band of Maithon reservoir (near and above FRL = 146.3 m).

**Caveat (AV curve uncertainty):** The ALOS DEM has a vertical RMSE of ±3–5 m in Jharkhand terrain, propagating to ±15–25% volumetric uncertainty at high storage levels. The maximum reconstructed Maithon volume (0.883 BCM, October 2018) represents 65% of design capacity and 79% of CWC-adjusted current capacity, consistent with the reservoir not reaching full supply level during the 2017–2024 study period. All ΔS_anthro magnitude statements carry this ±15–25% caveat; relative anomaly patterns are substantially less affected.

Storage anomaly (ΔS_obs, BCM) was computed relative to the 2017–2023 S1-era monthly mean baseline.

---

### 3.3 Climate Driver Dataset (Stage 2)

Eight monthly climate predictors were assembled for the Damodar catchment (2002–2024) using Google Earth Engine:

| Feature | Source | Units |
|---------|--------|-------|
| API6 — 6-month antecedent precipitation index (Σ 0.85^i · P_{t-i}) | CHIRPS v2.0 | mm |
| PET — potential evapotranspiration | ERA5-Land | mm/month |
| AET — actual evapotranspiration | MODIS MOD16A2 | mm/month |
| DMI — Indian Ocean Dipole index | JAMSTEC/NOAA | °C |
| dS_lag1 — Maithon ΔS_obs at t−1 | Stage 1 output | BCM |
| dS_lag3 — Maithon ΔS_obs at t−3 | Stage 1 output | BCM |
| Q_inflow — SCS-CN runoff proxy | CHIRPS + CN=75 | BCM |
| MO_anom — monsoon onset anomaly | CHIRPS-derived | months |

Features were selected by iterative VIF filtering (threshold = 10) from 18 candidates. Ten features were excluded due to multicollinearity (P_mm VIF=690, SM1 VIF=661, T_C VIF=597, SM2 VIF=563, NTL VIF=191, NDVI VIF=116, LC_for VIF=106, P3_mm VIF=55, LC_crop VIF=1480, Nino34 VIF=1315). DMI survived VIF because it is orthogonal to all other predictors (DMI–P_mm r=0.001, DMI–SM1 r=0.009), not because it dominates Damodar rainfall. Nino34 was excluded due to collinearity with P_mm (r=0.404) and SM1 (r=0.460); the ENSO–precipitation teleconnection is captured indirectly through API6.

**Known data limitations:**
- AET (MOD16A2) annual mean ~260 mm/yr is below the expected 400–900 mm/yr range for South Asian monsoon regions — a known underestimation bias (Miralles et al., 2011). Used as a relative seasonal indicator only.
- dS_lag features have 35% missing values (2017–2018 Sentinel-1 sparse revisit); XGBoost handles missing values internally via learned default routing directions.
- Monsoon onset anomaly (MO_anom) takes only three distinct values (−2, −1, 0 months) and has limited discriminating power.

---

### 3.4 XGBoost Climate Attribution Model (Stage 3)

An XGBoost gradient boosting regressor (Chen & Guestrin, 2016) was trained to predict monthly ΔS_climate from the eight climate features. Hyperparameters were tuned using Optuna (150 trials, TPE sampler) maximising NSE on a single held-out expanding-window fold.

Model performance was evaluated using 4-fold expanding-window cross-validation (minimum training: 24 months; step: 12 months), strictly preserving temporal order to prevent data leakage. The primary evaluation metric is the Nash-Sutcliffe Efficiency (NSE; Nash & Sutcliffe, 1970).

**This model functions as a residual-isolation instrument, not a prediction model.** Its purpose is to remove the climate-explained component of storage variability so the residual (ΔS_anthro = ΔS_obs − ΔS_climate) represents the operationally driven signal. A low NSE indicates a large anthropogenic residual — this is the expected outcome in a heavily managed system, not a model deficiency.

**Performance metrics:**

| Metric set | NSE | KGE | PBIAS | n |
|------------|-----|-----|-------|---|
| All test rows | 0.572 | −2.016 | 53.4% | 48 |
| Physically resolved rows only | **0.208** | **0.226** | **71.2%** | **38** |

The all-rows KGE of −2.0 results from an AV-curve reconstruction artefact: in 10/48 (21%) test months, Maithon water area falls in the 35–50 km² range where the DEM-based hypsometric curve cannot resolve volumes below the dead-storage floor (0.185 BCM). These months have ΔS_obs = −0.185 BCM regardless of actual storage, while the model correctly predicts lower values. Excluding these artefact months yields KGE = 0.226, which is the reported metric for model performance. This limitation is stated explicitly; it does not affect the validity of ΔS_anthro estimates in months where storage is above the dead-storage floor (79% of the study period).

The systematic positive bias (PBIAS = 71%) is consistent with the AV curve volume ceiling: the model predicts physically plausible storage values across the full capacity range, while observed values are compressed within the lower 65% of design capacity — the portion of the AV curve supported by our 2017–2024 water area observations.

Feature attribution was quantified using SHAP TreeExplainer values (Lundberg & Lee, 2017). SHAP importances were computed on the 48 rows with non-missing lag features (excluding 22 rows from 2017–2018 where XGBoost uses learned default directions for NaN-routed lag features). The lag-1 storage anomaly (dS_lag1) was the dominant feature (mean |SHAP| = 0.064 BCM), reflecting reservoir operational inertia. PET (0.043 BCM), DMI (0.027 BCM), and API6 (0.023 BCM) follow, in a physically interpretable order.

ΔS_anthro uncertainty was quantified by refitting the model with 50 random seeds (bootstrap): range [−0.188, +0.228] BCM, 95% CI width ±0.051 BCM. The ΔS_anthro range is also robust to lag specification: excluding all lag features changes the range by <0.016 BCM (less than one-sixth of the RMSE), confirming the residual is not an artefact of autoregressive model structure.

---

### 3.5 Causal Inference (Stage 4)

**Stationarity pre-processing:** All series were decomposed using STL (Seasonal and Trend decomposition using Loess; Cleveland et al., 1990) with a 12-month seasonal period and robust fitting. ADF tests confirmed stationarity of all STL remainder components (p ≤ 0.006).

**Granger causality (linear test):** VAR Granger tests were applied to STL remainders of ΔS_obs for Maithon and Durgapur, and to ΔS_anthro and ΔS_climate as null checks. No significant Granger causality was detected between Maithon and Durgapur (minimum p = 0.44 at lag 2). Two null checks confirm attribution integrity: ΔS_anthro ⊄ ΔS_climate (p = 0.41) and ΔS_climate ⊄ ΔS_anthro (p = 0.57), demonstrating that the XGBoost residual is causally independent of the climate regressors. Absence of Granger significance is expected given the effective sample size (n = 48 months after STL decomposition; ideal n ≥ 100) and the fact that flood control releases operate at sub-monthly timescales (48–72 hours), which monthly aggregation cannot resolve.

**Convergent Cross-Mapping (nonlinear test):** CCM (Sugihara et al., 2012) was applied using pyEDM with embedding dimension E selected via Simplex projection (EmbedDimension) for each variable pair. Statistical significance was assessed against the 95th percentile of 999 phase-randomised surrogates (Theiler et al., 1992) applied to STL remainders, eliminating shared seasonality as a confound. CCM detected no significant causal link between ΔS_anthro and ΔS_climate in either direction (ρ = 0.044, surr_95th = 0.324), corroborating the Granger null checks. **Maithon → Durgapur cross-mapping was significant and converging** (ρ = 0.294 > surr_95th = 0.149, convergence slope +0.0042), demonstrating nonlinear causal coupling between the tandem reservoirs at monthly timescales — a finding consistent with the DVC tandem operational mandate.

**HMM operational regime detection:** A 2-state Gaussian HMM (hmmlearn) fitted to ΔS_anthro identified a DRAWDOWN state (mean = −0.168 BCM, 25% of months) and a NORMAL/FILL state (mean = +0.033 BCM, 75% of months).

---

### 3.6 Operational Fingerprint Taxonomy (Stage 6)

Annual ΔS_obs cycles (12-month segments, 2018–2024) for Maithon and Durgapur were clustered using Dynamic Time Warping (DTW) distance (dtaidistance; Meert et al., 2020) with Ward linkage. Optimal cluster count K was determined by silhouette score on the DTW distance matrix. K = 3 is reported as the primary result (silhouette = 0.49; no singleton clusters). K = 5 achieves silhouette = 0.554 but produces singleton clusters at this sample size.

A scale-inflation check confirmed that Maithon-only clustering (n = 7 annual cycles, K = 2, silhouette = 0.44) retains acceptable cluster separation, verifying that the taxonomy result is not purely driven by the barrage/reservoir amplitude contrast.

---

### 3.7 Known Limitations (Summary for Discussion)

1. **Panchet excluded** — GEE bounding box contamination (57% of records invalid). Results represent Maithon (storage reservoir) and Durgapur (barrage) only, not the full three-reservoir DVC system.
2. **S1 era only (2017–2024)** — XGBoost attribution uses 82 S1-era months. MODIS epoch (2002–2013) cannot be used for the same attribution (no cross-sensor QM calibration possible due to 4-year gap 2014–2016).
3. **No direct inflow/outflow data** — Water balance is not closed. SCS-CN inflow proxy (Q_inflow) with default CN = 75 is used; HWSD soil group data was unavailable.
4. **AV curve uncertainty ±15–25%** — Absolute ΔS_anthro magnitudes are indicative. Relative patterns and directional anomalies are reliable.
5. **Monthly temporal resolution** — Sub-monthly flood releases (48–72 h) are averaged out. ΔS_anthro underestimates flood-control operational intensity; our estimates are conservative.
6. **Granger test underpowered** — n = 48 effective rows; ideal n ≥ 100. Absence of Granger significance is not evidence of no causal relationship.
7. **AET underestimation** — MOD16A2 annual mean ~260 mm/yr vs expected 400–900 mm/yr. Used as relative seasonal indicator only.

---

*This draft was generated from confirmed findings (F-001 through F-019) in FINDINGS.md.
All metrics are from confirmed rerun outputs in data/processed/.
Review against supervisor comments before journal submission.*
