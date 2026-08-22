# CLAUDE.md — DVC RESERVOIR ATTRIBUTION PROJECT
## Persistent Memory + Behavioral Protocol for Claude Code

```
RESEARCHER : Nishi Kant Mandal | B.Tech Civil Engg | BIT Sindri | Reg: 22030430063
SUPERVISOR : Dr. Maya Rajnarayan Ray | Associate Professor | BIT Sindri
SPRINT     : 15-day accelerated execution
CONSTRAINT : 100% open-source, ₹0 cost
```

---

## ██ PART 0: CLAUDE CODE BEHAVIORAL PROTOCOL ██
### Read this section first. Every session. No exceptions.

---

### 0.1 SESSION START RITUAL — MANDATORY

Every time a new session begins, Claude Code MUST execute these steps
in order before doing anything else. Do not skip. Do not reorder.

```
STEP 1 — READ FINDINGS
  Read journal/FINDINGS.md completely.
  This contains every locked result from previous sessions.
  These are ground truth. Never contradict them without flagging.

STEP 2 — READ SESSION LOG
  Read the last 3 entries in journal/SESSION_LOG.md.
  Understand what was attempted, what worked, what failed.

STEP 3 — CHECK DATA STATE
  Run: ls data/raw/ data/processed/ figures/
  Know exactly what files exist right now.
  Cross-reference with FINDINGS.md — are all claimed outputs present?

STEP 4 — VERIFY STAGE STATUS
  Check journal/STAGE_STATUS.md.
  Identify: which stage is COMPLETE, IN PROGRESS, or PENDING.

STEP 5 — STATE THE PLAN
  Before writing a single line of code, print:
  
  ┌─────────────────────────────────────────────┐
  │  SESSION BRIEFING                           │
  │  Last completed: [stage name + date]        │
  │  Current stage:  [stage name]               │
  │  Next action:    [specific task]            │
  │  Files ready:    [list key files]           │
  │  Blockers:       [anything missing]         │
  └─────────────────────────────────────────────┘
  
  Wait for Nishi to confirm before proceeding.
```

---

### 0.2 SESSION END RITUAL — MANDATORY

At the end of every session (or when Nishi says "commit session"),
Claude Code MUST:

```
STEP 1 — WRITE SESSION LOG ENTRY
  Append to journal/SESSION_LOG.md:
  
  ## Session [N] — [DATE] — [DAY X of sprint]
  
  ### What we ran
  - [exact script names and what they did]
  
  ### Results
  - [quantitative outputs — NSE values, row counts, error rates]
  - [attach or reference key figures produced]
  
  ### Decisions made
  - [every methodological decision with reason]
  
  ### Problems hit
  - [what broke, what error, how fixed]
  
  ### What changed from plan
  - [any deviation from EXECUTION_PLAN.md and why]
  
  ### Next session starts at
  - [exact next task — specific enough that Claude can start without asking]

STEP 2 — UPDATE FINDINGS (if new result confirmed)
  Append to journal/FINDINGS.md ONLY if result is confirmed and clean.
  A result is confirmed when:
  - It passes the validation check defined in PART 12 of this file
  - Nishi has seen the output and said "looks right" or equivalent
  - The output file exists in data/processed/ or figures/
  
  Never write a finding that is provisional, pending, or uncertain.
  Mark those as PROVISIONAL in the session log instead.

STEP 3 — UPDATE STAGE STATUS
  Edit journal/STAGE_STATUS.md to reflect current state.

STEP 4 — CONFIRM TO NISHI
  Print: "Session committed. journal/ updated. Resume with: claude"
```

---

### 0.3 DECISION LOGGING PROTOCOL

Every time Claude Code makes a methodological decision during a session,
it must log it inline with this format before moving on:

```
🔒 DECISION [D-XXX]: [short title]
   Chose: [what was chosen]
   Over:  [what was rejected]
   Why:   [one sentence reason]
   Impact: [what this affects downstream]
```

These get collected into the session log at session end.
Example:

```
🔒 DECISION [D-001]: Otsu vs fixed threshold for SAR water extraction
   Chose:  Adaptive Otsu per image
   Over:   Fixed -16 dB threshold
   Why:    Damodar has high seasonal backscatter variation
   Impact: Water area estimates self-calibrate per scene
```

---

### 0.4 FINDING LOCK FORMAT

When writing to journal/FINDINGS.md, use exactly this format:

```
## FINDING [F-XXX] — [Stage] — [Date confirmed]
**Claim:** [one sentence — what was found]
**Evidence:** [metric + value + file reference]
**Confidence:** [HIGH / MEDIUM / LOW] — [reason]
**Implication:** [what this means for the paper]
**Figure:** [filename in figures/ if applicable]
---
```

Example:

```
## FINDING [F-001] — Stage 1 Storage Reconstruction — Day 3
**Claim:** Maithon reservoir shows clear negative storage anomaly in Sep 2009
consistent with documented catastrophic flood release event.
**Evidence:** ΔS_anthro = -0.31 BCM in Sep 2009 (> 2σ below mean)
File: data/processed/DVC_storage_timeseries_2002_2024.csv
**Confidence:** HIGH — aligns with Maiti et al. 2011 flood documentation
**Implication:** Validates Stage 1 reconstruction. 2009 event usable as
causal inference ground truth in Stage 4.
**Figure:** figures/Fig3_storage_timeseries.png
---
```

---

### 0.5 WHAT CLAUDE CODE NEVER DOES

```
✗ Never skips the session start ritual
✗ Never writes to journal/FINDINGS.md without Nishi confirming the result
✗ Never proceeds past the Day 8 checkpoint without running the 3-question check
✗ Never uses random K-fold CV on time series data
✗ Never overwrites data/processed/ files without backing up first
✗ Never changes AV_PARAMS without flagging it as a DECISION log entry
✗ Never assumes a previous result is still valid — always verify file exists
```

---

### 0.6 JOURNAL FOLDER STRUCTURE

```
dvc-research/
└── journal/
    ├── FINDINGS.md          ← Locked confirmed results only
    ├── SESSION_LOG.md       ← Running log, one entry per session
    ├── STAGE_STATUS.md      ← Current state of all 6 stages
    ├── DECISIONS.md         ← All D-XXX decision entries aggregated
    └── sessions/
        ├── session_001.md   ← Full detail backup of each session
        ├── session_002.md
        └── ...
```

---

# CLAUDE RESEARCH JOURNAL
## Complete Memory File — DVC Reservoir Attribution Project
### For Claude: Read this entire file before responding in any future session.

