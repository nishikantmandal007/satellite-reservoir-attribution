# PHASE-0 RESULTS — "What Survives" Memo
## Track-A corrections executed 2026-08-22 (Session 016) | Route-B rebuild

> Scope: this memo records the effect of the Track-A code fixes (B2 units, B3 CV
> leakage, B4 CCM direction + Ward linkage, D10 PBIAS, D12 fail-closed, R1 hygiene)
> on every finding in `journal/FINDINGS.md`. **The Stage-1 geometry rebuild (B1) has
> NOT run yet** — it needs the CWC E-A-C table and GEE re-exports (Track B). Findings
> that depend on reservoir geometry are marked PENDING-GEOMETRY regardless of their
> B2/B3/B4 status. All v2 outputs live beside their v1 twins in `data/processed/`;
> v1 files were never overwritten.

---

## 1. New facts established today

| ID | Fact | Evidence |
|----|------|----------|
| N1 | **`data/raw/` is absent from this machine** — all GEE exports, CWC/DVC PDFs, GRACE NetCDF, DEM tiles lost; gitignored so unrecoverable from history | directory missing; `.gitignore` line 2 |
| N2 | pyEDM CCM direction convention pinned EMPIRICALLY on synthetic ground truth: output column `'A:B'` high+convergent ⇒ **B causes A** (v1 assumed the opposite) | `src/04b_ccm_direction_check.py` Part 1: known x→y system lights up `'y:x'` (ρ_final=0.989, slope>0) vs `'x:y'` (0.619) |
| N3 | Maithon-only taxonomy control reproduces EXACTLY under valid linkage: sil=0.4381 (average/K=2) = v1 Ward value | `06b --reservoirs maithon` |

## 2. Finding-by-finding verdicts

### Sensor / driver layer (unaffected by code fixes)
| Finding | Verdict | Notes |
|---|---|---|
| F-001 S1 Maithon validity | SURVIVES (sensor level) | volume claims pending geometry rebuild |
| F-002 Durgapur Rabi drawdown | SURVIVES (direction only) | magnitude pending geometry |
| F-003 Panchet contamination | SURVIVES | bbox fix already in `gee_scripts/s1_water_area.js:29`; re-run pending |
| F-004 MODIS monsoon gaps | SURVIVES | limitation statement unchanged |
| F-005 driver validation | SURVIVES as record | raw files must be re-acquired (N1) before any re-verification |
| F-006 VIF feature set (8 kept) | SURVIVES as engineering | v2 changes downstream usage: in-fold imputation replaces global AET fill |
| F-007 API6 formula correct | SURVIVES | pure formula check |

### Stage 3 — attribution model (B3 fixes applied)
| Finding | Verdict | v1 → v2 |
|---|---|---|
| F-008 (NSE=0.39) | DEAD long ago (superseded by F-009) | — |
| F-009 headline skill | **DEAD** | fold-mean NSE 0.572 → **pooled 0.254**; unclipped +0.208 → **−0.251** |
| F-017 dead-storage clipping metrics | SUPERSEDED | v2 pooled unclipped NSE=−0.251, KGE=+0.408, true-PBIAS unstable (Σobs≈0), nMAE_std=87.4 |
| F-024 baseline comparison | CONFIRMED & AMPLIFIED | persistence now beats XGBoost everywhere: **0.589 vs 0.254** (was 0.589 vs 0.581 leaked) |
| F-026 fold heterogeneity | CONFIRMED & AMPLIFIED | v2 folds [0.409, 0.189, 0.493, **−0.644**]; best_iter 3–8 (very shallow models) |
| F-031 regime-stratified failure | CONFIRMED & AMPLIFIED | negative-skill-within-regime pattern persists under leak-free evaluation |
| F-018 SHAP NaN-routing artifact | RESOLVED differently | v2 imputes lags in-fold from train climatology (no NaN routing); SHAP now out-of-sample per fold (`shap_values_oos_v2.csv`) |
| F-019 SHAP ranking | CHANGED | v1 [dS_lag1 > PET > DMI > dS_lag3 …] → v2 OOS: dS_lag1 41.5% > **DMI 21.7%** > Q_inflow 9.4% > API6 8.1% > PET 8.0% … PET collapses; DMI jumps — treat cautiously (small n=48), permutation test to re-run post-rebuild |
| F-013 bootstrap CI | CHANGED | ±0.051 BCM → **±0.090 BCM**; range [−0.259, +0.282] (`delta_S_anthro_bootstrap_ci_v2.csv`) |
| F-025 T_C residual contamination | PENDING re-run | check blocked by N1 (needs raw drivers); concern remains live |
| F-029 permutation importance | PENDING re-run | post-geometry, post-v2-residual |
| F-030 residual autocorrelation | PENDING re-run | ditto |
| F-010 HMM states | PENDING re-run | HMM fitted v1 residual; re-fit on `delta_S_anthro_v2.csv` required. Granger-null conclusion unchanged in spirit |

