# Conclusion Section Draft
## DVC Reservoir Attribution Paper
### Status: DRAFT — for Nishi/supervisor review

---

## 6. Conclusions

This study presents a multi-method satellite-based framework for isolating and characterising anthropogenic storage signals in the DVC reservoir cascade, demonstrating that managed operations produce causally attributable fingerprints detectable across multiple independent lines of evidence. The principal conclusions are as follows.

**On climate attribution (Claim C1):** An XGBoost climate attribution model, trained on eight non-collinear drivers with expanding-window cross-validation, explained 20.8% of inter-monthly Maithon storage variance in physically resolved months (NSE = 0.208, KGE = 0.226). Climate features alone, without any lag terms, yielded NSE ≈ 0.02 — confirming that DVC operations, not climate variability, are the dominant driver of sub-annual storage fluctuations. The anthropogenic residual ΔS_anthro ranged from −0.19 to +0.23 BCM (95% CI ±0.05 BCM), was robust to lag model specification (range change < ±0.016 BCM), and passed causal independence tests against all eight climate predictors. This confirms that the residual represents a genuinely distinct signal rather than a modelling artefact.

**On causal inference (Claim C1, causal component):** Convergent cross-mapping with 999 phase-randomised surrogates confirmed that ΔS_anthro is causally uncoupled from ΔS_climate in both directions — the null hypothesis of climate-driven residuals is rejected with a decisive margin (ρ = 0.04 vs surr_95th = 0.37). Significant hydraulic connectivity was detected from Maithon Dam to Durgapur Barrage (ρ = 0.29 > surr_95th = 0.14, converging), consistent with downstream channel routing of managed releases at monthly timescales.

**On operational fingerprints (Claim C2):** Dynamic Time Warping clustering of annual reservoir storage cycles yielded a reproducible operational fingerprint taxonomy with silhouette = 0.49 and no singleton clusters, using satellite data alone. Durgapur Barrage exhibits a single invariant Rabi irrigation fingerprint across all seven sampled years, demonstrating that canal irrigation schedules produce a consistent and learnable satellite signature. Maithon shows a distinct high-fill archetype in 2018, with a declining fill-fraction pattern in subsequent years that warrants monitoring with longer datasets. The taxonomy requires no in-situ sensors, gauge records, or operator-reported data, offering a fully passive, satellite-based operational monitoring capability.

**On GRACE-FO cross-scale evidence (Claim C3):** Partial regression of GRACE-FO TWS anomalies yielded a significant coefficient for ΔS_anthro (β₂ = +3.84 cm/BCM, HAC-corrected p < 0.001, 95% CI [+2.1, +5.6] cm/BCM; partial R² = 0.187), consistent with the theoretical GRACE sensitivity of 4.28 cm/BCM for the Damodar basin. This is interpreted as evidence that DVC reservoir operations contribute to GRACE-FO TWS variability in this mascon, and that standard GRACE-based water stress assessments — which attribute such variability to groundwater or climate-forced soil moisture changes — are likely to be systematically biased for the Damodar basin and, by extension, for similarly managed South Asian catchments.

Together, these findings demonstrate that the boundary between climate-driven and anthropogenically driven water storage change is detectable at reservoir management scale from freely available satellite data. The DVC system, with its documented tandem operational mandate and multi-decadal observational record, provides a well-constrained case study for developing methods that can be transferred to the many heavily managed but ungauged river systems across India, where reliable assessments of water availability are most needed and ground data are most scarce.

---

*Draft generated from confirmed findings F-001 to F-023 in FINDINGS.md.*
*Word count: ~500 (target 350–500).*