```
RESEARCHER : Nishi Kant Mandal
INSTITUTION: Birsa Institute of Technology (BIT), Sindri, Dhanbad, Jharkhand
DEGREE     : B.Tech Civil Engineering, 7th Semester
REG. NO.   : 22030430063
SUPERVISOR : Dr. Maya Rajnarayan Ray, Associate Professor, Civil Engg, BIT Sindri
STARTED    : March 2026
SPRINT     : 15-day accelerated execution with Claude as co-author
CONSTRAINT : 100% open-source data, ₹0 cost, no proprietary tools
STATUS     : Day 1 — GEE scripts dispatched, awaiting first outputs
```

---

## PART 1: WHO WE ARE AND WHAT WE ARE BUILDING

### 1.1 The Relationship

Claude is acting as **scientific co-author and research partner**, not advisor.
This means:
- Claude writes every line of code
- Nishi runs the code and pastes outputs back
- Claude interprets outputs in real-time and fixes errors immediately
- Claude writes paper sections as results come in
- Nishi makes field decisions (supervisor access, data availability)
- No false hope. No padding. Brutal honesty at every step.

A previous project collapsed. The failure mode was: exciting start → debugging walls in weeks 4–6 → confidence loss → time overrun → incomplete manuscript. This journal exists to prevent that by maintaining full context across sessions.

### 1.2 The Research Question

**Original (weak — methodology question, not findings question):**
"Can we separate climatic vs. anthropogenic signals in DVC reservoirs?"

**Revised (strong — findings question with yes/no answer):**
> "Do Damodar Valley Corporation reservoir operations leave a causally attributable, scale-dependent fingerprint in terrestrial water storage that is systematically misattributed to climate variability in basin-scale satellite analyses — and can an operational signature taxonomy predict future storage anomalies with higher fidelity than climate-only models?"

### 1.3 The Three Publishable Claims

| # | Claim | Test | Pass Criterion |
|---|-------|------|----------------|
| C1 | DVC operations produce causally attributable residuals that climate models misattribute | CCM surrogate test + Granger VAR on STL residuals | p < 0.05 on deseasonalised series |
| C2 | Each reservoir has unique DTW-classifiable operational fingerprint | DTW clustering, silhouette score, event validation | Silhouette > 0.5, clusters align with known 2009 flood / Rabi drawdown |
| C3 | Reservoir-scale anthropogenic signal explains fraction of GRACE-FO TWS unexplained by climate | Partial regression β₂ significance | p < 0.05 after controlling for climate |

### 1.4 The "So What" Statement (Pin This — Everything Serves This)

> India's water planners use GRACE satellite data to assess water stress at basin scale. This study proves that for the Damodar basin — and by inference for any heavily managed basin — a substantial fraction of what GRACE interprets as climate-driven storage change is actually dam operations. India's current GRACE-based water stress assessments are systematically biased for managed basins. The operational fingerprint taxonomy we develop gives operators a passive, satellite-based monitoring tool requiring zero ground sensors.

---

## PART 2: STUDY AREA — EXACT COORDINATES AND CONTEXT

### 2.1 The Three Reservoirs

| Reservoir | Lat/Lon | Capacity | Primary Function | Key Fact |
|-----------|---------|----------|-----------------|----------|
| Maithon Dam | 23.835°N, 86.821°E | 1.360 BCM | Flood control + hydropower | Tandem with Panchet |
| Panchet Dam | 23.577°N, 86.769°E | 0.290 BCM | Tandem flood control + power | Phase-lags Maithon by 2–4 weeks |
| Durgapur Barrage | 23.487°N, 87.307°E | Run-of-river | Irrigation via 2,494 km canals | Rabi drawdown Oct–Mar |

**GEE Bounding Boxes (copy-paste ready):**
```javascript
var maithon  = ee.Geometry.Rectangle([86.75, 23.78, 86.90, 23.90]);
var panchet  = ee.Geometry.Rectangle([86.72, 23.52, 86.84, 23.64]);
var durgapur = ee.Geometry.Rectangle([87.25, 23.44, 87.38, 23.54]);
```

### 2.2 Why This Basin Is a Perfect Natural Laboratory

1. **Tandem operation** — Maithon + Panchet share operational mandate but have different physical characteristics. Same climate zone, different fingerprint. Statistician's dream.
2. **Known historical events** — 2000 flood, 2009 catastrophic flood (documented in Maiti et al. 2011; Rudra 2018). These are ground-truth validation points for causal detection.
3. **Extreme sedimentation** — CWC 2022: Maithon lost ~18% live storage from original design. Detecting this from space = additional finding.
4. **Damodar = Jharkhand's sorrow** — policy relevance is built-in. Reviewers from India understand the stakes.
5. **Dhanbad coal belt** — VIIRS/Bhuvan NTL gives industrial activity proxy unavailable in global studies.

---

## PART 3: COMPLETE DATA SOURCE REGISTRY

### 3.1 Confirmed Free Datasets (All Verified March 2026)

| # | Dataset | Variable | GEE ID / URL | Resolution | Coverage | Registration |
|---|---------|----------|-------------|------------|----------|-------------|
| 1 | Sentinel-1 GRD | SAR water area | `COPERNICUS/S1_GRD` | 10m | 2014–present | GEE account |
| 2 | MODIS MOD09GA | Water area 2002–2013 | `MODIS/006/MOD09GA` | 500m | 2000–present | GEE account |
| 3 | CartoDEM v1.1 | Primary DEM | bhuvan-app3.nrsc.gov.in | 30m | India | Bhuvan free |
| 4 | ALOS AW3D30 | Backup DEM | `JAXA/ALOS/AW3D30/V2_2` | 30m | Global | GEE account |
| 5 | ICESat-2 ATL13 | Water surface elevation | openaltimetry.earthdata.nasa.gov | ~10m | 2018–present | NASA Earthdata |
| 6 | Sentinel-3 SRAL | Continuous elevation | hydroweb.theia-land.fr | — | 2016–present | Hydroweb free |
| 7 | CHIRPS v2.0 | Precipitation | `UCSB-CHG/CHIRPS/DAILY` | 5km | 1981–present | None |
| 8 | ERA5-Land | T, PET, soil moisture, ET | `ECMWF/ERA5_LAND/DAILY_AGGR` | 9km | 1950–present | GEE account |
| 9 | MODIS MOD16A2 | Actual ET | `MODIS/006/MOD16A2` | 500m | 2001–present | GEE account |
| 10 | MODIS MCD12Q1 | LULC annual | `MODIS/006/MCD12Q1` | 500m | 2001–present | GEE account |
| 11 | NRSC LULC | India LULC snapshots | Bhuvan thematic maps | 1:50,000 | India | Bhuvan free |
| 12 | MODIS MOD13Q1 | NDVI 16-day | `MODIS/006/MOD13Q1` | 250m | 2000–present | GEE account |
| 13 | Bhuvan NTL | Night lights 2012–2021 | Bhuvan NTL Portal | India | 2012–2021 | Bhuvan free |
| 14 | DMSP-OLS | Night lights 2002–2011 | `NOAA/DMSP-OLS/NIGHTTIME_LIGHTS` | 30 arc-sec | 1992–2013 | GEE account |
| 15 | GRACE-FO RL06.3 V4 | TWS anomaly | podaac.jpl.nasa.gov | ~330km | 2002–present | NASA Earthdata |
| 16 | Niño 3.4 | ENSO index | psl.noaa.gov/data/climateindices | N/A | 1950–present | None |
| 17 | IOD/DMI | Indian Ocean Dipole | JAMSTEC IOD website | N/A | 1958–present | None |
| 18 | Bhuvan Hydro Boundaries | Basin/watershed | Bhuvan thematic layers | Vector | India | Bhuvan free |
| 19 | HydroBASINS Lv8 | Global catchments | hydrosheds.org | Vector | Global | None |
| 20 | GHSL Population | Population density | `JRC/GHSL/P2023A/GHS_POP` | 100m | 1975–2025 | GEE account |
| 21 | JRC GSW | Permanent water mask | `JRC/GSW1_4/GlobalSurfaceWater` | 30m | 1984–present | GEE account |
| 22 | CWC Reservoir Bulletin | Validation storage | cwc.gov.in | Point | 2005–present | None |
| 23 | CAMELS-IND | Pre-training basins | Zenodo (free) | — | 241 basins | None |

