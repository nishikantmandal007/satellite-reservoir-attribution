# EXECUTION PLAYBOOK — DVC Reservoir Attribution, Route B
## Step-by-step SOPs for an executing agent (written for Claude Opus 4.8 / any capable agent)
### Created 2026-07-11 (Session 015) | This is the OPERATIONAL document — the roadmap says WHAT, this says exactly HOW

> **READ THIS FIRST, EXECUTOR.** You are working in `/home/stark007/dvc-research`
> (Ubuntu 24.04, uv + Python 3.11 — run everything as `uv run python ...`).
> This playbook assumes zero memory of prior sessions. Follow steps in order.
> Every step has an **ACCEPT** test. If an ACCEPT test fails, STOP that track,
> record the failure in `journal/SESSION_LOG.md`, and either follow the step's
> **ON-FAIL** branch or ask Nishi. Never mark a step done without its ACCEPT passing.
> Never write to `journal/FINDINGS.md` without Nishi's explicit confirmation.

---

## 0. DOCUMENT MAP & PRECEDENCE — resolve conflicts before acting

Read in this order at session start (after the CLAUDE.md ritual):

| Order | File | Role | Status |
|---|---|---|---|
| 1 | `journal/RECOVERY_ROADMAP.md` | **AUTHORITATIVE plan** — Route B phases, defect registry (D1–D16), extensions (X1–X9), gates | CURRENT |
| 2 | `journal/EXECUTION_PLAYBOOK.md` (this file) | **AUTHORITATIVE procedures** — the how, with commands and ACCEPT tests | CURRENT |
| 3 | `journal/PAPER_PRODUCTION_SOP.md` | **AUTHORITATIVE production procedures** — manuscript folder structure (Part A), figures/illustrations SOP-F (SVG/draw.io source → PDF submission, Part B), writing SOP-W (Part C), writing verification SOP-WV (Part D), verified journal specs (Part E). Executes in Phase 4; fig01–03 may start earlier as data lands | CURRENT |
| 4 | `journal/codex_review.md` | External audit that triggered Route B; §6 findings verified in Session 015 | CURRENT (reference) |
| 5 | `journal/NOVELTY_IMPACT_REVIEW.md` | Novelty verdicts, mandatory citations, portfolio, title principles | PARTIALLY SUPERSEDED — §2 citations/§5 portfolio/title principles remain valid; its submission timeline does NOT |
| 6 | `journal/PROJECT_PROSPECT.md` | Session-013 assessment | LARGELY SUPERSEDED — August-submission plan is CANCELLED (D-053); venue-cost research and EGU/ISRS conference facts remain valid |
| 7 | `journal/FINDINGS.md` | Append-only results registry | F-009→F-031 are PROVISIONAL per D-055 (do not cite as ground truth until Phase-0 rebuild); F-001–F-005 remain valid |

**Precedence rule:** RECOVERY_ROADMAP + this playbook > NOVELTY_IMPACT_REVIEW > PROJECT_PROSPECT.
On any numeric conflict, recompute from `data/processed/` — never trust a document over the data.

**Standing gate:** Phase-0 code changes require Nishi's explicit "roadmap approved / start Phase 0"
in a user message (D-054). Documentation-only work (this playbook's SOP-0 hygiene items marked
DOC-SAFE) may proceed when asked.

---

## 1. SOP-V — FINAL PAPER VERIFICATION (run before ANY preprint or submission)

Purpose: guarantee the manuscript survives hostile arithmetic, citation checks, and
code-text consistency. Run the whole SOP; produce `journal/verification_report_<date>.md`
listing every check with PASS/FAIL and evidence. ALL checks must PASS before upload anywhere.

### V1 — Number tracing (every quantitative claim)
1. Extract every number from the manuscript:
   `grep -oE '[0-9]+\.[0-9]+|[0-9]+\s*(BCM|km|m|cm|%)' reports/manuscript/manuscript.tex`
   plus a manual read of abstract, results, conclusions, table cells, figure captions.
2. For each number, record in the report: value → source file in `data/processed/` (or
   FINDINGS entry) → the command that reproduces it, e.g.
   `uv run python -c "import pandas as pd; print(pd.read_csv('data/processed/<file>.csv')['<col>'].mean())"`
3. **ACCEPT:** 100% of numbers trace; any untraceable number is DELETED from the manuscript
   (not "fixed to something plausible").
4. Known past failures this catches (do not repeat them): stale mean −0.029 vs true −0.014;
   β₁ p=0.573 vs file 0.696; "OLS SE 1.22" that was actually the DW statistic; fabricated
   validation-table rows (Session 012); standardized β labeled cm/BCM (Session 015).

