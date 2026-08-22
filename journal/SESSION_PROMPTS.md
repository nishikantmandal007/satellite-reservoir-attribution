# SESSION_PROMPTS.md — Route B Implementation Prompts for Executor Models
## One copy-paste prompt per session · Sonnet 5 / Opus 4.8 routing · created 2026-07-12 (Session 016, planned by Fable 5)
### rev 2 — 2026-07-12: D-062 E-A-C verification protocol (triple extraction + reduced-scope human sign-off); independent-review fixes folded in (pre-named Gate-2 fallback paper, config pulled forward to S-02, S-24b thesis alignment added, realistic count 35–45, S-19 multi-session, prereg timing disclosure, dual request-instrument drafts in S-09)

> **What this file is.** The Route B plan lives in `RECOVERY_ROADMAP.md` (WHAT) and
> `EXECUTION_PLAYBOOK.md` + `PAPER_PRODUCTION_SOP.md` (HOW). This file is the third layer:
> the exact prompt Nishi pastes into Claude Code at the start of each session, so a
> lower-cost executor model stays on rails. The intelligence is in the planning docs —
> the prompt's job is to point the model at the right sections, pin the gotchas, and
> refuse it permission to improvise.
>
> **How to use.** Start a fresh Claude Code session, pick the model per the routing table,
> paste ONE prompt verbatim. CLAUDE.md loads automatically (session ritual included).
> Do not run two prompts in one session — each ends with a session-log commit.
> If a session ends mid-prompt (rate limit, failure), re-paste the same prompt next
> session; the ACCEPT tests make every step idempotent to re-check.

---

## 0. MODEL ROUTING — Sonnet 5 vs Opus 4.8

**Verdict: hybrid.** Sonnet 5 executes ~60% of sessions safely because the playbook
carries the judgment (every step has ACCEPT/ON-FAIL). Opus 4.8 is reserved for sessions
where the model must *design or judge*, not just execute — leakage reasoning, causal
design, geometry/datum resolution, hostile verification, and manuscript prose.

| Route to **Opus 4.8** when the session… | Route to **Sonnet 5** when the session… |
|---|---|
| resolves ambiguity the docs don't fully close (datum conflicts, survives/dead calls) | has a written spec + mechanical ACCEPT test |
| designs statistics (CV scheme, event study, GRACE forward model, prereg) | scrapes, refactors, digitizes, restructures |
| writes manuscript prose under the claims ladder | regenerates figures from an existing style module |
| runs the hostile SOP-V verification pass | runs fix-lists produced by a previous Opus session |

Per-session assignments are in the map below. Where marked "Sonnet 5 OK", Opus adds
little. Where marked "Opus 4.8", do not downgrade — these are exactly the failure
modes (B1–B4) that a weaker execution created the first time.

**Escalation rule for Sonnet sessions:** if any ACCEPT test fails twice, or the data
contradicts the prompt, STOP, write the discrepancy to SESSION_LOG, and end the session.
The retry happens on Opus. Never "fix" the ACCEPT criterion to pass.

---

## 1. SESSION MAP — 26 prompts, realistically 35–45 working sessions, Phase 0 → submission

| # | Phase | Session content | Model | Gate |
|---|---|---|---|---|
| S-01 | 0 | CWC PDF acquisition + E-A-C digitization (P0.1–P0.2) | Sonnet 5 | — |
| S-02 | 0 | EACCurve module + Stage-1 rebuild (P0.3–P0.4) | **Opus 4.8** | — |
| S-03 | 0 | GRACE units + PBIAS + fail-closed (P0.5, P0.8) | Sonnet 5 | — |
| S-04 | 0 | De-leak XGBoost CV (P0.6) | **Opus 4.8** | — |
| S-05 | 0 | CCM direction + clustering fix (P0.7) | Sonnet 5 | — |
| S-06 | 0 | R1 hygiene + "what survives" memo (P0.9–P0.10) | **Opus 4.8** | **Gate 1** |
| S-07 | 1 | CWC bulletin full-archive scrape | Sonnet 5 | — |
| S-08 | 1 | DVC annual-report extraction + X7 hydropower proxy | Sonnet 5 | — |
| S-09 | 1 | Exact-date S1 validation + X3 ICESat-2 | **Opus 4.8** | **Gate 2** |
| S-10 | 2 | Panchet re-run processing + rebuild | Sonnet 5 | — |
| S-11 | 2 | Mass-balance model implementation | **Opus 4.8** | — |
| S-12 | 2 | Closure-error budget + event validation | **Opus 4.8** | — |
| S-13 | 3 | config.yaml + Makefile + tests + CI (R2–R4) | Sonnet 5 | — |
| S-14 | 3 | X8 OSF preregistration (before any Phase-3 modeling) | **Opus 4.8** | — |
| S-15 | 3 | Nested rolling-origin CV + baselines rebuild | **Opus 4.8** | — |
| S-16 | 3 | X2 event-study causal analysis (THE core) | **Opus 4.8** | — |
| S-17 | 3 | GRACE rebuild: D2 design + X5 forward model | **Opus 4.8** | — |
| S-18 | 3b | X6 uncertainty budget + X4 global-product benchmark | Sonnet 5 | — |
| S-19 | 3b | X1 transferability test (3–5 non-DVC reservoirs; spans 2–3 working sessions) | Sonnet 5 | — |
| S-20 | 4 | Manuscript folder restructure + figure pipeline (SOP Part A/B) | Sonnet 5 | — |
| S-21 | 4 | Writing I: Methods + Results (SOP-W) | **Opus 4.8** | — |
| S-22 | 4 | Writing II: Intro/Discussion/Abstract + citations (D11) | **Opus 4.8** | — |
| S-23 | 4 | SOP-V hostile verification V1–V7 | **Opus 4.8** | — |
| S-24 | 4 | Fix cycle from S-23 report + V-W writing checks | Sonnet 5 | — |
| S-24b | 4 | Thesis alignment — rebuild thesis results chapters from v2 outputs (BIT Sindri deliverable) | Sonnet 5 | — |
| S-25 | 5 | Freeze → Zenodo DOI → EarthArXiv → submission package | Sonnet 5 | V8 |

**Count:** 26 planned prompts (10 Opus, 16 Sonnet). Realistic working-session count:
**35–45** — fix cycles, S-19 spanning 2–3 sessions, Sonnet→Opus escalations, GEE export
waits, and Nishi's 7th-semester/placement bandwidth Aug–Dec are all real. Expected
landing: submission **Jan–Feb 2027** (inside the roadmap's Dec 2026–Feb 2027 window;
Dec 2026 is the stretch case, not the plan). Phase 0 is the compressible part: with
daily Opus sessions and same-day verification turnarounds from Nishi, S-01→S-06 can
run in ~4–6 days.