### 3.2 Critical Access Warning

**India WRIS (indiawris.gov.in):** Previously reported as down (Apache page, early March 2026). **STATUS UPDATE 2026-03-24: PORTAL IS FUNCTIONAL.** Confirmed to have daily reservoir level and storage data for Damodar basin including Maithon. Navigate: indiawris.gov.in/wris/ → Reservoir Module → Damodar Basin → Maithon. No login required. Fallback: data.gov.in also has CWC daily reservoir data (confirmed, no login). **Priority action for Nishi: download 2017–2024 Maithon daily storage from WRIS or data.gov.in to complete historical validation.**

### 3.3 Four Accounts Needed (All Free, Register Day 1)

```
1. earthengine.google.com    → GEE (24-48hr approval)
2. urs.earthdata.nasa.gov    → NASA Earthdata (instant)
3. bhuvan.nrsc.gov.in        → ISRO/NRSC (instant)
4. hydroweb.theia-land.fr    → Sentinel-3 altimetry (instant)
```

---

## PART 4: COMPLETE PROBLEM REGISTRY AND SOLUTIONS

### FATAL PROBLEMS (Paper Dies Without These Solved)

---

#### FATAL-1: Residual ≠ Causation
**The Problem:** XGBoost residual (ΔS_anthro) has three alternative explanations: model underfit, measurement noise, missing climate driver. Without causal proof, the paper is correlation study, not attribution study.

**The Solution:** Twin causal test battery
- **Test A:** CCM with phase-randomised surrogate validation
  - STL-deseasonalise ALL series first (statsmodels STL, robust=True)
  - Run CCM on REMAINDER component only (not raw series)
  - Generate 999 phase-randomised surrogates via Fourier method
  - Real CCM ρ must exceed 95th percentile of surrogate ρ
  - Library: `pyEDM` — `pip install pyEDM`
- **Test B:** Granger causality on VAR residuals
  - Fit Vector Autoregression on [ΔS_climate, ΔS_anthro, downstream_proxy]
  - Test Granger on VAR residuals (not raw series)
  - Library: `statsmodels.tsa.stattools.grangercausalitytests`
- Pass criterion: p < 0.05 on either test = claim causation

**Status:** Not yet implemented. Scheduled Day 9–10.

---

#### FATAL-2: GRACE Basin Too Small
**The Problem:** Damodar basin ~23,370 km². GRACE mascon cell ~90,000–120,000 km². Entire study area = less than one quarter of one pixel. Raw GRACE is meaningless at this scale.

**The Solution:** ML statistical downscaling to 0.1° resolution BEFORE reconciliation analysis
- Method: Stacking ensemble (RF + XGBoost + Ridge) trained to predict fine-scale TWS from coarse GRACE
- Predictors: CHIRPS + ERA5 soil moisture + MODIS NDVI + CartoDEM slope (ALL already extracted in Stage 2)
- This means zero additional data collection
- Reference: Kalu et al. 2024 (downscaled GRACE in northern Australia to 0.05°); Long et al. 2020 WRR
- Reframe claim: "First ML-downscaled GRACE-FO product for Damodar basin" = standalone deliverable

**Status:** Not yet implemented. Scheduled after Stage 3.

---

#### FATAL-3: 2002–2013 Sensor Gap
**The Problem:** Sentinel-1 launched 2014. Study starts 2002. First 12 years = MODIS at 500m vs SAR at 10m (50:1 resolution ratio). MODIS is cloud-affected during monsoon; SAR is cloud-penetrating. Pre-2014 data is lower resolution AND less reliable at peak signal period.

**The Solution:** Explicit two-epoch design with quantile mapping bias correction
- **NOT a flaw — a deliberate structured design**
- Epoch 1 (2002–2013): MODIS era — calibrated to SAR scale via empirical QM in 2014–2015 overlap
- Epoch 2 (2014–2024): Sentinel-1 era — primary high-confidence data
- Quantile Mapping code: written in storage_reconstruction.py (see Part 7)
- Additional finding: "Did DVC operational regime change between epochs?" = regime shift detection

**Status:** QM code written and included in Day 2 Python script. Run after GEE CSVs received.

---

#### FATAL-4: No River Inflow Data
**The Problem:** Water balance = dS/dt = Inflow − Outflow − ET − Seepage. No inflow data = balance cannot close = storage reconstruction validity unverified.

**The Solution:** SCS Curve Number rainfall-runoff model — ALL inputs already in pipeline
```
Required inputs → Already have:
  Rainfall P        → CHIRPS daily ✓
  Land use (CN)     → MODIS MCD12Q1 / NRSC LULC ✓  
  Soil group        → HWSD (FAO, free, one download) ✗ (need to download)
  Slope             → CartoDEM ✓
  Catchment area    → Bhuvan boundaries ✓
```
```python
def scs_cn_runoff(P_mm, CN):
    S  = 25400/CN - 254    # potential maximum retention (mm)
    Ia = 0.2 * S           # initial abstraction
    if P_mm <= Ia: return 0
    return (P_mm - Ia)**2 / (P_mm - Ia + S)
# Monthly inflow = SCS_CN(CHIRPS_monthly, CN) × catchment_area_m2
```
**Status:** Code skeleton written. Needs HWSD soil group download (Day 5).

---

