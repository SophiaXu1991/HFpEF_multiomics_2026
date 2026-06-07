"""
New Figure 3 (merged): GSE194151 transcriptomic analysis
Panel A: Volcano plot (DESeq2 DEGs)
Panel B: GSEA pathway NES bar chart (GSE194151)
Panel C: Per-sample z-scored heatmap (FAO / OxPhos / Fibrosis genes)
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
from matplotlib.lines import Line2D
import matplotlib.ticker as ticker
import pandas as pd
import gzip

matplotlib.rcParams.update({
    'font.family':       'Arial',
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'xtick.direction':   'out',
    'ytick.direction':   'out',
})

OUT = _os.path.join(BASE_DIR, 'figures_out/Fig_merged3.png')

# ── Colours (shared palette) ──────────────────────────────────────────────────
C_UP   = '#C0392B'   # upregulated / HFpEF
C_DN   = '#1A5E9A'   # downregulated / Control
C_NS   = '#CCCCCC'   # not significant
C_FAO  = '#C0392B'
C_OX   = '#1A5E9A'
C_FIB  = '#2D6A4F'

# ════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ════════════════════════════════════════════════════════════════════════════

# ── DEG (volcano) ─────────────────────────────────────────────────────────────
deg_all = pd.read_csv(_os.path.join(BASE_DIR, 'deg/GSE194151_DEG_all_genes.csv'))
deg_sym = pd.read_csv(_os.path.join(BASE_DIR, 'deg/GSE194151_DEG_gene_symbols.csv'))
# Row-aligned zip (truncates to shorter)
ens2sym = dict(zip(deg_all['gene_id'], deg_sym['Unnamed: 0']))
deg_all['symbol'] = deg_all['gene_id'].map(ens2sym).fillna('')
deg_all = deg_all.dropna(subset=['padj', 'log2FoldChange'])
deg_all['neg_log10_padj'] = -np.log10(deg_all['padj'].clip(lower=1e-300))

# Classification
deg_all['color'] = C_NS
sig = (deg_all['padj'] < 0.05) & (deg_all['log2FoldChange'].abs() > 0.5)
deg_all.loc[sig & (deg_all['log2FoldChange'] > 0), 'color'] = C_UP
deg_all.loc[sig & (deg_all['log2FoldChange'] < 0), 'color'] = C_DN

# Key gene labels
label_genes = {
    'Cpt1b': 'FAO', 'Hadha': 'FAO', 'Hadhb': 'FAO', 'Ppara': 'FAO',
    'Acadm': 'FAO', 'Acadvl': 'FAO',
    'Col1a1': 'FIB', 'Col3a1': 'FIB', 'Fn1': 'FIB',
    'Tgfb1': 'FIB', 'Acta2': 'FIB', 'Postn': 'FIB',
    'Ndufa1': 'OX', 'Cycs': 'OX', 'Cox4i1': 'OX',
}
label_color = {'FAO': C_DN, 'FIB': C_FIB, 'OX': C_UP}

# ── GSEA (NES bars) ──────────────────────────────────────────────────────────
gsea = pd.read_csv(_os.path.join(BASE_DIR, 'gsea/GSE194151_GSEA.csv'))
pathway_display = {
    'OxPhos_KEGG':      'OxPhos',
    'Ketone_GO':        'Ketone Body Metab.',
    'Insulin_Signaling':'Insulin Signaling',
    'PPAR_Signaling':   'PPARα Signaling',
    'Glycolysis_KEGG':  'Glycolysis',
    'FAO_KEGG':         'Fatty Acid Oxidation',
    'Cardiac_Fibrosis': 'Cardiac Fibrosis',
}
gsea['display'] = gsea['Term'].map(pathway_display)
gsea = gsea.dropna(subset=['display']).sort_values('nes')

# ── Heatmap data ──────────────────────────────────────────────────────────────
FAO_GENES      = ['Cpt1b','Hadha','Hadhb','Acadm','Acadl','Acadvl','Acsl1','Ppara','Rxra','Fabp3']
OXPHOS_GENES   = ['Ndufa1','Cycs','Cox4i1','Uqcrc1','Sdha','Sdhb','Atp5a1','Oxct1']
FIBROSIS_GENES = ['Col1a1','Col3a1','Col1a2','Col4a1','Fn1','Tgfb1','Acta2','Postn','Ctgf']
ALL_GENES = FAO_GENES + OXPHOS_GENES + FIBROSIS_GENES

with gzip.open(
    _os.path.join(BASE_DIR, 'data/GSE194151_GSE194151_HFpEF_B6.mm10_Ensembl97.kallisto_counts.txt.gz'),
    'rt'
) as f:
    counts_raw = pd.read_csv(f, sep='\t', index_col=0)

ctrl_cols  = [c for c in counts_raw.columns if not c.startswith('YF')][:15]
hfpef_cols = [c for c in counts_raw.columns if c.startswith('YF')][:15]
all_cols   = ctrl_cols + hfpef_cols
counts     = counts_raw[all_cols]

sym2ens = {v: k for k, v in ens2sym.items() if v}
gene_rows = {s: sym2ens[s] for s in ALL_GENES if s in sym2ens and sym2ens[s] in counts.index}
present   = [g for g in ALL_GENES if g in gene_rows]
pres_fao  = [g for g in FAO_GENES      if g in present]
pres_ox   = [g for g in OXPHOS_GENES   if g in present]
pres_fib  = [g for g in FIBROSIS_GENES if g in present]

mat     = counts.loc[[gene_rows[g] for g in present]].copy().astype(float)
mat.index = present
lib_sz  = mat.sum(axis=0)
log_cpm = np.log2(mat.div(lib_sz, axis=1) * 1e6 + 1)
zmat    = log_cpm.sub(log_cpm.mean(axis=1), axis=0).div(log_cpm.std(axis=1), axis=0)
n_g, n_s = len(present), len(all_cols)

# ════════════════════════════════════════════════════════════════════════════
# FIGURE LAYOUT
# ════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 13), facecolor='white')

# Outer: top half (volcano + GSEA) | bottom half (heatmap)
outer = gridspec.GridSpec(2, 1, figure=fig, hspace=0.42,
                           height_ratios=[1, 1.05],
                           top=0.93, bottom=0.05, left=0.06, right=0.95)

# Top row: Panel A + Panel B
top_gs = gridspec.GridSpecFromSubplotSpec(
    1, 2, subplot_spec=outer[0], wspace=0.38, width_ratios=[1, 0.8]
)

# Bottom row: Panel C (heatmap) — nested with color strip
bot_gs = gridspec.GridSpecFromSubplotSpec(
    1, 3, subplot_spec=outer[1], wspace=0.015,
    width_ratios=[0.025, 1, 0.035]
)

ax_a   = fig.add_subplot(top_gs[0])      # volcano
ax_b   = fig.add_subplot(top_gs[1])      # GSEA NES
ax_bar = fig.add_subplot(bot_gs[0])      # gene-cat color strip
ax_c   = fig.add_subplot(bot_gs[1])      # heatmap
ax_cb  = fig.add_subplot(bot_gs[2])      # colorbar

# ════════════════════════════════════════════════════════════════════════════
# PANEL A — Volcano plot
# ════════════════════════════════════════════════════════════════════════════
ALPHA_NS  = 0.18
ALPHA_SIG = 0.55
SIZE_NS   = 4
SIZE_SIG  = 6

# Plot non-significant grey first
ns_mask = deg_all['color'] == C_NS
ax_a.scatter(deg_all.loc[ns_mask, 'log2FoldChange'],
             deg_all.loc[ns_mask, 'neg_log10_padj'],
             s=SIZE_NS, c=C_NS, alpha=ALPHA_NS, linewidths=0, rasterized=True)

# Plot up/down
for col in [C_UP, C_DN]:
    mask = deg_all['color'] == col
    ax_a.scatter(deg_all.loc[mask, 'log2FoldChange'],
                 deg_all.loc[mask, 'neg_log10_padj'],
                 s=SIZE_SIG, c=col, alpha=ALPHA_SIG, linewidths=0, rasterized=True)

# Threshold lines
ax_a.axhline(-np.log10(0.05), color='#888888', lw=0.7, ls='--', alpha=0.7)
ax_a.axvline( 0.5,  color='#888888', lw=0.7, ls=':', alpha=0.7)
ax_a.axvline(-0.5,  color='#888888', lw=0.7, ls=':', alpha=0.7)

# Gene labels
labeled = deg_all[deg_all['symbol'].isin(label_genes)].copy()
for _, row in labeled.iterrows():
    sym = row['symbol']
    cat = label_genes[sym]
    col = label_color[cat]
    xo  = 0.25 if row['log2FoldChange'] > 0 else -0.25
    ax_a.annotate(
        sym,
        xy=(row['log2FoldChange'], row['neg_log10_padj']),
        xytext=(row['log2FoldChange'] + xo, row['neg_log10_padj'] + 2.5),
        fontsize=7.2, color=col, fontweight='bold', style='italic',
        arrowprops=dict(arrowstyle='-', color=col, lw=0.6),
        ha='center',
    )

# Counts annotation
n_up = int((deg_all['color'] == C_UP).sum())
n_dn = int((deg_all['color'] == C_DN).sum())
ax_a.text( 6.8, 2, f'Up: {n_up:,}', color=C_UP, fontsize=8.5, ha='right')
ax_a.text(-6.8, 2, f'Down: {n_dn:,}', color=C_DN, fontsize=8.5, ha='left')

ax_a.set_xlabel(r'log$_2$ Fold Change (HFpEF / Control)', fontsize=10)
ax_a.set_ylabel(r'$-$log$_{10}$(padj)', fontsize=10)
ax_a.set_xlim(-8, 8)
ax_a.set_ylim(0, deg_all['neg_log10_padj'].quantile(0.9997) * 1.08)
ax_a.tick_params(labelsize=9, length=3)
ax_a.spines['left'].set_linewidth(0.7)
ax_a.spines['bottom'].set_linewidth(0.7)

leg_a = [
    Line2D([0],[0], marker='o', color='w', markerfacecolor=C_UP, ms=7, label=f'Up-regulated (n={n_up:,})'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor=C_DN, ms=7, label=f'Down-regulated (n={n_dn:,})'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor=C_NS, ms=7, label='Not significant'),
]
ax_a.legend(handles=leg_a, fontsize=8, framealpha=0.9,
            edgecolor='#CCCCCC', loc='upper left', handletextpad=0.3)
ax_a.text(-0.08, 1.04, 'A', transform=ax_a.transAxes,
          fontsize=14, fontweight='bold', va='top')

# ════════════════════════════════════════════════════════════════════════════
# PANEL B — GSEA NES bar chart
# ════════════════════════════════════════════════════════════════════════════
nes_vals = gsea['nes'].values
fdr_vals = gsea['fdr'].values
labels_b = gsea['display'].values
bar_cols = [C_UP if n > 0 else C_DN for n in nes_vals]
bar_alpha = [1.0 if f < 0.10 else 0.38 for f in fdr_vals]

bars_b = ax_b.barh(
    range(len(gsea)), nes_vals,
    color=[c for c in bar_cols],
    alpha=1, height=0.62,
    edgecolor='white', linewidth=0.6, zorder=3
)
for bar, alpha in zip(bars_b, bar_alpha):
    bar.set_alpha(alpha)

# FDR label and stars
for i, (n, f) in enumerate(zip(nes_vals, fdr_vals)):
    star = '**' if f < 0.05 else ('*' if f < 0.10 else '')
    fdr_str = f'FDR={f:.3f}'
    xpos = n + (0.06 if n >= 0 else -0.06)
    ha   = 'left' if n >= 0 else 'right'
    col  = bar_cols[i]
    txt  = f'{fdr_str} {star}' if n >= 0 else f'{star} {fdr_str}'
    ax_b.text(xpos, i, txt, va='center', ha=ha, fontsize=7.5,
              color=col if f < 0.10 else '#888888',
              fontweight='bold' if star else 'normal')

ax_b.axvline(0, color='#333333', lw=0.8)
ax_b.axvline( 1.5, color='#AAAAAA', lw=0.6, ls='--', alpha=0.8)
ax_b.axvline(-1.5, color='#AAAAAA', lw=0.6, ls='--', alpha=0.8)
ax_b.set_yticks(range(len(gsea)))
ax_b.set_yticklabels(labels_b, fontsize=9.5)
ax_b.set_xlabel('Normalized Enrichment Score (NES)', fontsize=10)
ax_b.set_xlim(-2.4, 2.8)
ax_b.tick_params(axis='x', labelsize=9, length=3)
ax_b.tick_params(axis='y', length=0, pad=4)
ax_b.spines['left'].set_visible(False)
ax_b.spines['bottom'].set_linewidth(0.7)
ax_b.set_title('GSE194151  (HFD+L-NAME vs. Control)', fontsize=9,
               color='#444444', pad=4)
ax_b.text(-0.14, 1.04, 'B', transform=ax_b.transAxes,
          fontsize=14, fontweight='bold', va='top')

leg_b = [
    mpatches.Patch(color=C_UP,   label='Enriched in HFpEF'),
    mpatches.Patch(color=C_DN,   label='Suppressed in HFpEF'),
    mpatches.Patch(color='#CCCCCC', label='FDR ≥ 0.10 (ns)'),
]
ax_b.legend(handles=leg_b, fontsize=7.5, framealpha=0.9,
            edgecolor='#CCCCCC', loc='lower right', handlelength=1.0)

# ════════════════════════════════════════════════════════════════════════════
# PANEL C — Per-sample heatmap
# ════════════════════════════════════════════════════════════════════════════
group_bar_cols = (
    [C_FAO] * len(pres_fao) +
    [C_OX]  * len(pres_ox)  +
    [C_FIB] * len(pres_fib)
)
for i, col in enumerate(group_bar_cols):
    ax_bar.barh(i, 1, color=col, height=0.92, linewidth=0)
ax_bar.set_xlim(0, 1)
ax_bar.set_ylim(-0.5, n_g - 0.5)
ax_bar.invert_yaxis()
ax_bar.axis('off')

norm = TwoSlopeNorm(vcenter=0, vmin=-2.5, vmax=2.5)
im   = ax_c.imshow(zmat.values, aspect='auto', cmap='RdBu_r',
                    norm=norm, interpolation='nearest')

# Sample group header strip
strip_h = 1.1
for i in range(n_s):
    col = C_UP if i >= 15 else C_DN
    ax_c.add_patch(plt.Rectangle(
        (i - 0.5, -strip_h - 0.5), 1, strip_h,
        color=col, clip_on=False, transform=ax_c.transData, lw=0
    ))

ax_c.text(7,  -strip_h * 0.5 - 0.5, 'Control (n=15)',
          ha='center', va='center', fontsize=8.5, color='white',
          fontweight='bold', transform=ax_c.transData, clip_on=False)
ax_c.text(22, -strip_h * 0.5 - 0.5, 'HFpEF (n=15)',
          ha='center', va='center', fontsize=8.5, color='white',
          fontweight='bold', transform=ax_c.transData, clip_on=False)

ax_c.set_yticks(range(n_g))
ax_c.set_yticklabels(present, fontsize=8, style='italic', ha='right')
ax_c.tick_params(axis='y', length=0, pad=4)
ax_c.set_xticks([])
ax_c.set_xlim(-0.5, n_s - 0.5)
ax_c.set_ylim(n_g - 0.5, -0.5)

nf  = len(pres_fao)
no  = nf + len(pres_ox)
for y_d in [nf - 0.5, no - 0.5]:
    ax_c.axhline(y_d, color='white', linewidth=2.0, zorder=5)
ax_c.axvline(14.5, color='white', linewidth=1.5, zorder=5)

mids_c = [
    ((nf - 1) / 2,               'FAO /\nPPARα',   C_FAO),
    (nf + (len(pres_ox)  - 1)/2, 'OxPhos',          C_OX),
    (no + (len(pres_fib) - 1)/2, 'ECM /\nFibrosis', C_FIB),
]
for mid, lbl, col in mids_c:
    ax_c.text(n_s + 0.5, mid, lbl, va='center', ha='left',
              fontsize=8.5, color=col, fontweight='bold',
              transform=ax_c.transData, clip_on=False)
ax_c.spines[:].set_visible(False)

# Colorbar
cb = fig.colorbar(im, cax=ax_cb, orientation='vertical')
cb.set_label(r'Z-score (log$_2$ CPM)', fontsize=8, labelpad=8)
cb.ax.tick_params(labelsize=7.5)
cb.ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.5))
cb.outline.set_linewidth(0.5)

ax_bar.text(-2.5, -0.8, 'C', fontsize=14, fontweight='bold',
            transform=ax_bar.transData, va='top', clip_on=False)

# ════════════════════════════════════════════════════════════════════════════
# SUPER-TITLE
# ════════════════════════════════════════════════════════════════════════════
fig.suptitle(
    'Established HFpEF Transcriptomic Analysis  ·  GSE194151 (HFD+L-NAME vs. Control, n=15/15)',
    fontsize=12.5, fontweight='bold', y=0.975,
)

fig.savefig(OUT, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print(f'Saved: {OUT}')
