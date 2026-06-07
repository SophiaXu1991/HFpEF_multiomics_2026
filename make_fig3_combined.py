import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np
from PIL import Image

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
_os.makedirs(_os.path.join(BASE_DIR, 'figures_out'), exist_ok=True)

OUT  = _os.path.join(BASE_DIR, 'figures_out')
FIGS = _os.path.join(BASE_DIR, 'figures_r')

df = pd.read_csv(f'{FIGS}/FigS_STRING_interactions.csv')
ev_cols = ['nscore','fscore','pscore','ascore','escore','dscore','tscore']
ev_labels = {
    'tscore': 'Text mining',
    'ascore': 'Co-expression',
    'escore': 'Experiments',
    'dscore': 'Databases',
    'pscore': 'Protein homology',
    'nscore': 'Gene neighborhood',
    'fscore': 'Gene fusion',
}
for c in ev_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

# Hub gene degree
all_genes = pd.concat([df['preferredName_A'], df['preferredName_B']])
degree = all_genes.value_counts().head(12)
hub_genes = ['Fn1','Tgfb1','Col1a1','Ppara','Foxo1']
colors_d = ['#D6604D' if g in hub_genes else '#4472C4' for g in degree.index]

# Evidence counts (non-zero interactions per channel)
ev_counts = {ev_labels[c]: int((df[c]>0).sum()) for c in ev_cols}
ev_sorted = sorted(ev_counts.items(), key=lambda x: x[1], reverse=True)
ev_names, ev_vals = zip(*ev_sorted)
ev_colors = ['#D6604D','#F4A261','#4DAF4A','#4472C4','#9B59B6','#888','#aaa']

# ── Figure layout: 1 large left + 2 small right ──────────────
fig = plt.figure(figsize=(16, 9), facecolor='white')
fig.suptitle('Figure 3. STRING Functional Protein Interaction Network of Key HFpEF Genes',
             fontsize=13, fontweight='bold', y=0.99)

gs = gridspec.GridSpec(2, 2, figure=fig,
                       width_ratios=[1.6, 1],
                       hspace=0.45, wspace=0.32,
                       top=0.93, bottom=0.07, left=0.04, right=0.97)

# Panel A: STRING network image
ax_net = fig.add_subplot(gs[:, 0])
net_img = Image.open(f'{FIGS}/FigS_STRING_network_white.png').convert('RGB')
ax_net.imshow(net_img)
ax_net.axis('off')
ax_net.set_title('A   Protein Interaction Network\n'
                 '    (Mus musculus, confidence ≥ 0.700, n=23 genes, 1,617 edges)',
                 fontsize=10, fontweight='bold', loc='left', pad=6)

# Panel B: Score distribution histogram
ax_b = fig.add_subplot(gs[0, 1])
bins  = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
counts= [405, 258, 187, 189, 260, 314]
xlabels = ['0.70–\n0.75','0.75–\n0.80','0.80–\n0.85','0.85–\n0.90','0.90–\n0.95','0.95–\n1.00']
bar_colors = ['#ADB5BD','#ADB5BD','#7BAFD4','#7BAFD4','#F4A261','#D6604D']
bars = ax_b.bar(range(6), counts, color=bar_colors, edgecolor='white', width=0.75, zorder=3)
for bar, val in zip(bars, counts):
    ax_b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+4,
              str(val), ha='center', va='bottom', fontsize=9, fontweight='bold')
ax_b.set_xticks(range(6))
ax_b.set_xticklabels(xlabels, fontsize=8.5)
ax_b.set_ylabel('Number of interactions', fontsize=9)
ax_b.set_xlabel('STRING confidence score', fontsize=9)
ax_b.set_title('B   Interaction Score Distribution\n    (all 1,617 edges)',
               fontsize=10, fontweight='bold', loc='left')
ax_b.grid(axis='y', alpha=0.25, zorder=0)
ax_b.spines['top'].set_visible(False)
ax_b.spines['right'].set_visible(False)
legend_b = [mpatches.Patch(color='#D6604D', label='Very high (≥0.95)'),
            mpatches.Patch(color='#F4A261', label='High (0.90–0.95)'),
            mpatches.Patch(color='#7BAFD4', label='Medium-high'),
            mpatches.Patch(color='#ADB5BD', label='Medium (0.70–0.75)')]
ax_b.legend(handles=legend_b, fontsize=7.5, loc='upper left', framealpha=0.85)

# Panel C: Hub gene degree
ax_c = fig.add_subplot(gs[1, 1])
ax_c.bar(range(len(degree)), degree.values,
         color=colors_d, edgecolor='white', zorder=3)
ax_c.set_xticks(range(len(degree)))
ax_c.set_xticklabels(degree.index, rotation=45, ha='right', fontsize=9)
ax_c.set_ylabel('Interaction partners (degree)', fontsize=9)
ax_c.set_title('C   Hub Gene Connectivity\n    (top 12, by degree)',
               fontsize=10, fontweight='bold', loc='left')
ax_c.grid(axis='y', alpha=0.25, zorder=0)
ax_c.spines['top'].set_visible(False)
ax_c.spines['right'].set_visible(False)
legend_c = [mpatches.Patch(color='#D6604D', label='Key hub (Fn1, Tgfb1, Col1a1, PPARα, Foxo1)'),
            mpatches.Patch(color='#4472C4', label='Other network genes')]
ax_c.legend(handles=legend_c, fontsize=7.5, loc='upper right', framealpha=0.85)

plt.savefig(f'{OUT}/Fig3_STRING_combined.png', dpi=200,
            bbox_inches='tight', facecolor='white')
print('Saved Fig3_STRING_combined.png')