### V2 — Units audit
1. For every coefficient/regression output: open the producing script; confirm whether inputs
   were standardized, converted (cm↔BCM uses 0.196 BCM/cm ONLY if area=19,600 km² —
   one basin area must be used everywhere, from `config.yaml` after Phase 3), or logged.
2. Write the unit chain in the report: raw units → transformations → reported units.
3. **ACCEPT:** every reported coefficient's unit chain is written down and a reviewer could
   re-derive it; standardized and raw coefficients are reported side-by-side where both exist.

### V3 — Citation integrity
1. For each `\cite` key: extract DOI/title from `references.bib`; resolve DOI via
   `curl -sI https://doi.org/<doi> | grep -i location` or WebFetch; confirm the landing page
   title matches the bib title AND the claim the citation supports in the text.
2. **ACCEPT:** every DOI resolves to the cited work; every methods sentence naming a technique
   (Otsu, Newey-West, HMM, KGE, Granger, DTW, CCM) carries a citation; the 10 mandatory
   additions from NOVELTY_IMPACT_REVIEW §2 + Codex's additions (Xie 2022, Zhao 2023,
   Cooley 2021, Yao 2025, RECOG, Chen 2024, GROWL) are present and discussed.
3. Known past failures: Ji2023 DOI resolved to an unrelated isotope paper; Besseling2021
   unverifiable; Wada2017 key contained the 2014 ESD paper.

### V4 — Code–text consistency
1. For every methods sentence, locate the implementing code line; record `claim → file:line`.
2. **ACCEPT:** no contradiction. Known past failure: text claimed per-scene refined-Lee
   filtering; the GEE script had removed it and ran Otsu on monthly composites.

### V5 — Figure–data consistency
1. For each figure: identify the generating function in `src/regenerate_figures_pub.py` (or
   successor), re-run it, diff the output against the manuscript copy (visual + file hash).
2. **ACCEPT:** every figure regenerates from current data; captions match content (past
   failures: K=5 figure vs K=3 text; blank GRACE residual panel; "Bootstrap CI" caption
   for a seed-sensitivity band; map rectangle vs "basin boundary" caption).

### V6 — Claim–evidence alignment (the hostile pass)
1. List every claim sentence in abstract + conclusions. For each: strongest-skeptic question
   ("what else could produce this?"), and the paper's answer with section reference.
2. Vocabulary ban list (from codex_review §4, enforced by grep):
   `grep -inE 'causally attributable|causal independence|anthropogenic residual|misattribut|contaminat|taxonomy|100%|explainable AI' reports/manuscript/manuscript.tex`
   — every hit must be justified in the report or reworded.
3. **ACCEPT:** zero unjustified ban-list hits; every abstract claim has an identified estimand
   or is worded as association/description.

### V7 — Statistical reproduction
1. Fresh-clone reproduction: `git clone <repo> /tmp/claude-1000/.../repro-test && cd repro-test && make all`
   (after SOP-R gives us `make all`); compare key outputs to manuscript tables via the
   regression-test fixtures in `tests/`.
2. **ACCEPT:** headline table values reproduce to reported precision on a clean clone.

### V8 — Human sign-offs (cannot be done by the agent)
- [ ] Nishi has read every sentence and can defend it verbally
- [ ] Dr. Ray approves claims, venue, authorship, data release, AI disclosure (Gate 10)
- [ ] External reviewer (X9) has returned comments and blocking items are closed in writing
- [ ] AI-use disclosure present in the declarations section with the journal's exact wording

---

## 2. SOP-R — CODE REPO ALIGNMENT (consistent + reproducible)

Target end-state: a stranger clones the repo, reads README, runs one command, gets the
paper's tables and figures. Execute in this order; each step is atomic and committable.

### R1 — Hygiene batch (DOC-SAFE; may run before Phase-0 approval if Nishi asks)
1. `LICENSE` at repo root: MIT, copyright "2026 Nishi Kant Mandal".
2. `CITATION.cff`: cff-version 1.2.0; authors Mandal (ORCID when registered), Ray;
   title = repo name; add `preferred-citation` once the preprint DOI exists.
3. Delete `src/03_xgboost_shap.py` (verify first: `wc -c src/03_xgboost_shap.py` must show 0).
4. `README.md` fixes: replace the broken `03_xgboost_shap.py` command with
   `uv run python src/03_xgboost_attribution.py`; correct scope claims (two reservoirs
   quantitative, 2017–2024 primary window); replace "explains 57%" with the honest framing;
   add a "Script map" table declaring canonical scripts
   (03_xgboost_attribution.py, 04_causal_inference.py primary; 04_residual_diagnostics.py,
   analysis_*.py, integrity_check_*.py = auxiliary audits).