### Stage 4 — causal claims (B4a fixes applied)
| Finding | Verdict | v1 → v2 |
|---|---|---|
| F-015 Maithon→Durgapur significant convergent coupling | **DEAD** | matched per-L nulls + both directions + pinned convention: ρ=0.251 vs envelope 0.422 at Lmax, exceedance 0% → ns BOTH ways; v1 significance was a max-vs-single-size selection artifact read through an inverted direction convention |
| F-010 Granger ns | UNCHANGED in spirit | still no detectable coupling at n≈48 power; formal rerun on v2 residuals queued |
| F-014 | already superseded pre-Track-A | — |

### Stage 6 — taxonomy (B4b fixes applied)
| Finding | Verdict | v1 → v2 |
|---|---|---|
| F-011 K=5 sil=0.5535 (Ward-on-DTW) | CHANGED (method) — substance survives | invalid linkage replaced; best VALID = k-medoids K=4 **sil=0.5583**, stability ARI 0.904±0.103 |
| F-012 Maithon-only control sil=0.4381 | SURVIVES exactly | average/K=2 gives identical 0.4381 (N3) |

### Stage 5 — GRACE reconciliation (B2 fixes applied)
| Finding | Verdict | v1 → v2 |
|---|---|---|
| F-23 β₂=3.84 cm/BCM "within 10% of theory" | **DEAD as stated** | β₂ was cm-per-SD (and the deseasonalized twin was BCM-per-SD). Raw-unit truth: **+42.35 cm/BCM** seasonal (CI [+23.5,+61.2], p≈1e-5); **+35.71 cm/BCM** deseasonalized (CI [+16.5,+54.9], p≈0.0003) = **7–10× mass-only ceiling** (4.28–5.10) |
| F-27 deseasonalized survival | PARTIALLY SURVIVES | significance survives robustly (p=0.00026, partial R² 0.2005); the physical-consistency narrative does not. Reframed: cross-scale association with basin-wide water covariation |
| F-020 level validation RMSE 0.07 m | DOWNGRADED | pilot consistency only (pseudoreplication, Codex §6.8); exact-date redesign = roadmap D7; source PDFs lost (N1) |
| F-021 CWC capacity definitions | SURVIVES | conceptual clarification, bug-independent |
| F-022 AV +6.9% bias | PENDING-GEOMETRY | whole AV curve replaced by CWC E-A-C rebuild |
| F-016 volume ceiling | PENDING-GEOMETRY (moot) | superseded by B1: FSL 174.5 m itself is wrong |
| F-028 AV sensitivity | PENDING-GEOMETRY | will be re-derived against the official curve |

---

## 3. The honest bottom line for the paper

1. **What got stronger:** operations-dominance narrative (climate model adds nothing
   over persistence once leakage removed — F-024 amplified); operational-signature
   separation (F-011/F-012 survive audit with better methods); GRACE association
   existence (robust p-values, now honestly labelled).
2. **What died:** XGBoost headline skill (F-009); the Maithon→Durgapur CCM coupling
   (F-015); the "β₂ matches theory" GRACE claim (F-023); any framing of ΔS_anthro as
   an identified anthropogenic quantity (now explicitly *unexplained storage anomaly*).
3. **What is still unknown until Track B lands:** everything geometry-touching
   (Stage-1 rebuild), T_C/permutation/HMM re-runs, exact-date validation.

## 4. Reproduction commands

```
uv run python src/fix_b2_grace_raw_units.py      # B2; identities < 1e-8 PASS
uv run python src/03b_xgboost_deleak.py          # B3; ~6 min
uv run python src/04b_ccm_direction_check.py     # B4a; add --surr 999 for full protocol
uv run python src/06b_taxonomy_linkage_v2.py     # B4b; [--reservoirs maithon]
uv run python tests/test_units.py                # metric fixtures
uv run python tests/test_failclosed.py           # D12 tripwire
```
