"""
Figure 2: Biphasic NES Comparison — polished publication version
Side-by-side grouped bar chart: Phase 1 vs Phase 2 pathway NES.
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
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator
import pandas as pd

matplotlib.rcParams.update({
    'font.family': 'Arial',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
})

OUT = _os.path.join(BASE_DIR, 'figures_out/FigA_biphasic_NES.png')

# ── Data ──────────────────────────────────────────────────────────────────────
phase1 = pd.read_csv(_os.path.join(BASE_DIR, 'gsea/GSE209548_GSEA.csv'))
phase2 = pd.read_csv(_os.path.join(BASE_DIR, 'gsea/GSE194151_GSEA.csv'))

pathway_map = {
    'FAO_KEGG':         'Fatty Acid\nOxidation',
    'Glycolysis_KEGG':  'Glycolysis',
    'Insulin_Signaling':'Insulin\nSignaling',
    'OxPhos_KEGG':      'Oxidative\nPhosphorylation',
    'PPAR_Signaling':   'PPARα\nSignaling',
    'Ketone_GO':        'Ketone Body\nMetabolism',
    'Cardiac_Fibrosis': 'Cardiac\nFibrosis',
}

def build_lookup(df):
    return {row['Term']: (row['nes'], row['fdr']) for _, row in df.iterrows()}

p1 = build_lookup(phase1)
p2 = build_lookup(phase2)

pathways = list(pathway_map.keys())
labels   = list(pathway_map.values())
n        = len(pathways)

nes1 = [p1.get(pw, (0, 1))[0] for pw in pathways]
fdr1 = [p1.get(pw, (0, 1))[1] for pw in pathways]
nes2 = [p2.get(pw, (0, 1))[0] for pw in pathways]
fdr2 = [p2.get(pw, (0, 1))[1] for pw in pathways]

# ── Colour scheme ─────────────────────────────────────────────────────────────
C1_FULL  = '#C0392B'   # Phase 1 solid  (early, red-orange)
C1_FADE  = '#E8A89C'   # Phase 1 faded
C2_FULL  = '#1A5E9A'   # Phase 2 solid  (established, steel blue)
C2_FADE  = '#9AB8D9'   # Phase 2 faded

def bar_col(fdr, full, fade):
    return full if fdr < 0.10 else fade

c1 = [bar_col(f, C1_FULL, C1_FADE) for f in fdr1]
c2 = [bar_col(f, C2_FULL, C2_FADE) for f in fdr2]

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

x   = np.arange(n)
w   = 0.33
gap = 0.05

bars1 = ax.bar(x - w/2 - gap/2, nes1, w, color=c1,
               edgecolor='white', linewidth=0.8, zorder=3)
bars2 = ax.bar(x + w/2 + gap/2, nes2, w, color=c2,
               edgecolor='white', linewidth=0.8, zorder=3)

# ── Significance stars ────────────────────────────────────────────────────────
def sig_star(fdr):
    if fdr < 0.05: return '**'
    if fdr < 0.10: return '*'
    return ''

STAR_OFFSET = 0.08
for b, f, nv in zip(bars1, fdr1, nes1):
    s = sig_star(f)
    if s:
        ypos = nv + STAR_OFFSET if nv >= 0 else nv - STAR_OFFSET - 0.12
        va   = 'bottom' if nv >= 0 else 'top'
        ax.text(b.get_x() + b.get_width()/2, ypos, s,
                ha='center', va=va, fontsize=9, color=C1_FULL, fontweight='bold')

for b, f, nv in zip(bars2, fdr2, nes2):
    s = sig_star(f)
    if s:
        ypos = nv + STAR_OFFSET if nv >= 0 else nv - STAR_OFFSET - 0.12
        va   = 'bottom' if nv >= 0 else 'top'
        ax.text(b.get_x() + b.get_width()/2, ypos, s,
                ha='center', va=va, fontsize=9, color=C2_FULL, fontweight='bold')

# ── Reference lines ───────────────────────────────────────────────────────────
ax.axhline(0, color='#333333', linewidth=0.9, zorder=2)
for y_ref, label_ref in [(1.5, '+1.5'), (-1.5, '−1.5')]:
    ax.axhline(y_ref, color='#AAAAAA', linewidth=0.7,
               linestyle='--', alpha=0.8, zorder=1)
    ax.text(n - 0.45, y_ref + 0.04, f'NES = {label_ref}',
            fontsize=7, color='#888888', ha='right', va='bottom')

# ── Group separator ───────────────────────────────────────────────────────────
ax.axvline(5.5, color='#DDDDDD', linewidth=1.2, linestyle='-', zorder=0)

# Group header labels
ax.text(2.5,  2.42, 'Metabolic Pathways',
        fontsize=9, color='#555555', ha='center', va='bottom',
        fontweight='bold')
ax.text(6.0,  2.42, 'ECM / Fibrosis',
        fontsize=9, color='#555555', ha='center', va='bottom',
        fontweight='bold')

# Subtle background tint for each group
ax.axvspan(-0.55, 5.45, facecolor='#F5F5F5', alpha=0.45, zorder=0)
ax.axvspan( 5.55, n - 0.45, facecolor='#F0F4FF', alpha=0.45, zorder=0)

# ── OxPhos transition arrow annotation ───────────────────────────────────────
i_ox = pathways.index('OxPhos_KEGG')
ax.annotate('',
    xy=(x[i_ox] + w/2 + gap/2, nes2[i_ox] - 0.05),
    xytext=(x[i_ox] - w/2 - gap/2, nes1[i_ox] + 0.05),
    arrowprops=dict(arrowstyle='->', color='#444444',
                    connectionstyle='arc3,rad=0.25', lw=1.2))
ax.text(x[i_ox] + 0.55, 0.3,
        'OxPhos transition\n↑ Phase 2',
        fontsize=7.5, color='#333333', ha='left', va='center',
        style='italic',
        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#CCCCCC', lw=0.7))

# ── Axes formatting ───────────────────────────────────────────────────────────
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9.5)
ax.set_ylabel('Normalized Enrichment Score (NES)', fontsize=11)
ax.set_ylim(-2.6, 2.7)
ax.set_xlim(-0.65, n - 0.35)
ax.yaxis.set_minor_locator(MultipleLocator(0.25))
ax.tick_params(axis='y', labelsize=9.5, which='both', length=3)
ax.tick_params(axis='x', bottom=False, pad=6)
ax.spines['left'].set_linewidth(0.8)
ax.spines['bottom'].set_linewidth(0.8)

# ── Legend ────────────────────────────────────────────────────────────────────
leg_handles = [
    mpatches.Patch(color=C1_FULL, label='Phase 1  –  Early HFpEF  (GSE209548, cardiomyocyte, n=6/5)'),
    mpatches.Patch(color=C2_FULL, label='Phase 2  –  Established HFpEF  (GSE194151, whole heart, n=15/15)'),
    mpatches.Patch(color='#CCCCCC', label='FDR ≥ 0.10  (not significant)'),
]
ax.legend(handles=leg_handles, loc='lower left', fontsize=8.5,
          framealpha=0.95, edgecolor='#CCCCCC', handlelength=1.1,
          borderpad=0.7, labelspacing=0.45)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.set_title(
    'Biphasic Metabolic Reprogramming in HFpEF:\n'
    'Pathway-Level NES Comparison across Two Independent Mouse Models',
    fontsize=11.5, fontweight='bold', pad=12,
)

plt.tight_layout(pad=1.5)
fig.savefig(OUT, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print(f'Saved: {OUT}')
