"""
Supplementary Figures: FigS1 - FigS5
FigS1: GSE209548 early HFpEF GSEA (Phase 1 coordinated suppression)
FigS2: GSE53437 human plasma miRNA volcano
FigS3: Mouse transcriptomics WGCNA (existing figure)
FigS4: Human cardiac proteomics (existing figure)
FigS5: Phenotype specificity & cross-species divergence (existing figure)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
_os.makedirs(_os.path.join(BASE_DIR, 'figures_out'), exist_ok=True)

OUT   = _os.path.join(BASE_DIR, 'figures_out')
FIGS  = _os.path.join(BASE_DIR, 'figures_r')
EFIGS = 'C:/hfpef_figures'
W     = 2400

def load_img(path):
    im = Image.open(path)
    if im.mode == 'RGBA':
        bg = Image.new('RGB', im.size, (255,255,255))
        bg.paste(im, mask=im.split()[3])
        return bg
    return im.convert('RGB')

def scale_to_w(im, w=W):
    h = int(im.height * w / im.width)
    return im.resize((w, h), Image.LANCZOS)

def add_panel_label(im, text, x=8, y=6, size=60):
    im = im.copy()
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', size)
    except:
        font = ImageFont.load_default()
    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
        draw.text((x+dx, y+dy), text, font=font, fill=(255,255,255))
    draw.text((x, y), text, font=font, fill=(15,15,15))
    return im

def vstack_imgs(imgs, pad=28):
    total_h = sum(i.height for i in imgs) + pad*(len(imgs)-1)
    canvas = Image.new('RGB', (W, total_h), (255,255,255))
    y = 0
    for i in imgs:
        iw = scale_to_w(i, W)
        canvas.paste(iw, (0, y))
        y += iw.height + pad
    return canvas

def hstack_imgs(imgs, pad=28):
    h = min(i.height for i in imgs)
    resized = [i.resize((int(i.width*h/i.height), h), Image.LANCZOS) for i in imgs]
    total_w = sum(i.width for i in resized) + pad*(len(resized)-1)
    if total_w > W:
        scale = W / total_w
        h = int(h * scale)
        resized = [i.resize((int(i.width*scale), h), Image.LANCZOS) for i in resized]
        total_w = W
    canvas = Image.new('RGB', (total_w, h), (255,255,255))
    x = 0
    for i in resized:
        canvas.paste(i, (x, 0)); x += i.width + pad
    return canvas

# ================================================================
# FigS1 — GSE209548: Phase 1 Early Metabolic Suppression GSEA
# ================================================================
fig_s1, ax = plt.subplots(figsize=(10, 6), facecolor='white')
fig_s1.suptitle('Figure S1. GSE209548: Phase 1 Coordinated Metabolic Suppression\n'
                '(Mouse Cardiomyocyte-Enriched, HFD vs. Control, n=6/5)',
                fontsize=12, fontweight='bold', y=0.98)

terms  = ['FAO_KEGG','Glycolysis_KEGG','Insulin_Signaling','OxPhos_KEGG','PPAR_Signaling','Ketone_GO','Cardiac_Fibrosis']
nes    = [-1.897,-1.842,-1.711,-1.581,-1.251,-1.242, 0.991]
fdr    = [ 0.019, 0.016, 0.040, 0.078, 0.260, 0.219, 0.513]
colors_s1 = ['#D6604D' if n<0 else '#4DAF4A' for n in nes]
sig_mark  = ['★★' if f<0.05 else ('★' if f<0.10 else 'ns') for f in fdr]

order = np.argsort(nes)
y_pos = np.arange(len(terms))

bars = ax.barh(y_pos, [nes[i] for i in order],
               color=[colors_s1[i] for i in order],
               edgecolor='white', height=0.65, zorder=3)
ax.set_yticks(y_pos)
ax.set_yticklabels([terms[i] for i in order], fontsize=11)
ax.axvline(0, color='black', linewidth=0.8)
ax.axvline(-1.5, color='#D6604D', linestyle='--', linewidth=1.0, alpha=0.6)

for j, (bar, idx) in enumerate(zip(bars, order)):
    val = nes[idx]
    mark = sig_mark[idx]
    fdr_val = fdr[idx]
    x_text = val - 0.04 if val < 0 else val + 0.04
    ha = 'right' if val < 0 else 'left'
    ax.text(x_text, bar.get_y() + bar.get_height()/2,
            f'{val:+.3f}  {mark}  FDR={fdr_val:.3f}',
            va='center', ha=ha, fontsize=9.5, fontweight='bold')

ax.set_xlabel('Normalized Enrichment Score (NES)', fontsize=11)
ax.set_xlim(-2.5, 1.8)
ax.grid(axis='x', alpha=0.25, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

legend_s1 = [
    mpatches.Patch(color='#D6604D', label='Suppressed pathway (NES < 0)'),
    mpatches.Patch(color='#4DAF4A', label='Enriched pathway (NES > 0)'),
    plt.Line2D([0],[0], color='#D6604D', linestyle='--', label='|NES| > 1.5 threshold'),
]
ax.legend(handles=legend_s1, fontsize=9, loc='lower right')
ax.text(0.02, 0.97, '★★ FDR<0.05  ★ FDR<0.10  ns not significant',
        transform=ax.transAxes, fontsize=8.5, va='top', color='grey')

plt.tight_layout()
plt.savefig(f'{OUT}/FigS1_GSE209548_GSEA.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print('FigS1 saved')

# ================================================================
# FigS2 — GSE53437 miRNA Volcano (already rendered as PNG)
# ================================================================
mir_vol = load_img(f'{FIGS}/Fig5A_volcano_GSE53437_miRNA.png')
mir_vol = scale_to_w(mir_vol)

# Add title banner
banner_h = 100
banner = Image.new('RGB', (W, banner_h), (255,255,255))
d_ban = ImageDraw.Draw(banner)
try:
    fnt = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 44)
    fnt2 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 32)
except:
    fnt = fnt2 = ImageFont.load_default()
d_ban.text((W//2, 14), 'Figure S2. Human Plasma miRNA Differential Expression (GSE53437)',
           font=fnt, fill=(20,20,20), anchor='mt')
d_ban.text((W//2, 62), 'HFpEF (n=29) vs. Healthy Control (n=14) | Welch t-test + BH correction',
           font=fnt2, fill=(80,80,80), anchor='mt')

figs2 = vstack_imgs([banner, mir_vol], pad=0)
figs2 = add_panel_label(figs2, 'A', size=60)
figs2.save(f'{OUT}/FigS2_miRNA_volcano.png', dpi=(300,300))
print('FigS2 saved')

# ================================================================
# FigS3 — WGCNA Mouse Transcriptomics (existing tiff)
# ================================================================
wgcna = load_img(f'{EFIGS}/Figure2_mouse_transcriptomics_WGCNA.tiff')
wgcna = scale_to_w(wgcna)

banner3 = Image.new('RGB', (W, 100), (255,255,255))
d3 = ImageDraw.Draw(banner3)
d3.text((W//2, 14), 'Figure S3. Mouse HFpEF Transcriptomics: GSEA Bar Charts and WGCNA Module Architecture',
        font=fnt, fill=(20,20,20), anchor='mt')
d3.text((W//2, 62), 'GSE194151 (HFD+L-NAME, n=15/15) and GSE249409 (HFD+mTAC, n=5/5)',
        font=fnt2, fill=(80,80,80), anchor='mt')

figs3 = vstack_imgs([banner3, wgcna], pad=0)
figs3 = add_panel_label(figs3, 'A', size=60)
figs3.save(f'{OUT}/FigS3_WGCNA.png', dpi=(300,300))
print('FigS3 saved')

# ================================================================
# FigS4 — Human Cardiac Proteomics (existing tiff)
# ================================================================
prot = load_img(f'{EFIGS}/Figure3_human_proteomics.tiff')
prot = scale_to_w(prot)

banner4 = Image.new('RGB', (W, 100), (255,255,255))
d4 = ImageDraw.Draw(banner4)
d4.text((W//2, 14), 'Figure S4. Human Cardiac Proteomics: FAO Enzyme and PDH Complex Depletion',
        font=fnt, fill=(20,20,20), anchor='mt')
d4.text((W//2, 62), 'PXD033876 (SWATH-MS, n=11/7) and PXD060431 (DIA-MS, n=10/10)',
        font=fnt2, fill=(80,80,80), anchor='mt')

figs4 = vstack_imgs([banner4, prot], pad=0)
figs4 = add_panel_label(figs4, 'A', size=60)
figs4.save(f'{OUT}/FigS4_proteomics.png', dpi=(300,300))
print('FigS4 saved')

# ================================================================
# FigS5 — Phenotype Specificity + Cross-species (existing tiff)
# ================================================================
spec = load_img(f'{EFIGS}/Figure4_specificity_crossspecies.tiff')
spec = scale_to_w(spec)

banner5 = Image.new('RGB', (W, 100), (255,255,255))
d5 = ImageDraw.Draw(banner5)
d5.text((W//2, 14), 'Figure S5. HFpEF Metabolic Signature: Phenotype Specificity and Cross-Species Divergence',
        font=fnt, fill=(20,20,20), anchor='mt')
d5.text((W//2, 62), 'Comparison across HFpEF, DCM, and pressure-overload; cross-species FAO NES comparison',
        font=fnt2, fill=(80,80,80), anchor='mt')

figs5 = vstack_imgs([banner5, spec], pad=0)
figs5 = add_panel_label(figs5, 'A', size=60)
figs5.save(f'{OUT}/FigS5_specificity.png', dpi=(300,300))
print('FigS5 saved')

# ================================================================
# FigS6 — STRING interactions table summary (bar chart)
# ================================================================
import pandas as pd
idf = pd.read_csv(f'{FIGS}/FigS_STRING_interactions.csv')

fig_s6, axes = plt.subplots(1, 2, figsize=(14, 7), facecolor='white')
fig_s6.suptitle('Figure S6. STRING Protein Interaction Network Summary (GSE194151 Key Genes)',
                fontsize=12, fontweight='bold', y=0.98)

# Panel A: top interacting gene pairs by score
idf['score'] = pd.to_numeric(idf['score'], errors='coerce')
idf['pair'] = idf['preferredName_A'] + ' – ' + idf['preferredName_B']
top_pairs = idf.nlargest(15, 'score')[['pair','score']].reset_index(drop=True)
axes[0].barh(top_pairs['pair'][::-1], top_pairs['score'][::-1],
             color='#4472C4', edgecolor='white', height=0.65)
axes[0].set_xlabel('STRING Interaction Score', fontsize=10)
axes[0].set_title('A   Top 15 Protein Interaction Pairs\n    (confidence score)', fontsize=10, fontweight='bold', loc='left')
axes[0].set_xlim(0, 1050)
axes[0].axvline(900, color='#D6604D', linestyle='--', linewidth=1.0, label='High confidence (>900)')
axes[0].axvline(700, color='#F4A261', linestyle=':', linewidth=1.0, label='Threshold (700)')
axes[0].legend(fontsize=8)
axes[0].spines['top'].set_visible(False)
axes[0].spines['right'].set_visible(False)
axes[0].grid(axis='x', alpha=0.25)

# Panel B: degree distribution (how many partners each gene has)
all_genes = pd.concat([idf['preferredName_A'], idf['preferredName_B']])
degree = all_genes.value_counts().head(15)
colors_d = ['#D6604D' if g in ['Ppara','Tgfb1','Col1a1','Cpt1b'] else '#4472C4'
            for g in degree.index]
axes[1].bar(range(len(degree)), degree.values,
            color=colors_d, edgecolor='white', zorder=3)
axes[1].set_xticks(range(len(degree)))
axes[1].set_xticklabels(degree.index, rotation=45, ha='right', fontsize=9)
axes[1].set_ylabel('Number of Interaction Partners (Degree)', fontsize=10)
axes[1].set_title('B   Network Degree Distribution\n    (top 15 hub genes)', fontsize=10, fontweight='bold', loc='left')
axes[1].grid(axis='y', alpha=0.25, zorder=0)
axes[1].spines['top'].set_visible(False)
axes[1].spines['right'].set_visible(False)
legend_d = [mpatches.Patch(color='#D6604D', label='Key hub genes (PPARα, TGFβ1, etc.)'),
            mpatches.Patch(color='#4472C4', label='Other network genes')]
axes[1].legend(handles=legend_d, fontsize=8)

plt.tight_layout()
plt.savefig(f'{OUT}/FigS6_STRING_summary.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print('FigS6 saved')

print('\nAll supplementary figures saved to:', OUT)
