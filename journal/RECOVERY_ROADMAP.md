# RECOVERY ROADMAP — Route B: The Best Paper (2027)
## Codex review analysis · master defect registry · phased rebuild plan · code & data release plan
### Prepared 2026-07-11 (Session 015) | Status: AWAITING REVIEW by Nishi + Dr. Ray — no code has been changed

> **Decision context:** Nishi has chosen **Route B** — skip the narrow August rescue paper
> and build the strongest possible mass-balance attribution paper, targeting realistic 2027
> acceptance. This document is the plan for that. Nothing executes until this roadmap is
> reviewed and approved.
>
> **Supersession notice:** this roadmap supersedes the August-submission timeline in
> `PROJECT_PROSPECT.md` §4–6 and the "fix E1–E4 then submit" recommendation. Still valid
> from earlier documents: the novelty/citation audit and portfolio logic in
> `NOVELTY_IMPACT_REVIEW.md` §2/§5, the venue cost research, the conference plan
> (EGU waiver deadline Dec 1), and the title-honesty principles.

---

## 1. CODEX REVIEW ANALYSIS — verified, claim by claim

The Codex review (`journal/codex_review.md`) made four submission-blocking technical claims.
I verified each directly against the code and data on 2026-07-11. **All four are confirmed.**

### 1.1 The four blockers — CONFIRMED