**Human-only work not counted above (Nishi/Dr. Ray, no agent):** roadmap approval,
WRIS downloads, the DVC data-request decision (letter and/or RTI — drafts come from
S-09, humans decide and send), E-A-C reduced-scope verification per D-062 (disagreement
cells + anchors + 10-row sample, ~15 min), checking the DVC annual-report PDFs for dated
release events (~30 min, de-risks the X2 causal core — do this week), identifying and
inviting the external reviewer X9 by end of July, OSF account + prereg timestamp,
Zenodo OAuth, supervisor sign-offs (Gate 10), Nishi's own-voice revision pass.

**Pre-named fallback (Gate-2 fail):** if operational data is insufficient at Gate 2, the
salvage deliverable is the satellite-only validation/benchmark paper — exact-date S1
validation (S-09) + ICESat-2 (X3) + uncertainty budget (X6) + global-product benchmark
(X4) + transferability (X1) — which needs **no operational data**. S-09's Gate-2 memo
must assess it concretely, so a NO-GO re-scope meeting with Dr. Ray starts from an
option, not a blank page.

---

## 2. UNIVERSAL RULES (apply to every prompt; do not re-paste, they bind via CLAUDE.md + playbook §6)

1. Session start = CLAUDE.md ritual, then `EXECUTION_PLAYBOOK.md` §0 precedence map.
2. F-009→F-031 are PROVISIONAL (D-055). Never cite them as ground truth.
3. Never overwrite `data/processed/` without a dated backup copy.
4. New numbers → `*_v2.csv` alongside v1; the v1→v2 delta is itself a result.
5. Every claim written into any doc carries a reproduction command or file:line.
6. Vocabulary ban list (playbook SOP-V6) applies to ALL new public text.
7. Commit after each green ACCEPT: `phase<N>: <step>`. Session end = SESSION_LOG entry.
8. FINDINGS.md is written ONLY after Nishi confirms in-session.

---

## 3. THE PROMPTS

### ─── PHASE 0 (blocked until Nishi has said "roadmap approved / start Phase 0" — D-054) ───

#### S-01 — CWC report + E-A-C digitization · Sonnet 5

```
Execute Phase-0 steps P0.1 and P0.2 of journal/EXECUTION_PLAYBOOK.md exactly as written.

Scope: acquire the CWC 2020 Maithon sedimentation report PDF into data/external/, then
digitize its 2019 Elevation-Area-Capacity table to data/external/cwc_maithon_eac_2019.csv
per SOP-D-3 (columns elevation_m, area_km2, capacity_bcm; header comment block with source
URL, report title, page number, digitization date).

Non-negotiable anchors the digitized table MUST contain (from RECOVERY_ROADMAP §1.1 B1):
FRL = 150.88 m, dead storage 2019 = 0.0949 BCM, gross 2019 = 0.8739 BCM, FRL area = 85.95 km².
If the table you extract disagrees with these anchors, you have the wrong table or wrong
units — STOP and log it; do not adjust values to match.

Verification protocol (D-062 — MANDATORY; supersedes single-pass extraction and amends
SOP-D-3's "every row" requirement):
1. Extract the table via THREE independent channels: (a) PDF text layer
   (uv run python with pdfplumber/pdftotext), (b) the Read tool on the rendered page
   image(s), (c) OCR (tesseract) on the page image(s). Save the three raw extractions
   as separate CSVs in the scratchpad.
2. Three-way cell-by-cell diff → data/external/eac_extraction_diff.md: every cell where
   any channel disagrees, showing all three values.
3. Physics checks on the merged table: elevation, area, capacity each strictly monotone
   increasing; no increment jumping >3x its neighbors; the four anchors match exactly.
4. Human verification is REDUCED-SCOPE, not waived: present Nishi with (a) every
   disagreement cell, (b) the four anchor rows, (c) a random 10-row sample (seeded RNG,
   print the seed). He checks those against the PDF and signs off in a session message.
   The CSV is unusable by any later session until that sign-off is in SESSION_LOG.

Do not write src/ code this session. Do not touch data/processed/.

ACCEPT: PDF present and opens; all three extraction channels ran; diff file exists;
merged CSV passes every physics check; verification packet (disagreements + anchors +
seeded 10-row sample) presented to Nishi in the session's final message.
ON-FAIL (URL dead): search cwc.gov.in for "Maithon sedimentation"; if unfindable, stop and
ask Nishi to fetch it manually.
End: commit "phase0: P0.1-P0.2 eac digitization", write SESSION_LOG entry, state that
S-02 is blocked until Nishi's D-062 sign-off is recorded in the log.
```

#### S-02 — EACCurve module + Stage-1 rebuild · Opus 4.8

```
Precondition (verify before any code): Nishi has confirmed the digitized E-A-C rows from
S-01 in a session message, and data/external/cwc_maithon_eac_2019.csv exists. If not,
stop and say so.

Execute P0.3 and P0.4 of journal/EXECUTION_PLAYBOOK.md.

P0.3: create src/eac_curve.py — class EACCurve loading the CSV, PCHIP monotone
interpolation (scipy PchipInterpolator) for elevation→area, elevation→capacity, and
area→capacity via the inverted monotone area-elevation relation. Hard domain checks:
raise outside MDDL–FRL±buffer; never extrapolate silently. Write tests/test_eac_curve.py
reproducing the CWC anchors (dead 0.0949, gross 0.8739 BCM at FRL 150.88 m, area
85.95 km²) within 0.5%, plus a monotonicity property test.

P0.4: rebuild Maithon in src/01_storage_reconstruction.py — EACCurve.area_to_capacity()
replaces the power law; dead storage 0.0949 BCM; handle the CWC live/dead definition
explicitly (F-021 recorded an MDL-offset confusion — resolve it in code comments with
the arithmetic written out). Keep the old power-law path behind --legacy. Back up the old
output CSV to data/processed/backup_<date>/ first.

Judgment areas you own (this is why you're Opus): the elevation-datum question — the repo
has used 174.5 m, 155.5 m, and 146.3 m in different places (B1, F-016, F-021); the CWC
2019 table is the ONLY authority now, and every other datum reference in src/ must be
found (grep) and either corrected or dead-coded. Do not leave a mixed-datum pipeline.

Also this session (R2 pulled forward — B1 was a hardcoded-constant disaster, so constants
discipline starts HERE): create a minimal config.yaml + src/config.py holding every
constant this session introduces (FRL, dead storage, E-A-C CSV path, domain buffers),
each with a provenance comment. From this session on, no new geometry constant enters
any src/ file directly. S-13 completes the migration for legacy scripts.

ACCEPT: test_eac_curve.py green; new DVC_storage_timeseries CSV has Maithon max ≤ 0.8739
BCM; seasonal phase preserved (Oct peak, May–Jun trough per F-001, which remains valid);
old-vs-new comparison plot saved to figures/diag_stage1_rebuild.png; config.yaml exists
and grep shows no new hardcoded geometry constants in the session's src/ changes.
End: commit "phase0: P0.3-P0.4 stage1 rebuild on CWC curve", SESSION_LOG entry with the
old-vs-new summary stats (max, min, seasonal amplitude) as a table.
```

