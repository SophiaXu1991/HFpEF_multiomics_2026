"""
Temporal gene expression clustering: Phase 1 (GSE209548) vs Phase 2 (GSE194151)
Shows directional LFC changes for core pathway genes across disease progression
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
_os.makedirs(_os.path.join(BASE_DIR, 'figures_out'), exist_ok=True)

PUB = _os.path.join(BASE_DIR, 'figures_out')
DEG = _os.path.join(BASE_DIR, 'deg')

# Load DEG results
print("Loading DEG data...")
deg209 = pd.read_csv(os.path.join(DEG, 'GSE209548_DEG_gene_symbols.csv'), index_col=0)
deg194 = pd.read_csv(os.path.join(DEG, 'GSE194151_DEG_gene_symbols.csv'), index_col=0)

print(f"GSE209548 cols: {deg209.columns.tolist()}")
print(f"GSE194151 cols: {deg194.columns.tolist()}")

def get_lfc(df):
    for c in ['log2FoldChange', 'log2FC', 'LFC', 'logFC']:
        if c in df.columns:
            return c
    return df.columns[0]

lfc209_col = get_lfc(deg209)
lfc194_col = get_lfc(deg194)

# Normalize gene names to title case
def norm_index(df):
    df.index = [g.capitalize() if g[0].islower() else g for g in df.index]
    return df

deg209 = norm_index(deg209)
deg194 = norm_index(deg194)

# Core genes by pathway
gene_sets = {
    'FAO/PPARα':    ['Ppara', 'Cpt1b', 'Hadha', 'Hadhb', 'Acadm', 'Cpt2', 'Acadvl'],
    'OxPhos':       ['Ndufa1', 'Ndufb1', 'Sdha', 'Uqcrc1', 'Cox4i1', 'Atp5a1', 'Cycs'],
    'Glycolysis':   ['Hk1', 'Aldoa', 'Pfkm', 'Pkm', 'Ldhb', 'Gapdh', 'Eno1'],
    'Ketone':       ['Oxct1', 'Hmgcs2', 'Bdh1', 'Acat1', 'Hmgcl'],
    'ECM/Fibrosis': ['Col1a1', 'Col3a1', 'Fn1', 'Tgfb1', 'Acta2', 'Postn', 'Ctgf'],
    'Insulin':      ['Akt1', 'Akt2', 'Insr', 'Foxo1', 'Irs1', 'Gsk3b'],
}

pathway_colors = {
    'FAO/PPARα':    '#D62728',
    'OxPhos':       '#1F77B4',
    'Glycolysis':   '#FF7F0E',
    'Ketone':       '#9467BD',
    'ECM/Fibrosis': '#2CA02C',
    'Insulin':      '#8C564B',
}

# Collect data
records = []
for pw, genes in gene_sets.items():
    for gene in genes:
        g = gene.capitalize()
        p1 = deg209[lfc209_col].get(g, np.nan)
        p2 = deg194[lfc194_col].get(g, np.nan)
        records.append({'gene': g, 'pathway': pw, 'phase1': p1, 'phase2': p2,
                        'color': pathway_colors[pw]})

df = pd.DataFrame(records)
print(f"\nTotal genes tracked: {len(df)}")
print(f"Phase1 missing: {df['phase1'].isna().sum()}, Phase2 missing: {df['phase2'].isna().sum()}")

# Impute missing as 0 (not detected = no change)
df['p1_plot'] = df['phase1'].fillna(0)
df['p2_plot'] = df['phase2'].fillna(0)

# Classify trend
def classify(row):
    p1, p2 = row['p1_plot'], row['p2_plot']
    t = 0.3
    if p1 < -t and p2 < -t:    return 'Persistent\nsuppression'
    elif p1 < -t and p2 > t:   return 'Reversed\n(↓→↑)'
    elif p1 < -t:               return 'Early suppression\nonly'
    elif p2 > t and p1 >= -t:   return 'Late activation'
    elif p1 > t and p2 > t:     return 'Persistent\nactivation'
    else:                       return 'No clear trend'

df['trend'] = df.apply(classify, axis=1)
print(df['trend'].value_counts())

# ─── FIGURE ────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 6))
fig.suptitle(
    'Temporal Gene Expression Profiles: Phase 1 (GSE209548) vs Phase 2 (GSE194151)\n'
    'Note: cross-dataset comparison reflects distinct models, tissues, and backgrounds; '
    'not direct longitudinal tracking',
    fontsize=10, fontweight='bold', y=1.01
)

# ── Panel A: Phase1 vs Phase2 scatter ────────────────────────────────────────
ax = axes[0]
for pw, pcolor in pathway_colors.items():
    sub = df[df['pathway'] == pw]
    sub_valid = sub[~(sub['phase1'].isna() & sub['phase2'].isna())]
    if len(sub_valid) > 0:
        ax.scatter(sub_valid['p1_plot'], sub_valid['p2_plot'],
                   c=pcolor, s=85, alpha=0.85, label=pw,
                   edgecolors='white', linewidth=0.4, zorder=3)
        # Label genes
        for _, row in sub_valid.iterrows():
            if abs(row['p1_plot']) > 0.8 or abs(row['p2_plot']) > 1.5:
                ax.annotate(row['gene'],
                            xy=(row['p1_plot'], row['p2_plot']),
                            fontsize=7, color=pcolor, alpha=0.9,
                            xytext=(4, 2), textcoords='offset points')

ax.axhline(0, color='#888888', lw=0.8, ls='--', alpha=0.6)
ax.axvline(0, color='#888888', lw=0.8, ls='--', alpha=0.6)
ax.set_xlabel('Phase 1 log2FC (HFD, n=3/3)', fontsize=10)
ax.set_ylabel('Phase 2 log2FC (HFD+L-NAME, n=15/15)', fontsize=10)
ax.set_title('A  Phase 1 vs Phase 2 log2FC', fontsize=11, fontweight='bold', loc='left')
ax.legend(fontsize=7.5, frameon=True, loc='upper left', ncol=1)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Quadrant annotations
for txt, xy, color in [
    ('Q3: Both↓', (-2.2, -2.5), 'red'),
    ('Q1: Both↑', (0.3, 2.5), 'green'),
    ('Q2: ↓→↑', (-2.2, 2.5), 'purple'),
]:
    ax.text(xy[0], xy[1], txt, fontsize=7, color=color, alpha=0.6)

# ── Panel B: Slope charts for selected genes ─────────────────────────────────
ax2 = axes[1]
sel = [
    ('Ppara',   '#D62728'), ('Cpt1b', '#D62728'),
    ('Ndufa1',  '#1F77B4'), ('Cycs',  '#1F77B4'),
    ('Tgfb1',   '#2CA02C'), ('Col1a1','#2CA02C'),
    ('Hmgcs2',  '#9467BD'),
]
x = [0, 1]
for gene, gcolor in sel:
    row = df[df['gene'] == gene]
    if len(row) == 0:
        continue
    row = row.iloc[0]
    y = [row['p1_plot'], row['p2_plot']]
    ls = '--' if (row['phase1'] != row['phase1'] or row['phase2'] != row['phase2']) else '-'
    ax2.plot(x, y, 'o-', color=gcolor, lw=1.8, ms=7, alpha=0.85, ls=ls)
    ax2.text(1.05, y[1], gene, fontsize=8, va='center', color=gcolor)

ax2.axhline(0, color='#888888', lw=0.8, ls='--', alpha=0.5)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(['Phase 1\n(HFD)', 'Phase 2\n(HFD+L-NAME)'], fontsize=10)
ax2.set_ylabel('log2 Fold Change', fontsize=10)
ax2.set_xlim(-0.25, 1.6)
ax2.set_title('B  Representative gene trajectories', fontsize=11, fontweight='bold', loc='left')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Dashed = value imputed as 0 (missing from that dataset)
ax2.text(0.02, 0.02, 'Dashed line: Phase 1 not detected\n(imputed as 0)',
         transform=ax2.transAxes, fontsize=7, color='gray')

# ── Panel C: Trend distribution ───────────────────────────────────────────────
ax3 = axes[2]
trend_counts = df['trend'].value_counts()
trend_color_map = {
    'Persistent\nsuppression': '#D62728',
    'Late activation':         '#1F77B4',
    'Persistent\nactivation':  '#2CA02C',
    'Early suppression\nonly': '#FF7F0E',
    'Reversed\n(↓→↑)':        '#9467BD',
    'No clear trend':          '#AAAAAA',
}
bar_colors = [trend_color_map.get(t, '#AAAAAA') for t in trend_counts.index]
bars = ax3.barh(trend_counts.index, trend_counts.values,
                color=bar_colors, alpha=0.85, edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, trend_counts.values):
    ax3.text(val + 0.1, bar.get_y() + bar.get_height() / 2, str(val),
             va='center', fontsize=10)
ax3.set_xlabel('Gene count', fontsize=10)
ax3.set_title('C  Temporal trend classification\n(threshold: |log2FC| > 0.3)',
              fontsize=11, fontweight='bold', loc='left')
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.set_xlim(0, trend_counts.max() + 3)

plt.tight_layout()
plt.savefig(os.path.join(PUB, 'FigureS8_TemporalGeneProfiles.png'), dpi=180, bbox_inches='tight')
plt.close()
print("Saved FigureS8_TemporalGeneProfiles.png")
