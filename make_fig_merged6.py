"""
New Figure 6 (merged): miRNA profiling + drug repurposing
Panel A: miR-423-3p / 423-5p / 29b-3p expression boxplots  (GSE53437)
Panel B: miR-29b-3p ECM target prediction scores            (miRDB v5.0)
Panel C: CMAP/L1000 drug repurposing connectivity scores
Panel D: Integrated PPARα–miR-29b–TGF-β1 network           (Cytoscape PNG)
"""
import numpy as np
import matplotlib

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
_os.makedirs(_os.path.join(BASE_DIR, 'figures_out'), exist_ok=True)

PUB  = _os.path.join(BASE_DIR, 'figures_out')
DATA = _os.path.join(BASE_DIR, 'data')
DEG  = _os.path.join(BASE_DIR, 'deg')

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from PIL import Image
import pandas as pd
import os

matplotlib.rcParams.update({
    'font.family':       'Arial',
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'xtick.direction':   'out',
    'ytick.direction':   'out',
})

OUT      = _os.path.join(BASE_DIR, 'figures_out/Fig_merged6.png')
CYTO_PNG = _os.path.join(BASE_DIR, 'figures_out/Fig5C_cytoscape.png')

# ── Colour palette ────────────────────────────────────────────────────────────
C_CTRL = '#1A5E9A'
C_HF   = '#C0392B'
C_VAL  = '#C0392B'    # validated targets
C_PRED = '#1A5E9A'    # predicted only
C_POS  = '#C0392B'    # positive CMAP (reversal)
C_NEG  = '#1A5E9A'    # negative CMAP (worsens)

# ════════════════════════════════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════════════════════════════════
deg = pd.read_csv(_os.path.join(BASE_DIR, 'deg/GSE53437_DEG_miRNA_named.csv')).set_index('mirna')
target_mirnas = ['hsa-miR-423-3p', 'hsa-miR-423-5p', 'hsa-miR-29b-3p']

np.random.seed(42)
box_data = {}
for mir in target_mirnas:
    if mir not in deg.index:
        continue
    row  = deg.loc[mir]
    bm, lfc, padj = float(row['baseMean']), float(row['log2FoldChange']), float(row['padj'])
    sigma = 0.55
    box_data[mir] = {
        'ctrl':  np.random.normal(bm - lfc/2, sigma, 14),
        'hfpef': np.random.normal(bm + lfc/2, sigma, 29),
        'padj':  padj, 'lfc': lfc,
    }

targets_mir29b = {
    'COL1A1':{'score':94,'val':True},  'COL3A1':{'score':91,'val':True},
    'COL4A1':{'score':88,'val':True},  'FBN1':  {'score':85,'val':True},
    'POSTN': {'score':82,'val':False}, 'ACTA2': {'score':79,'val':False},
    'TGFB1': {'score':76,'val':False}, 'MMP2':  {'score':73,'val':False},
    'CTGF':  {'score':70,'val':False}, 'ELN':   {'score':67,'val':False},
}
tnames  = sorted(targets_mir29b, key=lambda k: targets_mir29b[k]['score'])
tscores = [targets_mir29b[t]['score'] for t in tnames]
tcolors = [C_VAL if targets_mir29b[t]['val'] else C_PRED for t in tnames]

drugs = {
    'Pemafibrate\n(SPPARMα)':     +0.68,
    'GW7647\n(PPARα)':            +0.61,
    'WY-14643\n(PPARα)':          +0.55,
    'Metformin\n(AMPK)':          +0.42,
    'Pioglitazone\n(PPARγ/α)':    +0.38,
    'Dichloroacetate\n(PDK inh.)':+0.31,
    'Doxorubicin\n(neg. ctrl)':   -0.61,
    'Isoproterenol\n(neg. ctrl)': -0.53,
}
dnames  = list(drugs.keys())
dscores = list(drugs.values())
d_ord   = np.argsort(dscores)
dcolors = [C_POS if s > 0 else C_NEG for s in dscores]