#### S-03 — GRACE units, PBIAS, fail-closed diagnostics · Sonnet 5

```
Execute P0.5 and P0.8 of journal/EXECUTION_PLAYBOOK.md. Three mechanical fixes with tests.

Fix 1 (B2, GRACE units): src/05_grace_reconciliation.py and
src/analysis_grace_deseasonalized.py currently z-standardize predictors (05:418-419), so
the reported β₂=3.84 is cm-per-SD, not cm/BCM (true raw ≈ 41.9 cm/BCM; SD(dS_anthro)=0.0917).
Fit BOTH raw-unit and standardized regressions; save both coefficient sets with explicit
unit labels; summary text must read "β₂ (raw) = X cm/BCM; β₂ (standardized) = Y cm per SD".
Write tests/test_coefficients.py: standardized→raw back-transformation identity on
synthetic data. Do NOT interpret the new numbers — that is S-06's job.

Fix 2 (D10): the pbias() function in src/03_xgboost_attribution.py computes normalized MAE.
Implement true PBIAS = Σ(sim−obs)/Σ(obs)×100. Audit every other metric function (NSE, KGE)
against its literature definition. Write tests/test_units.py with hand-computed fixtures.

Fix 3 (D12): rewrite src/critical_checks.py fail-closed — read-only; missing input ⇒
sys.exit(1) listing missing files; never writes MISSING rows; never prints CLEAR unless
every check ran. Write tests/test_failclosed.py.

ACCEPT: all three new test files green under `uv run pytest`; rerun of script 05 prints
both coefficient sets and raw≈standardized/SD within 1e-6; critical_checks.py in a tree
without data/raw exits nonzero with `git status --porcelain` empty.
Outputs to *_v2.csv, never overwrite v1.
End: commit "phase0: P0.5+P0.8 units pbias failclosed", SESSION_LOG entry.
```

#### S-04 — De-leak the XGBoost CV · Opus 4.8

```
Execute P0.6 of journal/EXECUTION_PLAYBOOK.md: remove all test-information leakage from
src/03_xgboost_attribution.py. Read RECOVERY_ROADMAP.md §1.1 B3 first — it lists the four
confirmed leaks with line numbers: (1) Optuna objective evaluates on the last 25% of the
FULL series, overlapping CV test folds; (2) every CV fold early-stops on its own test fold
(eval_set=[(X_test,y_test)]); (3) seasonal AET imputation is fit before splitting;
(4) SHAP comes from an in-sample final model.

Required design: Optuna validation slice ends BEFORE the first CV test date; early
stopping uses the last 20% of each TRAINING window; imputation fit inside each training
window only; SHAP from per-fold models on their own test rows only. Write
tests/test_no_leakage.py that instruments the split and asserts no test index reaches any
tuning / early-stopping / imputation-fitting set — the playbook calls this the single most
important test in the repo. Think adversarially: after implementing, actively search for
any remaining path test information can reach training (scaler fit? feature selection?
lag construction across the boundary?) and close or document each.

Save leak-free metrics to data/processed/xgb_cv_results_v2.csv (keep v1 — the delta is a
result for the paper's honesty narrative). Expect NSE to DROP, possibly below persistence
(F-024 context). Do not soften the numbers; do not tune until they look better. One
Optuna budget, pre-registered in your session log before running.

ACCEPT: test_no_leakage.py green; v2 metrics saved; a v1-vs-v2 comparison table in the
session log with zero editorializing.
End: commit "phase0: P0.6 de-leaked CV", SESSION_LOG entry.
```

#### S-05 — CCM direction + clustering validity · Sonnet 5

```
Execute P0.7 of journal/EXECUTION_PLAYBOOK.md. Two spec'd fixes; do not redesign anything
beyond the spec (Phase-3 S-16/S-17 will decide what survives into the paper).

Fix 1 (B4a, src/04_causal_inference.py:525-531): the code reads only out['cause:effect']
and interprets pyEDM direction backwards. Convention (write this as a comment block in the
code): in pyEDM/Sugihara CCM, cross-map skill of "X xmap Y" is evidence that Y DRIVES X.
Report BOTH directions pyEDM returns. Also fix the null: the current test compares
max-ρ-across-library-sizes to a surrogate null computed at the largest library size only —
build the surrogate null at EVERY library size; significance = real ρ exceeding the null
envelope consistently across library sizes, not max-vs-endpoint. Keep 999 surrogates.

Fix 2 (B4b, src/06_fingerprint_taxonomy.py:176-177): Ward linkage is invalid on
non-Euclidean DTW distances (SciPy docs). Replace with method='average' AND a separate
k-medoids (PAM) run on the same DTW matrix; report silhouettes for both.

Outputs to ccm_results_v2.csv and fingerprint_clusters_v2.csv. Produce a plain "what
changed" table (old direction/significance/silhouette vs new) in the session log — no
interpretation, S-06 does that.

ACCEPT: both scripts run green end-to-end; both pyEDM directions present in the v2 CSV
with the convention comment verbatim in code; both linkage variants reported; v1 files
untouched.
End: commit "phase0: P0.7 ccm direction + clustering", SESSION_LOG entry.
```

#### S-06 — Hygiene batch + "what survives" memo + Gate 1 · Opus 4.8

```
Two tasks: close Phase 0 and judge it.

Task 1 — execute P0.9 = SOP-R R1 hygiene batch from journal/EXECUTION_PLAYBOOK.md §2:
LICENSE (MIT, 2026 Nishi Kant Mandal), CITATION.cff, delete the 0-byte
src/03_xgboost_shap.py (verify wc -c = 0 first), README repairs per R1.4 (broken command,
scope claims, script map table), pyproject metadata, ReservoirWatch truth-in-labeling per
R1.6 (retitle "Research Demonstrator (retrospective data to Dec 2024)", hide Panchet,
delete the hard-coded confidence display and "automatic monthly updates" claim — no
redesign). Also SOP-D-1: data/raw/README.md manifest, one row per expected input.
Run the R1 ACCEPT tests as written.

Task 2 — execute P0.10: write journal/PHASE0_RESULTS.md. For EVERY finding F-009…F-031,
state its status under the corrected code: SURVIVES / CHANGED to <new value> / DEAD, with
v1-vs-v2 numbers side by side and the reproduction command for each v2 number. This is a
judgment task: for each CHANGED finding, say what the paper can still claim and what it
must stop claiming. Known expectations to check against (not force): B2 means "within 10%
of theory" is dead but the association may survive; B3 means NSE drops; B4 means the
Maithon→Durgapur CCM direction claim is unreliable as previously stated.

Then run Gate 1 (physical): does the rebuilt pipeline reproduce known CWC values (weekly
live storage within the F-021 definitional caveat, E-A-C anchors)? Write GO or NO-GO with
evidence. If NO-GO: diagnose, do not proceed, do not soften.

ACCEPT: R1 accept-tests green; PHASE0_RESULTS.md covers all of F-009…F-031 with commands;
Gate-1 verdict written with evidence.
End: commit "phase0: P0.9-P0.10 hygiene + what-survives", SESSION_LOG entry, and present
PHASE0_RESULTS.md to Nishi for review — Phase 1 does not start until he has read it.
```

