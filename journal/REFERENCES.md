# REFERENCES.md — Citation Audit
## DVC Reservoir Attribution Project

> Two sections:
> 1. USED — references actually cited in code, decisions, or methods so far
> 2. PLANNED — references in the reading list for Stages 3–6, not yet used
>
> Update this file whenever a new source is cited in code or decisions.

---

## SECTION 1: REFERENCES ACTUALLY USED (Sessions 001–004)

### Datasets / Platforms

| # | Source | Used For | Where Cited | GEE ID / URL |
|---|--------|----------|-------------|--------------|
| D1 | **Sentinel-1 GRD C-band SAR** (ESA/Copernicus) | SAR water area extraction, 10m, 2014–2024 | s1_water_area.js, D-004 | `COPERNICUS/S1_GRD` |
| D2 | **MODIS MOD09GA** (NASA) | Optical water area backfill, 500m, 2002–2013 | modis_water_area.js | `MODIS/006/MOD09GA` |
| D3 | **ALOS AW3D30 v2.2** (JAXA) | Hypsometry / A-V curve derivation | av_hypsometry.js, D-007 | `JAXA/ALOS/AW3D30/V2_2` |
| D4 | **JRC Global Surface Water v1.4** (Pekel et al. 2016) | Permanent water mask to filter rice paddy confusion | s1_water_area.js | `JRC/GSW1_4/GlobalSurfaceWater` |
| D5 | **CHIRPS v2.0** (Funk et al. 2015) | Monthly precipitation driver | driver_extraction.js, X_climate_final.csv | `UCSB-CHG/CHIRPS/DAILY` |
| D6 | **ERA5-Land DAILY_AGGR** (ECMWF / Muñoz-Sabater et al. 2021) | PET, soil moisture, 2m temperature | driver_extraction.js, X_climate_final.csv | `ECMWF/ERA5_LAND/DAILY_AGGR` |
| D7 | **MODIS MOD16A2** (Running et al.) | Actual evapotranspiration, 500m | driver_extraction.js, X_climate_final.csv | `MODIS/006/MOD16A2` |
| D8 | **MODIS MOD13Q1** (Didan et al.) | NDVI 16-day composite, 250m | driver_extraction.js | `MODIS/006/MOD13Q1` |
| D9 | **MODIS MCD12Q1** (Friedl & Sulla-Menashe) | Annual LULC IGBP, 500m | driver_extraction.js | `MODIS/006/MCD12Q1` |
| D10 | **DMSP-OLS Nighttime Lights** (NOAA) | Industrial activity proxy 2002–2013 | driver_extraction.js | `NOAA/DMSP-OLS/NIGHTTIME_LIGHTS` |
| D11 | **CartoDEM v1.1** (NRSC/ISRO) | DEM backup (downloaded, not used in pipeline yet) | data/raw/cartoDEM/ | bhuvan-app3.nrsc.gov.in |
| D12 | **Niño 3.4 SST index** (NOAA/CPC, ERSSTv5) | ENSO teleconnection driver | nino34_monthly.csv | psl.noaa.gov/data/correlation/nina34.data |
| D13 | **IOD/DMI index** (HadISST1.1, NOAA PSL) | Indian Ocean Dipole driver | iod_dmi_monthly.csv | psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data |
| D14 | **CWC Reservoir Sedimentation Atlas** (CWC 2022) | Sedimentation correction rates | 01_storage_reconstruction.py, line ~54 | cwc.gov.in |

### Methods / Algorithms

| # | Reference | Used For | Where Cited | Status |
|---|-----------|----------|-------------|--------|
| M1 | **Otsu, N. (1979).** A threshold selection method from gray-level histograms. *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66. | Adaptive SAR threshold for water/non-water classification | s1_water_area.js (Section 3), D-004 | ✓ USED |
| M2 | **Hulsman, P. et al. (2024).** Satellite-based area-volume-elevation relationships for reservoir storage monitoring. *Remote Sensing of Environment* (or similar — verify exact citation). | AW3D30 DSM-DTM bias correction, ±20-40% volume uncertainty quantification | 01_storage_reconstruction.py line 24, D-007, D-008 | ✓ USED — **exact citation needs verification** |
| M3 | **USDA Natural Resources Conservation Service (1986).** *Urban Hydrology for Small Watersheds, Technical Release 55.* Washington, DC: USDA. | SCS Curve Number rainfall-runoff model (CN=75, Class C soil) | 02_feature_engineering.py compute_scs_cn_inflow(), CLAUDE.md Part 4 FATAL-4 | ✓ USED |
| M4 | **Pekel, J-F., Cottam, A., Gorelick, N., & Belward, A.S. (2016).** High-resolution mapping of global surface water and its long-term changes. *Nature*, 540, 418–422. | JRC permanent water mask for rice paddy filter | s1_water_area.js, SERIOUS-1 in project design | ✓ USED |
| M5 | **Twele, A., Cao, W., Plank, S., & Martinis, S. (2016).** Sentinel-1-based flood mapping: a fully automated processing chain. *International Journal of Remote Sensing*, 37(13), 2990–3004. | SAR flood mapping methodology reference for Otsu + VV polarisation choice | s1_water_area.js comments | ✓ USED (cited in code) |
| M6 | **Funk, C. et al. (2015).** The climate hazards infrared precipitation with stations — a new environmental record for monitoring extremes. *Scientific Data*, 2, 150066. | CHIRPS v2.0 dataset citation | driver_extraction.js, D-005 equivalent | ✓ USED — needs explicit in-text citation |
| M7 | **Muñoz-Sabater, J. et al. (2021).** ERA5-Land: A state-of-the-art global reanalysis dataset for land applications. *Earth System Science Data*, 13(9), 4349–4383. | ERA5-Land dataset citation | driver_extraction.js | ✓ USED — needs explicit in-text citation |