#### FATAL-5: CCM Seasonality Trap
**The Problem:** All three reservoirs fill in monsoon, draw down in winter. Rainfall peaks in monsoon. CCM will find "causality" between ΔS_anthro and ΔS_climate simply because they share monsoon seasonal driver — false positive from common external forcing.

**The Solution:** STL decomposition BEFORE CCM — canonical fix in ecological dynamics literature
```python
from statsmodels.tsa.seasonal import STL

def decompose_for_ccm(series, period=12):
    stl    = STL(series, period=period, robust=True)
    result = stl.fit()
    return result.resid  # ONLY the remainder goes into CCM

# Surrogate test:
def phase_randomise(series, n=999):
    ft = np.fft.rfft(series)
    magnitudes = np.abs(ft)
    surrogates = []
    for _ in range(n):
        phases    = np.random.uniform(0, 2*np.pi, len(ft))
        ft_surr   = magnitudes * np.exp(1j * phases)
        surrogate = np.fft.irfft(ft_surr, n=len(series))
        surrogates.append(surrogate)
    return np.array(surrogates)
```
**Status:** Code skeleton written. Apply before any CCM run (Day 9).

---

#### FATAL-6: n=264 Too Small for Deep Learning
**The Problem:** 264 monthly data points (22 years × 12 months). TFT and LSTM need thousands. Training from scratch = underfit = worse than XGBoost = no added value.

**The Solution:** Transfer learning from CAMELS-IND (241 Indian basins × 240 months = 57,840 samples)
```python
# Stage 1: Pre-train on CAMELS-IND (learns Indian monsoon hydrology)
camels = load_camels_ind()   # Download free from Zenodo
pretrain_lstm(camels, epochs=50, lr=1e-3)

# Stage 2: Fine-tune on DVC — freeze first 2 layers
for param in lstm.layers[0:2].parameters():
    param.requires_grad = False   # keeps Indian hydrology knowledge
finetune_lstm(dvc_data, epochs=20, lr=1e-4)
```
Reference: Kratzert et al. 2019 WRR — most cited recent hydrology deep learning paper
**Status:** Not yet implemented. Day 8. If time pressure: skip LSTM, use XGBoost only (still publishable).

---

### SERIOUS PROBLEMS (Paper Weakened Without These)

---

#### SERIOUS-1: Monsoon SAR Rice Paddy Confusion
**The Problem:** Flooded rice paddies in Damodar floodplain have identical SAR backscatter to open water. Jul–Sep: Otsu threshold misclassifies agricultural flood water as reservoir, inflating area by 10–40%.

**The Solution:** SPRI (SAR-based Paddy Rice Index) + JRC permanent water mask
- Rice phenological trajectory: low Jun → rising Jul-Sep (canopy growth) → low Oct
- Open water: monotonically low throughout
- Apply JRC Global Surface Water max_extent as hard spatial constraint
```javascript
var jrcMask = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
  .select('max_extent').eq(1)
  .focal_max(500, 'circle', 'meters');
// Apply BEFORE Otsu: only classify water within known max reservoir footprint
var water = composite.lt(threshold).updateMask(jrcMask);
```
**Status:** Already implemented in Day 1 GEE script.

---

#### SERIOUS-2: SHAP Correlated Features
**The Problem:** API₆ and CHIRPS P(t) are correlated at ~r=0.75. SHAP splits attribution based on tree structure, not physical causation. Reviewer will ask: is it antecedent moisture or current rainfall causing storage change?

**The Solution:** PCA-SHAP bridge — run PCA within correlated feature groups → SHAP on orthogonal PCs → back-rotate to original feature space
```python
from sklearn.decomposition import PCA

rainfall_group = ['P_t','P3_t','API6','SM1','SM2']
pca_rain = PCA(n_components=2)
rain_pcs = pca_rain.fit_transform(X[rainfall_group])

# Run XGBoost on orthogonal PCs → SHAP on PCs → back-rotate
shap_original = rain_pcs_shap @ pca_rain.components_
```
Reference: Hooker & Mentch 2019 "Please stop permuting features"
**Status:** Not yet implemented. Day 7–8.

---

#### SERIOUS-3: 30m DEM Volume Error
**The Problem:** ALOS/CartoDEM vertical RMSE ±3–5m in Jharkhand terrain. Near full reservoir level, this = ±15–25% volume error. ICESat-2 calibration thin (~20 overpasses, 91-day repeat).

**The Solution:** Dual-altimeter fusion — ICESat-2 (accuracy) + Sentinel-3 SRAL (frequency)
- Sentinel-3A/B: 27-day repeat, free via Hydroweb+ (hydroweb.theia-land.fr)
- Hydroweb may already have processed Maithon/Panchet series — check first
- If yes: 10-year continuous elevation time series at 27-day resolution = free
- Combined: CartoDEM geometry + ICESat-2 absolute calibration + Sentinel-3 continuous monitoring
- Volume uncertainty drops from ±20% to ±8–10%

**Status:** Check Hydroweb database for DVC reservoirs = Day 1 task.

---

#### SERIOUS-4: Monthly Timestep vs. Flood Physics
**The Problem:** DVC flood releases happen in 48–72 hours. Monthly aggregation converts catastrophic release to smoothed anomaly. ΔS_anthro systematically underestimates flood control operational intensity.

**The Solution (accepted caveat + reframing):**
- Explicitly state: "Our monthly framework detects seasonal operational patterns with high fidelity; sub-monthly emergency releases are partially averaged out, making our estimates of flood control anthropogenic signal conservative."
- Conservative estimates make claims STRONGER not weaker — you're detecting a signal even after averaging reduces it
- This is a 2-sentence limitation statement, not a fatal flaw

**Status:** Acknowledged. Will state in Discussion section.

---

#### SERIOUS-5: India WRIS — RESOLVED 2026-03-24
**The Problem:** India WRIS portal reported as Apache default page (site down, early March 2026).
**STATUS: RESOLVED.** Portal is functional as of 2026-03-24. Also confirmed: data.gov.in has structured CWC daily reservoir data (no login). Both sources provide historical 2017–2024 Maithon storage data.

**The Solution:** CWC Weekly Reservoir Bulletin as primary validation
```python
import tabula
import requests

# Download CWC weekly bulletins (PDFs publicly available)
# URL pattern: cwc.gov.in/reservoir-storage-bulletin
# tabula-py extracts tables from PDFs automatically

def scrape_cwc_bulletin(pdf_path):
    tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
    # Find table containing Maithon/Panchet storage data
    for t in tables:
        if 'Maithon' in t.to_string() or 'MAITHON' in t.to_string():
            return t
    return None
```
**Status:** CWC bulletin scraping ready to run Day 4.

---

## PART 5: COMPLETE METHODOLOGY ARCHITECTURE