5. `pyproject.toml`: real description; authors; keywords.
6. `reservoir_watch/app.py` truth-in-labeling: title suffix "— Research Demonstrator
   (retrospective data to Dec 2024)"; remove/hide Panchet from the reservoir selector;
   delete the hard-coded 0.70–0.82 "confidence" display; remove the "automatic monthly
   updates" sidebar claim. Do NOT redesign the app now.
7. **ACCEPT R1:** `uv run python -c "import pathlib; assert pathlib.Path('LICENSE').exists() and pathlib.Path('CITATION.cff').exists()"`;
   README contains no reference to 03_xgboost_shap.py; grep for "57%"/"three DVC reservoirs"
   in README returns nothing; app renders (see `run` instructions) without Panchet.

### R2 — Configuration unification (Phase 0/3)
1. Create `config.yaml` at repo root — single source for: reservoir geometry (post-CWC-rebuild
   values WITH provenance comments), basin/catchment areas (ONE value, used everywhere),
   bounding boxes, date windows, baseline period, CV fold spec, random seeds, thresholds.
2. Add `src/config.py`: `load_config()` returning a validated dataclass; fail loudly on
   missing keys.
3. Refactor every `src/*.py` to import from config; delete the fit_av_params→01 manual
   copy step (01 reads the AV table file path from config).
4. **ACCEPT R2:** `grep -rnE '174\.5|19600|23370|0\.185|1\.360' src/ --include='*.py'`
   returns ZERO hits outside `config.py`/`config.yaml` (all constants centralized);
   full pipeline runs green from config alone.

### R3 — One-command workflow (Phase 3)
1. `Makefile` targets: `data-check` (validate raw manifest presence + checksums),
   `stage1` … `stage6`, `figures`, `paper` (latexmk), `all`, `test`, `clean`.
   Each stage writes to `data/processed/` and refuses to overwrite unless `FORCE=1`
   (implements the CLAUDE.md backup rule).
2. Every script gets `--input/--output` args (no hidden cwd assumptions) and a
   `if __name__ == '__main__'` guard.
3. **ACCEPT R3:** on a fresh clone with raw data present: `make all` completes;
   `make all` twice is idempotent; `make test` green.

### R4 — Tests + CI (Phase 3)
Create `tests/` with, at minimum:
- `test_units.py`: BCM↔cm↔km² conversions; PBIAS/NSE/KGE against hand-computed fixtures
  (kills the pbias-is-actually-nMAE class of bug, D10)
- `test_eac_curve.py`: interpolated CWC curve reproduces the CWC 2019 anchor rows
  (dead 0.0949 BCM, gross 0.8739 BCM at FRL 150.88 m, area 85.95 km²) within 0.5%
- `test_no_leakage.py`: instrument the CV split; assert no test index appears in any
  tuning/early-stopping/imputation-fitting set (D3 tripwire — this test is the single
  most important one in the repo)
- `test_alignment.py`: all merged monthly series share identical DatetimeIndex, no
  silent NaN-fill
- `test_coefficients.py`: standardized→raw back-transformation identity on synthetic data (D2)
- `test_failclosed.py`: `critical_checks.py` exits nonzero and writes nothing when inputs
  are missing (D12)
CI: `.github/workflows/ci.yml` — ubuntu, `uv sync`, `make test` on a committed
`tests/fixtures/` mini-dataset (~50 rows per file, no network).
**ACCEPT R4:** CI green on GitHub on a commit that touches src/.

### R5 — Diagnostics fail closed (Phase 0)
Rewrite `critical_checks.py`: read-only; missing input ⇒ `sys.exit(1)` with an explicit
list of missing files; never writes MISSING rows; never prints CLEAR unless every check ran.
**ACCEPT R5:** run it in a tree with `data/raw` absent → nonzero exit, zero files modified
(`git status --porcelain` empty).

---

## 3. SOP-D — DATASET RELEASE

### D-1 — Raw data manifest (Phase 0, DOC-SAFE)
Create `data/raw/README.md`: one table row per expected input —
`filename | source (URL/GEE asset id) | retrieval method (script or click-path) | date acquired | version | columns+units | license | sha256 (if redistributable)`.
Cover: the two GEE water-area CSVs, DVC_drivers/ exports (6), nino34, iod_dmi, GRACE mascon
file, CWC bulletin PDFs, DVC annual report PDFs, CartoDEM tiles, the CWC 2020 sedimentation
report PDF (URL in codex_review §16). Mark each REDISTRIBUTABLE / RETRIEVAL-ONLY.
**ACCEPT:** a reader could re-acquire every input without asking questions; `make data-check`
validates presence + checksums of redistributables.