---

## SECTION 2: PLANNED REFERENCES (Stages 3–6, not yet used)

### Stage 3 — XGBoost + SHAP
- Chen, T., & Guestrin, C. (2016). XGBoost: a scalable tree boosting system. *KDD 2016*.
- Lundberg, S.M., & Lee, S.I. (2017). A unified approach to interpreting model predictions. *NIPS 30*.
- Hooker, G., & Mentch, L. (2019). Please stop permuting features. *arXiv:1905.03151*.
- Nash, J.E., & Sutcliffe, J.V. (1970). River flow forecasting. *Journal of Hydrology*, 10(3), 282–290.
- Kling, H., Fuchs, M., & Paulin, M. (2012). Runoff conditions in the upper Danube. *Journal of Hydrology*, 424–425, 264–278.
- Ji, R. et al. (2023). Separating climate- and human-induced changes in TWS. *Journal of Hydrology*, 625, 129142.
- Wada, Y. et al. (2017). Human and climate impacts on global water storage. *Nature Geoscience*, 10, 834–839.

### Stage 4 — Causal Inference
- Granger, C.W.J. (1969). Investigating causal relations. *Econometrica*, 37(3), 424–438.
- Sugihara, G. et al. (2012). Detecting causality in complex ecosystems. *Science*, 338(6106), 496–500.
- Ye, H. et al. (2015). Distinguishing time-delayed causal interactions using CCM. *Scientific Reports*, 5, 14750.
- Theiler, J. et al. (1992). Testing for nonlinearity: the method of surrogate data. *Physica D*, 58, 77–94.

### Stage 5 — GRACE
- Tapley, B.D. et al. (2019). Contributions of GRACE to understanding climate change. *Nature Climate Change*, 9, 358–369.
- Rodell, M., Velicogna, I., & Famiglietti, J.S. (2009). Satellite-based estimates of groundwater depletion in India. *Nature*, 460, 999–1002.
- Kalu, I. et al. (2024). Downscaling GRACE data using ML for northern Australia. *Journal of Hydrology*.
- Long, D. et al. (2020). South Asia's surprising monsoon anomalies. *GRL*, 47(5).

### Stage 6 — Taxonomy
- Sakoe, H., & Chiba, S. (1978). Dynamic programming for spoken word recognition. *IEEE Trans. ASSP*, 26(1), 43–49.
- Biemans, H. et al. (2011). Impact of reservoirs on river discharge. *WRR*, 47(3), W03509.

### General Context
- Maiti, S., & Bhattacharya, A.K. (2011). Flood analysis: Damodar River basin. *JISRS*, 39(4), 535–545.
- Rudra, K. (2018). *Rivers of the Ganga-Brahmaputra-Meghna Delta*. Springer.
- Central Water Commission (2022). *Reservoir Sedimentation Atlas of India*. MoJS, GoI.
- IPCC (2022). *Climate Change 2022: Impacts, Adaptation and Vulnerability*. CUP.
- Diebold, F.X., & Mariano, R.S. (1995). Comparing predictive accuracy. *JBES*, 13(3), 253–263.
- Kratzert, F. et al. (2019). Towards learning universal hydrological equations. *HESS*, 23(12), 5089–5110.

---

## SECTION 3: REFERENCES NEEDING EXACT VERIFICATION

| Ref | Issue | Action needed |
|-----|-------|--------------|
| Hulsman et al. 2024 | Exact journal, volume, pages unknown — cited as "Hulsman 2024" in D-007 | Find full citation before paper submission |
| MOD16A2 algorithm | Several versions of Mu et al. — need correct version (v6) | Verify: Mu, Q., Zhao, M., & Running, S.W. (2011). Improvements to a MODIS global terrestrial ET algorithm. *RSE*, 115(8), 1781–1800 |
| DMSP-OLS inter-satellite calibration | Need citation for known 2002→2003 satellite switch artifact | Elvidge, C.D. et al. (2009). A fifteen year record of global natural gas flaring. *Energies*, 2(3), 595–622 may cover this |

---

*Last updated: Session 004, 2026-03-22*
*Next update: Session 005 when Stage 3 references are activated*