### ─── PHASE 1 — Operational data acquisition (interleaves with Nishi's manual downloads) ───

#### S-07 — CWC weekly bulletin archive scrape · Sonnet 5

```
Phase-1 task (RECOVERY_ROADMAP §3 Phase 1): extend the CWC weekly bulletin scraping from
the existing 9 validation points to the FULL available archive for Maithon (and Panchet
if listed). Start from the lineage of src/07_cwc_validation.py — but first fix its known
column bug (D7 in the defect registry).

Steps: enumerate available bulletin PDFs on cwc.gov.in (reservoir storage bulletin
archive); download to data/raw/cwc_bulletins/ with a polite rate limit (2s between
requests); extract Maithon rows (level_m, live_storage_bcm, date) into
data/raw/cwc_maithon_weekly_full.csv with a source-PDF column per row; validate each
extracted level against the plausible range 130–151 m (FRL=150.88) and storage 0–0.8739
BCM — out-of-range rows go to a quarantine CSV, not silently dropped.

Do NOT compare against our storage series yet (that is Phase-2/3 work with the rebuilt
pipeline). This session is acquisition + parsing only.

ACCEPT: > 100 distinct weekly dates extracted (if the archive is shallower, log exactly
how many exist and why); zero rows outside physical range in the main CSV; every row
traceable to its source PDF; manifest updated (data/raw/README.md).
ON-FAIL (site blocks scraping): save what you got, document the block, draft the manual
download click-path for Nishi.
End: commit "phase1: cwc bulletin archive", SESSION_LOG entry with row counts by year.
```

#### S-08 — DVC annual reports + X7 hydropower release proxy · Sonnet 5

```
Phase-1 task + extension X7 (RECOVERY_ROADMAP §3): extract operational data from the DVC
annual report PDFs in data/raw/ (two already present: dvc_annual_report_2021-22.pdf,
2022-23.pdf; Nishi may have added more — check and list what exists).

Extract into data/raw/dvc_operations.csv: any tables of reservoir levels, releases,
flood-moderation events with dates, and hydropower generation (monthly/annual, by
station). Every row gets source_pdf and page columns. Flag low-confidence cells.

X7 implementation: src/hydropower_release_proxy.py — turbine discharge
Q ≈ Generation / (ρ·g·head·η), with head from the rebuilt storage series elevations
(EACCurve), η as an explicit config parameter (default 0.85, sensitivity 0.75–0.90), and
honest per-month uncertainty from the head range. Output
data/processed/release_proxy_v1.csv. This is insurance for Gate 2, not yet a result —
label the CSV header accordingly.

ACCEPT: dvc_operations.csv exists with traceable rows; proxy script runs green and its
output covers every month where generation data exists; unit test for the proxy formula
against one hand-computed month (tests/test_release_proxy.py).
End: commit "phase1: dvc reports + X7 proxy", SESSION_LOG entry listing which
operational quantities were actually found (this feeds the Gate-2 decision).
```

#### S-09 — Exact-date validation + X3 ICESat-2 + Gate 2 · Opus 4.8

```
Phase-1 validation core + extension X3 + the Gate-2 verdict. Read RECOVERY_ROADMAP §1.2
(the §6.8 pseudoreplication assessment) first — the old 9-point validation compared 7
weekly gauge readings against only 2 distinct satellite values; this session replaces it.

Task 1 — exact-date Sentinel-1 scene validation: write/extend the GEE script to extract
water area for INDIVIDUAL S1 scenes (not monthly composites) on 12–24 distinct dates
spanning monsoon + dry seasons and the full elevation range, chosen to coincide with CWC
weekly bulletin dates from S-07 (±2 days). Nishi runs the GEE export; you prepare the
script, the date list with matching rationale, and the analysis code that will compare
scene-level elevations (via EACCurve) against CWC gauge readings, clustering repeated
weekly observations properly (no pseudoreplication), reporting ALL-point error (no
post-hoc outlier exclusion in the headline).

Task 2 — X3: pull ICESat-2 ATL13 water surface heights over Maithon 2018–2024
(openaltimetry/earthdata; NASA Earthdata account exists). Build
data/raw/icesat2_maithon_atl13.csv (date, height_m, uncertainty, n_photons). Also check
Hydroweb for a catalogued Maithon/Panchet series. These are exact-date ±10 cm elevations
independent of the E-A-C curve.

Task 3 — Gate 2 assessment: with S-07/S-08 inventory + whatever WRIS data Nishi has
downloaded, write the GO/NO-GO: "distinct multi-season exact-date observations exist" and
"sufficient operational data for mass balance". Regardless of verdict, draft BOTH request
instruments (drafts only — humans decide and send, playbook §6 rule 6): (a) a data-request
letter from Dr. Ray on BIT Sindri letterhead to DVC asking for gate/spillway release logs
2017–2024, (b) the RTI application template as backstop. If NO-GO on operational data:
the memo must also concretely assess the pre-named fallback paper (§1 of this file) —
satellite-only validation/benchmark, needing no operational data — so the re-scope
meeting with Dr. Ray starts from an option, not a blank page.

ACCEPT: GEE script + date list ready for Nishi; ICESat-2 CSV non-empty or documented-empty
with the query trail; Gate-2 memo written with an explicit inventory table of operational
variables (levels ✓/✗, releases ✓/✗, generation ✓/✗, by period).
End: commit "phase1: exact-date validation + X3 + gate2", SESSION_LOG entry.
```

### ─── PHASE 2 — Physical mass balance ───

#### S-10 — Panchet rebuild · Sonnet 5