### D-2 — Data dictionary (Phase 3)
`data/processed/DATA_DICTIONARY.md`: for each of the CSVs actually used by the paper —
every column: name, unit, definition, producing script, valid range. Delete or move to
`data/processed/deprecated/` any CSV no longer produced by the pipeline (the current 27
include superseded artifacts — decide per file by checking which script writes it).
**ACCEPT:** every CSV in `data/processed/` is either documented or in deprecated/.

### D-3 — The digitized CWC 2019 E-A-C table (Phase 0 — this file is a first-class output)
`data/external/cwc_maithon_eac_2019.csv`: columns `elevation_m, area_km2, capacity_bcm`
exactly as printed in the CWC 2020 report table, plus a header comment block: source URL,
report title, page number, digitization date, digitizer.
Human verification per 🔒 D-062 (2026-07-12, amends the original "every row" rule): the
agent performs THREE independent extractions (PDF text layer, page-image read, OCR),
a three-way cell diff, and physics checks (monotonicity, increment sanity, the four CWC
anchors); Nishi verifies against the PDF only (a) every disagreement cell, (b) the four
anchor rows, (c) a seeded random 10-row sample. Full protocol: SESSION_PROMPTS.md S-01.
**ACCEPT:** D-062 verification packet confirmed by Nishi in a session message;
`test_eac_curve.py` anchors pass.

### D-4 — Licensing & archival (Phase 5, only after results freeze)
1. `data/LICENSE` = CC-BY-4.0 (covers processed data + digitized table with attribution
   note to CWC as the underlying source).
2. GitHub → Settings → link Zenodo integration (Nishi does the OAuth click-through).
3. Tag `v1.0.0` on the frozen commit → Zenodo mints DOI → paste DOI into manuscript Data
   Availability (replacing the placeholder) and CITATION.cff.
4. Zenodo record contents check: code, processed data, E-A-C table, retrieval scripts,
   README renders correctly.
**ACCEPT:** the DOI resolves; the archive's `make test` passes when downloaded as a zip
(spot-check); manuscript contains no "[repository URL to be assigned]" placeholder
(`grep -c 'to be assigned' reports/manuscript/manuscript.tex` = 0).

---

## 4. SOP-A — AI-ASSISTANCE COMPLIANCE (operationalizes D-057)

1. **Ledger:** maintain `journal/AI_ASSISTANCE_LOG.md` — one line per work product:
   `date | artifact | AI role (drafting/code/analysis) | human verification performed`.
   The verification column must name the SOP-V check or test that validated it.