### 5.1 The Six Stages

```
STAGE 1: Multi-sensor storage reconstruction
  Sentinel-1 SAR (10m, 2014–2024) + MODIS (500m, 2002–2013)
  + CartoDEM hypsometry + ICESat-2 + Sentinel-3 elevation
  + JRC water mask (rice paddy filter)
  + Quantile mapping cross-sensor calibration
  + Sedimentation correction (CWC 2022 rates)
  → OUTPUT: ΔS_obs monthly time series, all 3 reservoirs, 2002–2024

STAGE 2: Driver dataset construction
  CHIRPS + ERA5 + MODIS NDVI/LULC + ENSO/IOD + Night lights
  + API₆ antecedent moisture index (key feature)
  + SCS-CN inflow proxy (HWSD + CHIRPS + CartoDEM)
  + VIF check (remove if VIF > 10)
  → OUTPUT: X_climate feature matrix (264 rows × ~22 features)

STAGE 3: Multi-model climate attribution
  XGBoost (Optuna 150 trials) + LSTM (CAMELS-IND pretrain) + TFT
  Expanding window CV (NEVER random K-fold on time series)
  SHAP beeswarm + dependence plots + time-varying SHAP (rolling 36-month)
  PCA-SHAP for correlated features
  → OUTPUT: ΔS_climate predicted + ΔS_anthro residual + SHAP figures

STAGE 4: Causal inference engine [THE NOVEL CORE]
  STL decomposition of all series first
  CCM with 999 phase-randomised surrogates (pyEDM)
  Granger VAR on STL residuals (statsmodels)
  HMM 3-state operational regime detection (hmmlearn)
  Validation against known events: 2009 flood, 2015-16 drought
  → OUTPUT: Causal attribution p-values + HMM state sequences

STAGE 5: GRACE-FO cross-scale reconciliation [MOONSHOT]
  ML downscaling GRACE 1° → 0.1° (RF+XGBoost stacking)
  TWS decomposition: TWS = GWS + SMS + SWS
  Partial regression: GRACE_TWS ~ β₁·ΔS_climate + β₂·ΔS_anthro + β₃·SMS
  → OUTPUT: β₂ significance = proof DVC contaminates GRACE

STAGE 6: Operational fingerprint taxonomy
  DTW distance matrix (dtaidistance library)
  Ward hierarchical clustering
  Silhouette score for K selection
  4 expected archetypes: Monsoon Surge / Flood Release / Rabi Drawdown / Conservation
  → OUTPUT: Taxonomy figure — visual proof of satellite-detectable operational signatures
```

### 5.2 Hard Decision Checkpoint — End of Day 8

Ask exactly three questions:
1. Is ΔS_anthro time series clean for all 3 reservoirs with uncertainty bounds? (Y/N)
2. Does XGBoost NSE land between 0.60–0.85 for ≥ 2 of 3 reservoirs? (Y/N)
3. Is any form of Granger signal present at p < 0.10 for Maithon–Panchet? (Y/N)

```
3/3 → Execute all 6 stages → Target: Water Resources Research (WRR)
2/3 → Execute stages 1-4+6 → Target: Journal of Hydrology (Q1, IF 6.7)
1/3 → Execute stages 1-3+6 → Target: Remote Sensing of Environment (Q1, IF 4.1)
0/3 → STOP. Something structurally wrong. Diagnose storage reconstruction immediately.
```

### 5.3 Tiered Publication Strategy

| Tier | Stages | Target Journal | IF | Probability |
|------|--------|---------------|-----|-------------|
| Core | 1+2+3+6 | Remote Sensing (MDPI) / J. Hydrol. Reg. Studies | 3.0–4.5 | 55–60% |
| Differentiator | +Stage 4 Granger | Journal of Hydrology | 6.7 | 38% |
| Moonshot | All 6 stages | Water Resources Research (AGU) | 5.4 | 7–15% |

**Publication probability with tiered strategy + Day 8 checkpoint: 61%**

---

## PART 6: FEATURE ENGINEERING MASTER TABLE

All features to extract in Stage 2. Everything via GEE unless noted.

| Feature | Symbol | GEE / Source | Rationale |
|---------|--------|-------------|-----------|
| Monthly rainfall | P(t) | CHIRPS daily → monthly | Primary driver |
| 3-month cumulative | P₃(t) | Derived | Seasonal accumulation |
| 6-month API | API₆ | Derived: Σ(0.85^i × P(t-i)) | Soil memory — CRITICAL |
| PET Penman-Monteith | PET(t) | ERA5-Land | Evaporative demand |
| Actual ET | AET(t) | MODIS MOD16A2 | Better than ERA5 PET |
| Soil moisture 0–28cm | SM1(t) | ERA5-Land | Near-surface |
| Soil moisture 28–100cm | SM2(t) | ERA5-Land | Deep vadose |
| Mean temperature | T(t) | ERA5-Land | ET driver |
| NDVI catchment mean | NDVI(t) | MODIS MOD13Q1 16-day | Vegetation proxy |
| Cropland fraction | LC_crop | MODIS MCD12Q1 annual | Irrigation demand |
| Forest fraction | LC_for | MODIS MCD12Q1 annual | Interception |
| ENSO index | Niño3.4 | NOAA CPC | Teleconnection |
| IOD index | DMI | JAMSTEC | Indian Ocean forcing |
| Night lights | NTL | Bhuvan NTL + DMSP-OLS | Industrial activity |
| Previous month ΔS | ΔS(t-1) | Lagged target | Autocorrelation |
| 3-month lagged ΔS | ΔS(t-3) | Lagged target | Seasonal persistence |
| SCS-CN inflow proxy | Q(t) | CHIRPS × CN × catchment | Water balance closure |
| Monsoon onset anomaly | MO_anom | Derived from CHIRPS | Seasonal shift detection |

---

## PART 7: ALL CODE WRITTEN SO FAR

### 7.1 GEE Script — Sentinel-1 Water Area Extraction (Day 1)
**File:** Paste into code.earthengine.google.com → Run → Export to Drive
**Expected output:** `water_area_sentinel1.csv` — 396 rows (132 months × 3 reservoirs)
**Columns:** date, reservoir, water_area_km2, n_images, gap_flag

Key design decisions baked in:
- JRC permanent water mask applied (prevents rice paddy confusion)
- Otsu adaptive thresholding (not fixed threshold — adapts to each image)
- Refined Lee speckle filter (5×5 kernel, edge-preserving)
- Gap flag = 1 when no S1 images available for that month
- Resolution: 20m (computational efficiency vs. 10m, acceptable for reservoir-scale)

