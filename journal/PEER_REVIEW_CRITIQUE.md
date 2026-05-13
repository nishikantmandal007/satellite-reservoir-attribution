# Peer Review Critique
## DVC Reservoir Attribution Project — Internal Scrutiny Report
### Generated: 2026-03-24 | Status: ACTION REQUIRED before submission

---

## CRITICAL FLAWS — paper rejected without fixing these

### FLAW 1: GRACE regression circular argument
- **Problem:** ΔS_anthro is derived from Maithon (~23,000 km²) which is a sub-component of the GRACE mascon cell (~90,000 km²). Regressing a component of TWS onto TWS is partly tautological. DW=1.22 + non-normal residuals (Omnibus p=0.010, JB p=0.008) mean OLS standard errors are deflated — p=0.003 is overstated.
- **Fix:** Apply HAC-corrected SE: change `model.fit()` → `model.fit(cov_type='HAC', cov_kwds={'maxlags': 3})` in src/05_grace_reconciliation.py. Report HAC p-value alongside OLS p-value. Reword claim from "confirms DVC contaminates GRACE" → "is consistent with DVC operations contributing to GRACE TWS signal."

### FLAW 2: NSE headline is inconsistent and overstated
- **Problem:** NSE=0.572 (all rows) buries the fact that Folds 1 and 4 have NEGATIVE unclipped NSE. The headline metric survives only because dead-storage-clipped rows inflate it artificially.
- **Fix:** Report fold-level unclipped NSE as primary metric. Compute mean NSE_unclipped across 4 folds from xgb_cv_results.csv. The honest headline is something like "Mean unclipped NSE = X.XX across 4 folds; two folds produced negative NSE, reflecting model instability in drawdown months."

### FLAW 3: Panchet exclusion breaks tandem coupling claim
- **Problem:** Maithon-Durgapur is a storage-dam to run-of-river-barrage pair. They are NOT the tandem pair — Maithon-Panchet is the tandem pair. The CCM finding of Maithon→Durgapur coupling reflects downstream hydraulic connectivity, NOT tandem flood-control operations. This is a physical misinterpretation.
- **Fix:** Either (a) rerun Panchet GEE with corrected bbox [86.72, 23.52, 86.95, 23.68] to get the real tandem pair, OR (b) rewrite the CCM interpretation: "Maithon→Durgapur coupling reflects downstream hydraulic connectivity as Maithon releases propagate to the barrage, consistent with the ~200 km river distance and 2–4 week travel time."

### FLAW 4: Climate-only NSE = 0.018 invalidates attribution framing
- **Problem:** With lag features removed, NSE drops to 0.018. This means climate predictors alone explain ~2% of storage variance. ΔS_climate ≈ 0 for most months → ΔS_anthro ≈ ΔS_obs. You haven't isolated the anthropogenic signal — you've reproduced the raw observed signal.
- **Fix:** Reframe as a FINDING: "Climate drivers alone (API6, PET, AET, DMI, Q_inflow, MO_anom) explain <2% of storage variance (NSE=0.018). Operational memory (dS_lag1) accounts for the majority of predictable variance. This confirms that DVC reservoir operations overwhelm climatological forcing — the anthropogenic signal is dominant, not residual."

---

## SERIOUS WEAKNESSES — reviewers will demand explanation

### W1: Validation only covers one season / one elevation band
CWC validation = Nov–Dec 2024 (upper operating band 147–148m only). The dead-storage regime and mid-fill are unvalidated. State explicitly in limitations.

### W2: Only 199 CCM surrogates (protocol specified 999)
Rerun with N_SURROGATES=999 in src/04_causal_inference.py. The Maithon-Durgapur margin (Δρ=0.145) is large enough to survive, but the protocol deviation will be noticed.

### W3: E=1 embedding dimension is the degenerate CCM case
E=1 means no nonlinear structure detected. CCM at E=1 ≈ linear cross-map. Acknowledge explicitly: "E=1 selected by Simplex projection; this suggests the STL remainder does not exhibit high-dimensional nonlinear dynamics. Results are interpreted as evidence of linear-to-weakly-nonlinear coupling."

### W4: DMI as third-ranked SHAP feature is spurious
DMI–P_mm r=0.001. DMI is ranked third only because it's orthogonal to all other predictors — XGBoost assigns it residual variance by elimination, not physical teleconnection. Add permutation importance test. Add caveat: "DMI survived VIF due to orthogonality, not a known IOD–Damodar teleconnection."

### W5: PBIAS=71% worsens across folds (Fold 4 = 100%)
Bias increasing with more training data = model trained on filling months fails in drawdown months. Run regime-stratified metrics: NSE_filling vs NSE_drawdown separately.

---

## STATISTICAL FIXES (code changes)

| Issue | Fix | Code location |
|-------|-----|---------------|
| HAC standard errors | `model.fit(cov_type='HAC', cov_kwds={'maxlags':3})` | src/05_grace_reconciliation.py ~line 416 |
| 199 surrogates → 999 | Change `N_SURROGATES = 199` → `999` | src/04_causal_inference.py |
| Residual contamination check | Spearman(ΔS_anthro, 10 dropped features); flag r>0.3 | New analysis needed |
| Regime-stratified NSE | Split test rows by dS_obs sign; compute NSE separately | src/03_xgboost_attribution.py |

---

## GENUINE STRENGTHS (reviewers will praise)

1. **Level validation RMSE=0.07m** — genuinely strong against ALOS DEM spec ±3–5m
2. **Null-check CCM design** — running both directions and reporting both ns is above standard
3. **Dead-storage floor clipping diagnosis** — transparent and honest
4. **Bootstrap CI ±0.051 BCM** — addresses uncertainty quantification directly  
5. **GRACE β₂ physical sanity check** — 3.84 vs theoretical 4.28 cm/BCM (within 10%) is excellent science
6. **Durgapur 7/7 within-cluster cohesion** — cleanest visual finding in the paper

---

## REALISTIC JOURNAL TARGET

With current flaws: **rejected at Journal of Hydrology**
After critical fixes: **Remote Sensing of Environment or HESS (Q1)** — 55–65% probability
With Panchet fixed: **Journal of Hydrology plausible** (still needs Granger signal)