```
Phase-2 task (D8): restore Panchet. Precondition: Nishi has run the corrected-bbox GEE
export ([86.72, 23.52, 86.95, 23.68], script already updated per F-003) and the new CSV
is in data/raw/. If not present, stop and tell him exactly which script to run.

Steps: validate the new Panchet S1 series the same way F-001 validated Maithon — area
range vs known capacity (0.290 BCM design, run-of-river-adjacent dynamics), seasonal
phase, gap structure, and NO dry-season contamination spikes (the old failure mode:
canal-flood peaks in Mar–Jun, F-003). Then rebuild Panchet storage: if a CWC/official
E-A-C source exists for Panchet use it (check the CWC sedimentation atlas + WRIS), else
ALOS hypsometry WITH the honest uncertainty label, direction-only claims (D8 rule).
Durgapur stays direction-only per D8 regardless.

ACCEPT: validation plot figures/diag_panchet_v2.png shows physically plausible range and
seasonality; bimodality test on the area histogram passes (no contamination mode);
storage series added to the Stage-1 v2 output with provenance flags per reservoir
(cwc_curve / alos_curve / direction_only).
ON-FAIL (still contaminated): quarantine the data, log the geometry, stop — do not
hand-trim outliers.
End: commit "phase2: panchet rebuild", SESSION_LOG entry. If validation passed, note that
Nishi must confirm before any FINDINGS entry.
```

#### S-11 — Mass-balance model · Opus 4.8

```
Phase-2 core (RECOVERY_ROADMAP §3 Phase 2): implement the monthly water balance for
Maithon — dS/dt = Q_in − Q_release − E_lake + P_lake − seepage_residual.

Inputs (all should now exist): dS/dt from the rebuilt CWC-curve storage series (S-02);
Q_in from SCS-CN (existing skeleton, now testable against closure); Q_release from DVC
records and/or the X7 hydropower proxy (S-08) and/or WRIS outflow if Nishi's download has
it; E_lake from ERA5/MODIS over the water surface (area-weighted by monthly water area);
P_lake from CHIRPS over the surface. Seepage+error is the closing residual — named
"closure residual", never "anthropogenic".

Design ownership (why Opus): decide and document the term hierarchy — which terms are
measured, which modeled, which assumed; propagate per-term uncertainty (the E-A-C table
uncertainty from S-02, classifier area uncertainty, proxy η range from S-08) into a
per-month closure uncertainty. Where a term has two sources (release proxy vs records),
compute the balance both ways and report the spread.

Implementation: src/08_mass_balance.py (new canonical script), config-driven, outputs
data/processed/mass_balance_v1.csv with one column per term + closure + uncertainty.

ACCEPT: script green; every term has a unit test with a hand-computed month
(tests/test_mass_balance.py); closure residual and its uncertainty plotted
(figures/diag_mass_balance.png); no interpretation of whether closure is "good" yet.
End: commit "phase2: mass balance v1", SESSION_LOG entry with the term-source table.
```

#### S-12 — Closure budget + event validation · Opus 4.8

```
Phase-2 completion: judge the mass balance from S-11 and validate against documented
operational events.

Task 1 — closure-error budget: monthly closure error vs the <20% target (CLAUDE.md
Part 11, now actually testable). Stratify by season (monsoon/non-monsoon) and by
storage regime. Attribute dominant error sources per stratum using the per-term
uncertainties from S-11. If closure fails the target: diagnose which term (SCS-CN inflow
is the least-constrained candidate) and document what would fix it — do not tune CN
post-hoc to force closure; if you adjust CN at all it must be calibrated on a held-out
period and logged as a 🔒 DECISION.

Task 2 — event validation (S1-era only, 2019–2024): from S-08's dvc_operations.csv, take
every documented flood-moderation release and drawdown event; check the storage series
and balance terms show the right sign and approximate magnitude at those dates. Build the
event inventory table that S-16's event study will use: event_id, type (flood release /
Rabi canal opening / pre-monsoon drawdown), source document, start/end dates, expected
signature. Rabi canal openings at Durgapur (each Oct) count as scheduled events.

ACCEPT: closure budget table saved (data/processed/closure_budget.csv) + written honestly
in the session log; event inventory has ≥5 externally-dated events with sources (if fewer
exist, log the true count — S-16's viability depends on this number, flag it loudly);
Gate check: is the mass balance publication-grade? GO/NO-GO with evidence.
End: commit "phase2: closure + events", SESSION_LOG entry. Nishi reviews before Phase 3.
```

### ─── PHASE 3 — Modeling and attribution done right ───

#### S-13 — Config unification + Makefile + tests + CI · Sonnet 5

```
Execute SOP-R R2, R3, R4 from journal/EXECUTION_PLAYBOOK.md §2, in that order. This is
pure engineering with explicit ACCEPT greps — follow the spec exactly.

R2: complete the config.yaml begun in S-02 (geometry from the CWC rebuild WITH provenance comments;
ONE basin area value everywhere; bboxes, windows, baseline, CV spec, seeds, thresholds);
src/config.py with validated dataclass loading; refactor every src/*.py to import from
config. ACCEPT: `grep -rnE '174\.5|19600|23370|0\.185|1\.360' src/ --include='*.py'`
returns zero hits outside config files; pipeline runs green from config alone.

R3: Makefile targets data-check / stage1…stage6 / figures / paper / all / test / clean;
stages refuse to overwrite without FORCE=1; every script gets --input/--output args and a
main guard. ACCEPT: fresh-clone `make all` completes; running twice is idempotent.

R4: tests/ per the playbook list (test_units, test_eac_curve, test_no_leakage,
test_alignment, test_coefficients, test_failclosed — most exist from Phase 0; add
test_alignment and any missing), plus tests/fixtures/ mini-dataset (~50 rows per file,
no network) and .github/workflows/ci.yml (ubuntu, uv sync, make test).
ACCEPT: CI green on GitHub.

Do not change any statistical logic while refactoring — if outputs differ pre/post
refactor beyond float noise, that is a bug in the refactor. Verify with a before/after
hash of key CSVs.
End: commit per sub-step, SESSION_LOG entry.
```

#### S-14 — OSF preregistration (X8) · Opus 4.8

```
Extension X8 — MUST complete before any Phase-3 modeling runs (playbook §5 last
paragraph). Draft the OSF preregistration for the Phase-3 analysis.

Contents to pre-specify, drawing on RECOVERY_ROADMAP §3 Phase 3 + X2 + X5 and the S-12
event inventory: (1) the estimand — managed-release contribution to monthly storage
change, measured against operational records; (2) the X2 event-study design: event
windows, matched climate-only control windows, the matching criteria (season, antecedent
API6, storage level), the test statistic, and the minimum detectable effect given the
event count from S-12; (3) the nested rolling-origin CV spec (folds, tuning budget,
baselines: persistence, climatology, linear, GAM); (4) the GRACE analysis form — X5
forward model as primary, D2-corrected regression as secondary, with the placebo tests
named (neighboring region, placebo reservoir); (5) what gets reported regardless of
outcome (all pre-specified analyses, no garden of forking paths); (6) the exclusion rules
decided BEFORE seeing results; (7) an honest timing disclosure — Phases 0–2 (storage
rebuild, mass balance, event inventory) contacted the data before this prereg, so it
pre-specifies the Phase-3 ANALYSES only; state this plainly in the OSF form, because an
undisclosed post-data-contact prereg reads as theater and does more harm than none.

This is a design document — think hard about what a hostile reviewer would say the
degrees of freedom are, and pin each one. The project's reframing history (documented in
NOVELTY_IMPACT_REVIEW) is exactly why this exists.

Output: journal/OSF_PREREGISTRATION_DRAFT.md, ready for Nishi to paste into OSF after
Dr. Ray reviews. Include the metadata OSF asks for (title, contributors, license).

ACCEPT: every Phase-3 analysis session (S-15…S-19) can point to a pre-specified section;
no analysis parameter left "to be decided later" without an explicit named rule for
deciding it.
End: commit "phase3: X8 prereg draft", SESSION_LOG entry. Blocked-on-human: Nishi + Dr.
Ray review, then Nishi timestamps it on OSF BEFORE S-15 runs.
```