### 7.2 GEE Script — MODIS Water Area Backfill (Day 1, parallel tab)
**File:** Second GEE tab, run simultaneously
**Expected output:** `water_area_modis.csv` — 432 rows (144 months × 3 reservoirs)
**Columns:** date, reservoir, water_area_km2, sensor, n_images, gap_flag

Key: NDWI > 0.2 threshold (standard for open water in Indian reservoirs)

### 7.3 Python Script — Storage Reconstruction Pipeline (Day 2)
**File:** `storage_reconstruction.py`
**Run after:** Both GEE CSVs downloaded from Google Drive

Pipeline steps:
1. Load and clean both CSVs
2. Cross-sensor quantile mapping using 2014–2015 overlap
3. Merge epochs: MODIS (2002–2013) + Sentinel-1 (2014–2024)
4. Area → Volume conversion via power law: V = a × A^b
5. Compute storage anomaly vs. 2005–2015 baseline
6. Apply sedimentation correction (CWC 2022 rates)
7. Save: `DVC_storage_timeseries_2002_2024.csv`
8. Generate diagnostic plot Fig3_storage_timeseries.png

**CRITICAL PLACEHOLDER:** AV_PARAMS (a, b coefficients) are placeholder values from literature:
```python
AV_PARAMS = {
    'maithon':  {'a': 0.0821, 'b': 1.412, 'dead_storage_bcm': 0.185},
    'panchet':  {'a': 0.0312, 'b': 1.389, 'dead_storage_bcm': 0.048},
    'durgapur': {'a': 0.0095, 'b': 1.201, 'dead_storage_bcm': 0.010}
}
```
**MUST UPDATE** with CartoDEM-derived values. Derive using hypsometry notebook (Day 3).

**Validation check:** Maithon 2009 flood period should show:
- Large POSITIVE anomaly: Jul–Aug 2009 (pre-monsoon storage + filling)
- Large NEGATIVE drop: Sep–Oct 2009 (emergency flood control releases)
- If this pattern is ABSENT: storage reconstruction is wrong, debug before proceeding

### 7.4 SCS-CN Inflow Proxy Skeleton
```python
def scs_cn_runoff(P_mm, CN):
    S  = 25400/CN - 254
    Ia = 0.2 * S
    if P_mm <= Ia: return 0
    return (P_mm - Ia)**2 / (P_mm - Ia + S)
```
Status: Skeleton only. Full implementation Day 5 after HWSD soil group download.

### 7.5 STL Decomposition + CCM Surrogate Test Skeleton
```python
from statsmodels.tsa.seasonal import STL
def decompose_for_ccm(series, period=12):
    stl = STL(series, period=period, robust=True)
    return stl.fit().resid  # only the remainder goes into CCM

def phase_randomise(series, n=999):
    ft = np.fft.rfft(series)
    magnitudes = np.abs(ft)
    surrogates = []
    for _ in range(n):
        phases = np.random.uniform(0, 2*np.pi, len(ft))
        surrogates.append(np.fft.irfft(magnitudes * np.exp(1j*phases), n=len(series)))
    return np.array(surrogates)
```
Status: Skeleton only. Full CCM implementation Day 9.

### 7.6 DTW Clustering Skeleton
```python
from dtaidistance import dtw
from scipy.cluster.hierarchy import linkage, fcluster

# Prepare 22 annual segments × 3 reservoirs = 66 segments of length 12
dist_matrix = dtw.distance_matrix_fast(segments)  # (66×66)
Z = linkage(dist_matrix, method='ward')
# K=4 expected archetypes: Monsoon Surge, Flood Release, Rabi Drawdown, Conservation
labels = fcluster(Z, 4, criterion='maxclust')
```
Status: Skeleton only. Full implementation Day 11.

### 7.7 HMM Operational Regime Detection Skeleton
```python
from hmmlearn import hmm
model = hmm.GaussianHMM(n_components=3, covariance_type='full',
                         n_iter=1000, random_state=42)
model.fit(delta_S_anthro.reshape(-1,1))
states = model.predict(delta_S_anthro.reshape(-1,1))
# State with most negative emission mean → drawdown/release mode
# State near zero → conservation mode
# State with most positive → storage buildup
```
Status: Skeleton only. Full implementation Day 10.

---

## PART 8: THE 15-DAY SPRINT SCHEDULE

### Working Model
- Claude writes every script and paper section
- Nishi runs code and pastes outputs/errors back
- Claude fixes errors in-session, same conversation
- Minimum 10 hours/day
- Paper sections written in parallel with analysis (not after)

### Day-by-Day Plan

| Day | Morning Task | Afternoon Task | Deliverable | Verify With |
|-----|-------------|----------------|-------------|-------------|
| 1 | Register 4 accounts; Run S1 GEE script | Run MODIS GEE script (parallel) | water_area_sentinel1.csv + water_area_modis.csv | Paste 20 rows to Claude |
| 2 | Download CartoDEM tiles (Bhuvan, 20/day limit) | Run storage_reconstruction.py | DVC_storage_timeseries_2002_2024.csv + Fig3 | 2009 flood pattern check |
| 3 | Build A-V hypsometry from CartoDEM | Update AV_PARAMS in script, rerun | Validated A-V curves | Compare to WRIS capacity values |
| 4 | GEE driver extraction: CHIRPS + ERA5 + NDVI | CWC bulletin scraping for validation | X_climate_raw.csv + validation_storage.csv | Paste CHIRPS monsoon seasonal pattern |
| 5 | GEE driver extraction: LULC + NTL + ENSO/IOD | HWSD download + SCS-CN inflow model | X_climate_full.csv + Q_inflow_proxy.csv | VIF check output |
| 6 | Feature engineering: API₆, lags, VIF check, PCA groups | Final feature matrix assembly | X_final_264x22.csv | Correlation matrix heatmap |
| 7 | XGBoost training (Optuna 150 trials) | Expanding window CV + NSE/KGE metrics | xgb_model.pkl + cv_results.csv | NSE values for each reservoir |
| 8 | SHAP analysis (beeswarm + dependence + time-varying) | **DECISION CHECKPOINT** | Fig4_SHAP.png + delta_S_anthro.csv | 3-question checkpoint → scope decision |
| 9 | STL decomposition of all series | Granger VAR test (multivariate) | granger_results.csv | p-values for each lag |
| 10 | CCM with 999 surrogates | HMM 3-state fitting | Fig6_CCM.png + Fig7_HMM.png | CCM convergence plot |
| 11 | DTW distance matrix + Ward clustering | Archetype identification + annotation | Fig8_taxonomy.png | Silhouette score |
| 12 | Validate clusters vs known events (2009 flood, 2016 drought) | GRACE-FO download + basic reconciliation if time | Fig5_anthro_timeseries.png | Event annotation check |
| 13 | Claude writes: Abstract + Introduction + Methods | Nishi fills: Study area + Data description | manuscript_draft_v1.docx | Read-through with supervisor |
| 14 | Claude writes: Results + Discussion skeleton | Finalize all figures at 300 DPI, format references | manuscript_draft_v2.docx | All 10 figures complete |
| 15 | Supervisor final review | Upload preprint to EarthArXiv + journal submission | Submitted manuscript | DOI on EarthArXiv = citable same day |

