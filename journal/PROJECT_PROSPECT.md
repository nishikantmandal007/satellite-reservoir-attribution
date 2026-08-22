# PROJECT PROSPECT — DVC Reservoir Attribution

> ⚠️ **SUPERSESSION NOTICE (2026-07-11, Session 015 / D-053):** The August-submission plan,
> July sprint calendar (§4–6), and probability tables in this document are **CANCELLED** —
> the Codex review (`codex_review.md`) revealed submission-blocking code defects and Route B
> was adopted. Current authority: `RECOVERY_ROADMAP.md` (plan) + `EXECUTION_PLAYBOOK.md`
> (procedures). Still valid here: §3 weakness analysis (subsumed into the roadmap's defect
> registry), venue-cost research, and the EGU/ISRS conference facts.

## Honest Assessment & Publication Roadmap
### Prepared 2026-07-11 | Multi-agent review (rigor audit + submission readiness + publication strategy) synthesized by Claude

> **How this was produced:** three independent review agents were run in parallel —
> a hostile-reviewer rigor audit of the manuscript against FINDINGS.md and the source code,
> a submission-readiness review against three journals' requirements, and a web-researched
> publication-timeline strategy. Every load-bearing number below was independently re-verified
> against `data/processed/` files before inclusion.

---

## 1. VERDICT — Is this good research?

**Yes — this is genuinely publishable research, at the Q1-regional / solid-Q2 tier, not the A\* tier.**
It is an unusually honest, multi-method, fully open-data study with one result that is
objectively strong (0.07 m elevation validation), one that is novel and defensible
(GRACE β₂ significance surviving deseasonalization), and one clean proof-of-concept
(the Durgapur fingerprint). For a B.Tech project it is exceptional; the internal 7.2/10
rating remains fair.

**But three things stand between you and submission:**

1. **The manuscript currently contains three checkable numerical errors** (Section 3.1 below —
   found by this review, not present in the March critique). Any reviewer who does the
   arithmetic will find them, and arithmetic errors in the flagship GRACE result would sink
   an otherwise honest paper. These are fixable in 1–2 days and are **non-negotiable before
   any submission or preprint.**
2. **The ₹0 budget eliminates the "fast" journals.** MDPI Remote Sensing (~CHF 2,700 APC,
   no automatic India waiver) and JHRS (gold OA, ~USD 500–1,200 even after India discount)
   both cost money. The CLAUDE.md assumption that MDPI Remote Sensing is a "guaranteed
   fallback" is **wrong on cost**. The guaranteed-free routes are Journal of Hydrology,
   RSE, and JISRS (subscription routes) — all slow.
3. **Your timeline goals need re-definition** (Section 4): *submitted by August* — yes,
   realistic. *Journal-accepted by Oct/Nov* — not at ₹0. *Publicly published and citable
   with a DOI by Oct/Nov* — yes, via EarthArXiv, at ₹0, with ~95% certainty.

---

## 2. WHAT THIS PROJECT ACTUALLY PROVES

What survives hostile scrutiny, in plain language:

| # | Defensible claim | Evidence | Strength |
|---|---|---|---|
| 1 | A ₹0, open-data Sentinel-1 + DEM-hypsometry pipeline reconstructs Maithon water surface elevation to **0.07–0.23 m RMSE** against independent CWC/DVC measurements | F-020, n=9 points, two independent sources | **Strong — the paper's best result** |
| 2 | Monthly climate predictors have near-zero skill (NSE=0.018) for Maithon storage → **operations, not climate, dominate sub-annual storage variability** | F-017/F-019; honest negative-space finding | Strong, if framed correctly |
| 3 | The reservoir-derived residual is a **significant predictor of GRACE-FO TWS** after climate controls, surviving deseasonalization in significance (β₂ p=0.0003, partial R² 0.19→0.20) | F-023, F-027 — verified in `grace_regression_summary.txt` | Novel and defensible as "consistent with a contribution" — NOT as "GRACE systematically misattributes" |
| 4 | Barrage vs storage-dam operations are **separable from satellite data alone** (Durgapur 7/7 annual-cycle cohesion, silhouette 0.49/0.44) | F-011, F-012 | Clean proof-of-concept (n=14 cycles — not yet a "taxonomy") |