#### S-15 — Nested CV + baselines rebuild · Opus 4.8

```
Precondition: the OSF preregistration (S-14) is timestamped. Confirm with Nishi before
running — if not timestamped, stop.

Phase-3 modeling core (RECOVERY_ROADMAP §3 Phase 3): rebuild the predictive modeling on
the corrected foundation, exactly per the prereg. Nested rolling-origin CV with ALL
preprocessing in-fold (S-04's de-leaked machinery is the starting point; this session
extends it to the full nested design on the REBUILT storage series from Phase 0/2).
Baselines: persistence, climatology, linear regression, GAM. Uncertainty: blocked
bootstrap + observation-level Monte Carlo (propagating the S-11 per-term uncertainties).

The target variable and feature set are whatever the prereg says — do not re-open those
decisions. Report every model and baseline on identical folds with NSE/KGE/true-PBIAS,
overall AND regime-stratified (the old F-031 result showed aggregate NSE can mask
within-regime failure — that diagnostic is now standard output).

Outputs: data/processed/model_comparison_v2.csv, per-fold table, uncertainty bands CSV.
Figures: predicted-vs-observed and fold-stability diagnostics via the pubstyle module if
it exists (else matplotlib defaults, restyled in S-20).

ACCEPT: test_no_leakage.py still green against the new pipeline; every number in the
comparison table carries its reproduction command in the session log; results reported
without editorializing — if XGBoost loses to a GAM or persistence, that IS the result and
feeds the "what satellite-only monitoring can and cannot do" narrative.
End: commit "phase3: nested CV rebuild", SESSION_LOG entry.
```

#### S-16 — X2 event-study causal analysis · Opus 4.8

```
THE causal core of the Route-B paper (X2 replaced CCM/Granger per D-056). Execute exactly
per the preregistered design (S-14) using the event inventory from S-12.

Design recap: known-date operational interventions (Rabi canal openings, documented flood
releases, pre-monsoon drawdown deadlines) give externally-dated event windows; compare
storage behavior in those windows against matched climate-only control windows (matching
per prereg: season, antecedent API6, storage level). Scheduled interventions with
external dates = an identified estimand — the thing the old paper lacked.

Implementation: src/09_event_study.py, config-driven. For each event: effect size with
CI (per prereg statistic), placebo checks (same test on non-event windows), and a
per-event panel figure (storage + balance terms, event window shaded).

Discipline: n_events is small (5–10 expected). Report exact per-event results, the
pre-specified aggregate, and the minimum-detectable-effect honesty check from the prereg.
No post-hoc event additions or removals — if an event turns out to be misdated, document
it and rerun with it flagged, showing both.

Also this session: the corrected CCM (S-05 v2 output) gets its final disposition per the
roadmap's claim gate — it survives into the paper ONLY with operational ground truth to
anchor it; default is supplement or cut. Write the disposition memo paragraph.

ACCEPT: every prereg item for the event study has a corresponding output; effect table
data/processed/event_study_results.csv; per-event figures saved; disposition memo for
CCM/HMM/DTW written.
End: commit "phase3: X2 event study", SESSION_LOG entry. Present to Nishi — this is the
paper's centerpiece; he must be able to defend every event.
```

#### S-17 — GRACE done right: D2 design + X5 forward model · Opus 4.8

```
Rebuild the GRACE analysis per defect D2's design spec and extension X5, as preregistered.

X5 (primary form): forward-model the test — inject the known Maithon (+Panchet if valid)
mass series into GRACE mascon observation space with leakage-aware spatial handling
(RECOG-style; see the RECOG citation in the D11 mandatory list) and test consistency
between predicted and observed TWS signal. This replaces TWS-on-storage regression as the
headline. Per the novelty audit this is unreported for a ~1 BCM system — but the honest
prior is that a ~1 BCM signal in a ~90,000 km² mascon may be undetectable; a clean
"below detectability, and here is the detectability threshold we derive" is a publishable
negative result and must be written up with the same care as a positive one.

D2 (secondary form): the corrected regression — raw units (S-03 machinery), basin polygon
from HydroBASINS Lv8 (in the data registry) not a bounding box, gap flags retained instead
of blanket interpolation, neighboring-region and placebo-reservoir tests as preregistered.

Judgment call you own: whether the GRACE section survives into the paper at all
(roadmap: "kept only if it survives"). Write the keep/cut recommendation with evidence;
Nishi decides.

ACCEPT: forward-model consistency result with detectability threshold; corrected
regression with both unit conventions and placebos; keep/cut memo; all outputs *_v2/v3
CSVs with reproduction commands.
End: commit "phase3: GRACE forward model + corrected regression", SESSION_LOG entry.
```

#### S-18 — X6 uncertainty budget + X4 global-product benchmark · Sonnet 5

```
Two bounded Phase-3b extensions with clear specs.

X6 — end-to-end uncertainty budget table: propagate classifier → area → E-A-C curve →
storage → attribution. Sources now all exist: scene-level classifier accuracy (S-09),
area uncertainty, CWC table interpolation uncertainty (S-02 tests), balance term
uncertainties (S-11), model uncertainty (S-15 bootstrap). Output: one table
(data/processed/uncertainty_budget.csv + a manuscript-ready version) with per-stage
contribution and the total, plus one stacked figure. State explicitly what satellite-only
monitoring CANNOT resolve at each stage — that sentence structure is the point of X6.

X4 — benchmark vs global products: obtain the Maithon record from Zhao et al. 2023
(7,245-reservoir dataset, publicly archived) and GROWL; align to our monthly series and
CWC truth (S-07 full archive); report RMSE/bias/correlation for ours-vs-CWC,
Zhao-vs-CWC, GROWL-vs-CWC on identical months. No cherry-picking the comparison window —
use every month all sources cover.

ACCEPT: budget table sums correctly (components vs total, within rounding); benchmark
table on identical-month samples with n stated; both figures generated; if a global
product doesn't cover Maithon, document the lookup trail and report the ones that do.
End: commit "phase3b: X6 + X4", SESSION_LOG entry.
```