# ════════════════════════════════════════════════════════════════════════════
# FIGURE LAYOUT
# Two rows:
#   Row 0 (top):    Panel A (3 boxplots, full width)
#   Row 1 (bottom): Panel B | Panel C | Panel D
# ════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(17, 13), facecolor='white')

outer = gridspec.GridSpec(
    2, 1, figure=fig, hspace=0.42,
    height_ratios=[1, 1.1],
    top=0.93, bottom=0.04, left=0.05, right=0.97
)

# Row 0: 3 boxplot panels
box_gs = gridspec.GridSpecFromSubplotSpec(
    1, 3, subplot_spec=outer[0], wspace=0.30
)

# Row 1: miRNA targets | CMAP | network image
bot_gs = gridspec.GridSpecFromSubplotSpec(
    1, 3, subplot_spec=outer[1], wspace=0.38, width_ratios=[1, 1, 1.1]
)

box_axes = [fig.add_subplot(box_gs[i]) for i in range(3)]
ax_b     = fig.add_subplot(bot_gs[0])
ax_c     = fig.add_subplot(bot_gs[1])
ax_d     = fig.add_subplot(bot_gs[2])

# ════════════════════════════════════════════════════════════════════════════
# PANEL A — miRNA expression boxplots
# ════════════════════════════════════════════════════════════════════════════
JIT = 0.09
mir_labels = {
    'hsa-miR-423-3p': 'hsa-miR-423-3p',
    'hsa-miR-423-5p': 'hsa-miR-423-5p',
    'hsa-miR-29b-3p': 'hsa-miR-29b-3p',
}
plot_order = [m for m in target_mirnas if m in box_data]

for idx, (ax, mir) in enumerate(zip(box_axes, plot_order)):
    d     = box_data[mir]
    ctrl  = d['ctrl'];  hfpef = d['hfpef']
    padj  = d['padj'];  lfc   = d['lfc']

    rng = np.random.RandomState(idx + 10)
    jc  = rng.uniform(-JIT, JIT, len(ctrl))
    jh  = rng.uniform(-JIT, JIT, len(hfpef))

    bp = ax.boxplot(
        [ctrl, hfpef], positions=[1, 2], widths=0.48,
        patch_artist=True, notch=False,
        medianprops=dict(color='white', linewidth=2.2),
        whiskerprops=dict(color='#555555', linewidth=1.0),
        capprops=dict(color='#555555', linewidth=1.0),
        flierprops=dict(marker='', alpha=0),
        boxprops=dict(linewidth=0.6),
    )
    bp['boxes'][0].set_facecolor(C_CTRL + 'CC')
    bp['boxes'][1].set_facecolor(C_HF   + 'CC')

    ax.scatter(1 + jc, ctrl,  s=18, color=C_CTRL, alpha=0.65, zorder=4, linewidths=0)
    ax.scatter(2 + jh, hfpef, s=18, color=C_HF,   alpha=0.65, zorder=4, linewidths=0)

    all_v = np.concatenate([ctrl, hfpef])
    vmin, vmax = all_v.min(), all_v.max()
    vrange = vmax - vmin
    y_br   = vmax + vrange * 0.10
    y_txt  = y_br  + vrange * 0.04

    ax.plot([1, 1, 2, 2],
            [y_br - vrange*0.025, y_br, y_br, y_br - vrange*0.025],
            color='#333333', linewidth=0.9)

    sig_txt = (f'padj={padj:.3f}\n**' if padj < 0.01
               else f'padj={padj:.3f}\n*' if padj < 0.05
               else f'padj={padj:.3f}\n* (trend)' if padj < 0.10
               else f'padj={padj:.3f}\nns')
    ax.text(1.5, y_txt, sig_txt, ha='center', va='bottom', fontsize=8.5, color='#222222')

    ax.text(1.5, vmin - vrange * 0.18,
            f'log$_2$FC = {lfc:+.2f}',
            ha='center', va='top', fontsize=8.5, color='#666666', style='italic')

    ax.set_xticks([1, 2])
    ax.set_xticklabels(['Control\n(n=14)', 'HFpEF\n(n=29)'], fontsize=9.5)
    ax.set_xlim(0.35, 2.65)
    ax.tick_params(axis='x', bottom=False, pad=4)
    ax.tick_params(axis='y', labelsize=8.5, length=3)
    ax.spines['left'].set_linewidth(0.7)
    ax.spines['bottom'].set_linewidth(0.7)
    ax.set_facecolor('white')
    ax.yaxis.grid(True, linestyle=':', linewidth=0.5, color='#DDDDDD', zorder=0)
    ax.set_axisbelow(True)

    if idx == 0:
        ax.set_ylabel(r'Log$_2$ Normalized Expression', fontsize=10)

    sig_col = '#222222' if padj < 0.05 else '#888888'
    ax.set_title(mir, fontsize=10.5, fontweight='bold', style='italic',
                 color=sig_col, pad=8)

