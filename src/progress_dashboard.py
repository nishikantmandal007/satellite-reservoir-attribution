"""
progress_dashboard.py
DVC Reservoir Attribution Project — Sprint Progress Dashboard
Run: uv run python src/progress_dashboard.py
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path

FIGURES_DIR = Path('figures')
FIGURES_DIR.mkdir(exist_ok=True)

# ── Colour palette ──────────────────────────────────────────────────────────
BG      = '#0d1117'
PANEL   = '#161b22'
GREEN   = '#3fb950'
YELLOW  = '#d29922'
RED     = '#f85149'
BLUE    = '#58a6ff'
PURPLE  = '#bc8cff'
GREY    = '#8b949e'
WHITE   = '#e6edf3'

fig = plt.figure(figsize=(20, 14), facecolor=BG)
fig.suptitle(
    'DVC RESERVOIR ATTRIBUTION PROJECT  ·  Sprint Dashboard  ·  Day 3 of 15',
    fontsize=16, fontweight='bold', color=WHITE, y=0.98
)

# ── Helper: styled panel box ─────────────────────────────────────────────────
def panel(ax, title):
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values():
        sp.set_edgecolor('#30363d')
        sp.set_linewidth(1.2)
    ax.set_title(title, color=BLUE, fontsize=9, fontweight='bold',
                 loc='left', pad=6)
    ax.tick_params(colors=GREY, labelsize=7)

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 1: Sprint timeline (top-left)
# ═══════════════════════════════════════════════════════════════════════════
ax1 = fig.add_axes([0.02, 0.74, 0.28, 0.18])
panel(ax1, '① SPRINT TIMELINE')

days = np.arange(1, 16)
colors_bar = []
for d in days:
    if d < 3:
        colors_bar.append(GREEN)
    elif d == 3:
        colors_bar.append(YELLOW)
    else:
        colors_bar.append('#21262d')

bars = ax1.bar(days, [1]*15, color=colors_bar, edgecolor='#30363d', linewidth=0.5, width=0.85)
ax1.set_xlim(0.4, 15.6)
ax1.set_ylim(0, 1.6)
ax1.set_xticks(days)
ax1.set_xticklabels([str(d) for d in days], color=GREY, fontsize=7)
ax1.set_yticks([])
ax1.set_xlabel('Day', color=GREY, fontsize=8)

# Day labels
day_labels = {
    1: 'GEE\nScripts', 2: 'A-V\nFit', 3: 'Storage\nRecon★',
    7: 'XGB\nTrain', 8: 'CHECK\nPOINT', 10: 'CCM\nCausal',
    11: 'DTW\nCluster', 15: 'Submit'
}
for d, lbl in day_labels.items():
    col = WHITE if d <= 3 else GREY
    ax1.text(d, 1.05, lbl, ha='center', va='bottom', fontsize=5.5,
             color=col, fontweight='bold' if d in (3, 8, 15) else 'normal')

ax1.text(8, 1.45, '← Day 8 Gate →', ha='center', color=YELLOW, fontsize=7,
         fontweight='bold')

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 2: 6-Stage pipeline (top-centre)
# ═══════════════════════════════════════════════════════════════════════════
ax2 = fig.add_axes([0.33, 0.74, 0.38, 0.18])
panel(ax2, '② SIX-STAGE PIPELINE STATUS')
ax2.set_xlim(0, 10)
ax2.set_ylim(-0.5, 6.5)
ax2.axis('off')

stages = [
    ('Stage 1', 'Multi-sensor Storage Reconstruction', 75, YELLOW, '▶ IN PROGRESS'),
    ('Stage 2', 'Driver Dataset Construction',         0,  GREY,   '○ PENDING'),
    ('Stage 3', 'ML Climate Attribution (XGBoost)',    0,  GREY,   '○ PENDING'),
    ('Stage 4', 'Causal Inference (CCM + Granger)',    0,  GREY,   '○ PENDING'),
    ('Stage 5', 'GRACE-FO Cross-scale Reconciliation', 0, GREY,   '○ MOONSHOT'),
    ('Stage 6', 'Operational Fingerprint Taxonomy',    0,  GREY,   '○ PENDING'),
]

for i, (stg, desc, pct, col, status) in enumerate(stages):
    y = 5.8 - i * 1.0
    # Progress bar background
    ax2.add_patch(FancyBboxPatch((2.5, y-0.18), 5.0, 0.36,
                                  boxstyle='round,pad=0.02',
                                  facecolor='#21262d', edgecolor='#30363d'))
    # Progress fill
    if pct > 0:
        ax2.add_patch(FancyBboxPatch((2.5, y-0.18), 5.0*pct/100, 0.36,
                                      boxstyle='round,pad=0.02',
                                      facecolor=col, alpha=0.7,
                                      edgecolor='none'))
    ax2.text(0.0, y, stg, color=col, fontsize=8, fontweight='bold', va='center')
    ax2.text(2.6, y, desc, color=WHITE, fontsize=7, va='center')
    ax2.text(7.7, y, status, color=col, fontsize=7, va='center', fontweight='bold')
    ax2.text(7.6, y-0.28, f'{pct}%', color=col, fontsize=6.5, va='center', ha='right')

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 3: Stage 1 sub-tasks (top-right)
# ═══════════════════════════════════════════════════════════════════════════
ax3 = fig.add_axes([0.74, 0.74, 0.24, 0.18])
panel(ax3, '③ STAGE 1 CHECKLIST')
ax3.axis('off')
ax3.set_xlim(0, 10)
ax3.set_ylim(0, 10)

tasks = [
    ('✓', GREEN,  'GEE S1 script — fixed & running'),
    ('✓', GREEN,  'GEE MODIS script — exported'),
    ('✓', GREEN,  'av_hypsometry.js — exported'),
    ('✓', GREEN,  'fit_av_params.py — AV calibrated'),
    ('✓', GREEN,  'CartoDEM tiles — downloaded'),
    ('⟳', YELLOW, 'S1 export — running in GEE'),
    ('○', GREY,   'water_area_sentinel1.csv'),
    ('○', GREY,   '01_storage_reconstruction.py'),
    ('○', GREY,   '2009 flood validation'),
    ('○', GREY,   'DVC_storage_timeseries.csv'),
]

for i, (icon, col, txt) in enumerate(tasks):
    y = 9.4 - i * 0.95
    ax3.text(0.3, y, icon, color=col, fontsize=9, va='center', fontweight='bold')
    ax3.text(1.2, y, txt, color=WHITE if col != GREY else GREY,
             fontsize=7.2, va='center')

# Blocker note
ax3.add_patch(FancyBboxPatch((0, 0.1), 9.8, 0.75,
                              boxstyle='round,pad=0.05',
                              facecolor='#2d1b00', edgecolor=YELLOW, linewidth=1))
ax3.text(5, 0.48, '⚠  BLOCKER: Waiting on S1 GEE export',
         color=YELLOW, fontsize=7.5, ha='center', va='center', fontweight='bold')

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 4: 3 Publishable Claims tracker (middle-left)
# ═══════════════════════════════════════════════════════════════════════════
ax4 = fig.add_axes([0.02, 0.42, 0.44, 0.28])
panel(ax4, '④ PUBLISHABLE CLAIMS EVIDENCE TRACKER')
ax4.axis('off')
ax4.set_xlim(0, 10)
ax4.set_ylim(0, 10)

claims = [
    ('C1', 'Causal attribution: DVC ops → misattributed residuals',
     [('Stage 1 foundation', GREEN, 1.0),
      ('Stage 2 drivers',    GREY,  0.0),
      ('Stage 3 XGBoost',    GREY,  0.0),
      ('Stage 4 CCM',        GREY,  0.0)],
     25, 'CCM p<0.05 + Granger p<0.05'),
    ('C2', 'Unique DTW-classifiable operational fingerprints',
     [('Stage 1 timeseries', GREEN, 1.0),
      ('Stage 6 DTW',        GREY,  0.0),
      ('Silhouette >0.5',    GREY,  0.0),
      ('2009 event validate', GREY, 0.0)],
     25, 'Silhouette > 0.5, cluster = events'),
    ('C3', 'Reservoir signal explains GRACE TWS unexplained by climate',
     [('Stage 3 residual',   GREY, 0.0),
      ('Stage 5 downscale',  GREY, 0.0),
      ('Partial reg. β₂',   GREY, 0.0),
      ('p < 0.05',          GREY, 0.0)],
     0, 'β₂ significant after climate control'),
]

for ci, (cid, desc, evidence, pct, criterion) in enumerate(claims):
    y0 = 9.0 - ci * 3.1
    col_c = GREEN if pct > 50 else (YELLOW if pct > 0 else GREY)

    # Claim header
    ax4.add_patch(FancyBboxPatch((0, y0-0.02), 9.8, 0.6,
                                  boxstyle='round,pad=0.05',
                                  facecolor='#161b22', edgecolor=col_c,
                                  linewidth=1.2))
    ax4.text(0.2, y0+0.28, cid, color=col_c, fontsize=10,
             fontweight='bold', va='center')
    ax4.text(0.9, y0+0.28, desc, color=WHITE, fontsize=7.5, va='center')
    ax4.text(9.6, y0+0.28, f'{pct}%', color=col_c, fontsize=9,
             fontweight='bold', va='center', ha='right')

    # Evidence steps
    for ei, (ev_name, ev_col, ev_done) in enumerate(evidence):
        ex = 0.2 + ei * 2.4
        ey = y0 - 0.85
        ax4.add_patch(FancyBboxPatch((ex, ey-0.2), 2.2, 0.45,
                                      boxstyle='round,pad=0.04',
                                      facecolor='#21262d' if ev_done < 1 else ev_col,
                                      edgecolor=ev_col, linewidth=0.8, alpha=0.6))
        ax4.text(ex+1.1, ey+0.05, ev_name, color=WHITE if ev_done else GREY,
                 fontsize=6.2, ha='center', va='center')

    # Pass criterion
    ax4.text(0.2, y0 - 1.5, f'Pass: {criterion}', color=GREY,
             fontsize=6.5, va='center', style='italic')

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 5: Day-8 checkpoint gauges (middle-right)
# ═══════════════════════════════════════════════════════════════════════════
ax5 = fig.add_axes([0.49, 0.42, 0.24, 0.28])
panel(ax5, '⑤ DAY-8 CHECKPOINT GAUGES')
ax5.axis('off')
ax5.set_xlim(0, 10)
ax5.set_ylim(0, 10)

questions = [
    ('Q1', 'ΔS_obs clean\nfor all 3 reservoirs?', 'NOT YET', YELLOW),
    ('Q2', 'XGBoost NSE\n0.60–0.85?',             'NOT YET', GREY),
    ('Q3', 'Granger signal\np < 0.10?',            'NOT YET', GREY),
]

ax5.text(5, 9.5, 'Gate: 2/3 → Journal of Hydrology',
         color=BLUE, fontsize=7.5, ha='center', fontweight='bold')

outcomes = [
    ('3/3', GREEN,  'WRR (IF 5.4)'),
    ('2/3', BLUE,   'J. Hydrology (IF 6.7)'),
    ('1/3', YELLOW, 'RS Environ (IF 4.1)'),
    ('0/3', RED,    'STOP — debug Stage 1'),
]

for i, (q_id, q_txt, status, col) in enumerate(questions):
    cx, cy = 1.5 + i * 3.0, 6.5
    # Circle gauge
    circle = plt.Circle((cx, cy), 1.1, color='#21262d', linewidth=2,
                          ec=col, transform=ax5.transData)
    ax5.add_patch(circle)
    ax5.text(cx, cy+0.15, q_id, color=col, fontsize=11,
             ha='center', va='center', fontweight='bold')
    ax5.text(cx, cy-0.45, status, color=col, fontsize=6,
             ha='center', va='center', fontweight='bold')
    ax5.text(cx, cy-2.1, q_txt, color=WHITE, fontsize=6.5,
             ha='center', va='center')

ax5.text(5, 3.5, 'OUTCOME MAP', color=GREY, fontsize=7, ha='center',
         fontweight='bold')
for i, (score, col, journal) in enumerate(outcomes):
    y = 2.9 - i * 0.7
    ax5.add_patch(FancyBboxPatch((0.3, y-0.22), 9.3, 0.44,
                                  boxstyle='round,pad=0.03',
                                  facecolor='#21262d', edgecolor=col,
                                  linewidth=0.8))
    ax5.text(1.0, y, score, color=col, fontsize=8,
             fontweight='bold', va='center')
    ax5.text(2.2, y, journal, color=WHITE, fontsize=7, va='center')

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 6: Publication trajectory
# ═══════════════════════════════════════════════════════════════════════════
ax6 = fig.add_axes([0.76, 0.42, 0.22, 0.28])
panel(ax6, '⑥ PUBLICATION TRAJECTORY')

tiers = ['Guaranteed\n(MDPI RS)', 'Tier 1\n(J.Hydrol)', 'Tier 2\n(RSE)', 'Moonshot\n(WRR)']
probs = [55, 38, 18, 10]
colors_t = [GREEN, BLUE, PURPLE, YELLOW]

bars6 = ax6.barh(tiers, probs, color=colors_t, edgecolor='#30363d',
                  linewidth=0.8, height=0.55)
ax6.set_xlim(0, 75)
ax6.set_xlabel('Probability (%)', color=GREY, fontsize=7)
ax6.set_facecolor(PANEL)
ax6.tick_params(colors=GREY, labelsize=7)
ax6.spines['top'].set_visible(False)
ax6.spines['right'].set_visible(False)
ax6.spines['bottom'].set_edgecolor('#30363d')
ax6.spines['left'].set_edgecolor('#30363d')
ax6.xaxis.label.set_color(GREY)

for bar, prob in zip(bars6, probs):
    ax6.text(prob + 1.5, bar.get_y() + bar.get_height()/2,
             f'{prob}%', color=WHITE, fontsize=7.5, va='center',
             fontweight='bold')

ax6.text(35, -0.7, 'Combined strategy: 61% submittable',
         color=YELLOW, fontsize=7, ha='center', fontweight='bold',
         transform=ax6.get_xaxis_transform())

# ═══════════════════════════════════════════════════════════════════════════
# PANEL 7: Key decisions log (bottom)
# ═══════════════════════════════════════════════════════════════════════════
ax7 = fig.add_axes([0.02, 0.04, 0.96, 0.34])
panel(ax7, '⑦ LOGGED DECISIONS — D-001 to D-009')
ax7.axis('off')
ax7.set_xlim(0, 20)
ax7.set_ylim(0, 8)

decisions = [
    ('D-001', GREEN,  'Adaptive Otsu\nthreshold for SAR',
     'Self-calibrates per scene;\nDamodar has high seasonal\nbackscatter variation'),
    ('D-002', GREEN,  'JRC max_extent mask\nbefore Otsu',
     'Prevents rice paddy\nconfusion (SERIOUS-1);\nmandatory for monsoon'),
    ('D-003', RED,    'Remove Refined Lee\n(OOM fix for 11yr)',
     'Median composite\nprovides equivalent\ndespeckling for reservoirs'),
    ('D-004', GREEN,  'Expand Panchet\nbbox east to 87.05°E',
     'Dam at 86.769°E;\nreservoir floods valley\neastward to ~87.0°E'),
    ('D-005', YELLOW, 'Restore Otsu\n(user preference)',
     'User: "no let the\noriginal run I dont\nwant to compromise"'),
    ('D-006', GREEN,  'AW3D30 over CartoDEM\nfor hypsometry',
     'Hulsman 2024: fill ratio\n<8% vs CartoDEM 33%;\nbetter for reservoirs'),
    ('D-007', GREEN,  'Calibrate a from\nCWC capacity',
     'AW3D30=DSM overestimates\nvolume +87–161%;\nb from DEM, a from CWC'),
    ('D-008', GREEN,  'Use GEE for\nhypsometry (not local)',
     'Local CartoDEM gave\n42 BCM vs 1.36 BCM;\nGEE has JRC mask built-in'),
    ('D-009', YELLOW, 'Durgapur: S1 only\n(MODIS 500m sub-pixel)',
     'Run-of-river barrage\ntoo narrow for 500m;\nuse 2014–2024 S1 only'),
]

cols_per_row = 5
for i, (did, col, title, rationale) in enumerate(decisions):
    row = i // cols_per_row
    col_i = i % cols_per_row
    x = 0.2 + col_i * 4.0
    y = 7.0 - row * 3.8

    ax7.add_patch(FancyBboxPatch((x-0.1, y-3.2), 3.8, 3.3,
                                  boxstyle='round,pad=0.1',
                                  facecolor='#21262d',
                                  edgecolor=col, linewidth=1.0))
    ax7.text(x+0.05, y-0.15, did, color=col, fontsize=8,
             fontweight='bold', va='top')
    ax7.text(x+0.05, y-0.75, title, color=WHITE, fontsize=7,
             va='top', linespacing=1.3)
    ax7.text(x+0.05, y-2.0, rationale, color=GREY, fontsize=6.2,
             va='top', style='italic', linespacing=1.3)

# ── Footer ─────────────────────────────────────────────────────────────────
fig.text(0.5, 0.005,
         'Nishi Kant Mandal · BIT Sindri · 22030430063  |  '
         'Supervisor: Dr. Maya Rajnarayan Ray  |  '
         'Sprint Day 3 / 15  ·  2026-03-21',
         ha='center', color=GREY, fontsize=7)

out = FIGURES_DIR / 'progress_dashboard.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print(f"Saved: {out}")