**How the original claims fared:**
- **C1 (causal attribution):** survives only in weakened form. What is proven is an
  *integrity check* — the residual is statistically independent of retained climate
  predictors (CCM + Granger null checks pass) — not positive attribution to operational
  decisions. No gate logs or in-era documented events tie the residual to decisions, and
  T_C contamination (r=−0.52, F-025) shows the residual is not fully clean of climate.
- **C2 (fingerprint taxonomy):** survives as proof-of-concept. n=14 annual cycles from 2
  structures cannot support the word "taxonomy."
- **C3 (GRACE contamination):** survives as "consistent with a contribution." The part–whole
  circularity (Maithon ⊂ the mascon cell), the ~34% deseasonalized coefficient drop
  (currently hidden by a units error — see 3.1), and the signal sitting near GRACE's noise
  floor (±0.2 BCM ≈ 1 cm LWE) rule out the abstract's "systematically misattribute" wording.

---

## 3. WEAKNESSES — severity-ranked, with fix cost

### 3.1 NEW numerical errors found by this review (MUST FIX — ~1–2 days, all text/arithmetic)

These were independently verified against the data files on 2026-07-11:

| # | Error | Where | Verified fact | Fix |
|---|---|---|---|---|
| E1 | **Deseasonalized GRACE CI printed in wrong units, hiding a 34% coefficient collapse.** Manuscript reports CI "[+0.23, +0.76] cm BCM⁻¹" — those are raw BCM/BCM values. True deseasonalized β₂ = 0.496/0.196 = **2.53 cm/BCM**, CI **[1.17, 3.89]** — 34% below the 3.84 headline, and the CI **excludes the theoretical 4.28** | manuscript.tex ~line 795 | `grace_deseasonalized_results.csv`: β₂=0.496, CI [0.230, 0.763] BCM/BCM; conversion 0.196 BCM/cm from `src/05:51` | Convert units, report the drop honestly, temper the "larger fraction" sentence |
| E2 | **Basin-area inconsistency manufactures "within 10% of theoretical."** Theoretical 4.28 cm/BCM uses A=23,370 km²; the pipeline's own conversion and Table 2 use **19,600 km²**, which gives theoretical 5.10 cm/BCM → fitted is 75%, not 90% | manuscript.tex lines 448 vs 540–541 | `src/05:48` `CATCHMENT_AREA_KM2 = 19600.0` | Pick one area, recompute, state the range honestly (e.g. "75–90% of theoretical depending on basin delineation") |
| E3 | **Stale mean ΔS_anthro = −0.029 BCM; true mean is −0.014 BCM** — and either value is inside the ±0.051 BCM CI, so the abstract's "net management-driven drawdown" claim is statistically unsupported | abstract line 126–127, line 702 | `delta_S_anthro.csv` mean = −0.0139 (n=48) | Update the number and **delete the drawdown claim** |
| E4 | Minor untraceables: β₁ p=0.573 (file says 0.696); "OLS SE 1.22" (suspiciously = the DW statistic 1.222); Ljung-Box lag-3/lag-12 p-values not in any findings file; one figure caption still says "Bootstrap 95% CI" after the text was reframed to seed-sensitivity | scattered | `grace_regression_summary.txt` | Trace or delete each |

### 3.2 Structural weaknesses (the top reviewer attacks, ranked)

