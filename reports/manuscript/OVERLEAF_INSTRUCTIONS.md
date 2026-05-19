# How to Upload and Compile in Overleaf

## Files to Upload
1. `manuscript.tex` — main paper
2. `references.bib` — all 25 references
3. All figure files from `../figures/` (see list below)

## Step-by-Step

1. Go to overleaf.com → New Project → Upload Project
2. Upload `manuscript.tex` and `references.bib` together
3. Upload figures (see list below) — Overleaf stores them flat, no subfolders needed
4. Change the `\includegraphics` paths if Overleaf doesn't find them:
   - Replace `figures/Fig4a_SHAP_beeswarm.png` → `Fig4a_SHAP_beeswarm.png`
5. Set compiler to: **pdfLaTeX**
6. Compile → should build in ~15 seconds

## Figures Needed (from ../figures/)
| File | Used in |
|------|---------|
| Fig3_storage_timeseries.png | Fig 2 (storage ts) |
| Fig4a_SHAP_beeswarm.png | Fig 3a |
| Fig4b_SHAP_dependence_top.png | Fig 3b |
| Fig9_anthro_timeseries.png | Fig 4 |
| Fig6c_CCM_convergence.png | Fig 5 |
| Fig9_GRACE_reconciliation.png | Fig 6 |
| Fig8_taxonomy.png | Fig 7 |

> Note: Fig1_study_area.png does not exist yet — the \includegraphics line
> will show a placeholder box. This is fine for review draft.
> Create a simple map later using QGIS or Python folium.

## Packages Required (all standard in Overleaf)
- elsarticle (built-in)
- siunitx, booktabs, tabularx, xcolor, natbib
- microtype, cleveref, lineno, subcaption
- All available on Overleaf by default — no manual installation needed

## Target Journal: Remote Sensing of Environment (Elsevier)
- Submission portal: https://www.editorialmanager.com/RSE
- Article type: Research Article
- Word limit: none (typically 8,000–12,000 words for full paper)
- Figure limit: 10 main + unlimited supplementary
- Current paper: ~7,500 words (within range)

## Before Submission Checklist
- [ ] Add Fig1_study_area (QGIS map)
- [ ] Update figure paths if needed
- [ ] Final check all numbers match FINDINGS.md
- [ ] Supervisor Dr. Maya Ray review
- [ ] Add institutional address/email confirmation
- [ ] Register for ORCID if not done
- [ ] Assign GitHub/Zenodo DOI for code repository (replace placeholder in Data Availability)