| # | Codex claim | My verification | Verdict |
|---|---|---|---|
| B1 | **Maithon geometry is wrong** (§6.1) | `src/fit_av_params.py:39` `FSL['maithon'] = 174.5` m and `:46` capacity 1.360 BCM, dead 0.185 BCM (`src/01_storage_reconstruction.py:56`). Official CWC 2020 sedimentation report: FRL = **150.88 m**, 2019 dead = **0.0949 BCM**, 2019 gross = **0.8739 BCM**, full 2019 E-A-C table published. The fit uses "elevation ≤ FSL+5m" = 179.5 m — terrain far above the actual dam crest — and the fitted exponent **b = 3.000 sits exactly at the optimizer upper bound** (`:107` `bounds=([1e-6,0.5],[10.0,3.0])`), a classic sign of a degenerate fit. Note the repo's own F-016/F-021 recorded elevation-datum confusion (155.5 m, 146.3 m, 174.5 m in different places) without resolving it. | **CONFIRMED — BLOCKER** |
| B2 | **GRACE β₂ is per-SD, not per-BCM** (§6.2) | `src/05_grace_reconciliation.py:418-419`: `X_std = (X_raw − mean)/std` before OLS. So β₂ = 3.8424 is **cm TWS per 1 SD of dS_anthro**. SD(dS_anthro) = 0.0917 BCM (computed from `delta_S_anthro.csv`) → true coefficient = 3.8424/0.0917 ≈ **41.9 cm/BCM** vs theoretical 4.28–5.10 cm/BCM. The celebrated "within 10% of theory" match was an accidental comparison of incompatible quantities. Cross-check: the deseasonalized CSV's β₂ = 0.7531 = 3.8424 × 0.196 exactly — both regressions are standardized; my Session-013 E1 finding (units mislabel) was correct but too shallow. | **CONFIRMED — BLOCKER.** The statistical *association* (p<0.001) survives; the physical-consistency validation does not. A true coefficient ~8–10× the mass-only sensitivity means β₂ captures reservoir-correlated basin-wide water variations (soil moisture, groundwater, irrigation), not reservoir mass per se |
| B3 | **XGBoost CV leaks test information** (§6.4) | `src/03_xgboost_attribution.py:221-249`: Optuna objective trains on first 75% and evaluates on the **last 25% of the full series** — dates that overlap the expanding-window CV test folds (2019–2023). Lines 303-309: every CV fold fits with `eval_set=[(X_test, y_test)]` and `early_stopping_rounds=20` — **the test fold steers training in every fold**. Also confirmed: seasonal AET imputation happens before splitting; SHAP is computed on an in-sample final model; the `pbias` function computes normalized MAE, not percent bias. | **CONFIRMED — BLOCKER.** All reported NSE/KGE values are optimistically biased by an unknown amount; given persistence already beats XGBoost on pooled rows (F-024), de-leaked skill may be lower still |
| B4 | **CCM direction inverted; Ward invalid on DTW** (§6.6–6.7) | `src/04_causal_inference.py:525-531`: calls `pyEDM.CCM(columns='cause', target='effect')` and reads only `out['cause:effect']`. In pyEDM/Sugihara convention, skill of "X xmap Y" is evidence that **Y drives X** — the code interprets the mapping backwards and discards the other direction that pyEDM returns. Additionally the significance test compares max-ρ-across-library-sizes against a surrogate null computed only at the largest library size (selection/test mismatch, `:544-553`). `src/06_fingerprint_taxonomy.py:176-177`: `linkage(dist_condensed, method='ward')` on a DTW matrix — SciPy documents Ward as correctly defined only for Euclidean distances. | **CONFIRMED — BLOCKER** for the CCM findings (F-015's Maithon→Durgapur direction claim is unreliable as coded) and **MAJOR** for the taxonomy (F-011/F-012 silhouettes need re-derivation with a valid linkage) |

### 1.2 The rest of the Codex findings — assessed

| Codex item | Assessment |
|---|---|
| §6.5 Weak climate model ≠ anthropogenic residual | **Valid and fundamental.** The residual identity (operations + omitted climate + errors) plus T_C r=−0.52 (F-025) means "anthropogenic" was never earned. Route B's operational data is the only real fix — this is exactly why Route B was chosen |
| §6.8 Validation pseudoreplication | **Valid.** The 9 F-020 points include 7 weekly CWC readings compared against only 2 distinct monthly satellite values (147.75 m ×4, 147.55 m ×4) — not 9 independent predictions. The 0.07 m headline also post-hoc excludes the largest error. **Nuance to keep:** as a *pilot* consistency check the result is still encouraging; it is the framing as formal validation that fails. Route B Phase 1 replaces it with exact-date, multi-season validation |
| §6.9 Durgapur/Panchet cannot support system claims | **Valid.** Durgapur uses a hand-picked linear coefficient + hard cap (`src/01:58`, "valid for direction only") yet feeds CCM/HMM/DTW quantitatively; Panchet is known-invalid (F-003). System-level claims need both rebuilt |
| §6.10 Citation integrity (Ji2023 DOI wrong; Besseling2021 unverifiable; refined-Lee text contradicts GEE script) | **Accepted for the Phase-4 citation audit** — merges with the 10 mandatory citation additions from NOVELTY_IMPACT_REVIEW.md §2 |
| §7 Reproducibility gaps (no LICENSE/tests/DAG/manifest; broken README command; `critical_checks.py` fails open; placeholder pyproject) | **Valid, all spot-checked.** `src/03_xgboost_shap.py` is 0 bytes and is the command README advertises. Absorbed into the release plan (Section 4) |
| §8 ReservoirWatch is a retrospective demo mislabeled as operational | **Valid.** Relabel + disable Panchet is a Phase-0 item; the operational upgrade is post-paper work |
| §9 Literature position | Consistent with NOVELTY_IMPACT_REVIEW.md, and adds important closest-prior citations we missed: **Xie et al. 2022** (reservoir operations in GRACE, Yellow River — directly threatens claim (e)), **Zhao et al. 2023** (7,245-reservoir global storage), **Cooley et al. 2021**, **Yao et al. 2025**, **RECOG** (leakage-aware GRACE lake/reservoir correction), **Chen et al. 2024**, **GROWL 2026**. All go into the mandatory-citation list |
| §12–13 Venue strategy & multi-paper program | Broadly consistent with our portfolio doc; Codex adds **Water Resources Management** (IF 5.7, 23-day first decision, hybrid = free subscription route) as venue #2 for the Route-B paper — adopted |

**Bottom line of the analysis:** the Codex review is correct on every load-bearing point.
Its two most consequential sentences are: *"Low model skill makes the residual closer to
the raw target; it does not make it more anthropogenic"* and *"Method count is not rigor."*
Route B is the answer to both.

---

## 2. MASTER DEFECT REGISTRY

Merged from Codex §6–§8, my Session-013 E1–E4, and the reviewer-attack list.
Phases refer to Section 3.

| ID | Defect | Severity | Fix spec | File(s) | Phase |
|---|---|---|---|---|---|
| D1 | Maithon geometry: FSL 174.5 m, dead 0.185, power-law AV with b at bound | **BLOCKER** | Digitize CWC 2019 E-A-C table; replace power law with monotone interpolation (PCHIP) of the official curve; use CWC live/dead definitions; keep ALOS curve only as sensitivity comparison; propagate table + classifier uncertainty | `src/fit_av_params.py`, `src/01_storage_reconstruction.py` | 0 |
| D2 | GRACE β in per-SD units labeled cm/BCM (incl. E1/E2 unit & basin-area errors) | **BLOCKER** | Refit in raw units; report raw + standardized side by side; single basin area from a true basin polygon (HydroBASINS Lv8 — already in the data registry) not a bounding box; retain gap flags instead of blanket interpolation; add neighboring-region + placebo-reservoir tests; reframe C3 as cross-scale association | `src/05_grace_reconciliation.py`, `src/analysis_grace_deseasonalized.py` | 0 (units) + 3 (design) |
| D3 | CV leakage: Optuna on overlapping window; early stopping on test folds; pre-split imputation; in-sample SHAP | **BLOCKER** | Nested rolling-origin CV: imputation, feature selection, tuning, early stopping strictly inside each training window (early-stop on tail of train); SHAP from per-fold out-of-sample models; report leakage-free metrics vs persistence/climatology/linear/GAM baselines | `src/03_xgboost_attribution.py` | 0 (de-leak) + 3 (full rebuild) |
| D4 | CCM direction inverted; max-ρ vs single-library-size null; ns treated as proven independence | **BLOCKER** | Report both pyEDM directions with explicit convention comment; matched null per library size; power simulation at n=48; independence claims removed — replaced by "no detectable coupling at this power" | `src/04_causal_inference.py` | 0 (direction) + 3 (redesign) |
| D5 | "Anthropogenic residual" unidentified (no operational records; T_C r=−0.52) | **BLOCKER** | Route B core: acquire release/level/hydropower records; physical mass balance; estimand defined before modeling. Until then the quantity is "unexplained storage anomaly" | design-level | 1–3 |
| D6 | Ward linkage on DTW matrix | MAJOR | k-medoids (PAM) or average/complete linkage on DTW; bootstrap cluster stability; drop "taxonomy" from the Route-B paper (revisit at multi-reservoir scale per portfolio paper 3) | `src/06_fingerprint_taxonomy.py` | 3 (or drop) |
| D7 | Validation pseudoreplication; single-season band; Stage-7 script doesn't reproduce the table | MAJOR | Exact-date S1 scene validation, 12–24 distinct dates across monsoon+dry seasons and elevation range; cluster repeated weekly obs; report all-point error; fix `src/07_cwc_validation.py` column bug | `src/07_cwc_validation.py`, GEE scripts | 1 |
| D8 | Durgapur hand-scaled proxy used quantitatively; Panchet invalid | MAJOR | Panchet GEE re-run (bbox already corrected in script); Durgapur restricted to direction-only statements unless a defensible barrage geometry is obtained | GEE scripts, `src/01` | 2 |
| D9 | E3: abstract mean −0.029 stale (true −0.014, inside CI); E4 untraceables (β₁ p, "OLS SE 1.22", Ljung-Box lags) | MAJOR | Fixed automatically by the Phase-4 rewrite-from-new-results rule: **no old number survives by inheritance** | manuscript | 4 |
| D10 | `pbias()` computes normalized MAE | MAJOR | Implement true PBIAS; audit every metric function against its definition; unit tests | `src/03` | 0 |
| D11 | Citation integrity: Ji2023 DOI wrong; Besseling2021 unverifiable; refined-Lee text vs GEE script contradiction; + 10 missing closest-prior citations (NOVELTY_IMPACT_REVIEW §2) + Codex's additions (Xie 2022, Zhao 2023, Cooley 2021, Yao 2025, RECOG, Chen 2024, GROWL) | MAJOR | Full DOI-resolution audit; every method sentence checked against executable code; positioning paragraphs vs closest priors | `references.bib`, manuscript | 4 |
| D12 | `critical_checks.py` fails open (overwrites valid results with MISSING and prints CLEAR) | MAJOR | Fail closed on missing inputs; diagnostics read-only by default | `src/critical_checks.py` | 0 |
| D13 | README: broken command (0-byte `03_xgboost_shap.py`), overstated claims (3 reservoirs, 57%) | MINOR | Fix command; align claims with rebuilt results; clarify canonical scripts | `README.md`, `src/` | 0 |
| D14 | No LICENSE/CITATION.cff/manifest/tests/CI/workflow DAG; placeholder pyproject | MAJOR (for release) | Section 4 plan | repo root | 0/3/5 |
| D15 | ReservoirWatch overstatements (fake confidence constant, 2.5 km circles, Panchet shown, "auto monthly updates" claim, Maithon metrics for all reservoirs) | MAJOR (integrity) | Relabel "research demonstrator"; disable Panchet; remove fabricated confidence; truth-in-labeling pass. Operational upgrade = post-paper | `reservoir_watch/` | 0 (relabel) |
| D16 | Manuscript/figure issues: pdftitle "Causally Attributable"; K=5 figure vs K=3 text; blank GRACE residual panel; CCM "convergence" figure showing endpoint bars; map rectangle vs caption basin | MINOR–MAJOR | All regenerated in Phase 4 from rebuilt results | manuscript, `figures/` | 4 |

---

## 3. ROUTE B — PHASED ROADMAP (Jul 2026 → 2027)

**The Route-B question (from Codex §10, adopted):**
> How much of monthly storage change in a data-sparse managed Indian reservoir is explained
> by inflow, precipitation, and evaporation versus measured managed releases — and what can
> satellite-only monitoring contribute where operator records are incomplete?

**Working title:** *"Separating hydroclimatic inflow and managed releases in a data-sparse
Indian reservoir using Sentinel-1 and a satellite-constrained mass balance."*

### Phase 0 — Foundation rebuild (mid → late July, ~2 weeks) — *starts on roadmap approval*
| Task | Owner | Exit test |
|---|---|---|
| Download CWC 2020 Maithon sedimentation report; digitize the 2019 E-A-C table (MDDL→FRL) | Claude (code) + Nishi (verify numbers against PDF) | Interpolated curve reproduces CWC 2019 dead 0.0949 / gross 0.8739 BCM and FRL area 85.95 km² |
| Rebuild Maithon storage series on the CWC curve; ALOS curve demoted to sensitivity | Claude | New series consistent with CWC weekly live storage (F-021 definition handled explicitly) |
| Fix B2 (GRACE raw units), B3 (de-leak CV), B4 (CCM direction), D10 (pbias), D12 (fail-closed checks) | Claude | Unit tests pass; a "what survives" memo records which findings hold under corrected code |
| Release hygiene: LICENSE, CITATION.cff, data manifest, README fix, pyproject, remove 0-byte script, ReservoirWatch relabel + Panchet disable | Claude | Stranger-clone test: README instructions run without error |
| **Gate 1 (physical):** CWC geometry and units reproduce known Maithon values | — | GO/NO-GO |

### Phase 1 — Operational data acquisition (late July → August)
| Task | Owner |
|---|---|
| India-WRIS daily Maithon (+ Panchet) levels/storage 2017–2024 | Nishi |
| CWC weekly bulletin archive scrape (full history, not 9 points) | Claude (scraper exists: `07_cwc_validation.py` lineage) |
| DVC annual reports — releases, hydropower generation (proxy for turbine outflow); two PDFs already in `data/raw/` | Nishi collects, Claude extracts |
| If gate/release logs not public: RTI application to DVC (template drafted by Claude; supervisor co-signs) | Nishi + Dr. Ray |
| Exact-date Sentinel-1 scene validation: 12–24 distinct dates spanning monsoon + dry + elevation range; scene-level classifier accuracy | Claude (GEE) + Nishi (runs) |
| **Gate 2 (validation):** distinct multi-season exact-date observations exist | GO/NO-GO — if operational data is unobtainable by end-Aug, convene with Dr. Ray to re-scope |

### Phase 2 — Physical mass balance (August → September)
- dS/dt = Q_in − Q_release − E_lake + P_lake − seepage, with measured levels (WRIS), reconstructed inflow (SCS-CN, now validated against balance closure), DVC release/hydropower records, ERA5/MODIS lake evaporation
- Panchet S1 re-run (corrected bbox) → tandem system restored if valid
- Closure-error budget: target < 20% monthly (per CLAUDE.md Part 11 threshold, now actually testable)
- Validation against documented operational events (2019–2024 S1 era)

### Phase 3 — Modeling and attribution done right (September → October)
- Nested rolling-origin CV (all preprocessing in-fold); baselines: persistence, climatology, linear, GAM; blocked-bootstrap + observation Monte Carlo uncertainty
- Attribution with an identified estimand: managed-release contribution measured against operational records — not a residual label
- GRACE section rebuilt per D2 design (raw units, basin polygon, leakage treatment, placebos) — framed as cross-scale association; kept only if it survives
- CCM/HMM/DTW: re-run corrected; **each survives into the paper only with operational ground truth to anchor it** (Codex claim gate) — default is to cut DTW taxonomy and HMM to supplement or out

### Phase 4 — Manuscript rewritten from new results (October → November)
- **Rule: no number is inherited from the old manuscript.** Rewrite from the rebuilt outputs
- New title (above), estimand-first framing, citation audit (D11), positioning vs Xie 2022 / Hou 2022 / Vu 2022 / GERD literature
- Independent reviewer pass (one external hydrologist/statistician) + Dr. Ray sign-off
- All 10 Codex go/no-go gates (§14) checked in writing

### Phase 5 — Release, preprint, submit (November 2026 → January 2027)
- Freeze results → tagged GitHub release → **Zenodo DOI** → **EarthArXiv preprint** → submit
- **Venue ladder:** Journal of Hydrology (subscription route, ₹0) → Water Resources Management (hybrid, ₹0, 23-day first decision) → JISRS (₹0 regional fallback)
- EGU Roland Schlich waiver application **Dec 1, 2026** (registration waiver + abstract support); ISRS symposium abstract in parallel
- Realistic acceptance window: **mid-to-late 2027**

### Phase 2b/3b — BEST-PAPER EXTENSIONS (approved for folding in, 2026-07-11)

Nine additions that raise the paper's ceiling beyond "fixed." Ranked by tier-lift per effort;
each is assigned to a phase and carries its own gate so it can be cut without harming the core.

| # | Extension | Phase | Effort | Why it lifts the tier | Cut-safe? |
|---|---|---|---|---|---|
| X1 | **Out-of-basin transferability test** — run the rebuilt pipeline *unchanged* on 3–5 non-DVC reservoirs with WRIS daily storage; report the cross-reservoir RMSE table | 3b | 2–3 wks | Converts "Maithon case study" → "validated transferable method on N reservoirs" — the JoH→WRR difference per every audit. Doubles as the pilot for portfolio paper #2 | Yes — drop to follow-up paper if time runs out |
| X2 | **Event-study causal design** — storage behavior in windows around *known-date* operations (Rabi canal openings at Durgapur each Oct; documented flood releases from DVC annual reports; pre-monsoon drawdown deadlines) vs matched climate-only windows | 3 (replaces CCM/Granger as the causal core) | 1–2 wks after Phase-1 data | Scheduled interventions with external dates = an **identified estimand** — the thing Codex said the project lacks. 5–10 clean events beat 48 noisy months | Core, not cut-safe — this IS the attribution design |
| X3 | **ICESat-2 ATL13 elevations over Maithon 2018–2024** (+ Sentinel-3/Hydroweb if catalogued) | 1 (validation) | ~1 wk, ₹0 | Dozens of exact-date ±10 cm elevations across the full operating range and all seasons — permanently kills the pseudoreplication/single-band criticism; gives elevation a leg independent of the E-A-C curve | Yes, but cheapest insurance on the list |
| X4 | **Benchmark vs global products** — compare Zhao et al. 2023 (7,245-reservoir) and GROWL Maithon records against ours and CWC truth | 3b | ~1 wk | If the tailored pipeline beats global products, that's a quantified "why local calibration matters" finding — flips the novelty problem from competing with the global datasets to auditing them | Yes |
| X5 | **Forward-model the GRACE test** — inject the known reservoir mass series into mascon observation space (leakage-aware, RECOG-style) and test consistency, instead of TWS-on-storage regression | 3 (replaces the D2 regression redesign as the preferred form) | 1–2 wks | The technically correct version of C3; per the novelty audit, unreported for a ~1 BCM system. One figure; genuinely novel if it survives | Yes — cut entirely if it doesn't survive |
| X6 | **End-to-end uncertainty budget table** — classifier → area → curve → storage → attribution, propagated | 3 | ~1 wk | Papers that state what satellite-only monitoring *cannot* resolve are rare and become methodology references | No — required by Gate 5 anyway; this formalizes it |
| X7 | **Hydropower generation as release proxy** — turbine discharge ≈ generation/(g·ρ·head·η) from DVC published generation data | 1–2 | days | A ₹0 route to "measured releases" if gate logs never materialize; insurance for Gate 2 | Yes |
| X8 | **Preregister the Phase-3 analysis plan on OSF** before running it | 3 entry (one afternoon) | 0.5 d | Timestamped pre-specified analysis is the strongest answer to garden-of-forking-paths suspicion given this project's reframing history; near-zero cost, high reviewer signal | Yes |
| X9 | **One external co-author** (hydrologist/statistician — e.g., an IIT contact of Dr. Ray's) reviewing Phase 3 before submission | 3–4 | ongoing | Independent methodological credibility for a first-paper team; realistically worth several acceptance points | Yes — but ask early; discuss with Dr. Ray at roadmap review |

**Explicitly rejected additions:** deep learning (n too small), standalone GRACE downscaling
(saturated field), additional causal methods beyond X2 (method count ≠ rigor), MODIS-era
extension (unvalidatable).

**Schedule impact:** X3, X7, X8 fit inside existing phases at negligible cost. X2 replaces
(not adds to) the CCM/Granger core. X1+X4+X5 together add ~3–4 weeks → Phase 3 runs
Sep→early Nov, manuscript Nov, submission **Dec 2026–Feb 2027**. Acceptance-tier upside:
with X1/X2 landed, WRR (fee-waiver request) becomes a credible primary target above JoH.

### AI assistance & authorship policy (for supervisor review)

Facts as of mid-2026, to verify against the target journal's current author guide at submission:
- **All candidate publishers (Elsevier, Springer, Copernicus, AGU/Wiley, MDPI) permit
  generative-AI assistance in manuscript preparation IF disclosed; none permit AI as an
  author; the human authors bear full responsibility for accuracy and integrity.**
- What gets papers flagged/rejected/retracted is **undisclosed** AI use plus its hallmarks:
  fabricated or wrong references (this repo already had two — Ji2023 DOI, Besseling2021),
  numbers inconsistent with data, template AI prose, leftover AI artifacts.
- Project policy, effective now: (1) Nishi is the intellectual owner — runs the pipeline,
  makes the decisions, verifies every number against the data; (2) AI drafting assistance is
  disclosed in the manuscript's declaration section per the journal's required wording;
  (3) every citation is DOI-resolved by a human before submission (D11); (4) final text passes
  through Nishi's own revision so the voice and reasoning are his; (5) Dr. Ray signs off on
  the AI-use disclosure (Codex Gate 10).

### What November 2026 honestly looks like under Route B
Corrected, validated, reproducible work; Zenodo archive + EarthArXiv preprint with DOI;
manuscript submitted or in final supervisor review. **Not** an accepted journal paper —
and that trade was made knowingly for a paper whose central claim can survive hostile
arithmetic, physical checks, and clean reproduction.

| Outcome | Probability (est.) |
|---|---|
| Phase 0 gates pass, foundation rebuilt by early Aug | ~90% |
| Sufficient operational data acquired (WRIS + bulletins + DVC reports; RTI if needed) | ~70% |
| Preprint + submission by Dec 2026–Jan 2027 | ~75% |
| Acceptance at JoH/WRM tier during 2027 | ~40–55% (vs ~15–25% for the old integrated paper) |
| Some respectable acceptance by early 2028 (incl. JISRS fallback) | ~85% |

---

## 4. CODE & DATA RELEASE PLAN

Goal: a release that a stranger can clone, understand, and rerun — the artifact that makes
this project citable regardless of journal timing. Phased so it never blocks the science.

### With Phase 0 (immediate hygiene)
1. `LICENSE` — MIT for code; `data/LICENSE` — CC-BY-4.0 for processed data
2. `CITATION.cff` (paper + software citation)
3. `data/raw/README.md` **manifest**: every expected input file — source URL, GEE export name, retrieval script/instructions, columns, units, version/date, checksum for anything redistributable
4. README repair: fix the broken `03_xgboost_shap.py` command; align claims with reality; document which scripts are canonical (`03_xgboost_attribution.py`, `04_causal_inference.py`); delete the 0-byte file
5. `pyproject.toml` real description + metadata (uv.lock already good)
6. `critical_checks.py` fail-closed (D12)
7. ReservoirWatch truth-in-labeling (D15): "Research demonstrator — retrospective data to Dec 2024"; Panchet hidden; fixed "confidence" constant removed

### With Phase 3 (structural)
8. All constants (geometry, areas, thresholds, dates) → single versioned `config.yaml`; scripts read config, never hardcode — kills the fit_av_params→01 manual copy step
9. One-command workflow: `Makefile` (simplest adequate DAG: raw → stage1 → features → models → figures) with immutable, timestamped outputs
10. `tests/`: unit conversions (BCM/cm/km²), E-A-C interpolation against CWC anchor values, date alignment, CV-leakage tripwire (asserts no test index reaches tuning/early-stopping), coefficient back-transformation, metric definitions (PBIAS!)
11. CI (GitHub Actions): run tests + a fixture-dataset pipeline pass without network access

### With Phase 5 (archival)
12. Freeze → `v1.0.0` tag → Zenodo-GitHub integration → DOI in the manuscript's Data Availability (replaces the placeholder)
13. Deposit contents: processed datasets (CC-BY), code (MIT), the digitized CWC 2019 E-A-C table with provenance note, retrieval scripts for non-redistributable raw data (GEE/NASA)
14. EarthArXiv preprint links the DOI; ReservoirWatch demo linked as supplementary material ("demonstrator")

---

## 5. NEXT ACTIONS (this week, upon approval)

1. **Nishi + Dr. Ray review this roadmap** — especially: Route B commitment, the RTI fallback for operational data, and the authorship/venue ladder
2. On approval → Phase 0 starts: CWC PDF digitization first (everything depends on it)
3. Nishi in parallel: WRIS account/download test for Maithon daily data (de-risks Gate 2 early)

---

*Verification trail: every CONFIRMED verdict in §1 cites the file:line inspected on
2026-07-11; β_raw computed from `data/processed/delta_S_anthro.csv` (SD=0.0917);
CWC values from the CWC 2020 Maithon sedimentation report
(cwc.gov.in/...sedimentation-assessment-maithon-reservoir...may-2020.pdf, per codex_review §16).*