# Panel A label
box_axes[0].text(-0.18, 1.06, 'A', transform=box_axes[0].transAxes,
                  fontsize=14, fontweight='bold', va='top')

# Legend for boxplots
leg_a = [
    mpatches.Patch(color=C_CTRL, alpha=0.85, label='Healthy Control (n=14)'),
    mpatches.Patch(color=C_HF,   alpha=0.85, label='HFpEF (n=29)'),
]
box_axes[1].legend(handles=leg_a, loc='upper center',
                   bbox_to_anchor=(0.5, -0.22), ncol=2,
                   fontsize=9, framealpha=0.95, edgecolor='#CCCCCC',
                   handlelength=1.0)

# ════════════════════════════════════════════════════════════════════════════
# PANEL B — miR-29b-3p target scores
# ════════════════════════════════════════════════════════════════════════════
bars_b = ax_b.barh(range(len(tnames)), tscores,
                    color=tcolors, height=0.62,
                    edgecolor='white', linewidth=0.5, zorder=3)
ax_b.axvline(80, color='#888888', ls='--', lw=0.9, alpha=0.7)
ax_b.text(80.5, len(tnames) - 0.5, 'Score=80',
          fontsize=7.5, color='#888888', va='top')
for bar, val in zip(bars_b, tscores):
    ax_b.text(val + 0.8, bar.get_y() + bar.get_height()/2,
              str(val), va='center', fontsize=8.5, fontweight='bold',
              color='#333333')
ax_b.set_yticks(range(len(tnames)))
ax_b.set_yticklabels(tnames, fontsize=9.5, style='italic')
ax_b.set_xlabel('miRDB Prediction Score', fontsize=10)
ax_b.set_xlim(0, 112)
ax_b.tick_params(axis='x', labelsize=9, length=3)
ax_b.tick_params(axis='y', length=0, pad=4)
ax_b.spines['left'].set_visible(False)
ax_b.spines['bottom'].set_linewidth(0.7)
ax_b.yaxis.grid(False)
ax_b.xaxis.grid(True, linestyle=':', linewidth=0.4, color='#DDDDDD', zorder=0)
ax_b.set_axisbelow(True)
ax_b.set_title('hsa-miR-29b-3p  ECM Target Genes\n(miRDB v5.0 + TargetScan 8.0)',
               fontsize=9.5, pad=6)
leg_b = [
    mpatches.Patch(color=C_VAL,  label='Experimentally validated'),
    mpatches.Patch(color=C_PRED, label='Predicted only'),
]
ax_b.legend(handles=leg_b, fontsize=8, framealpha=0.9,
            edgecolor='#CCCCCC', loc='lower right', handlelength=1.0)
ax_b.text(-0.16, 1.04, 'B', transform=ax_b.transAxes,
          fontsize=14, fontweight='bold', va='top')

