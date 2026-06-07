"""
Figure 3: DEG Heatmap — FAO / OxPhos / Fibrosis genes, GSE194151
Per-sample log2-CPM z-scored heatmap, n=30 (15 HFpEF vs 15 Control)
Polished publication version.
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
from matplotlib.colors import TwoSlopeNorm
import matplotlib.ticker as ticker
import pandas as pd
import gzip

matplotlib.rcParams.update({
    'font.family': 'Arial',
})

OUT = _os.path.join(BASE_DIR, 'figures_out/FigB_DEG_heatmap.png')

# ── Gene sets ─────────────────────────────────────────────────────────────────
FAO_GENES      = ['Cpt1b', 'Hadha', 'Hadhb', 'Acadm', 'Acadl', 'Acadvl',
                  'Acsl1', 'Ppara', 'Rxra', 'Fabp3']
OXPHOS_GENES   = ['Ndufa1', 'Cycs', 'Cox4i1', 'Uqcrc1', 'Sdha', 'Sdhb',
                  'Atp5a1', 'Oxct1']
FIBROSIS_GENES = ['Col1a1', 'Col3a1', 'Col1a2', 'Col4a1', 'Fn1',
                  'Tgfb1', 'Acta2', 'Postn', 'Ctgf']
ALL_GENES = FAO_GENES + OXPHOS_GENES + FIBROSIS_GENES

# ── Load data ─────────────────────────────────────────────────────────────────
with gzip.open(
    _os.path.join(BASE_DIR, 'data/GSE194151_GSE194151_HFpEF_B6.mm10_Ensembl97.kallisto_counts.txt.gz'),
    'rt'
) as f:
    counts_raw = pd.read_csv(f, sep='\t', index_col=0)

ctrl_cols  = [c for c in counts_raw.columns if not c.startswith('YF')][:15]
hfpef_cols = [c for c in counts_raw.columns if c.startswith('YF')][:15]
all_cols   = ctrl_cols + hfpef_cols
counts     = counts_raw[all_cols]

# ── Ensembl → symbol mapping ──────────────────────────────────────────────────
deg_all = pd.read_csv(_os.path.join(BASE_DIR, 'deg/GSE194151_DEG_all_genes.csv'))
deg_sym = pd.read_csv(_os.path.join(BASE_DIR, 'deg/GSE194151_DEG_gene_symbols.csv'))
ens2sym = dict(zip(deg_all['gene_id'], deg_sym['Unnamed: 0']))
sym2ens = {v: k for k, v in ens2sym.items()}

gene_rows = {}
for sym in ALL_GENES:
    ens = sym2ens.get(sym)
    if ens and ens in counts.index:
        gene_rows[sym] = ens

present      = [g for g in ALL_GENES if g in gene_rows]
ens_ids      = [gene_rows[g] for g in present]
pres_fao     = [g for g in FAO_GENES      if g in present]
pres_oxphos  = [g for g in OXPHOS_GENES   if g in present]
pres_fib     = [g for g in FIBROSIS_GENES if g in present]

# ── Normalize: log2(CPM+1), then z-score row-wise ─────────────────────────────
mat     = counts.loc[ens_ids].copy().astype(float)
mat.index = present
lib_sz  = mat.sum(axis=0)
cpm     = mat.div(lib_sz, axis=1) * 1e6
log_cpm = np.log2(cpm + 1)
zmat    = log_cpm.sub(log_cpm.mean(axis=1), axis=0).div(log_cpm.std(axis=1), axis=0)

n_genes = len(present)
n_samp  = len(all_cols)

# ── Colour palette ────────────────────────────────────────────────────────────
COL_FAO  = '#C0392B'   # warm red
COL_OX   = '#1A5E9A'   # steel blue
COL_FIB  = '#2D6A4F'   # forest green
COL_HF   = '#C0392B'
COL_CT   = '#1A5E9A'

group_bar = (
    [COL_FAO] * len(pres_fao) +
    [COL_OX]  * len(pres_oxphos) +
    [COL_FIB] * len(pres_fib)
)

# ── Layout ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(13, 10))
fig.patch.set_facecolor('white')

# GridSpec: [colorbar strip | main heatmap | colorbar_heat | right labels]
gs = gridspec.GridSpec(
    1, 3,
    width_ratios=[0.025, 1, 0.04],
    wspace=0.02,
    left=0.06, right=0.88, top=0.88, bottom=0.08
)

ax_bar  = fig.add_subplot(gs[0])   # gene-category color strip
ax_heat = fig.add_subplot(gs[1])   # heatmap
ax_cb   = fig.add_subplot(gs[2])   # colorbar

# ── Gene category color strip ─────────────────────────────────────────────────
for i, col in enumerate(group_bar):
    ax_bar.barh(i, 1, color=col, height=0.92, linewidth=0)
ax_bar.set_xlim(0, 1)
ax_bar.set_ylim(-0.5, n_genes - 0.5)
ax_bar.invert_yaxis()
ax_bar.axis('off')

# ── Heatmap ───────────────────────────────────────────────────────────────────
norm = TwoSlopeNorm(vcenter=0, vmin=-2.5, vmax=2.5)
im   = ax_heat.imshow(
    zmat.values, aspect='auto',
    cmap='RdBu_r', norm=norm, interpolation='nearest'
)

# ── Sample group header strip ─────────────────────────────────────────────────
strip_h = 1.2   # height in data units above row 0
for i in range(n_samp):
    col = COL_HF if i >= 15 else COL_CT
    ax_heat.add_patch(plt.Rectangle(
        (i - 0.5, -strip_h - 0.5), 1, strip_h,
        color=col, clip_on=False, transform=ax_heat.transData, lw=0
    ))

# Group labels above strip
ax_heat.text(7,   -strip_h - 0.5 - 0.15, 'Control (n=15)',
             ha='center', va='bottom', fontsize=9,
             color=COL_CT, fontweight='bold',
             transform=ax_heat.transData, clip_on=False)
ax_heat.text(22,  -strip_h - 0.5 - 0.15, 'HFpEF (n=15)',
             ha='center', va='bottom', fontsize=9,
             color=COL_HF, fontweight='bold',
             transform=ax_heat.transData, clip_on=False)

# ── Gene labels (italic, right-aligned) ───────────────────────────────────────
ax_heat.set_yticks(range(n_genes))
ax_heat.set_yticklabels(
    present, fontsize=8, style='italic', ha='right'
)
ax_heat.tick_params(axis='y', length=0, pad=4)

# ── X-axis ────────────────────────────────────────────────────────────────────
ax_heat.set_xticks([])
ax_heat.set_xlim(-0.5, n_samp - 0.5)
ax_heat.set_ylim(n_genes - 0.5, -0.5)

# ── Divider lines between gene groups ────────────────────────────────────────
nf = len(pres_fao)
no = nf + len(pres_oxphos)
for y_div in [nf - 0.5, no - 0.5]:
    ax_heat.axhline(y_div, color='white', linewidth=2.0, zorder=5)
ax_heat.axvline(14.5, color='white', linewidth=1.5, zorder=5)

# ── Gene group bracket labels (right side) ───────────────────────────────────
mids = [
    ((nf - 1) / 2,                         'FAO /\nPPARα',   COL_FAO),
    (nf + (len(pres_oxphos) - 1) / 2,      'OxPhos',          COL_OX),
    (no + (len(pres_fib)    - 1) / 2,      'ECM /\nFibrosis', COL_FIB),
]
for mid, lbl, col in mids:
    ax_heat.text(
        n_samp + 0.4, mid, lbl,
        va='center', ha='left', fontsize=9,
        color=col, fontweight='bold',
        transform=ax_heat.transData, clip_on=False
    )

ax_heat.spines[:].set_visible(False)

# ── Colorbar (vertical, right) ────────────────────────────────────────────────
cb = fig.colorbar(im, cax=ax_cb, orientation='vertical')
cb.set_label(r'Z-score (log$_2$ CPM)', fontsize=9, labelpad=8)
cb.ax.tick_params(labelsize=8)
cb.ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))
cb.outline.set_linewidth(0.6)

# ── Title ─────────────────────────────────────────────────────────────────────
fig.suptitle(
    'Key Gene Expression: FAO/PPARα · Oxidative Phosphorylation · ECM-Fibrosis\n'
    'GSE194151  (HFD+L-NAME vs. Control, n=15/15 per group)',
    fontsize=12, fontweight='bold', y=0.97
)

# ── Legend patches ────────────────────────────────────────────────────────────
patches = [
    mpatches.Patch(color=COL_FAO, label='FAO / PPARα genes'),
    mpatches.Patch(color=COL_OX,  label='OxPhos genes'),
    mpatches.Patch(color=COL_FIB, label='ECM / Fibrosis genes'),
    mpatches.Patch(color=COL_HF,  label='HFpEF samples'),
    mpatches.Patch(color=COL_CT,  label='Control samples'),
]
fig.legend(
    handles=patches, loc='lower center', ncol=5,
    fontsize=8.5, framealpha=0.95, edgecolor='#CCCCCC',
    bbox_to_anchor=(0.47, 0.00), handlelength=1.1,
)

fig.savefig(OUT, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print(f'Saved: {OUT}')