#### S-19 — X1 transferability test · Sonnet 5

```
Extension X1, the JoH→WRR lifter: run the rebuilt pipeline UNCHANGED on 3–5 non-DVC
Indian reservoirs that have WRIS daily storage (Nishi selects/downloads the WRIS truth
data; candidate criteria: >0.3 BCM capacity, S1 coverage 2017+, an official E-A-C or
WRIS-published capacity table, different climate zones preferred).

"Unchanged" is the claim, so it is the constraint: per-reservoir config entries
(bbox, E-A-C source, dates) are the ONLY thing that may differ — zero per-reservoir code
edits, zero threshold tuning. If the pipeline fails structurally on a reservoir, that
failure is a reported result with its diagnosis, not something to patch quietly.

Steps per reservoir: GEE water-area export (prepare scripts; Nishi runs), E-A-C
acquisition, storage reconstruction, validation vs WRIS daily truth. Output: the
cross-reservoir RMSE/bias/KGE table (data/processed/transferability_results.csv) and a
one-page-per-reservoir diagnostic figure set.

This prompt spans 2–3 working sessions by design (GEE exports land asynchronously):
session A prepares scripts, per-reservoir config entries, and the candidate table;
sessions B/C process exports as they arrive. Re-paste this prompt for each continuation —
the session map counts it once, the calendar should not.

ACCEPT: ≥3 reservoirs fully processed with validation against WRIS truth; the results
table has no excluded-after-the-fact reservoirs (every attempted reservoir appears, even
failures); config diff proves no code changes between reservoirs.
End: commit "phase3b: X1 transferability", SESSION_LOG entry.
```

### ─── PHASE 4 — Manuscript (rewritten from new results; NO number inherited) ───

#### S-20 — Manuscript restructure + figure pipeline · Sonnet 5

```
Execute journal/PAPER_PRODUCTION_SOP.md Part A (folder restructure) and Part B SOP-F
(figure pipeline) exactly as specified there.

Part A: migrate the manuscript monolith to sections/ per the spec; figures_src/ vs
figures_pub/ split. ACCEPT per the SOP: page-count-identical PDF rebuild from split
sections (D-060).

Part B: extract src/pubstyle.py from regenerate_figures_pub.py (Track 1); regenerate the
Route-B figure set fig01–08 per the SOP's figure plan from the v2/v3 data of Phase 3 —
NOT from any v1 data. Track 2 (draw.io) illustrations: create/update the .drawio sources
(D-059: draw.io mandated for all illustrations; Wong palette; fixed series-color mapping).
Submission format is PDF (Elsevier accepts EPS/PDF only, per SOP Part E); SVG/.drawio are
the committed sources.

Per-figure ACCEPT from the SOP: regenerates from current data via `make figures`;
pdffonts shows embedded fonts; CVD simulation check; caption drafted next to each figure
in sections/. The old figure defects in D16 (K=5 vs K=3, blank GRACE panel, endpoint-bar
"convergence", map rectangle caption) must be impossible now because every figure comes
from v2+ data — verify none of the old PNGs are referenced anywhere.

End: commit "phase4: restructure + figures", SESSION_LOG entry with the fig01–08
checklist table.
```

#### S-21 — Writing I: Methods + Results · Opus 4.8

```
Execute journal/PAPER_PRODUCTION_SOP.md Part C (SOP-W) for Methods and Results, figures
first. Governing rule from RECOVERY_ROADMAP Phase 4: NO number is inherited from the old
manuscript — every number comes from a v2+ CSV in data/processed/ and you record its
reproduction command in journal/number_trace_worksheet.md AS YOU WRITE (this becomes
SOP-V V1's input, saving S-23 a full pass).

Working title (roadmap): "Separating hydroclimatic inflow and managed releases in a
data-sparse Indian reservoir using Sentinel-1 and a satellite-constrained mass balance."

Methods: written against the code as it IS (V4 discipline — for each method sentence,
note file:line in the worksheet). Cover: data + E-A-C provenance, classifier + exact-date
validation (S-09), mass balance (S-11/12), preregistered event study (S-16), nested CV
(S-15), GRACE forward model (S-17), uncertainty budget (X6), transferability (X1).
Results: follow the two-stage drafting recipe in SOP-W (outline with key numbers →
prose); claims ladder discipline — every sentence at or below what its evidence supports.

Vocabulary ban list is live (SOP-V6 grep): causally attributable / causal independence /
anthropogenic residual / misattribut* / contaminat* / taxonomy / 100% / explainable AI.
The estimand language from the prereg replaces all of it.

ACCEPT: sections/methods.tex + sections/results.tex compile in the restructured build;
worksheet has an entry for every number and method sentence; ban-list grep returns zero
unjustified hits on the new sections.
End: commit "phase4: methods + results draft", SESSION_LOG entry.
```

#### S-22 — Writing II: Intro, Discussion, Abstract + citation audit · Opus 4.8

```
Complete the manuscript per PAPER_PRODUCTION_SOP.md Part C, then run the citation work
(defect D11).

Intro/Discussion positioning (from NOVELTY_IMPACT_REVIEW §2 — still valid per the
supersession banner): position against the closest priors honestly — Hou et al. 2022
(global reservoir climate-vs-management), Vu et al. 2022, Suresh 2024, Humphrey &
Gudmundsson 2019, Vanthof & Kelly 2020, Xie et al. 2022 (reservoir ops in GRACE — the
direct threat to the GRACE claim), Zhao et al. 2023, Cooley 2021, Yao 2025, RECOG,
Chen 2024, GROWL, plus the GERD literature (Abdelmohsen 2024, Wang 2011, Yi 2017) and
Turner 2021/Steyaert 2022. Every one of these enters references.bib DOI-verified and is
actually DISCUSSED where relevant, not citation-dumped.

Citation audit: for EVERY \cite key (old and new), resolve the DOI and confirm the landing
page matches both the bib entry and the claim it supports (V3 procedure from
EXECUTION_PLAYBOOK SOP-V). Known past failures to specifically re-check: Ji2023 DOI
(resolved to an unrelated isotope paper), Besseling2021 (unverifiable), Wada2017 (wrong
year's paper). Record each resolution in the worksheet.

Abstract + conclusions: claims-ladder discipline; abstract numbers only from the
worksheet. Also: Elsevier GenAI declaration with exact wording + placement per SOP
Part E, and the AI-assistance ledger entry (SOP-A).

ACCEPT: full manuscript compiles; every bib entry DOI-resolved with a worksheet line;
positioning paragraphs exist for Xie 2022 and Hou 2022 specifically; declarations section
complete; ban-list grep zero unjustified hits manuscript-wide.
End: commit "phase4: full draft + citations", SESSION_LOG entry.
```

#### S-23 — SOP-V hostile verification · Opus 4.8