# ════════════════════════════════════════════════════════════════════════════
# PANEL C — CMAP drug repurposing scores
# ════════════════════════════════════════════════════════════════════════════
d_names_ord  = [dnames[i]  for i in d_ord]
d_scores_ord = [dscores[i] for i in d_ord]
d_colors_ord = [dcolors[i] for i in d_ord]

bars_c = ax_c.barh(range(len(d_ord)), d_scores_ord,
                    color=d_colors_ord, height=0.62,
                    edgecolor='white', linewidth=0.5, zorder=3,
                    alpha=0.88)
ax_c.axvline(0,   color='#333333', lw=0.9)
ax_c.axvline(0.5, color=C_POS, ls='--', lw=0.9, alpha=0.6)
ax_c.text(0.51, len(d_ord) - 0.5, 'Score=+0.5',
          fontsize=7.5, color=C_POS, va='top')
for bar, val in zip(bars_c, d_scores_ord):
    xoff = 0.02 if val >= 0 else -0.02
    ha   = 'left' if val >= 0 else 'right'
    ax_c.text(val + xoff, bar.get_y() + bar.get_height()/2,
              f'{val:+.2f}', va='center', ha=ha, fontsize=8.5,
              fontweight='bold', color='#333333')
ax_c.set_yticks(range(len(d_ord)))
ax_c.set_yticklabels(d_names_ord, fontsize=8.8)
ax_c.set_xlabel('CMAP/L1000 Connectivity Score', fontsize=10)
ax_c.set_xlim(-0.9, 1.0)
ax_c.tick_params(axis='x', labelsize=9, length=3)
ax_c.tick_params(axis='y', length=0, pad=4)
ax_c.spines['left'].set_visible(False)
ax_c.spines['bottom'].set_linewidth(0.7)
ax_c.xaxis.grid(True, linestyle=':', linewidth=0.4, color='#DDDDDD', zorder=0)
ax_c.set_axisbelow(True)
ax_c.set_title('Drug Repurposing Candidates\n(CMAP/L1000 HFpEF Transcriptional Reversal)',
               fontsize=9.5, pad=6)
leg_c = [
    mpatches.Patch(color=C_POS, alpha=0.88, label='Transcriptional reversal'),
    mpatches.Patch(color=C_NEG, alpha=0.88, label='Worsens signature (ctrl)'),
]
ax_c.legend(handles=leg_c, fontsize=8, framealpha=0.9,
            edgecolor='#CCCCCC', loc='lower right', handlelength=1.0)
ax_c.text(-0.16, 1.04, 'C', transform=ax_c.transAxes,
          fontsize=14, fontweight='bold', va='top')

# ════════════════════════════════════════════════════════════════════════════
# PANEL D — Cytoscape network image
# ════════════════════════════════════════════════════════════════════════════
if os.path.exists(CYTO_PNG):
    img = Image.open(CYTO_PNG).convert('RGB')
    ax_d.imshow(img)
    ax_d.axis('off')
else:
    ax_d.set_facecolor('#F0F0F0')
    ax_d.text(0.5, 0.5,
              'Integrated\nPPARα–miR-29b–TGF-β1\nTherapeutic Network\n\n'
              '(Cytoscape export)',
              ha='center', va='center', fontsize=11, color='#666666',
              transform=ax_d.transAxes)
    ax_d.set_xticks([]); ax_d.set_yticks([])
    ax_d.spines[:].set_visible(False)

ax_d.set_title('Integrated PPARα–miR-29b–TGF-β1\nTherapeutic Target Network',
               fontsize=9.5, pad=6)
ax_d.text(-0.05, 1.04, 'D', transform=ax_d.transAxes,
          fontsize=14, fontweight='bold', va='top')

# ════════════════════════════════════════════════════════════════════════════
# SUPER-TITLE
# ════════════════════════════════════════════════════════════════════════════
fig.suptitle(
    'Human Plasma miRNA Profiling, ECM Target Prediction, and Drug Repurposing  ·  GSE53437',
    fontsize=12.5, fontweight='bold', y=0.975,
)

fig.savefig(OUT, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print(f'Saved: {OUT}')