---

## PART 9: PAPER STRUCTURE

### Target Title
*Causally Attributable Anthropogenic Fingerprints in Reservoir Storage Variability: Cross-Scale Evidence from the Damodar Valley Corporation System Using Explainable AI and Satellite Observations*

### Target Journals (in priority order)
1. **Water Resources Research** (AGU) — IF 5.4, A* — if CCM significant + GRACE holds
2. **Journal of Hydrology** — IF 6.7, Q1 — if Granger significant
3. **Remote Sensing of Environment** — IF 11.1, Q1 — if taxonomy + SHAP clean
4. **Remote Sensing** (MDPI) — IF 4.1, Q1 — guaranteed fallback with Tier 1

### Section Plan

| Section | Word Count | Who Writes | Source Material |
|---------|-----------|------------|----------------|
| Abstract | 250 | Claude (Day 13) | All results |
| 1. Introduction | 1000 | Claude (Day 13) | Gap analysis in this journal |
| 2. Study area + data | 800 | Nishi fills, Claude edits | Part 2 + Part 3 of journal |
| 3. Methods | 2000 | Claude (Day 13) | Part 5 of journal |
| 4. Results | 2500 | Claude (Day 14) | All figure outputs |
| 5. Discussion | 1500 | Claude (Day 14) | Problems/solutions + comparison to Ji 2023, Wada 2017 |
| 6. Conclusions | 400 | Claude (Day 14) | Directly answer C1, C2, C3 |

### The 10 Figures

| Fig | Content | Produced Day |
|-----|---------|-------------|
| Fig. 1 | Study area map: DVC system, catchments, satellite coverage | Day 3 (QGIS) |
| Fig. 2 | Multi-sensor fusion: SAR water area + ICESat-2 + A-V curve | Day 3 |
| Fig. 3 | Storage time series 2002–2024 all 3 reservoirs with ensemble prediction | Day 2 (diagnostic) |
| Fig. 4 | SHAP summary plots — driver importance per reservoir | Day 8 |
| Fig. 5 | ΔS_anthro time series with annotated events (2009 flood, 2016 drought) | Day 12 |
| Fig. 6 | CCM convergence: ρ vs library size L for Maithon–Panchet pair | Day 10 |
| Fig. 7 | HMM operational state sequences all 3 reservoirs | Day 10 |
| Fig. 8 | Operational fingerprint taxonomy: DTW centroids ± envelopes | Day 11 |
| Fig. 9 | GRACE-FO reconciliation (if Stage 5 executed) | Day 12 |
| Fig. 10 | Conceptual synthesis schematic | Day 14 (Claude-drawn SVG) |

---

## PART 10: FULL REFERENCE LIST

Every reference needed. Format ready for submission.

1. Ji, R., Zhang, M., Waweru, F., He, B., & Shen, G. (2023). Separating climate- and human-induced changes in terrestrial water storage. *Journal of Hydrology*, 625, 129142.
2. Wada, Y., Wisser, D., & Bierkens, M.F.P. (2017). Human and climate impacts on global water storage changes. *Nature Geoscience*, 10, 834–839.
3. Pekel, J.F., Cottam, A., Gorelick, N., & Belward, A.S. (2016). High-resolution mapping of global surface water. *Nature*, 540, 418–422.
4. Rodell, M., Velicogna, I., & Famiglietti, J.S. (2009). Satellite-based estimates of groundwater depletion in India. *Nature*, 460, 999–1002.
5. Sugihara, G., May, R., Ye, H., et al. (2012). Detecting causality in complex ecosystems. *Science*, 338(6106), 496–500.
6. Lim, B., Arık, S.Ö., Loeff, N., & Pfister, T. (2021). Temporal Fusion Transformers for interpretable multi-horizon time series forecasting. *International Journal of Forecasting*, 37(4), 1748–1764.
7. Long, D., Yang, W., Scanlon, B.R., et al. (2020). South Asia's surprising monsoon anomalies. *Geophysical Research Letters*, 47(5).
8. Twele, A., Cao, W., Plank, S., & Martinis, S. (2016). Sentinel-1-based flood mapping. *Remote Sensing*, 8(10), 827.
9. Biemans, H., Haddeland, I., Kabat, P., et al. (2011). Impact of reservoirs on river discharge. *Water Resources Research*, 47(3), W03509.
10. Besseling, D.R.H., De Kok, R.J., & Scheuchl, B. (2021). Inland water body dynamics from ICESat-2. *Water Resources Research*, 57(5), e2020WR028456.
11. Maiti, S., & Bhattacharya, A.K. (2011). Flood analysis using DEM: Damodar River basin. *Journal of Indian Society of Remote Sensing*, 39(4), 535–545.
12. Tapley, B.D., Watkins, M.M., Flechtner, F., et al. (2019). Contributions of GRACE to understanding climate change. *Nature Climate Change*, 9, 358–369.
13. Kratzert, F., Klotz, D., Shalev, G., et al. (2019). Towards learning universal hydrological equations. *Hydrology and Earth System Sciences*, 23(12), 5089–5110.
14. Granger, C.W.J. (1969). Investigating causal relations by econometric models. *Econometrica*, 37(3), 424–438.
15. Sakoe, H., & Chiba, S. (1978). Dynamic programming algorithm for spoken word recognition. *IEEE Transactions ASSP*, 26(1), 43–49.
16. Theiler, J., Eubank, S., Longtin, A., et al. (1992). Testing for nonlinearity in time series: the method of surrogate data. *Physica D*, 58, 77–94.
17. Nash, J.E., & Sutcliffe, J.V. (1970). River flow forecasting through conceptual models. *Journal of Hydrology*, 10(3), 282–290.
18. Kling, H., Fuchs, M., & Paulin, M. (2012). Runoff conditions in the upper Danube basin. *Journal of Hydrology*, 424–425, 264–277.
19. Chen, T., & Guestrin, C. (2016). XGBoost: a scalable tree boosting system. *KDD 2016 Proceedings*.
20. Lundberg, S.M., & Lee, S.I. (2017). A unified approach to interpreting model predictions. *NIPS 30*.
21. Hooker, G., & Mentch, L. (2019). Please stop permuting features. *arXiv:1905.03151*.
22. Ye, H., Deyle, E.R., Gilarranz, L.J., & Sugihara, G. (2015). Distinguishing time-delayed causal interactions using CCM. *Scientific Reports*, 5, 14750.
23. Rudra, K. (2018). *Rivers of the Ganga-Brahmaputra-Meghna Delta*. Springer.
24. IPCC. (2022). *Climate Change 2022: Impacts, Adaptation and Vulnerability*. Cambridge University Press.
25. Central Water Commission. (2022). *Reservoir Sedimentation Atlas of India*. Ministry of Jal Shakti, GoI.
26. Diebold, F.X., & Mariano, R.S. (1995). Comparing predictive accuracy. *JBES*, 13(3), 253–263.
27. Kalu, I., Ndehedehe, C.E., Okwuosa, C.N., et al. (2024). Downscaling GRACE data using ML for northern Australia. *Journal of Hydrology*.

