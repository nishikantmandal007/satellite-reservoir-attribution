# NOVELTY, TITLE & MULTI-PAPER REVIEW — DVC Reservoir Attribution

> ⚠️ **PARTIAL SUPERSESSION (2026-07-11, Session 015 / D-053):** the §4 enhancement list's
> August timeline is CANCELLED (Route B adopted — see `RECOVERY_ROADMAP.md` +
> `EXECUTION_PLAYBOOK.md`). **Still fully valid:** §1 title principles, §2 novelty verdicts
> and the 10 mandatory citations, §3 impact assessment, §5 portfolio (now refined by the
> roadmap's X1 transferability extension). The Route-B paper title comes from the roadmap,
> not §1's candidates.

## Brutal honest researched review: title alignment · genuine novelty · impact · best-shape enhancements · publication portfolio
### Prepared 2026-07-11 (Session 014) | Companion to PROJECT_PROSPECT.md

> **How this was produced:** a web-researched literature novelty audit (~20 targeted searches
> across 2019–2026 literature), a venue-verified multi-paper portfolio analysis, and a
> main-thread title–work alignment audit against the Session-013 rigor findings.
> All external claims carry URLs; all internal numbers trace to FINDINGS.md.

---

## 1. DOES THE TITLE MATCH THE WORK? — No, in three places.

Current title (manuscript.tex:81–83):
*"Satellite-Detectable Anthropogenic Fingerprints in Reservoir Storage Variability:
Multi-Method Attribution Evidence from the Damodar Valley Corporation System Using Explainable AI"*

| Component | Promise | What the paper actually proves | Verdict |
|---|---|---|---|
| "Satellite-Detectable" | Detection from satellite alone | Yes — Sentinel-1-only pipeline, CWC-validated to 0.07 m RMSE (F-020) | **ALIGNED — keep.** This is the paper's strongest true claim |
| "Anthropogenic Fingerprints" | Signatures traceable to operations | The residual is independent of retained climate features (CCM nulls) but carries T_C contamination r=−0.52 (F-025), and no operational records tie it to decisions | **OVERREACH** — "fingerprint" is earned only by the DTW/Durgapur result, not by ΔS_anthro |
| "Multi-Method Attribution Evidence" | Converging positive attribution | The five methods are integrity checks on one construct (the Session-012 audit itself called "five independent methods" overclaimed) | **OVERREACH** — "attribution" should become "separation/detection" language |
| "Using Explainable AI" | XAI is central to the contribution | SHAP is a tool here; the model has NSE=0.208 and 4/8 significant features (F-029) | **LIABILITY** — a JoH reviewer reads "Explainable AI" + modest skill as buzzword inflation |
| *(absent)* | — | The most defensible headline finding: **operations dominate sub-annual storage variability** (climate-only NSE=0.018) + a gauge-validated ₹0 pipeline | **MISSING from the title entirely** |

**Misaligned metadata (fix in the sprint):**
- `manuscript.tex:56` pdftitle still says the abandoned **"Causally Attributable"** title — the PDF metadata will contradict the printed title
- "causally attributable storage signals" survives in the **abstract** (line ~141) and **Conclusions** (line ~972) despite the title softening
- **README.md** headline claims "explains 57% of variance" (the clipped-rows NSE the paper itself demoted to secondary) and "three DVC reservoirs… 2002–2024" (paper: two reservoirs, 2017–2024)
- manuscript header/comments still target **RSE** while the plan is JoH — reconcile before submission

### Recommended titles (ranked)

1. **"Reservoir operations dominate sub-annual storage variability: satellite-based
   separation of operational and climatic signals in the Damodar Valley Corporation
   system, India"**
   — Leads with the finding; "separation" not "attribution"; names system + country
   (JoH regional relevance + discoverability). This completes the FLAW-4 reframing
   strategy the internal critique prescribed — the current title contradicts it.
2. **"Satellite-only detection of reservoir operating signatures and their imprint on
   GRACE-FO terrestrial water storage: a Damodar basin case study"**
   — Leads with the two most novel elements; "imprint … case study" is the safe C3 framing.
3. **"Separating operational and climatic drivers of reservoir storage from open
   satellite data: multi-method evidence from the Damodar Valley Corporation, India"**
   — Closest to the current structure with every overreach removed.

---

## 2. WHAT IS GENUINELY NEW — per-claim verdicts against the literature

The uncomfortable summary first: **none of the individual methods is new. The genuine
novelty is the integration, the inferential hygiene, and one narrow first.** Verdicts:

| # | Claimed novelty | Verdict | Closest prior work |
|---|---|---|---|
| a | Sentinel-1 + DEM hypsometry storage, gauge-validated, India | **ALREADY DONE as a method** — keep only as a site/validation contribution | Vanthof & Kelly 2020 *RSE* (India tanks, TanDEM-X+S1); RAT 2.0–3.0 (Das 2022, Minocha 2024 *GMD* — operational on Indian reservoirs); Suresh et al. 2024 *RSE* (satellite tracking of Indian dam ops, Kerala 2018); Tortini 2020 *ESSD*; ICESat-2 Rihand Dam validation |
| b | ML-residual anthropogenic isolation at reservoir scale | **INCREMENTAL** — paradigm is Humphrey & Gudmundsson 2019 (GRACE-REC) and Ji 2023; **Hou et al. 2022 *HESS*** already did global reservoir-scale climate-vs-management attribution | Defensible advance: single-reservoir management resolution + surrogate-tested causal verification of residual independence — no prior residual study does that check |
| c | Surrogate-tested CCM on managed reservoir hydrology | **INCREMENTAL, defensible narrow first** — CCM on a two-dam system exists (*Physica A* 2022); CCM is accepted in hydrology (Bonotto 2022 *WRR*) | "First phase-randomized-surrogate-tested CCM on **satellite-derived** storage of a dam→barrage cascade" survives, said with "to our knowledge" |
| d | DTW "operational fingerprint taxonomy" from satellite | **INCREMENTAL — the weakest claim.** Vu et al. 2022 *HESS* already inferred operating rules/filling strategies for 10 Mekong reservoirs from satellite alone; DTW clustering of reservoir operations exists (*Water* 2021) | With 2 structures × ~7 annual cycles and silhouette 0.49 (below the project's own 0.5 target), "taxonomy" overclaims. **Rename to "operational signature separation"** and frame as a demonstration |
| e | Specific dam system's operational signal in GRACE-FO via partial regression with climate controls, sub-mascon | **FIRST (narrowly)** — for a ~1 BCM-class system with a formal regression design. But specific-dam GRACE detection exists for big systems: Three Gorges (Wang 2011 *WRR*), Longyangxia (Yi 2017 *WRR*), **GERD (Abdelmohsen 2024 *PNAS Nexus*)** — all 10–40× your signal | Keep the manuscript's existing hedge ("consistent with a contribution"), never "detection." The real exposure is plausibility (0.2 BCM ≈ 0.8 cm LWE ≈ mascon noise), not novelty — pre-empt with the Yi/GERD magnitude comparison and a confounder paragraph (irrigation/groundwater covariance) |

Also verified: **no prior GRACE–Damodar or DVC-specific satellite study exists** — the
regional first is real.

### Mandatory citation additions (currently only Ji 2023 is in references.bib)

These are the papers a reviewer will use for "you missed X" — cite them or be rejected on
positioning alone:
1. **Hou et al. 2022**, *HESS* 26:3785 — global reservoir climate-vs-management attribution (biggest threat)
2. **Vu, Dang, Galelli & Hossain 2022**, *HESS* 26:2345 — satellite-only operating-rule inference, Mekong
3. **Suresh, Hossain et al. 2024**, *RSE* 307:114149 — satellite tracking of Indian dam operations
4. **Humphrey & Gudmundsson 2019**, *ESSD* 11:1153 — GRACE-REC residual paradigm
5. **Abdelmohsen et al. 2024**, *PNAS Nexus* 3:pgae219 — GERD in GRACE-FO with climate controls
6. **Wang et al. 2011** *WRR* (Three Gorges) + **Yi et al. 2017** *WRR* (Longyangxia) — dam-in-GRACE magnitude anchors
7. **Vanthof & Kelly 2020**, *RSE* 235:111437 — India satellite reservoir storage
8. **Turner et al. 2021** *J.Hydrol.* + **Steyaert et al. 2022** *Sci. Data* (ResOpsUS) — operating-rule inference context
9. **Physica A 2022** (604:127893, CCM on a dam system) + **Bonotto et al. 2022** *WRR* — CCM-in-hydrology precedent
10. **Asoka & Mishra 2020** *JGR-Atmos.* / **Arshad et al. 2024** *WRR* — India anthropogenic-vs-climate TWS separation

### The honest novelty statement (usable in the JoH cover letter)

> While satellite-based reservoir storage estimation, climate-residual attribution of water
> storage, and satellite inference of reservoir operating patterns have each been demonstrated
> individually, this study is, to our knowledge, the first to integrate them into a single
> verifiable attribution chain at individual-reservoir management resolution: gauge-validated
> Sentinel-1 storage reconstruction, an explainable climate-only model whose residual is
> subjected to surrogate-tested causal diagnostics (Granger, convergent cross-mapping), and a
> regression-based test — with explicit climate controls and autocorrelation-robust inference —
> of whether a small (~1 BCM-class) dam system's operational anomaly is expressible in GRACE-FO
> at sub-mascon scale. Applied to the Damodar Valley Corporation system, it provides the first
> such multi-method operational attribution for an Indian reservoir cascade and a fully
> open-data, reproducible template for other managed basins.

### What to STOP claiming
- Any implication that S1+hypsometry storage estimation is methodologically new (it isn't — RAT already runs it operationally on Indian reservoirs)
- "Taxonomy" (n=14 cycles, 2 structures → "operational signature separation")
- "Attribution evidence" as positive attribution (it is residual isolation + integrity checks)
- "Detection" of DVC in GRACE (use "consistent with a contribution")
- "Five independent methods" (they are five views of one construct)

---

## 3. IMPACT — who cares, and how much

**Audiences that will actually cite this:**
1. **Satellite reservoir-monitoring groups** (Hossain/SASWE-RAT, Gao/TAMU, Deltares Global
   Water Watch) — as an India case study and gauge-validation point
2. **GRACE attribution community** (Humphrey, Ji, Arshad, Mishra lineages) — as a sub-mascon
   boundary test of what GRACE can resolve
3. **Causal-hydrology / EDM users** — as a managed-system CCM application with proper
   surrogate control
4. **Indian water policy/academia** — DVC relevance + a caution on GRACE-based stress
   assessments in managed basins; plus a ₹0 pipeline any Indian institution can rerun

**Realistic 5-year citation range for a JoH-tier regional paper: ~15–40** — upper end if the
code/data release is genuinely reusable and the GRACE result survives review intact; ~10–20
if the GRACE section gets cut in revision. Method-defining papers in this space (Vanthof &
Kelly, Hosseini-Moghari) hit 60–150; a two-structure case study will not — the durable
citation driver is the **methodological package + open pipeline**, not any single finding.

**The honest impact sentence:** this paper will not change how GRACE products are made; it
gives the community a carefully-checked, fully open worked example that operations dominate
a managed reservoir's storage signal and can register at mascon scale — a template and a
caution, not a new instrument.

---

## 4. BEST-SHAPE ENHANCEMENT LIST (merged with the July sprint)

Priority-ordered. Items marked ★ are NEW from this review (beyond PROJECT_PROSPECT.md §6):

| # | Item | Effort | Payoff |
|---|---|---|---|
| 1 | Fix numerical errors E1–E4 (GRACE units/CI, basin area, stale mean, untraceables) — PROSPECT §3.1 | 1–2 d | Blocks a fatal reviewer catch |
| 2 | Attack-#1 reframing ("climate drivers" containing target lags; define residual pathway) | 2–3 d | Blocks the #1 structural attack |
| 3 | ★ **Retitle** (candidate #1 above) + fix pdftitle, abstract/conclusions "causally attributable", README claims, RSE→JoH header | 0.5 d | Aligns every claim surface with what is proven |
| 4 | ★ **Add the 10 mandatory citations** + a positioning paragraph in the Introduction (vs Hou 2022, Vu 2022, Suresh 2024) and a GRACE-magnitude paragraph in the Discussion (vs Three Gorges/Longyangxia/GERD: "prior GRACE-dam detections involved 13–43 BCM systems; we test a ~1 BCM-class system with formal climate controls") | 1–1.5 d | Converts "you missed X" rejections into "well-positioned" |
| 5 | ★ Rename "operational fingerprint taxonomy" → "operational signature separation" throughout; keep "fingerprint" only for the Durgapur 7/7 result | 0.5 d | Removes the weakest overclaim |
| 6 | WRIS/CWC daily storage validation (9 points → ~2,800) | 3–5 d | +8–12 pts acceptance probability |
| 7 | Panchet S1 re-run (restores tandem pair) → Granger/CCM re-run | 6–9 d | +5–10 pts, upside +10–15 if Granger flips |
| 8 | ★ GRACE **confounder paragraph** (β₂ may proxy correlated irrigation/groundwater dynamics — argue magnitude + timing, cite Yi 2017 framing) | 0.5 d | Pre-empts the strongest C3 attack |
| 9 | T_C bounding analysis | 1 d | Cheap insurance |
| 10 | Packaging (highlights, abstract trim, cover letter with the §2 novelty statement, CRediT/AI statements, Zenodo DOI, bib fixes) — PROSPECT §3.4 | 4–5 d | Submission mechanics |

Items 3, 4, 5, 8 add ~3 days to the July calendar in PROJECT_PROSPECT.md §6 — still fits
before the Aug 10 EarthArXiv / Aug 14 JoH dates (the calendar had ~4 slack days).

---

## 5. MULTIPLE PAPERS? — Yes: realistically 2 strong papers + 1 dataset DOI + conferences

Full analysis with verified costs in the portfolio audit; the ranked verdicts:

| Candidate | Verdict | Venue (₹0 route) | Effort |
|---|---|---|---|
| **1. Main attribution paper** | **DO NOW** (Aug 2026) | JoH subscription route (verified: no author fee); free fallback chain: RSE subscription → Hydrological Sciences Journal → JHRS only if Elsevier geo-pricing quote is affordable | 4–6 wks to submission |
| **2a. Zenodo dataset DOI** (27 CSVs + code snapshot, CC-BY/MIT, versioned) | **DO NOW** — takes an afternoon, required for the Data Availability statement anyway | Zenodo (free) | 0.5–1 wk |
| **2b. Data paper as-is (2 reservoirs)** | **SKIP** — too thin AND no free venue (Scientific Data $2,290+, ESSD €1,400, Data in Brief $1,330 — India gets no automatic waiver at any) | — | — |
| **3. Reservoir Watch → JOSS software paper** | **SKIP as-is** — a ~560-line GUI-only Streamlit app fails three JOSS criteria (GUI-only scope exclusion, <6-month public history, "minor utility"). Becomes viable in mid-2027 IF the pipeline is refactored into a pip-installable library during the scale-up | JOSS (free) after refactor | 6–10 wks engineering |
| **4. Scaled follow-up: signatures across 20–150 Indian reservoirs (WRIS + S1)** | **DO AFTER MAIN PAPER — the highest-value spin-off** and the natural M.Tech/PhD paper; also retroactively fixes the main paper's n=14 weakness | WRR (fully OA but AGU states no accepted article is refused for inability to pay — request waiver in writing at submission); guaranteed-free fallback JoH | 4–8 months |
| **5. Standalone GRACE downscaling (Damodar)** | **SKIP** — saturated field: an 80-paper systematic review (2011–2025) exists; 0.1° RF downscaling published 2025; your exact RF+XGB+Ridge stacking design published 2026. Fold a downscaling component into #4 only if it serves a question | — | — |
| **6. Conferences at ₹0** | **DO selectively**: EGU (virtual + Roland Schlich waiver, apply ~Dec 1 2026; abstract €50), ISG-ISRS National Symposium (best in-person value, student rate), AGU online-only (India qualifies for abstract-fee waiver). Roorkee Water Conclave was Feb 2026 — next ~2028, perfect for paper #4 | €50–₹6,500 total | days each |

**Salami-slicing guardrails (all verified against policy):**
- Thesis→paper and preprint→paper are both explicitly allowed by Elsevier — declare both in the cover letter
- The Zenodo DOI, a future India-scale data paper, the scaled follow-up, and a JOSS paper are all **clean companions** (distinct contributions)
- **Never do:** splitting Maithon/Durgapur into two papers; publishing the DTW result or CWC validation as separate short papers; putting any attribution finding in a data paper or dashboard docs before the main paper is accepted
- **Settle authorship with Dr. Ray now, in writing** — especially her role in the scaled follow-up if it happens at a different institution

**Sequencing (mid-2026 → end-2027):** Zenodo DOI (Jul) → EarthArXiv + JoH (Aug) →
ISRS abstract + 5-reservoir WRIS pilot of #4 (Sep–Oct) → EGU waiver application (Dec 1) →
JoH decision + scale-up + library refactor (Dec–Mar) → EGU virtual (Apr 2027) →
main paper accepted + #4 submitted to WRR (mid-2027) → JOSS if the library is real (late 2027).
Realistic end-2027 total: **2 journal papers, 1 dataset DOI, 1 preprint, 2–3 conference
presentations, possibly 1 JOSS paper.**

---

## 6. BOTTOM LINE — the brutal paragraph

The work is better than its title and worse than its abstract. Every individual method in
this paper already exists in the literature — Sentinel-1 storage estimation runs
operationally on Indian reservoirs today (RAT), reservoir-scale climate-vs-management
attribution was done globally in 2022 (Hou), satellite-only operating-rule inference was
done in 2022 (Vu), and dams have been found in GRACE since 2011 (Three Gorges) — so the
title's "Anthropogenic Fingerprints… Attribution Evidence… Explainable AI" is writing
checks the results don't cash, while the genuinely strong material (a 0.07 m gauge
validation, the operations-dominate finding, the first formal climate-controlled regression
test of a ~1 BCM system in GRACE-FO, and unusually honest integrity checking) is buried.
Retitle around the finding, add the ten missing citations before a reviewer adds them for
you, fix the three arithmetic errors, downgrade "taxonomy" to what n=14 supports, and this
is a solid, citable JoH-tier paper (~15–40 citations in 5 years) — the first of a realistic
two-paper-plus-dataset portfolio whose second paper (the 20–150 reservoir India scale-up)
is where the real career value lives. What kills papers like this is not weak novelty; it
is claiming the wrong novelty. Claim the integration and the honesty, not the methods.

---

*Cross-reference: publication timelines, costs, scenarios and the July sprint calendar are in
`journal/PROJECT_PROSPECT.md`. Items 3, 4, 5, 8 of Section 4 above are additions to that
sprint. Sources for every novelty verdict and venue cost are in the agent audit outputs;
key URLs inline above.*