2. **Disclosure text** (adapt to the journal's current required wording at submission):
   > During the preparation of this work the authors used Claude (Anthropic) to assist with
   > code development, data analysis, and manuscript drafting. The authors reviewed, verified,
   > and edited all content and take full responsibility for the integrity of the work.
3. **Human-ownership requirements before submission:** Nishi performs a full own-voice
   revision pass on the manuscript (tracked as a commit authored by him); Nishi can answer,
   without notes, "why this method / why this number" for every section (rehearse with
   Dr. Ray); reviewer-response letters are drafted by Nishi first, AI-polished second.
4. **Hard rules:** no undisclosed AI use; no AI-generated citation enters the bib without V3
   resolution; no AI-generated number enters the text without V1 tracing. These three rules
   are exactly the failure modes that get AI-assisted papers retracted.

---

## 5. PHASE-0 RUNBOOK (execute ONLY after Nishi says "roadmap approved / start Phase 0")

Ordered, atomic steps. Commit after each green ACCEPT with message `phase0: <step>`.

**P0.1 — Acquire the CWC report.** Download
`https://cwc.gov.in/sites/default/files/sedimentation-assessment-maithon-reservoir-jharkhand-through-remote-sensing-may-2020.pdf`
to `data/external/`. ON-FAIL (URL dead): search cwc.gov.in for "Maithon sedimentation";
fall back to asking Nishi to fetch it. ACCEPT: PDF opens; contains the 2019 E-A-C table.

**P0.2 — Digitize the E-A-C table** per SOP-D-3 (Read tool on the PDF pages; build the CSV;
flag every low-confidence cell for Nishi). ACCEPT: SOP-D-3 ACCEPT.

**P0.3 — New curve module.** `src/eac_curve.py`: `class EACCurve` loading the CSV, PCHIP
monotone interpolation (scipy.interpolate.PchipInterpolator) for elevation→area,
elevation→capacity, area→capacity (via inverted monotone area-elevation), with hard
domain checks (raise outside MDDL–FRL±buffer, never extrapolate silently).
ACCEPT: `test_eac_curve.py` anchors + monotonicity property test pass.

**P0.4 — Rebuild Stage 1.** Modify `src/01_storage_reconstruction.py`: Maithon volume via
`EACCurve.area_to_capacity()` replacing the power law; dead storage 0.0949 BCM (from config);
CWC live/dead definitions handled explicitly (document the MDL offset from F-021 in code
comments); keep the old power-law path behind `--legacy` for the sensitivity comparison;
back up the old output CSV to `data/processed/backup_<date>/` before writing (CLAUDE.md rule).
ACCEPT: new `DVC_storage_timeseries_2002_2024.csv` produced; Maithon series max ≤ CWC gross
0.8739 BCM; seasonal phase (Oct peak, May–Jun trough per F-001) preserved; comparison plot
old-vs-new saved to `figures/diag_stage1_rebuild.png`.

**P0.5 — Fix B2 (GRACE units).** In `src/05_grace_reconciliation.py`: fit BOTH raw-unit and
standardized regressions; print/save both coefficient sets with explicit unit labels; the
summary text must state "β₂ (raw) = X cm/BCM; β₂ (standardized) = Y cm per SD". Same for
`analysis_grace_deseasonalized.py`. ACCEPT: `test_coefficients.py` passes; rerun output shows
raw β₂ ≈ standardized/SD within 1e-6 on the same data.

**P0.6 — Fix B3 (leakage).** In `src/03_xgboost_attribution.py`: Optuna validation slice must
end BEFORE the first CV test date; early stopping uses the last 20% OF THE TRAINING WINDOW,
never the test fold; AET seasonal imputation fit inside each training window only; SHAP from
per-fold models on their own test rows. ACCEPT: `test_no_leakage.py` passes; new leak-free
metrics saved to `data/processed/xgb_cv_results_v2.csv` (do not overwrite v1 — the delta IS
a result for the paper's honesty narrative).

**P0.7 — Fix B4 (CCM + Ward).** `src/04_causal_inference.py`: report both pyEDM directions
with a comment block stating the convention ("skill of X-xmap-Y is evidence Y→X"); build the
surrogate null at EVERY library size; significance = real ρ exceeding the null envelope
consistently, not max-vs-endpoint. `src/06_fingerprint_taxonomy.py`: replace Ward with
`method='average'` AND a k-medoids (PAM) run; report both. ACCEPT: scripts run green;
outputs to `*_v2.csv`; a "what survives" comparison table is produced.

**P0.8 — D10 + D12.** True PBIAS implementation (Σ(sim−obs)/Σobs×100); `critical_checks.py`
fail-closed rewrite. ACCEPT: `test_units.py`, `test_failclosed.py` pass.

**P0.9 — R1 hygiene batch** (if not already done). ACCEPT: R1 ACCEPT.

**P0.10 — The "what survives" memo.** Write `journal/PHASE0_RESULTS.md`: for each finding
F-009…F-031, its status under corrected code (SURVIVES / CHANGED to <new value> / DEAD),
with the v1-vs-v2 numbers side by side. Append a Session entry. Present to Nishi.
**GATE 1 check (physical):** CWC values reproduce → GO to Phase 1; otherwise STOP and diagnose.

Phases 1–5 procedures: follow `RECOVERY_ROADMAP.md` §3 with the same discipline
(one ACCEPT per task, session-log every session, FINDINGS only on Nishi's confirmation).
Extensions X1–X9 execute inside their assigned phases; X2's event-study design must be
specified in the OSF preregistration (X8) BEFORE Phase-3 modeling begins.

---

## 6. STANDING RULES FOR THE EXECUTING AGENT

1. Session start: CLAUDE.md ritual (FINDINGS → SESSION_LOG last 3 → data state → STAGE_STATUS
   → briefing), THEN §0 of this playbook.
2. Never overwrite `data/processed/` outputs without a dated backup copy.
3. New results are PROVISIONAL until Nishi confirms; log decisions as 🔒 D-XXX entries.
4. Every claim you write into any document must carry its reproduction command or file:line.
5. If a step's instructions conflict with observed reality (file missing, number different),
   trust reality, record the discrepancy, and re-verify the surrounding assumptions before
   proceeding — do not force the step.
6. Do not start Phase-1 data acquisition involving RTI or emails without explicit human action —
   draft templates only.
7. The vocabulary ban list (SOP-V6) applies to ALL new public-facing text, including README
   and dashboard, not just the manuscript.