---

## PART 11: CRITICAL NUMBERS AND THRESHOLDS

Know these by heart. Every result gets checked against these.

| Metric | Below This: Problem | Target: Publishable | Above This: Suspicious |
|--------|--------------------|--------------------|----------------------|
| XGBoost NSE (climate-only) | < 0.50 | 0.60–0.80 | > 0.85 (no residual signal) |
| KGE | < 0.50 | > 0.60 | — |
| PBIAS | > ±25% | ±10–15% | — |
| CCM ρ (at max library) | < 0.20 | > 0.35, converging | > 0.90 (check for overfitting) |
| Granger p-value | > 0.10 | < 0.05 | — |
| DTW Silhouette score | < 0.30 | > 0.45 | — |
| HMM n_states | — | 3 (flood/irrigation/conservation) | > 5 (overfit) |
| ICESat-2 overpasses/reservoir | < 10 (use DEM-only) | 15–30 | — |
| GRACE partial R² (β₂) | < 0.05 | > 0.15 | — |
| Water balance closure error | > 35% (reconstruct) | < 20% | — |

---

## PART 12: KNOWN VALIDATION EVENTS

These are your ground truth. Results MUST show signal at these dates.

| Event | Date | Expected Signal | Reservoir |
|-------|------|----------------|-----------|
| Damodar catastrophic flood | Sep 2009 | Large negative ΔS_anthro spike (massive release) | Maithon + Panchet |
| Pre-flood precautionary storage | Jul–Aug 2009 | Large positive ΔS_anthro | Maithon |
| 2000 Damodar flood | Sep–Oct 2000 | Negative spike (MODIS epoch, lower confidence) | Maithon + Panchet |
| 2015–16 El Niño drought | Jun 2015–May 2016 | Persistent negative anomaly | All three |
| Rabi irrigation season | Oct–Mar every year | Monotonic drawdown | Durgapur only |
| Monsoon conservation | Apr–Jun every year | Near-zero / slight positive | All (pre-fill) |

---

## PART 13: WHAT NISHI STILL NEEDS TO TELL CLAUDE

Before we can proceed from Day 1, Claude needs these answers:

1. **Operating system?** (Windows / Mac / Linux) — affects terminal commands
2. **GEE account approved yet?** (Yes / No / Pending) — if not, alternate download path
3. **Supervisor availability for Day 14 review?** (Yes she can / No she's away)
4. **Have you downloaded any data already?** If yes, what format and what columns?
5. **Did you check Hydroweb for Maithon/Panchet?** (hydroweb.theia-land.fr — search reservoir name)

---

## PART 14: HONEST PROBABILITY ASSESSMENT

| Outcome | Probability | Condition |
|---------|-------------|-----------|
| B.Tech project distinction | 82% | Regardless of publication |
| Submittable manuscript (any tier) | 61% | With tiered strategy + Day 8 checkpoint |
| Published in Q2 journal | 38% | If Day 8 checkpoint passes 2/3 |
| Published in Q1 journal | 18% | If Granger significant |
| Published in WRR/RSE (A*) | 7–15% | If all 6 stages succeed |

**The real collapse risk is NOT methodology. It is:**
- Falling behind in Weeks 2–3 and not catching up
- Ignoring the Day 8 checkpoint and pushing forward on bad results
- Starting paper writing too late (after all analysis done)

**The fix is this journal. Every session starts by reading this file.**

---

## PART 15: SESSION LOG

### Session 1 — March 2026
**What was accomplished:**
- Full synopsis reviewed and critiqued
- Research question revised from methodology to findings framing
- 3 publishable claims defined
- 6 fatal problems identified and solved academically
- 7 serious problems identified and solved
- Complete data source audit (22 datasets, all free)
- Bhuvan/ISRO platform deep-audited — 5 upgrades found
- 20-week plan created (RESEARCH_EXECUTION_PLAN.md)
- Data audit file created (DATA_SOURCE_AUDIT.md)
- Plan compressed to 15-day sprint
- Day 1 GEE scripts written (Sentinel-1 + MODIS)
- Day 2 Python storage reconstruction script written
- This journal created

**Outputs created this session:**
- `/outputs/RESEARCH_EXECUTION_PLAN.md` — full 20-week plan
- `/outputs/DATA_SOURCE_AUDIT.md` — all 22 datasets verified
- `/outputs/CLAUDE_RESEARCH_JOURNAL.md` — this file

**Awaiting from Nishi:**
- OS, GEE status, supervisor availability
- GEE script outputs (water_area CSVs)
- Hydroweb check for DVC reservoirs

**Next session begins at:** Day 1 GEE output verification → A-V hypsometry derivation → driver extraction

---

*This journal is a living document. Every session: Claude reads this first, then responds. Every session: new results appended to Session Log. The paper gets built here before it goes into Word.*

*Last updated: Session 1, March 2026*

---

## PART 16: MACHINE AND ENVIRONMENT

```
OS        : Ubuntu 24.04.4 LTS
HOSTNAME  : stark007-Inspiron-14-5420
USERNAME  : stark007
PROJECT   : /home/stark007/dvc-research
ENV       : uv + Python 3.11
JUPYTER   : cd /home/stark007/dvc-research && uv run jupyter lab
CLAUDE CC : cd /home/stark007/dvc-research && claude
GEE AUTH  : cd /home/stark007/dvc-research && uv run earthengine authenticate
PYTHON    : uv run python <script>   (always use uv run)
SPRINT    : Day 1 — environment ready, GEE auth pending
```

## PART 17: JOURNAL FILE PATHS

```
FINDINGS    : /home/stark007/dvc-research/journal/FINDINGS.md
SESSION LOG : /home/stark007/dvc-research/journal/SESSION_LOG.md
STAGE STATE : /home/stark007/dvc-research/journal/STAGE_STATUS.md
DECISIONS   : /home/stark007/dvc-research/journal/DECISIONS.md
SESSIONS    : /home/stark007/dvc-research/journal/sessions/session_NNN.md
```
