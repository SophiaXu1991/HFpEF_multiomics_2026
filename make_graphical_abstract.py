"""
Graphical Abstract for HFpEF Multi-Omics Paper
Output: figures_out/GraphicalAbstract.png
Size: 1200x1200 px at 150 DPI (8x8 inches)
Style: Cell Press minimal
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))

# ── Color palette ──────────────────────────────────────────────────────────────
CP_BLUE      = '#00467F'
PHASE1_BLUE  = '#4E9AC7'
PHASE2_RED   = '#D6604D'
NET_ORANGE   = '#F4A261'
THER_GREEN   = '#2A9D8F'
TEXT_DARK    = '#1A1A2E'
PANEL_GRAY   = '#F5F5F5'

# Panel fill colours
PHASE1_FILL  = '#E8F4FD'
PHASE2_FILL  = '#FDE8E4'
NET_FILL     = '#F0F0F0'
DRUG_FILL    = '#E8F5F3'
MIRNA_FILL   = '#FEF3E8'

# ── Figure setup ───────────────────────────────────────────────────────────────
DPI = 150
FIG_W = FIG_H = 8.0          # inches  →  1200 px at 150 DPI

fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI, facecolor='white')
ax  = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# ── Layout constants (y from BOTTOM, fraction of figure) ──────────────────────
# bands from top downward:
#   header  : y in [0.88, 1.00]  h=0.12
#   row1    : y in [0.58, 0.86]  h=0.28
#   row2    : y in [0.34, 0.56]  h=0.22
#   row3    : y in [0.10, 0.32]  h=0.22
#   footer  : y in [0.00, 0.10]  h=0.10

MARGIN = 0.025   # horizontal/vertical padding
GAP    = 0.015   # inter-panel gap


# ═══════════════════════════════════════════════════════════════════════════════
# 1. TOP HEADER BAND
# ═══════════════════════════════════════════════════════════════════════════════
header_y  = 0.88
header_h  = 0.12

header = FancyBboxPatch(
    (0, header_y), 1.0, header_h,
    boxstyle='square,pad=0',
    linewidth=0, facecolor=CP_BLUE, zorder=2
)
ax.add_patch(header)

fig.text(0.5, header_y + header_h * 0.62,
         'Multi-Omics Framework: Biphasic Metabolic Dysregulation\nand PPARα–miR-29b–TGF-β1 Axis in HFpEF',
         ha='center', va='center', color='white',
         fontsize=14, fontweight='bold', zorder=3)

fig.text(0.5, header_y + header_h * 0.22,
         'Integrative Multi-Omics Analysis',
         ha='center', va='center', color='white',
         fontsize=11, zorder=3)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ROW 1  –  Phase 1  |  arrow  |  Phase 2
# ═══════════════════════════════════════════════════════════════════════════════
row1_y  = 0.58
row1_h  = 0.28
row1_yc = row1_y + row1_h / 2   # vertical centre of the row

# --  Phase 1 panel  ----------------------------------------------------------
p1_x = MARGIN
p1_w = 0.375
p1_y = row1_y + MARGIN * 0.5
p1_h = row1_h - MARGIN

p1_box = FancyBboxPatch(
    (p1_x, p1_y), p1_w, p1_h,
    boxstyle='round,pad=0.012',
    linewidth=1.2, edgecolor=PHASE1_BLUE,
    facecolor=PHASE1_FILL, zorder=2
)
ax.add_patch(p1_box)

# label block
lbl_y = p1_y + p1_h - 0.026
fig.text(p1_x + p1_w/2, lbl_y,
         'PHASE 1',
         ha='center', va='center',
         color=PHASE1_BLUE, fontsize=9, fontweight='bold', zorder=3)

fig.text(p1_x + p1_w/2, lbl_y - 0.026,
         'GSE209548  |  Early HFpEF',
         ha='center', va='center',
         color='#666666', fontsize=7.5, zorder=3)

# down-arrows with GSEA labels
arrow_entries = [
    ('FAO ↓',         'NES = −1.90**'),
    ('Glycolysis ↓',  'NES = −1.84**'),
    ('Insulin sign. ↓', 'NES = −1.71**'),
]
line_h = 0.045
start_y = lbl_y - 0.066
for i, (pathway, nes) in enumerate(arrow_entries):
    iy = start_y - i * line_h
    # small triangle down
    fig.text(p1_x + 0.06, iy,
             '▼',
             ha='center', va='center',
             color=PHASE2_RED, fontsize=7.5, zorder=3)
    fig.text(p1_x + 0.12, iy,
             pathway,
             ha='left', va='center',
             color=TEXT_DARK, fontsize=7.5, fontweight='bold', zorder=3)
    fig.text(p1_x + 0.30, iy,
             nes,
             ha='right', va='center',
             color='#555555', fontsize=7, zorder=3)

# green checkmark
ck_y = start_y - 3 * line_h - 0.01
fig.text(p1_x + p1_w/2, ck_y,
         '✓  No Fibrosis Activation',
         ha='center', va='center',
         color=THER_GREEN, fontsize=8, fontweight='bold', zorder=3)


# --  Center progression arrow  -----------------------------------------------
arr_cx   = 0.5
arr_cy   = row1_yc
arr_half = 0.055   # half-width of arrow shaft

fig.text(arr_cx, arr_cy + 0.055,
         'Disease\nProgression',
         ha='center', va='center',
         color=CP_BLUE, fontsize=7.5, fontweight='bold',
         multialignment='center', zorder=3)

arrow_patch = FancyArrowPatch(
    (arr_cx - arr_half, arr_cy - 0.01),
    (arr_cx + arr_half, arr_cy - 0.01),
    arrowstyle='->', mutation_scale=18,
    linewidth=2, color=CP_BLUE, zorder=3
)
ax.add_patch(arrow_patch)


# --  Phase 2 panel  ----------------------------------------------------------
p2_x = 1.0 - MARGIN - p1_w
p2_y = p1_y
p2_h = p1_h
p2_w = p1_w

p2_box = FancyBboxPatch(
    (p2_x, p2_y), p2_w, p2_h,
    boxstyle='round,pad=0.012',
    linewidth=1.2, edgecolor=PHASE2_RED,
    facecolor=PHASE2_FILL, zorder=2
)
ax.add_patch(p2_box)

lbl2_y = p2_y + p2_h - 0.026
fig.text(p2_x + p2_w/2, lbl2_y,
         'PHASE 2',
         ha='center', va='center',
         color=PHASE2_RED, fontsize=9, fontweight='bold', zorder=3)

fig.text(p2_x + p2_w/2, lbl2_y - 0.026,
         'GSE194151  |  Established HFpEF',
         ha='center', va='center',
         color='#666666', fontsize=7.5, zorder=3)

# up + down arrows
p2_entries = [
    ('▲', 'OxPhos ↑',        'NES = +1.87**',  THER_GREEN),
    ('▼', 'FAO ↓',           '(persistent)',    PHASE2_RED),
    ('▼', 'PPARα ↓',         'log2FC = −1.9',   PHASE2_RED),
]
start2_y = lbl2_y - 0.068
for i, (sym, label, val, col) in enumerate(p2_entries):
    iy = start2_y - i * line_h
    fig.text(p2_x + 0.06, iy, sym,
             ha='center', va='center',
             color=col, fontsize=7.5, zorder=3)
    fig.text(p2_x + 0.12, iy, label,
             ha='left', va='center',
             color=TEXT_DARK, fontsize=7.5, fontweight='bold', zorder=3)
    fig.text(p2_x + 0.36, iy, val,
             ha='right', va='center',
             color='#555555', fontsize=7, zorder=3)

# fibrosis warning
warn_y = start2_y - 3 * line_h - 0.010
fig.text(p2_x + p2_w/2, warn_y,
         '⚠  Fibrosis DEGs ↑  (Col1a1, Tgfb1)',
         ha='center', va='center',
         color=PHASE2_RED, fontsize=7.5, fontweight='bold', zorder=3)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ROW 2  –  STRING Network Hubs  (full width)
# ═══════════════════════════════════════════════════════════════════════════════
row2_y  = 0.34
row2_h  = 0.22

net_box = FancyBboxPatch(
    (MARGIN, row2_y + MARGIN * 0.5),
    1.0 - 2 * MARGIN,
    row2_h - MARGIN,
    boxstyle='round,pad=0.012',
    linewidth=1.0, edgecolor='#CCCCCC',
    facecolor=NET_FILL, zorder=2
)
ax.add_patch(net_box)

# title
fig.text(0.5, row2_y + row2_h - 0.020,
         'STRING Network Hubs',
         ha='center', va='center',
         color=TEXT_DARK, fontsize=10, fontweight='bold', zorder=3)

# stats label top-right
fig.text(1.0 - MARGIN - 0.015, row2_y + row2_h - 0.018,
         '856 proteins  |  1,617 edges',
         ha='right', va='center',
         color='#777777', fontsize=7, zorder=3)

# draw connecting lines between nodes FIRST (so they are under circles)
node_cx = [0.27, 0.50, 0.73]
node_cy_base = row2_y + row2_h * 0.38
import matplotlib.lines as mlines

for i in range(len(node_cx) - 1):
    line = mlines.Line2D(
        [node_cx[i], node_cx[i+1]],
        [node_cy_base, node_cy_base],
        linewidth=2, color='#AAAAAA', zorder=2
    )
    ax.add_line(line)

# nodes
nodes = [
    (node_cx[0], node_cy_base, 0.052, PHASE2_RED,  'Fn1',    'degree = 227'),
    (node_cx[1], node_cy_base, 0.065, CP_BLUE,     'TGF-β1', 'degree = 167'),
    (node_cx[2], node_cy_base, 0.052, PHASE1_BLUE, 'Col1a1', 'degree = 144'),
]

for (cx, cy, r, color, label, deg_text) in nodes:
    circle = plt.Circle((cx, cy), r,
                         transform=ax.transData,
                         facecolor=color, edgecolor='white',
                         linewidth=1.5, zorder=4)
    ax.add_patch(circle)

    # protein name inside circle
    fig.text(cx, cy + 0.005,
             label,
             ha='center', va='center',
             color='white', fontsize=9, fontweight='bold',
             transform=fig.transFigure, zorder=5)

    # degree below circle
    fig.text(cx, cy - r - 0.018,
             deg_text,
             ha='center', va='center',
             color='#555555', fontsize=7,
             transform=fig.transFigure, zorder=5)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ROW 3  –  PPARα Screening  |  Human Plasma miRNA
# ═══════════════════════════════════════════════════════════════════════════════
row3_y  = 0.10
row3_h  = 0.22

half_w = (1.0 - 2 * MARGIN - GAP) / 2

# --  LEFT: PPARα Virtual Screening  -----------------------------------------
dp_x = MARGIN
dp_y = row3_y + MARGIN * 0.5
dp_w = half_w
dp_h = row3_h - MARGIN

dp_box = FancyBboxPatch(
    (dp_x, dp_y), dp_w, dp_h,
    boxstyle='round,pad=0.012',
    linewidth=1.0, edgecolor=THER_GREEN,
    facecolor=DRUG_FILL, zorder=2
)
ax.add_patch(dp_box)

fig.text(dp_x + dp_w/2, dp_y + dp_h - 0.020,
         'PPARα Virtual Screening',
         ha='center', va='center',
         color=THER_GREEN, fontsize=9, fontweight='bold', zorder=3)

# Drug entries
drug_entries = [
    ('GW7647',      'ΔG = −11.2 kcal/mol', False),
    ('Pemafibrate', 'ΔG = −10.5 kcal/mol', True),   # clinical candidate
]
bar_max_w = dp_w * 0.48
dg_max = 11.2

dentry_y = dp_y + dp_h - 0.062
for name, dg_txt, is_highlight in drug_entries:
    # horizontal bar proportional to affinity
    dg_val = float(dg_txt.split('=')[1].split('k')[0].strip().replace('−', '-'))
    bar_w  = bar_max_w * abs(dg_val) / dg_max
    bar_color = '#F4A261' if is_highlight else '#AAAAAA'
    bar_rect = FancyBboxPatch(
        (dp_x + 0.015, dentry_y - 0.010),
        bar_w, 0.016,
        boxstyle='round,pad=0.002',
        linewidth=0, facecolor=bar_color, zorder=3
    )
    ax.add_patch(bar_rect)

    fw = 'bold' if is_highlight else 'normal'
    col = TEXT_DARK if is_highlight else '#666666'
    fig.text(dp_x + dp_w/2, dentry_y + 0.008,
             f'{name}   {dg_txt}',
             ha='center', va='center',
             color=col, fontsize=7.5, fontweight=fw, zorder=4)

    if is_highlight:
        fig.text(dp_x + dp_w - 0.012, dentry_y + 0.008,
                 '★',
                 ha='right', va='center',
                 color='#F4A261', fontsize=9, zorder=4)

    dentry_y -= 0.052

# CMAP line
fig.text(dp_x + dp_w/2, dp_y + 0.022,
         'CMAP score: +0.68  (rank #1)',
         ha='center', va='center',
         color=THER_GREEN, fontsize=7.5, fontstyle='italic', zorder=3)


# --  RIGHT: Human Plasma miRNA  ----------------------------------------------
mi_x = MARGIN + half_w + GAP
mi_y = dp_y
mi_w = half_w
mi_h = dp_h

mi_box = FancyBboxPatch(
    (mi_x, mi_y), mi_w, mi_h,
    boxstyle='round,pad=0.012',
    linewidth=1.0, edgecolor=NET_ORANGE,
    facecolor=MIRNA_FILL, zorder=2
)
ax.add_patch(mi_box)

fig.text(mi_x + mi_w/2, mi_y + mi_h - 0.020,
         'Human Plasma miRNA',
         ha='center', va='center',
         color=NET_ORANGE, fontsize=9, fontweight='bold', zorder=3)

mirna_entries = [
    ('hsa-miR-423-3p  ↓',  'padj = 0.022', True),
    ('hsa-miR-423-5p  ↓',  'padj = 0.036', True),
    ('hsa-miR-29b-3p  ↓',  'padj = 0.064', False),  # sub-threshold italic
]
mir_y = mi_y + mi_h - 0.060
for mirna, padj, is_sig in mirna_entries:
    col  = TEXT_DARK if is_sig else '#999999'
    fw   = 'normal'
    fs   = 'italic' if not is_sig else 'normal'
    fig.text(mi_x + 0.015, mir_y,
             f'▼  {mirna}',
             ha='left', va='center',
             color=col, fontsize=7.5, fontstyle=fs, fontweight=fw, zorder=3)
    fig.text(mi_x + mi_w - 0.012, mir_y,
             padj,
             ha='right', va='center',
             color='#777777', fontsize=7, fontstyle=fs, zorder=3)
    mir_y -= 0.040

# mechanism arrow
fig.text(mi_x + mi_w/2, mi_y + 0.030,
         'miR-29b-3p ↓  →  COL1A1 / COL3A1 ↑',
         ha='center', va='center',
         color=PHASE2_RED, fontsize=7.5, fontweight='bold', zorder=3)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. FOOTER BAND
# ═══════════════════════════════════════════════════════════════════════════════
footer_h = 0.10
footer_y = 0.0

footer = FancyBboxPatch(
    (0, footer_y), 1.0, footer_h,
    boxstyle='square,pad=0',
    linewidth=0, facecolor=THER_GREEN, zorder=2
)
ax.add_patch(footer)

fig.text(0.5, footer_y + footer_h * 0.65,
         'Proposed Therapeutic Axis:  PPARα (pemafibrate)  —  miR-29b  —  TGF-β1',
         ha='center', va='center',
         color='white', fontsize=9.5, fontweight='bold', zorder=3)

fig.text(0.5, footer_y + footer_h * 0.22,
         'Pending in vivo validation',
         ha='center', va='center',
         color='white', fontsize=8, fontstyle='italic', zorder=3)


# ═══════════════════════════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════════════════════════
out_dir  = _os.path.join(BASE_DIR, 'figures_out')
out_path = os.path.join(out_dir, 'GraphicalAbstract.png')

os.makedirs(out_dir, exist_ok=True)

fig.savefig(out_path, dpi=DPI, bbox_inches='tight',
            facecolor='white', pad_inches=0)
plt.close(fig)

# Verify dimensions
from PIL import Image
with Image.open(out_path) as im:
    w, h = im.size

print(f'Saved: {out_path}')
print(f'Size:  {w} x {h} pixels  (DPI={DPI})')