```
Run the COMPLETE SOP-V from journal/EXECUTION_PLAYBOOK.md §1 against the full manuscript:
V1 number tracing (the S-21/S-22 worksheet is your input — verify it, don't trust it),
V2 units audit (write the unit chain for every coefficient), V3 citation integrity
(re-resolve; do not reuse S-22's session as evidence), V4 code–text consistency
(claim → file:line for every methods sentence), V5 figure–data consistency (regenerate
every figure, diff against manuscript copies), V6 claim–evidence alignment (the hostile
pass: for every abstract/conclusion claim, the strongest-skeptic question and the paper's
answer with section reference; ban-list grep), V7 statistical reproduction (fresh clone
to the scratchpad, `make all`, compare headline tables).

Mindset: you are the reviewer trying to kill this paper. The project's history includes
fabricated table rows, stale numbers, mislabeled units, and a wrong-direction causal
claim — all found AFTER they were written. Assume the current draft contains at least
one such defect and find it.

Output: journal/verification_report_<date>.md — every check PASS/FAIL with evidence and
reproduction commands. Do NOT fix anything in this session (separation of duties: S-24
fixes). Untraceable numbers get listed for DELETION, not correction.

ACCEPT: report covers all of V1–V7 with zero checks skipped; every FAIL has an exact
location and a specified fix; V8 (human sign-offs) listed as the open checklist for
Nishi/Dr. Ray.
End: commit "phase4: SOP-V report", SESSION_LOG entry stating the FAIL count plainly.
```

#### S-24 — Verification fix cycle · Sonnet 5

```
Input: journal/verification_report_<date>.md from S-23. Execute every specified fix,
exactly as specified — this session has no design authority. If a fix turns out to be
ambiguous or the specified fix contradicts the data when you attempt it, SKIP it, mark it
BLOCKED in the report, and it returns to Opus/Nishi; do not improvise a resolution.

Order: V1 deletions/corrections first (numbers), then V2 unit-labeling fixes, V3 bib
fixes, V4 text-to-match-code edits, V5 figure regenerations, V6 rewordings. After all
fixes: rerun the mechanical checks yourself (ban-list grep, number spot-traces on every
edited sentence, full rebuild, `make test`, `make figures`).

Then run PAPER_PRODUCTION_SOP.md Part D (SOP-WV V-W1–V-W8 writing verification) on the
fixed manuscript, including the SOP's flagged submission-day recheck items (the AGU
figure-page detail marked UNVERIFIED in Part E — recheck only if AGU/WRR is the live
target).

ACCEPT: every S-23 FAIL is either FIXED (with evidence) or BLOCKED (with reason);
manuscript compiles; make test green; a clean delta summary of every change made.
End: commit "phase4: verification fixes", SESSION_LOG entry. Hand to Nishi for the V8
human pass: his own-voice revision, Dr. Ray sign-off, external reviewer (X9) if arranged.
```

#### S-24b — Thesis alignment (BIT Sindri deliverable) · Sonnet 5

```
The B.Tech thesis was compiled in the Session-012 era on results now superseded per
D-055: old Maithon geometry (B1), leaked CV metrics (B3), per-SD GRACE coefficient
labeled cm/BCM (B2), inverted CCM direction (B4). It must not be defended or archived
at BIT Sindri carrying those numbers.

Locate it first (`git ls-files | grep -i thesis`). Then rebuild the thesis results
chapters from the SAME v2+ outputs and number-trace worksheet the manuscript uses
(S-21/S-22 products). Reuse manuscript sections where the thesis structure allows;
the thesis may keep more explanatory background material, but every NUMBER comes from
the worksheet with its reproduction command. Run the vocabulary ban-list grep and a
V1-style number spot-trace on every rebuilt chapter.

If a copy of the old thesis has already been submitted to the department, draft an
errata sheet and surface the question to Nishi explicitly — whether and how to file it
is his and Dr. Ray's call, but the question must not be left unasked.

ACCEPT: thesis compiles; zero numbers inherited from the old thesis (spot-trace
evidence in the session log); ban-list grep clean; errata question put to Nishi in the
session's final message.
End: commit "phase4: thesis alignment", SESSION_LOG entry.
```

### ─── PHASE 5 — Release + submit ───

#### S-25 — Freeze, archive, preprint, submit · Sonnet 5

```
Precondition (verify each, stop if any missing): V8 sign-offs done — Nishi's own-voice
revision committed under his authorship, Dr. Ray's approval recorded, external review
(X9) closed or explicitly waived by Nishi, AI disclosure in the declarations section.

Execute EXECUTION_PLAYBOOK.md SOP-D-4 + RECOVERY_ROADMAP §4 Phase-5 items:
1. Results freeze: final `make all` + `make test` green; tag v1.0.0.
2. Zenodo: Nishi does the GitHub-Zenodo OAuth click-through (give him the exact steps);
   verify the minted DOI resolves; check the archive contents per SOP-D-4 (code, processed
   data CC-BY, digitized E-A-C table with CWC provenance note, retrieval scripts, README
   renders); spot-check `make test` passes from the downloaded zip.
3. Manuscript: paste the DOI into Data Availability and CITATION.cff;
   `grep -c 'to be assigned' reports/manuscript/**/*.tex` must be 0.
4. EarthArXiv preprint package: PDF + metadata + license choice; prepare, Nishi uploads.
5. Journal submission package for the venue ladder (RECOVERY_ROADMAP Phase 5: Journal of
   Hydrology subscription route first; Water Resources Management second; JISRS fallback;
   if X1/X2 landed strongly, WRR-with-waiver may be the primary — Nishi + Dr. Ray's call,
   confirm which before packaging): cover letter draft, highlights, declarations,
   suggested reviewers list drafted for Nishi to vet, exact figure formats per SOP Part E
   for the chosen venue.
6. Calendar reminders in the session log: EGU Roland Schlich waiver Dec 1 2026; ISRS
   abstract deadline (verify current date on the ISRS site).

ACCEPT: DOI resolves; zip's make test passes; zero placeholders; submission package
complete for the confirmed venue; SESSION_LOG final entry written.
End: commit "phase5: release + submission package". The rest is human: Nishi clicks
submit.
```

---

## 4. MAINTENANCE OF THIS FILE

- When a session deviates from its prompt (they will), the NEXT session's prompt gets a
  one-line "Context update:" prefix written during the session-end ritual — do not let
  drift accumulate silently.
- If a Gate fails (1: geometry, 2: operational data), sessions after it are void until
  the re-plan; re-planning is a Fable/Opus session, not a prompt from this file.
- This file plans sessions S-01…S-25. It does NOT override RECOVERY_ROADMAP or
  EXECUTION_PLAYBOOK — on any conflict, those win and this file gets corrected
  (precedence per D-058, with this file below all four CURRENT documents).
