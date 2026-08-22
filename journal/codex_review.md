       # DVC Reservoir Research Publication Prospectus
      2 +
      3 +## Independent technical, novelty, practicality, and publication audit
      4 +
      5 +**Audit date:** 11 July 2026
      6 +**Project:** DVC Reservoir Attribution
      7 +**Scope reviewed:** repository, processed outputs, thesis, journal manuscript, figures, dashboard, research journal, current literature, and current journal information
      8 +**Method:** primary-agent audit plus three independent reviews covering technical rigor, novelty, and publication strategy
      9 +
     10 +> This is a decision document, not promotional text. It intentionally uses the
     11 +> strongest skeptical interpretation a serious reviewer could take. It preserves
     12 +> the useful work while separating demonstrated evidence from attractive claims.
     13 +> It also supersedes the optimistic readiness and probability estimates in
     14 +> PROJECT_PROSPECT.md where the two documents conflict.
     15 +
     16 +---
     17 +
     18 +## 1. Executive Verdict
     19 +
     20 +### Is this a good final-year project?
     21 +
     22 +**Yes. It is an unusually ambitious and well-documented final-year prototype.**
     23 +The repository shows serious effort: an open-data remote-sensing pipeline,
     24 +time-aware modelling attempts, uncertainty checks, causal-analysis attempts,
     25 +publication figures, a manuscript, a thesis, a dashboard, and a candid internal
     26 +research journal. For a B.Tech project, the scope and presentation are strong.
     27 +
     28 +### Is the current manuscript a good high-index research paper?
     29 +
     30 +**No, not in its current scientific form.** The core storage calibration is
     31 +inconsistent with the authoritative CWC Maithon geometry; the flagship GRACE
     32 +coefficient is reported in the wrong units; XGBoost validation leaks test
     33 +information; the CCM causal direction is interpreted backwards; and an
     34 +underperforming model residual is called anthropogenic without release or gate
     35 +records. These are central validity failures, not cosmetic reviewer comments.
     36 +
     37 +### Can it become publishable?
     38 +
     39 +**Yes. Salvage potential is high if the paper is narrowed and rebuilt from the
     40 +physical foundation.** The best immediate contribution is a rigorously validated
     41 +Sentinel-1 Maithon storage record using the official CWC elevation-area-capacity
     42 +curve. A strong causal attribution paper needs additional operational data and a
     43 +different design.
     44 +
     45 +### Scorecard
     46 +
     47 +| Dimension | Honest score | Interpretation |
     48 +|---|---:|---|
     49 +| Importance of the problem | 8/10 | Managed-reservoir monitoring and transparent water accounting matter |
     50 +| Final-year project quality | 8/10 | Ambitious, documented, visually strong, and technically broad |
     51 +| Regional usefulness | 6/10 | DVC is underrepresented and operationally important |
     52 +| Methodological novelty | 3/10 | The individual methods and most integrations already exist |
     53 +| Current physical validity | 2/10 | Storage calibration must be rebuilt |
     54 +| Current causal validity | 1/10 | The existing design does not identify operator effects |
     55 +| Reproducibility | 3/10 | Lockfile and outputs exist, but clean reproduction is impossible |
     56 +| Dashboard practicality | 2/10 | Retrospective demonstrator, not an operational monitor |
     57 +| Current high-index readiness | 1/10 | Submission now would risk rapid rejection |
     58 +| Salvage potential | 8/10 | Authoritative curves and a meaningful regional question are available |
     59 +
     60 +---
     61 +
     62 +## 2. Direct Answers
     63 +
     64 +### Do the work and title match?
     65 +
     66 +**No.** The current manuscript title is:
     67 +
     68 +> Satellite-Detectable Anthropogenic Fingerprints in Reservoir Storage
     69 +> Variability: Multi-Method Attribution Evidence from the Damodar Valley
     70 +> Corporation System Using Explainable AI
     71 +
     72 +The title overstates every load-bearing noun:
     73 +
     74 +| Title phrase | What the evidence currently supports |
     75 +|---|---|
     76 +| Satellite-detectable | Sentinel-1 detects surface-water extent at Maithon |
     77 +| Anthropogenic | Not established; the quantity is an unexplained model residual |
     78 +| Fingerprints | Exploratory post-hoc clusters without external operational labels |
     79 +| Reservoir storage | Potentially recoverable for Maithon after CWC recalibration |
     80 +| DVC system | Core model is Maithon-only; Panchet is invalid and Durgapur is heuristic |
     81 +| Multi-method evidence | Several methods reuse the same generated residual and are not independent |
     82 +| Attribution | No measured releases, gates, or complete water balance |
     83 +| Explainable AI | SHAP explains fitted model behavior, not management causes |
     84 +
     85 +### What is genuinely new?
     86 +
     87 +The defensible novelty is **regional and integrative**, not algorithmic:
     88 +
     89 +1. A potentially valuable multi-year Sentinel-1 water-area and storage record for
     90 +   Maithon in a data-sparse Indian reservoir system.
     91 +2. A reproducible open-data case study connecting reservoir-scale observations,
     92 +   hydroclimatic predictability, and basin-scale satellite observations.
     93 +3. A useful demonstration of the limits of inferring reservoir operations from
     94 +   climate-model residuals when operator records are unavailable.
     95 +4. A foundation for independent reservoir transparency, if the pipeline is made
     96 +   current, uncertainty-aware, and externally validated.
     97 +
     98 +The following are **not new by themselves**: Sentinel-1 water extraction, DEM or
     99 +hypsometric storage reconstruction, XGBoost, SHAP, HMM, Granger causality, CCM,
    100 +DTW clustering, or detection of reservoir storage in GRACE.
    101 +
    102 +### Can the work be completed in July and submitted in August 2026?
    103 +
    104 +**A sharply narrowed Maithon reconstruction paper can possibly be submitted in
    105 +late August, but the current integrated causal-attribution paper cannot be made
    106 +high-index ready by cosmetic revision.** The narrow route requires immediate
    107 +access to raw Sentinel-1 outputs and exact-date validation records. It remains an
    108 +aggressive schedule.
    109 +
    110 +### Can it be peer-reviewed and published by October or November 2026?
    111 +
    112 +**That outcome cannot be responsibly planned or promised.**
    113 +
    114 +- A corrected EarthArXiv preprint with a DOI by August or autumn is realistic.
    115 +- Being under review or in revision by November is realistic.
    116 +- Acceptance at a strong conventional journal by November is unlikely.
    117 +- MDPI Remote Sensing has a schedule where an October-November online outcome is
    118 +  possible after acceptance, but it charges CHF 2,700 and does not guarantee
    119 +  either acceptance or that the required scientific rebuild will finish on time.
    120 +
    121 +### Can this produce multiple papers?
    122 +
    123 +**The present dataset supports one paper after correction.** Splitting the same
    124 +48-month residual into separate XGBoost, CCM, HMM, GRACE, and DTW papers would be
    125 +salami slicing. Two or three follow-up papers are legitimate only after collecting
    126 +new data, expanding scale, and answering distinct questions.
    127 +
    128 +---
    129 +
    130 +## 3. The Research Meaning Worth Keeping
    131 +
    132 +The strongest meaningful question is not:
    133 +
    134 +> Can an AI residual prove that DVC operations contaminate GRACE?
    135 +
    136 +It is:
    137 +
    138 +> How accurately can open satellite observations reconstruct monthly storage
    139 +> dynamics in a data-sparse managed reservoir, and what can and cannot be inferred
    140 +> about hydroclimatic forcing and operation without complete operator records?
    141 +
    142 +This question has practical and scientific value because it:
    143 +
    144 +- produces a transparent storage-monitoring record where public observations are sparse;
    145 +- quantifies the uncertainty of satellite-only monitoring instead of hiding it;
    146 +- tests whether commonly used climate-only attribution logic is reliable in a regulated system;
    147 +- creates a reusable workflow for other Indian reservoirs after external validation;
    148 +- gives CWC, DVC, researchers, and disaster-management users an independent evidence layer.
    149 +
    150 +The project becomes more meaningful by being **honest about the boundary between
    151 +observation and attribution**. A carefully demonstrated limitation can be a
    152 +research result. An unsupported causal label cannot.
    153 +
    154 +---
    155 +
    156 +## 4. Recommended Titles and Claims
    157 +
    158 +### Recommended immediate rescue title
    159 +
    160 +> **Sentinel-1 reconstruction of Maithon Reservoir storage using an updated
    161 +> elevation-area-capacity curve: validation and uncertainty**
    162 +
    163 +This is the most defensible August-scope paper.
    164 +
    165 +### Broader title after a successful physical and statistical rebuild
    166 +
    167 +> **Satellite-derived storage dynamics and hydroclimatic predictability of
    168 +> Maithon Reservoir, eastern India**
    169 +
    170 +### Future causal title, only after operational data exist
    171 +
    172 +> **Separating hydroclimatic inflow and managed releases in a data-sparse Indian
    173 +> reservoir using Sentinel-1 and a satellite-constrained mass balance**
    174 +
    175 +### Terms to remove now
    176 +
    177 +- causally attributable
    178 +- causal independence
    179 +- anthropogenic residual
    180 +- systematic GRACE misattribution
    181 +- GRACE contamination
    182 +- operational taxonomy
    183 +- 100% classification accuracy
    184 +- DVC system validation
    185 +- climate explains X percent, when X is an NSE value
    186 +
    187 +### Safer replacements
    188 +
    189 +- unexplained storage anomaly
    190 +- association or cross-scale consistency
    191 +- exploratory operating-pattern clusters
    192 +- limited hydroclimatic predictability
    193 +- Maithon case study
    194 +- proof-of-concept monitoring workflow
    195 +
    196 +---
    197 +
    198 +## 5. What Survives and What Does Not
    199 +
    200 +| Claim | Current verdict | Required action |
    201 +|---|---|---|
    202 +| Sentinel-1 captures Maithon water-area seasonality | Potentially defensible | Validate exact scenes and classifier accuracy |
    203 +| A monthly Maithon storage series can be produced | Salvageable | Replace the DEM power law with the CWC 2019 curve |
    204 +| RMSE is 0.07 m | Overstated | Use independent dates, cluster repeated weekly observations, report all-point error |
    205 +| Climate-only model has limited predictive skill | Defensible after clean CV | Rebuild nested temporal validation |
    206 +| Residual equals operator influence | Unsupported | Call it unexplained or obtain a physical water balance and release data |
    207 +| Operations dominate 98% or 43% of variance | Unsupported | Do not interpret NSE as variance explained |
    208 +| Residual is causally independent of climate | Unsupported | Non-significance does not prove independence |
    209 +| Maithon causes Durgapur | Not established | Correct CCM direction and obtain physically valid Durgapur data |
    210 +| HMM states are real operating regimes | Unsupported | Validate states against releases, rules, or operator labels |
    211 +| DTW provides an operational taxonomy | Unsupported | Replace Ward, enlarge sample, test stability and external classification |
    212 +| GRACE beta matches theory within 10% | False | Correct units, area, spatial support, and leakage treatment |
    213 +| Maithon storage covaries with basin TWS | Plausible association | Test with correct units, masks, uncertainty, and placebos |
    214 +| Standard GRACE studies misattribute DVC changes | Unsupported generalization | Requires a multi-basin correction study |
    215 +| Dashboard provides current operational monitoring | False currently | Relabel as retrospective demo or implement actual ingestion and validation |
    216 +
    217 +---
    218 +
    219 +## 6. Submission-Blocking Scientific Findings
    220 +
    221 +### 6.1 The Maithon storage calibration uses the wrong physical geometry
    222 +
    223 +Repository constants use Maithon FSL 174.5 m, design-scale capacity around
    224 +1.36 BCM, and dead storage 0.185 BCM in src/fit_av_params.py and
    225 +src/01_storage_reconstruction.py.
    226 +
    227 +The authoritative Central Water Commission 2020 Sentinel-1 assessment reports:
    228 +
    229 +- full reservoir level: 150.88 m;
    230 +- maximum water level: 152.40 m;
    231 +- 2019 dead storage: 0.09490 BCM;
    232 +- 2019 live storage: 0.77898 BCM;
    233 +- 2019 gross storage: 0.87388 BCM;
    234 +- water-spread area at FRL: 85.95 km2;
    235 +- a complete 2019 elevation-area-capacity table from MDDL to FRL.
    236 +
    237 +The fitted Maithon exponent b = 3.0 is exactly at the optimizer upper bound.
    238 +The stored sensitivity output also indicates that a 10% exponent change can
    239 +invert the temporal pattern, contradicting the locked claim that +/-10% is stable.
    240 +
    241 +**Consequence:** the current storage anomaly, XGBoost target, residual, HMM, CCM,
    242 +GRACE regression, and clustering must be considered provisional until Stage 1 is
    243 +rebuilt.
    244 +
    245 +**Recovery:** interpolate the official CWC 2019 elevation-area-capacity table,
    246 +use the CWC current live/dead storage definitions, propagate table and classifier
    247 +uncertainty, and use ALOS only as a comparison or gap-filling sensitivity model.
    248 +
    249 +### 6.2 The GRACE coefficient is in the wrong units
    250 +
    251 +At src/05_grace_reconciliation.py:417-421 all predictors are z-standardized.
    252 +The coefficient 3.8424 is therefore **cm TWS per one standard deviation of the
    253 +residual**, not cm/BCM. It is directly labeled cm/BCM at
    254 +src/05_grace_reconciliation.py:438-465 and in the manuscript.
    255 +
    256 +Using the current lag-model residual standard deviation gives approximately:
    257 +
    258 +- correctly unstandardized beta: 42.35 cm/BCM;
    259 +- HAC 95% CI: 23.51 to 61.19 cm/BCM;
    260 +- code-area theoretical sensitivity for 19,600 km2: 5.10 cm/BCM;
    261 +- manuscript-area theoretical sensitivity for 23,370 km2: 4.28 cm/BCM.
    262 +
    263 +The claimed 3.84 versus 4.28 physical agreement is an accidental comparison
    264 +between incompatible quantities. The deseasonalized script also uses GRACE in
    265 +BCM while the manuscript labels its standardized coefficients as cm/BCM.
    266 +
    267 +**Consequence:** statistical association may remain, but the flagship physical
    268 +validation and "within 10%" statement collapse.
    269 +
    270 +### 6.3 The GRACE design cannot prove misattribution
    271 +
    272 +Maithon storage is physically part of basin TWS. A significant relationship
    273 +between reservoir storage and GRACE TWS is therefore expected and does not prove
    274 +operator causation or prior-study misattribution. The present code also:
    275 +
    276 +- averages a rectangular bounding box rather than a true basin polygon;
    277 +- uses two inconsistent basin areas;
    278 +- does not forward-model mascon leakage or gain factors;
    279 +- interpolates every missing GRACE month without retaining flags;
    280 +- controls only a limited subset of other TWS components;
    281 +- lacks neighboring-region and placebo-reservoir tests.
    282 +
    283 +The correct framing is cross-scale detectability or association, not contamination.
    284 +
    285 +### 6.4 XGBoost performance is not cleanly out of sample
    286 +
    287 +At src/03_xgboost_attribution.py:220-249, Optuna tunes on the last 25% of the
    288 +complete series. Those dates overlap the reported evaluation period. At
    289 +src/03_xgboost_attribution.py:303-309, every test fold is also used for early
    290 +stopping. Seasonal AET imputation uses all years before splitting.
    291 +
    292 +Additional issues:
    293 +
    294 +- SHAP values are computed on a final in-sample model;
    295 +- persistence beats XGBoost on all 48 pooled test rows;
    296 +- physically resolved fold performance is negative in two of four folds;
    297 +- NSE is negative within both filling and drawdown regimes;
    298 +- the function named pbias computes normalized MAE, not percent bias;
    299 +- fifty random model seeds are not a bootstrap or a 95% confidence interval.
    300 +
    301 +**Recovery:** use nested rolling-origin validation; perform imputation, feature
    302 +selection, hyperparameter tuning, and early stopping only inside each training
    303 +window; compare persistence, climatology, linear/GAM, and physical baselines; and
    304 +use blocked resampling plus observation Monte Carlo for uncertainty.
    305 +
    306 +### 6.5 A weak climate model does not identify an anthropogenic residual
    307 +
    308 +The residual identity is:
    309 +
    310 +observed storage - fitted model prediction =
    311 +operations + omitted climate + hydrologic error + observation error + model error.
    312 +
    313 +The repository already finds:
    314 +
    315 +- temperature correlation with the residual: r = -0.523, p = 0.00013;
    316 +- significant residual autocorrelation;
    317 +- near-zero no-lag NSE;
    318 +- negative regime-specific NSE;
    319 +- no measured release, gate, or complete inflow series.
    320 +
    321 +Low model skill makes the residual closer to the raw target; it does not make it
    322 +more anthropogenic. NSE is a prediction skill score relative to an observed mean,
    323 +not a general fraction of variance explained.
    324 +
    325 +### 6.6 CCM direction and significance are implemented incorrectly
    326 +
    327 +The code embeds the variable named cause and predicts effect, then interprets
    328 +that mapping as cause-to-effect. CCM logic is the reverse: if X drives Y,
    329 +information about X should be recoverable from Y's manifold. PyEDM returns both
    330 +directions, but the code reads only the first.
    331 +
    332 +The code also selects the maximum rho across library sizes and compares it with a
    333 +surrogate null calculated only at the largest library size. This is a mismatched
    334 +selection test. Non-significant tests are then treated as proof of independence,
    335 +which is invalid, especially at low power.
    336 +
    337 +**Recovery:** define causal direction explicitly, report both returned mappings,
    338 +align all series by timestamps, build a matched null at every library size,
    339 +simulate power and false-positive behavior at the observed sample size, and use
    340 +operator-grounded evidence before making a causal claim.
    341 +
    342 +### 6.7 The DTW taxonomy is mathematically and empirically weak
    343 +
    344 +At src/06_fingerprint_taxonomy.py:166-177, Ward linkage is applied to a
    345 +precomputed DTW matrix. SciPy explicitly states that Ward is correctly defined
    346 +only for Euclidean pairwise distances. DTW is generally not Euclidean.
    347 +
    348 +The analysis has only 14 annual cycles from two structures, searches K on the
    349 +same data used to score it, contains singleton clusters, has no bootstrap
    350 +stability, uses post-hoc archetype names, and compares Maithon with a hand-scaled
    351 +and capped Durgapur storage proxy. The executable selects K = 5 while the paper
    352 +manually reports K = 3.
    353 +
    354 +**Recovery:** remove taxonomy from the immediate paper. A future taxonomy needs
    355 +many reservoirs, external operating labels, shape and amplitude normalization,
    356 +DTW k-medoids or average/complete linkage, cluster stability, and held-out
    357 +classification.
    358 +
    359 +### 6.8 Validation contains pseudoreplication
    360 +
    361 +Seven weekly CWC points in November-December are compared with only two repeated
    362 +monthly satellite estimates. They are not seven independent satellite
    363 +predictions. The headline 0.07 m RMSE also excludes the largest error after the
    364 +fact; the all-nine-points RMSE is 0.23 m.
    365 +
    366 +Validation covers a narrow water-level and seasonal range. Stage 7 does not
    367 +reproduce the manuscript's level-validation table and refers to a nonexistent
    368 +storage column.
    369 +
    370 +**Recovery:** validate exact Sentinel-1 acquisition dates, use distinct dates
    371 +across monsoon and dry seasons, report scene segmentation accuracy, cluster
    372 +uncertainty by month, and hold out part of the elevation range or years.
    373 +
    374 +### 6.9 Durgapur and Panchet cannot support system-level claims
    375 +
    376 +- Panchet is explicitly invalid because of bounding-box contamination.
    377 +- Durgapur storage uses a hand-selected linear coefficient and a hard cap after
    378 +  the physical power-law model failed.
    379 +- The code states Durgapur is valid for direction only, yet it is used in CCM,
    380 +  HMM interpretation, and amplitude-sensitive clustering.
    381 +
    382 +Until both structures have valid geometry and independent observations, the
    383 +quantitative paper should be Maithon-focused.
    384 +
    385 +### 6.10 Citation and method integrity need a complete audit
    386 +
    387 +- The Ji2023 DOI in the bibliography belongs to an unrelated isotope paper.
    388 +- A central Besseling2021 reference appears unverifiable.
    389 +- The manuscript says a refined-Lee filter is used per scene, while the GEE
    390 +  script says the filter was removed and Otsu is applied to a monthly composite.
    391 +- National-policy and "first study" claims lack adequate sources.
    392 +
    393 +Every DOI, dataset version, factual number, and method description must be checked
    394 +against a primary source and executable code before preprinting.
    395 +
    396 +---
    397 +
    398 +## 7. Repository, Formatting, and Reproducibility Audit
    399 +
    400 +### Strengths
    401 +
    402 +- Clear top-level separation of source, GEE, figures, reports, journal, and app.
    403 +- A locked uv environment and Python 3.11 marker.
    404 +- Processed outputs and most publication figures are versioned.
    405 +- All Python source files pass syntax compilation.
    406 +- Time-series CV was attempted instead of random K-fold.
    407 +- The research journal records negative results and known limitations unusually well.
    408 +- Figures have a coherent publication-oriented visual style.
    409 +- The thesis and manuscript are substantially drafted rather than aspirational.
    410 +
    411 +### Blocking gaps
    412 +
    413 +| Gap | Evidence or effect |
    414 +|---|---|
    415 +| Missing raw inputs | data/raw does not exist in the working tree |
    416 +| Broken README command | README runs zero-byte src/03_xgboost_shap.py instead of src/03_xgboost_attribution.py |
    417 +| No automated tests | No tests directory, CI, or regression fixtures |
    418 +| No workflow DAG | No DVC, Snakemake, Make, or equivalent one-command pipeline |
    419 +| No raw manifest | Missing URLs, acquisition versions, checksums, and licenses |
    420 +| No formal license | README text is not a LICENSE file |
    421 +| Placeholder package metadata | pyproject.toml still says "Add your description here" |
    422 +| Unsafe checks | critical_checks.py overwrites a valid result with MISSING rows when raw files are absent and prints CLEAR |
    423 +| Manual parameter copying | fit_av_params.py requires values to be copied into another script |
    424 +| External requirements unclear | Java is needed for tabula; NASA and GEE credentials are not fully automated |
    425 +| Results registry conflicts | Append-only findings preserve superseded and contradictory claims |
    426 +| Clean LaTeX build unavailable | Local compilation lacks elsarticle.cls; figure paths are also suspect |
    427 +
    428 +### Manuscript and figure formatting issues
    429 +
    430 +- PDF metadata still says "Causally Attributable" while the visible title differs.
    431 +- The abstract and highlights need target-journal length checks.
    432 +- The K = 5 taxonomy figure does not match the K = 3 manuscript claim.
    433 +- The GRACE figure contains a blank residual panel and invalid coefficient units.
    434 +- The CCM figure is labeled as convergence evidence but primarily presents endpoint bars.
    435 +- The study map appears to use a bounding rectangle while the caption describes a basin boundary.
    436 +- Supplementary figures exist without a complete, separately packaged supplement.
    437 +- Figure paths from reports/manuscript do not clearly reach the repository figures directory.
    438 +- Method citations exist in the bibliography but are inconsistently cited in text.
    439 +
    440 +### Minimum reproducibility standard before submission
    441 +
    442 +1. Add LICENSE, CITATION.cff, a data dictionary, and a source manifest.
    443 +2. Archive legally redistributable raw inputs; for restricted inputs, archive
    444 +   retrieval scripts, exact IDs, dates, hashes, and expected checksums.
    445 +3. Replace scattered constants with versioned YAML or TOML configuration.
    446 +4. Build a one-command workflow with explicit dependencies and immutable outputs.
    447 +5. Add tests for units, date alignment, gap filling, area-volume conversion,
    448 +   CV leakage, coefficient back-transformation, and figure/table numbers.
    449 +6. Add CI that reproduces a small fixture dataset without network access.
    450 +7. Make diagnostic scripts read-only by default and fail closed on missing inputs.
    451 +8. Create a tagged release and Zenodo DOI only after the results are frozen.
    452 +
    453 +---
    454 +
    455 +## 8. Practicality of ReservoirWatch
    456 +
    457 +ReservoirWatch is currently a **retrospective visualization demo**, not an
    458 +operational monitoring system:
    459 +
    460 +- its latest state is December 2024;
    461 +- the sidebar advertises 2002-2026 coverage and automatic monthly updates;
    462 +- no scheduler or live ingestion path exists;
    463 +- "confidence" is a fixed rule constant between 0.70 and 0.82, not calibrated probability;
    464 +- Panchet results are displayed despite known invalid data;
    465 +- the map draws a fixed 2.5 km circle rather than measured water extent;
    466 +- Maithon model metrics are shown regardless of selected reservoir.
    467 +
    468 +### What would make it practically meaningful
    469 +
    470 +1. Relabel the current version "research demonstrator" immediately.
    471 +2. Disable invalid reservoirs and show data-quality status prominently.
    472 +3. Add scheduled Sentinel-1 ingestion and a visible last-successful-update timestamp.
    473 +4. Publish observed polygons, not symbolic circles.
    474 +5. Show uncertainty intervals and validation coverage, not invented confidence.
    475 +6. Separate observation, model inference, and operator-confirmed status.
    476 +7. Add alerts only after prospective validation against DVC/CWC data.
    477 +8. Conduct a user study with DVC, irrigation, or flood-management personnel.
    478 +
    479 +The dashboard can become an impact artifact, but it should not be used as evidence
    480 +that the scientific model is operational.
    481 +
    482 +---
    483 +
    484 +## 9. Literature and Novelty Position
    485 +
    486 +The problem is important, but the current manuscript understates existing work.
    487 +Examples already in the literature include:
    488 +
    489 +- detection of reservoir-operation effects in GRACE in the Yellow River;
    490 +- storage and climate/management analysis for thousands of reservoirs;
    491 +- global reservoir storage records for more than 7,000 reservoirs;
    492 +- global or continental surface-water dynamics and human/climate attribution;
    493 +- leakage-aware lake and reservoir correction in GRACE;
    494 +- Sentinel-1 plus altimetry/hypsometry storage reconstruction for hundreds of reservoirs;
    495 +- explainable ML in the Panchet reservoir-regulated catchment;
    496 +- CCM for hydrologic connectivity, with explicit cautions on seasonality and interpretation.
    497 +
    498 +Therefore the paper should not claim a globally first method. The defensible gap is:
    499 +
    500 +> A rigorously validated, open, multi-year storage record and inference audit for
    501 +> an operationally important but under-studied Indian reservoir.
    502 +
    503 +That regional gap is sufficient for a respectable applied paper if the validation
    504 +and uncertainty are excellent.
    505 +
    506 +---
    507 +
    508 +## 10. Recovery Strategy
    509 +
    510 +### Route A: August rescue paper
    511 +
    512 +**Question:** Can Sentinel-1 plus the CWC 2019 elevation-area-capacity curve
    513 +reconstruct Maithon storage accurately across seasons?
    514 +
    515 +**Keep:** Sentinel-1 processing, Maithon, authoritative CWC curve, exact-date
    516 +validation, uncertainty, open workflow.
    517 +
    518 +**Remove from main paper:** causal attribution, HMM, CCM, DTW taxonomy, Durgapur
    519 +storage, Panchet, and strong GRACE claims. A limited GRACE comparison may be a
    520 +supplement only if units and spatial treatment are corrected.
    521 +
    522 +**Likely contribution:** a validated regional data/method application.
    523 +
    524 +**Schedule risk:** high but possible for late August if raw inputs and CWC records
    525 +are available immediately.
    526 +
    527 +### Route B: Stronger attribution paper
    528 +
    529 +**Question:** How much of monthly storage change is explained by inflow,
    530 +precipitation, evaporation, and measured managed release?
    531 +
    532 +**Required new evidence:**
    533 +
    534 +- CWC/DVC water levels or storage across the full operating range;
    535 +- measured or defensibly reconstructed inflow;
    536 +- gate release, outflow, hydropower, or rule-curve records;
    537 +- lake precipitation and evaporation;
    538 +- physical mass-balance closure;
    539 +- multiple reservoirs or held-out operating events;
    540 +- prospective or quasi-experimental validation.
    541 +
    542 +**Schedule:** research through late 2026, journal submission in late 2026 or
    543 +early 2027, realistic acceptance during 2027.
    544 +
    545 +### Recommended decision
    546 +
    547 +If the goal is the **best paper possible**, choose Route B and stop optimizing for
    548 +an October-November acceptance date. If an **August submission is non-negotiable**,
    549 +choose Route A and publish one narrow, honest Maithon paper.
    550 +
    551 +Do not try to preserve every method in one manuscript. Method count is not rigor.
    552 +
    553 +---
    554 +
    555 +## 11. July-November 2026 Plan
    556 +
    557 +### Narrow August route
    558 +
    559 +| Date | Deliverable | Go/no-go test |
    560 +|---|---|---|
    561 +| 11-14 Jul | Freeze Maithon question, title, target, authorship, and source hierarchy | Supervisor signs off on narrowed claim |
    562 +| 15-21 Jul | Rebuild storage from CWC 2019 table; reprocess exact Sentinel-1 acquisitions | Units and known CWC points reproduce |
    563 +| 22-27 Jul | Independent multi-season validation and observation uncertainty | At least 12-24 distinct dates across range; no pseudoreplication |
    564 +| 28 Jul-3 Aug | Clean temporal baselines and sensitivity analysis | No test leakage; conclusions stable to plausible uncertainty |
    565 +| 4-10 Aug | Rewrite manuscript, figures, supplement, references, and repository | One-command clean rerun succeeds |
    566 +| 11-17 Aug | Supervisor plus independent hydrology/statistics review | All blocking findings closed in writing |
    567 +| 18-25 Aug | Corrected EarthArXiv preprint and Zenodo code/data release | Frozen DOI version matches manuscript |
    568 +| 25-31 Aug | Submit to selected journal | No causal or system-level overclaim remains |
    569 +
    570 +If distinct validation data are not available by 21 July, do not force an August
    571 +journal submission.
    572 +
    573 +### Stronger impact route
    574 +
    575 +| Month | Deliverable |
    576 +|---|---|
    577 +| July | Correct storage physics and reconstruct Maithon |
    578 +| August | Obtain operational records and build a reservoir water balance |
    579 +| September | Multi-event or multi-reservoir validation; nested modelling and uncertainty |
    580 +| October | Independent review, manuscript rewrite, reproducible release, preprint |
    581 +| November | Submit to a strong scope-matched journal or finish requested additional validation |
    582 +| 2027 | Peer review, major revision, and realistic acceptance window |
    583 +
    584 +### Realistic November status
    585 +
    586 +The responsible target is:
    587 +
    588 +> Corrected preprint published with DOI, reproducible archive released, and
    589 +> journal manuscript under review or in revision.
    590 +
    591 +That is a strong outcome. It should not be described as peer-reviewed publication
    592 +until a journal accepts it.
    593 +
    594 +---
    595 +
    596 +## 12. Venue Strategy
    597 +
    598 +"High indexed" should mean current coverage in Scopus and preferably Web of
    599 +Science SCIE, verified by exact journal title and ISSN on submission day. Impact
    600 +factor, quartile, scope, fees, and review speed are separate properties.
    601 +
    602 +The following publisher metrics were current on 11 July 2026:
    603 +
    604 +| Venue | Current official facts | Honest fit after rebuild |
    605 +|---|---|---|
    606 +| Remote Sensing of Environment | SCIE and Scopus; IF 11.4; 192-day median to acceptance; free subscription route | Very high reach; broad remote-sensing advance is currently
         missing |
    607 +| Journal of Hydrology | SCIE and Scopus; IF 6.3; 159-day median to acceptance; free subscription route | One defensible reach after strong physical validation |
    608 +| Water Resources Management | SCIE and Scopus; IF 5.7; 23-day median first decision; hybrid | Good if operational management and decision relevance are demonstrated |
    609 +| Remote Sensing | Publisher-listed JCR Q1; IF 4.3; roughly 49-52-day median publication time; CHF 2,700 APC | Schedule-plausible only with confirmed funding; acceptance not g
         uaranteed |
    610 +| Journal of the Indian Society of Remote Sensing | SCIE and Scopus; IF 2.1; 20-day median first decision; hybrid | Strong legitimate regional fallback for the narrow Sentinel
         -1 paper |
    611 +
    612 +### Recommended ladder
    613 +
    614 +For the narrow reconstruction paper:
    615 +
    616 +1. Journal of Hydrology only after an external hydrologist says the contribution
    617 +   generalizes beyond Maithon.
    618 +2. Otherwise start with Journal of the Indian Society of Remote Sensing.
    619 +3. Consider Remote Sensing only if APC funding is confirmed before submission
    620 +   and the supervisor accepts the cost and venue.
    621 +
    622 +For the stronger mass-balance attribution paper:
    623 +
    624 +1. Journal of Hydrology.
    625 +2. Water Resources Management.
    626 +3. Journal of the Indian Society of Remote Sensing as a regional fallback.
    627 +
    628 +Remote Sensing of Environment should not be the primary target without
    629 +multi-reservoir generalization or a real advance in remote-sensing methodology.
    630 +
    631 +Never submit simultaneously. Never use a broker, guaranteed-acceptance service,
    632 +WhatsApp publication offer, or a journal verified only by its own marketing.
    633 +
    634 +---
    635 +
    636 +## 13. Legitimate Multiple-Paper Program
    637 +
    638 +### Paper 1: 2026 regional reconstruction
    639 +
    640 +**Working title:** Sentinel-1 reconstruction of Maithon Reservoir storage using
    641 +an updated elevation-area-capacity curve: validation and uncertainty.
    642 +
    643 +**New unit of evidence:** exact-date SAR extent, official curve, independent
    644 +validation, uncertainty, and an open monthly storage record.
    645 +
    646 +### Paper 2: 2027 national GRACE correction
    647 +
    648 +**Working title:** Do reservoir operations bias GRACE groundwater estimates?
    649 +A leakage-aware correction across India's managed basins.
    650 +
    651 +**New unit of evidence:** many reservoirs and basins, forward modelling into
    652 +GRACE observation space, multiple mascon products, wells, neighboring-basin
    653 +placebos, and corrected groundwater trends.
    654 +
    655 +### Paper 3: 2027 or later operating-regime benchmark
    656 +
    657 +**Working title:** Learning reservoir operating regimes from space: a
    658 +multi-reservoir benchmark with out-of-basin validation.
    659 +
    660 +**New unit of evidence:** dozens or hundreds of reservoirs, external operator
    661 +labels, valid geometry, stable clustering, and held-out classification.
    662 +
    663 +### Optional data/software paper
    664 +
    665 +This is justified only if the project releases a substantial, validated,
    666 +versioned dataset or a reusable tested package. Publishing the current repository
    667 +alone is not enough.
    668 +
    669 +---
    670 +
    671 +## 14. Non-Negotiable Go/No-Go Gates
    672 +
    673 +Do not preprint or submit until all applicable gates pass:
    674 +
    675 +1. **Physical gate:** CWC geometry and units reproduce known Maithon values.
    676 +2. **Validation gate:** distinct exact-date observations cover multiple seasons
    677 +   and a useful elevation range.
    678 +3. **Leakage gate:** all preprocessing, tuning, and early stopping are inside
    679 +   training folds.
    680 +4. **Baseline gate:** results are compared against persistence, climatology, and
    681 +   simpler physical/statistical models.
    682 +5. **Uncertainty gate:** observation and model uncertainty are propagated; random
    683 +   seeds are not called a bootstrap.
    684 +6. **Claim gate:** no causal or anthropogenic term appears without an identified
    685 +   estimand and operational ground truth.
    686 +7. **GRACE gate:** coefficients are in raw units; basin masks, area, leakage, gaps,
    687 +   and placebos are documented.
    688 +8. **Reproducibility gate:** a clean clone can reproduce tables and figures from
    689 +   archived inputs or verified retrieval scripts.
    690 +9. **Citation gate:** every DOI resolves to the cited work and every "first" claim
    691 +   is supported by a documented search.
    692 +10. **Supervisor gate:** Dr. Ray approves authorship, data release, final claims,
    693 +    target venue, and AI-use disclosure.
    694 +
    695 +---
    696 +
    697 +## 15. Priority Checklist
    698 +
    699 +### Stop now
    700 +
    701 +- Do not upload the current manuscript as a preprint.
    702 +- Do not submit the current title or abstract.
    703 +- Do not market ReservoirWatch as live operational decision support.
    704 +- Do not use Panchet or Durgapur storage in quantitative system claims.
    705 +- Do not split the existing analyses into multiple papers.
    706 +
    707 +### Do first
    708 +
    709 +1. Replace Maithon storage geometry with the CWC 2019 table.
    710 +2. Restore and archive the raw data with provenance.
    711 +3. Reprocess exact Sentinel-1 scenes and validate water masks.
    712 +4. Obtain distinct CWC/DVC/WRIS/GROWL validation records.
    713 +5. Choose the narrow reconstruction route or the stronger mass-balance route.
    714 +6. Rewrite the title, estimand, and contribution statement before rerunning ML.
    715 +
    716 +### Do after the scientific base is correct
    717 +
    718 +1. Rebuild temporal validation without leakage.
    719 +2. Correct or remove CCM, HMM, DTW, and GRACE sections.
    720 +3. Repair the workflow, tests, metadata, license, and data release.
    721 +4. Rewrite the manuscript from the new results, not by patching old numbers.
    722 +5. Obtain an independent reviewer before public release.
    723 +
    724 +---
    725 +
    726 +## 16. Key Sources
    727 +
    728 +### Project-specific physical reference
    729 +
    730 +- [CWC, Sedimentation Assessment of Maithon Reservoir through Satellite Remote
    731 +  Sensing, 2020](https://cwc.gov.in/sites/default/files/sedimentation-assessment-maithon-reservoir-jharkhand-through-remote-sensing-may-2020.pdf)
    732 +
    733 +### Related work and novelty
    734 +
    735 +- [Hou et al. 2022, satellite reservoir storage and climate/management influence
    736 +  for 6,695 reservoirs](https://doi.org/10.5194/hess-26-3785-2022)
    737 +- [Zhao et al. 2023, global reservoir storage records for 7,245
    738 +  reservoirs](https://www.nature.com/articles/s41467-023-38843-5)
    739 +- [Cooley et al. 2021, human alteration of global surface-water
    740 +  storage](https://www.nature.com/articles/s41586-021-03262-3)
    741 +- [Yao et al. 2025, climate, hydrology, and management attribution across
    742 +  105,400 water bodies](https://www.nature.com/articles/s44221-024-00367-7)
    743 +- [Xie et al. 2022, reservoir-operation effects detected by
    744 +  GRACE](https://doi.org/10.1016/j.jhydrol.2022.127924)
    745 +- [Chen et al. 2024, monthly storage for hundreds of reservoirs from multisource
    746 +  remote sensing](https://doi.org/10.1029/2023WR036450)
    747 +- [RECOG, leakage-aware global lake and reservoir correction for
    748 +  GRACE](https://doi.org/10.5194/essd-13-2227-2021)
    749 +- [Bonotto et al. 2022, CCM in hydrology and interpretation
    750 +  cautions](https://doi.org/10.1029/2021WR030231)
    751 +- [GROWL 2026 observed lake and reservoir time-series
    752 +  benchmark](https://doi.org/10.1038/s41597-026-07091-9)
    753 +
    754 +### Method references
    755 +
    756 +- [Official pyEDM CCM documentation](https://sugiharalab.github.io/EDM_Documentation/ccm_/)
    757 +- [SciPy linkage documentation: Ward requires Euclidean
    758 +  distances](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html)
    759 +
    760 +### Current publication information
    761 +
    762 +- [Journal of Hydrology official insights](https://www.sciencedirect.com/journal/journal-of-hydrology/about/insights)
    763 +- [Remote Sensing of Environment official insights](https://www.sciencedirect.com/journal/remote-sensing-of-environment/about/insights)
    764 +- [Water Resources Management official page](https://link.springer.com/journal/11269)
    765 +- [Remote Sensing official page](https://www.mdpi.com/journal/remotesensing)
    766 +- [Remote Sensing official APC page](https://www.mdpi.com/journal/remotesensing/apc)
    767 +- [Journal of the Indian Society of Remote Sensing official
    768 +  page](https://link.springer.com/journal/12524)
    769 +- [EarthArXiv: DOI-bearing preprints are not peer
    770 +  review](https://eartharxiv.org/repository/about/)
    771 +- [Zenodo DOI and versioning guidance](https://help.zenodo.org/docs/deposit/about-records/)
    772 +- [Think.Check.Submit journal checklist](https://thinkchecksubmit.org/)
    773 +
    774 +---
    775 +
    776 +## Final Recommendation
    777 +
    778 +Do not discard this project. **Discard the unsupported interpretation.**
    779 +
    780 +The project can become a respectable publication by rebuilding Maithon storage
    781 +from the authoritative CWC curve, validating it properly, and asking a narrower
    782 +question that the data can answer. That is the credible August route.
    783 +
    784 +If the ambition is genuinely high impact, collect operational ground truth,
    785 +construct a physical mass balance, expand beyond one reservoir, and target a 2027
    786 +acceptance. The strongest paper is not the one with the most methods or the
    787 +fastest calendar. It is the one whose central claim survives hostile arithmetic,
    788 +physical checks, independent validation, and clean reproduction.