| # | Attack | Survivable? | Cost |
|---|---|---|---|
| 1 | *"Your 'climate model' contains the target's own lags (dS_lag1 carries 67% of importance) — the abstract's 'eight non-collinear climate drivers' is false for two of them, and you never state which residual (lag vs no-lag) feeds Stages 4–5."* | Yes — major text revision. Rename the feature set, define the residual pathway explicitly, foreground the ±0.016 BCM lag-robustness result (F-009). Drop "causally attributable" from title echoes in abstract/conclusions | 2–3 days writing |
| 2 | GRACE arithmetic (E1+E2 above) | Yes — after the fixes | 1–2 days |
| 3 | *"TWS-on-own-component regression is tautological; your signal ≈ GRACE noise floor."* | Fatal to the strong wording, fine as "consistent with contribution" — Discussion already has the right posture; abstract/Conclusion 4 don't | Text only |
| 4 | *"NSE=0.208, negative in 2/4 folds and in both regimes — no skill to define a residual with."* | Yes — already fully disclosed (Tables 3–5); the "low climate skill IS the finding" defense holds once attack #1 is fixed. Caps the journal tier | Already done |
| 5 | *"T_C correlates with your residual at −0.52 — it's part climate."* | Disclosed; a reviewer will likely demand a bounding analysis (refit with T_C included) | ~1 day, cheap insurance |
| 6 | *"CCM at E=1, n=48, shared processing pipeline = lagged cross-correlation, not causal discovery."* | Caveated already; add shared-pipeline caveat; don't lean on it | Text only |
| 7 | *"Validation covers 145–148 m in Nov–May only — monsoon and dead-storage regimes unvalidated"* (the March critique's W1 disclosure was never actually added to Limitations) | Yes — 2–3 sentences, or properly killed by the WRIS daily-data work (Section 6) | Text, or solved by new data |

### 3.3 What is already genuinely fixed (verified in the manuscript text)

FLAW 2 (NSE headline — now honest, best-repaired flaw), FLAW 3 (CCM reinterpreted as
hydraulic connectivity), W2 (999 surrogates), W3 (E=1 acknowledged), W5 (regime-stratified
NSE reported). The limitations section is unusually honest — reviewers will notice
that favorably.

### 3.4 Packaging gaps (submission mechanics — ~4–5 days total)

- All 5 Highlights exceed Elsevier's 85-char limit; abstract 297 words (trim to ≤250)
- No cover letter, no CRediT statement, no funding statement, no generative-AI-use
  disclosure (required by Elsevier and MDPI — must be drafted and supervisor-approved)
- No Zenodo DOI — Data Availability has a placeholder URL; no LICENSE file in repo
- `references.bib`: **Wada2017 is the wrong paper** (entry is Wada 2014 ESD, not Wada 2017
  Nat. Geosci.); Newey-West, Otsu, HMM, Granger, KGE methods used but uncited (keys exist
  in bib, never cited); `dtaidistance` @software entry will misrender
- `\graphicspath` bug: `../figures/` should be `../../figures/` (local compile fails)
- FigS1–S3 exist but are orphaned (never referenced); Supplementary Note S1 must be split
  into a separate file; Fig8_taxonomy needs a PDF export and version check
- README overstates vs manuscript ("three reservoirs 2002–2024", "explains 57%") —
  reconcile before the repo goes public with the paper

---

## 4. YOUR TWO TIMELINE QUESTIONS, ANSWERED DIRECTLY

**"Can we do this in July and apply for publication by August?"**
**Yes.** The science fixes (3.1, 3.2) plus packaging (3.4) plus the July data work
(Section 6) fit comfortably in July with your 10 h/day pace. Submission window:
**Aug 10–14.**

**"Can we be published by October–November?"**
Depends what "published" means:

| Definition | Achievable at ₹0? | How |
|---|---|---|
| Publicly online, citable, permanent DOI | **YES (~95%)** | EarthArXiv preprint, week of Aug 10 → DOI within days |
| Accepted at a peer-reviewed journal by Nov | **NO at ₹0.** Only MDPI Remote Sensing is fast enough (median first decision 22 days; ~35–45% chance of acceptance+online by mid-Nov) — but it costs ~CHF 2,700 (~₹2.6 lakh) with no automatic India waiver | Only if the college/a grant funds the APC. **Do not submit to MDPI hoping for a waiver** — denial after acceptance forces an ugly withdrawal |
| Under review at a good journal by Oct/Nov | **YES** | Journal of Hydrology (subscription route, ₹0), submitted mid-August |

---

## 5. THE TWO SCENARIOS

### Scenario A — Speed (₹0): "citable by mid-August, under review by September"

| Date | Milestone |
|---|---|
| Jul 14 – Aug 2 | July sprint (Section 6) — science fixes + new data work + manuscript revision |
| Aug 3 – 8 | Supervisor review with Dr. Ray; final 300-DPI figures; packaging complete |
| **Aug 10** | **EarthArXiv preprint → DOI in ~1–3 days → publicly citable** (post only after fixes are locked — the public version must not be the current flawed one) |
| Aug 14 | Submit to **Journal of Hydrology** (subscription route, ₹0; preprint explicitly permitted) |
| ~Aug 28 | Desk-check survival (JoH median ~10 days to desk decision) |
| Oct–Nov 2026 | Paper is online (EarthArXiv), citable, and "under review at Journal of Hydrology" — satisfies placement/grad-application/B.Tech-distinction needs |

Probability of hitting every milestone above: **~85–90%.**

*A2 variant (only if APC money materializes):* submit MDPI Remote Sensing Aug 10 →
first decision ~Sep 1 → acceptance+online Oct 15–Nov 15 at ~35–45% probability.
Worth 30 minutes checking whether BIT Sindri is ONOS-registered and whether the ONOS
APC fund covers anything relevant (almost certainly not — it covers only top-1% OA
journals) — then drop the idea unless funding appears.

### Scenario B — Impact (₹0): Journal of Hydrology, decision in 2027

| Date | Milestone |
|---|---|
| Aug 14, 2026 | Submit to JoH (IF 6.7, free via subscription route); cover letter cites the EarthArXiv preprint |
| Nov 2026 – Jan 2027 | First decision (median ~69 days post-review, 3–4.5 months total). Expect **major revision** |
| Dec 2026 – Feb 2027 | Revision + response |
| **Feb – Jun 2027** | Acceptance → online within 2–3 weeks |

Probability of eventual acceptance at JoH: **~15–25% as-is; ~25–35% with the full July
sprint executed** (Panchet + WRIS validation are the movers). RSE (IF ~11) is not
recommended: regional case study + single fully-validated reservoir + individually
standard RS methods = high desk-rejection probability (~5–10% success). HESS is
scientifically an excellent fit but its €1,800 APC is only waivable at editor discretion —
email the HESS editorial office *before* submitting if interested; if no waiver, drop it.

**Cascade if JoH rejects (~Dec 2026):** revise per reviews → JHRS if ~USD 800 can be found
(best scope fit — it explicitly wants regional studies) → else JISRS (Springer, ₹0
subscription route, Indian audience) → acceptance mid/late 2027. The EarthArXiv preprint
keeps the work citable throughout, so a rejection costs time, not visibility.

### Recommended path — do both simultaneously

**They are not mutually exclusive: Scenario A *is* the first half of Scenario B.**
July sprint → EarthArXiv (Aug 10) → JoH submission (Aug 14). You get the Oct/Nov
"published online" outcome guaranteed at ₹0, and a live shot at a Q1 (IF 6.7) acceptance
in 2027. Decide the cascade target only if/when JoH rejects. Ask Dr. Ray **this week**
whether any departmental/TEQIP/state fund could cover an APC — that answer alone
determines whether the MDPI fast lane exists.

---

## 6. JULY SPRINT ROADMAP

Work items ranked by acceptance-probability gain per week (strategist's assessment):

| Rank | Item | Effort | Expected gain |
|---|---|---|---|
| 0 | **Fix E1–E4 numerical errors + attack-#1 reframing** (non-negotiable, blocks everything) | 3–4 d | Prevents a guaranteed catch |
| 1 | **India-WRIS/CWC daily Maithon storage 2017–2024** → ~2,800 daily obs replaces the 9-point validation; converts the weakest section into the strongest | 3–5 d | +8–12 pts at JoH tier |
| 2 | **Panchet S1 re-run** with corrected bbox [86.72, 23.52, 86.95, 23.68] (already in the GEE script) → restores the physically correct Maithon–Panchet tandem pair | 5–7 d (GEE cheap; downstream reruns are the cost) | +5–10 pts; prerequisite for #3 |
| 3 | **Granger/CCM re-run with Panchet** — tiny marginal effort once #2 lands; if significant, flips C1 from suggestive to significant (JHRS-tier → JoH-tier difference) | 1–2 d | 0 pts if still ns (reframe honestly); +10–15 pts if significant |
| 4 | T_C bounding analysis (refit with T_C included) — cheap insurance vs attack #5 | ~1 d | +2–3 pts |
| — | GRACE period extension | 2–4 d | +1–3 pts — **skip** unless everything else finishes early |

### Week-by-week calendar

| Week | Nishi (runs/downloads) | Claude (code/writing) |
|---|---|---|
| **Jul 14–18** | WRIS/CWC daily storage download; launch Panchet GEE re-run (runs in background) | Fix E1–E4 in manuscript + rerun deseasonalized GRACE reporting in correct units; start attack-#1 reframing |
| **Jul 19–25** | Paste Panchet outputs; verify against known events | Panchet pipeline reruns (Stage 1 → AV params → storage series); WRIS validation analysis + new validation figure; T_C bounding analysis |
| **Jul 26–29** | Review results | Granger/CCM re-run with Panchet; integrate all new results into manuscript; regenerate affected figures |
| **Jul 30 – Aug 2** | — | Packaging: highlights ≤85 chars, abstract ≤250 words, cover letter, CRediT/funding/AI statements, bib fixes (Wada2017 etc.), supplement split, `\graphicspath` fix, Zenodo DOI + LICENSE, README reconciliation |
| **Aug 3–8** | **Dr. Ray full review**; ORCID registration; APC-funding answer | Address supervisor comments; final compile check |
| **Aug 10** | Post EarthArXiv preprint | — |
| **Aug 14** | Submit to Journal of Hydrology | — |

Buffer: the calendar has ~4 slack days. If Panchet re-run fails again (bbox still
contaminated), publish without it — the manuscript already handles its absence honestly.

---

## 7. RISKS & HONEST PROBABILITIES

| Outcome | Probability | Notes |
|---|---|---|
| EarthArXiv DOI online by mid-Aug (₹0) | ~95% | Moderation takes days; only risk is sprint slippage |
| JoH submission by Aug 14 | ~85% | Slack built in |
| JoH desk-check survival | ~60–70% | Regional scope + honest framing helps; first-author inexperience is invisible at desk stage |
| JoH eventual acceptance (with July sprint done) | ~25–35% | The single biggest movers: WRIS validation + Panchet |
| Accepted somewhere respectable by mid-2027 (JoH → JHRS/JISRS cascade) | ~70–80% | The work is fundamentally sound; it will land somewhere |
| Journal-accepted by Nov 2026 at ₹0 | ~0% | No free journal is that fast — plan around the preprint instead |
| Journal-accepted by Nov 2026 with APC funded (MDPI) | ~35–45% | Only if ~₹2.6 lakh materializes |

**The real risks are not methodological:**
1. Submitting/preprinting **before** fixing E1–E3 — arithmetic-level catches that would
   torch credibility with reviewers and anyone reading the preprint.
2. Burning the APC question too late — ask Dr. Ray in week 1, not week 4.
3. Scope creep in July (e.g., GRACE extension, LSTM revival) — the calendar above is full;
   everything not on it waits for the revision round.

---

## 8. SOURCES & TRACEABILITY

- All quantitative claims trace to `journal/FINDINGS.md` (F-001–F-031) or files in
  `data/processed/` (re-verified 2026-07-11: `grace_regression_summary.txt`,
  `grace_deseasonalized_results.csv`, `ccm_results.csv`, `baseline_comparison.csv`,
  `fold_level_metrics.csv`, `delta_S_anthro.csv`).
- Journal turnaround/cost claims: Elsevier Journal Insights (JoH: ~10 d desk, ~69 d
  post-review, ~159 d median to acceptance), MDPI journal pages (RS: median 22 d first
  decision H1-2026, APC CHF 2,700), Elsevier GPOA policy (India ≤80% OA discount, no
  automatic full waiver), HESS APC pages (€1,800, discretionary waiver only), ONOS APC
  guidelines (top-1% OA journals only), EarthArXiv FAQ/moderation policy, Elsevier
  preprint policy (preprints permitted "anywhere at any time").
