"""
run_sex_stratified.py
Sex-stratified re-analysis of GSE194151 (male n=15, female n=15 separately)
Generates Figure S4: sex-stratified NES comparison
"""
import os, gzip, warnings
warnings.filterwarnings('ignore')

import GEOparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats
import gseapy as gp

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))

BASE  = BASE_DIR
DATA  = _os.path.join(BASE_DIR, 'data')
OUT   = _os.path.join(BASE_DIR, 'figures_out')
os.makedirs(OUT, exist_ok=True)

MOUSE_GSETS = {
    'FAO_KEGG':         ['Cpt1a','Cpt1b','Cpt2','Slc25a20','Acsl1','Acsl3','Acsl4',
                         'Acadl','Acadm','Acads','Acadvl','Hadha','Hadhb','Hadh','Fabp3'],
    'Glycolysis_KEGG':  ['Hk1','Hk2','Pfkm','Aldoa','Gapdh','Eno1','Pkm','Ldha','Ldhb'],
    'OxPhos_KEGG':      ['Ndufa1','Ndufb1','Sdha','Sdhb','Uqcrc1','Cox4i1','Atp5a1','Cycs'],
    'Ketone_GO':        ['Hmgcs1','Hmgcs2','Hmgcl','Bdh1','Bdh2','Oxct1','Oxct2','Acat1'],
    'Insulin_Signaling':['Akt2','Slc2a4','Gsk3b','Akt1','Irs1','Irs2','Insr','Foxo1'],
    'PPAR_Signaling':   ['Lpl','Fabp4','Fabp3','Pparg','Ppara','Rxra','Acox1','Scd1'],
    'Cardiac_Fibrosis': ['Acta2','Vim','Col1a1','Col1a2','Col3a1','Tgfb1','Postn','Fn1','Ctgf'],
}

# ── Build Ensembl → symbol mapping from existing DEG files ───────────────────
print('Building Ensembl→symbol mapping...')
_ag = pd.read_csv(f'{BASE}/deg/GSE194151_DEG_all_genes.csv', index_col=0)
_gs = pd.read_csv(f'{BASE}/deg/GSE194151_DEG_gene_symbols.csv', index_col=0)
_ag2 = _ag[['log2FoldChange', 'baseMean']].round(6).copy()
_ag2['ens'] = _ag2.index
_gs2 = _gs[['log2FoldChange', 'baseMean']].round(6).copy()
_gs2['sym'] = _gs2.index
_m = _ag2.merge(_gs2, on=['log2FoldChange', 'baseMean'], how='inner')
ENS_TO_SYM = dict(zip(_m['ens'], _m['sym']))
print(f'  Ensembl→symbol map: {len(ENS_TO_SYM)} entries')

# ── Load count matrix ─────────────────────────────────────────────────────────
print('Loading GSE194151 count matrix...')
count_file = f'{DATA}/GSE194151_GSE194151_HFpEF_B6.mm10_Ensembl97.kallisto_counts.txt.gz'
with gzip.open(count_file, 'rt') as f:
    lines = f.readlines()
skip = sum(1 for l in lines if l.startswith('!') or l.startswith('#'))
from io import StringIO
counts_raw = pd.read_csv(StringIO(''.join(lines[skip:])), sep='\t', index_col=0)
counts_raw = counts_raw.select_dtypes(include=[np.number])
counts_raw = counts_raw.round(0).astype(int)
counts_raw = counts_raw[(counts_raw > 0).any(axis=1)]
print(f'  Count matrix: {counts_raw.shape}')

# ── Load metadata with sex labels ─────────────────────────────────────────────
print('Loading sample metadata...')
gse = GEOparse.get_GEO(geo='GSE194151', destdir=DATA, silent=True)
gsm_order = list(gse.gsms.keys())
assert len(gsm_order) == counts_raw.shape[1]
counts_raw.columns = gsm_order

rows = []
for gsm_name, gsm in gse.gsms.items():
    chars_list = gsm.metadata.get('characteristics_ch1', [])
    chars = ' '.join(chars_list).lower()
    title = gsm.metadata.get('title', [''])[0].lower()

    # Group
    if 'hfd' in chars or 'l-name' in chars or 'hfpef' in chars or 'hfpef' in title:
        group = 'HFpEF'
    elif 'control diet' in chars or 'control' in chars or 'ctrl' in chars:
        group = 'Control'
    else:
        group = None

    # Sex — look for "Sex: F" or "Sex: M" in characteristics
    sex = None
    for c in chars_list:
        cl = c.lower().strip()
        if cl.startswith('sex:'):
            val = cl.split('sex:')[-1].strip()
            if val.startswith('f'):
                sex = 'Female'
            elif val.startswith('m'):
                sex = 'Male'
        # Also try title prefix: YF* = young female, YM* = young male
    if sex is None:
        t = gsm.metadata.get('title', [''])[0]
        if '_YF' in t or '_F' in t:
            sex = 'Female'
        elif '_YM' in t or '_M' in t:
            sex = 'Male'

    rows.append({'sample': gsm_name, 'group': group, 'sex': sex})

meta_all = pd.DataFrame(rows).set_index('sample')
print(f'  Sex counts:\n{meta_all["sex"].value_counts()}')
print(f'  Group counts:\n{meta_all["group"].value_counts()}')

# ── DESeq2 + GSEA per sex ─────────────────────────────────────────────────────
def run_sex(sex_label, counts_raw, meta_all):
    print(f'\n--- {sex_label} ---')
    meta = meta_all[(meta_all['sex'] == sex_label) & (meta_all['group'].notna())][['group']].copy()
    counts = counts_raw[meta.index]

    # Pre-filter
    counts_t = counts.T
    keep = (counts_t >= 5).sum(axis=0) >= max(2, int(counts_t.shape[0] * 0.15))
    counts_t = counts_t.loc[:, keep]
    counts = counts_t.T
    print(f'  Samples: {meta["group"].value_counts().to_dict()}  Genes after filter: {counts.shape[0]}')

    # DESeq2
    meta_ds = meta.copy()
    meta_ds['group'] = meta_ds['group'].astype('category')
    dds = DeseqDataSet(counts=counts.T, metadata=meta_ds,
                       design_factors='group', refit_cooks=True, quiet=True)
    dds.deseq2()
    stat = DeseqStats(dds, contrast=['group','HFpEF','Control'], quiet=True)
    stat.summary()
    res = stat.results_df.dropna(subset=['pvalue'])

    # GSEA ranking
    res['rank'] = np.sign(res['log2FoldChange']) * (-np.log10(res['pvalue'].clip(lower=1e-300)))

    # Map Ensembl → symbol using pre-built mapping
    res.index = [ENS_TO_SYM.get(i, i) for i in res.index]

    rnk = res['rank'].sort_values(ascending=False)
    rnk = rnk[~rnk.index.duplicated(keep='first')]

    # GSEA
    results = {}
    for gs_name, genes in MOUSE_GSETS.items():
        gs_genes = [g for g in genes if g in rnk.index]
        if len(gs_genes) < 3:
            results[gs_name] = {'NES': 0.0, 'fdr': 1.0}
            continue
        try:
            pre = gp.prerank(rnk=rnk, gene_sets={gs_name: gs_genes},
                             min_size=3, max_size=500,
                             permutation_num=1000, seed=42, verbose=False)
            r = pre.res2d
            # gseapy uses lowercase column names: 'nes', 'fdr'
            nes_col = 'nes' if 'nes' in r.columns else ('NES' if 'NES' in r.columns else None)
            fdr_col = 'fdr' if 'fdr' in r.columns else ('FDR q-val' if 'FDR q-val' in r.columns else None)
            results[gs_name] = {
                'NES': float(r.loc[gs_name, nes_col]) if (gs_name in r.index and nes_col) else 0.0,
                'fdr': float(r.loc[gs_name, fdr_col]) if (gs_name in r.index and fdr_col) else 1.0
            }
        except Exception as e:
            results[gs_name] = {'NES': 0.0, 'fdr': 1.0}
            print(f'    GSEA error {gs_name}: {e}')
    return results

results_M = run_sex('Male',   counts_raw, meta_all)
results_F = run_sex('Female', counts_raw, meta_all)

# ── Figure S4: sex-stratified NES comparison ──────────────────────────────────
print('\nGenerating Figure S4...')
pathways = list(MOUSE_GSETS.keys())
short = ['FAO','Glycolysis','OxPhos','Ketone','Insulin','PPARα','Fibrosis']

nes_m = [results_M[p]['NES'] for p in pathways]
nes_f = [results_F[p]['NES'] for p in pathways]
fdr_m = [results_M[p]['fdr'] for p in pathways]
fdr_f = [results_F[p]['fdr'] for p in pathways]

x = np.arange(len(pathways))
width = 0.35

BLUE  = '#1F6FBF'
PINK  = '#C0396B'
ALPHA_SIG = 1.0
ALPHA_NS  = 0.45

fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

for i, (nm, nf, fm, ff) in enumerate(zip(nes_m, nes_f, fdr_m, fdr_f)):
    ax.bar(x[i]-width/2, nm, width, color=BLUE,
           alpha=ALPHA_SIG if fm<0.1 else ALPHA_NS, edgecolor='white', linewidth=0.5)
    ax.bar(x[i]+width/2, nf, width, color=PINK,
           alpha=ALPHA_SIG if ff<0.1 else ALPHA_NS, edgecolor='white', linewidth=0.5)
    # significance stars
    for xpos, nes, fdr in [(x[i]-width/2, nm, fm), (x[i]+width/2, nf, ff)]:
        if fdr < 0.05:
            ax.text(xpos, nes + (0.05 if nes >= 0 else -0.12), '**',
                    ha='center', va='bottom', fontsize=9, color='#222222', fontweight='bold')
        elif fdr < 0.10:
            ax.text(xpos, nes + (0.05 if nes >= 0 else -0.12), '*',
                    ha='center', va='bottom', fontsize=9, color='#222222')

ax.axhline(0, color='#333333', linewidth=0.8, zorder=0)
ax.axhline(1.5,  color='#888888', linewidth=0.6, linestyle='--', zorder=0, alpha=0.5)
ax.axhline(-1.5, color='#888888', linewidth=0.6, linestyle='--', zorder=0, alpha=0.5)

ax.set_xticks(x)
ax.set_xticklabels(short, fontsize=10)
ax.set_ylabel('Normalized Enrichment Score (NES)', fontsize=11)
ax.set_title('Figure S4. Sex-Stratified GSEA — GSE194151 (HFD+L-NAME vs. Control)\n'
             'Male (n=15) and Female (n=15) analyzed independently',
             fontsize=10, pad=10)
ax.set_ylim(-3.2, 3.0)
ax.spines[['top','right']].set_visible(False)

legend_els = [
    mpatches.Patch(color=BLUE,  label='Male (n=15)'),
    mpatches.Patch(color=PINK,  label='Female (n=15)'),
    mpatches.Patch(color='gray', alpha=0.4, label='FDR≥0.10 (not significant)'),
]
ax.legend(handles=legend_els, fontsize=9, loc='upper right', framealpha=0.85)
ax.text(0.01, 0.02,
        '** FDR<0.05   * FDR<0.10   Dashed lines: NES=±1.5',
        transform=ax.transAxes, fontsize=8, color='#555555', va='bottom')

plt.tight_layout()
outpath = f'{OUT}/FigureS4_SexStratified_GSEA.png'
plt.savefig(outpath, dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print(f'Saved: {outpath}')

# ── Save NES table ────────────────────────────────────────────────────────────
tbl = pd.DataFrame({
    'Pathway': pathways,
    'NES_Male': nes_m, 'FDR_Male': fdr_m,
    'NES_Female': nes_f, 'FDR_Female': fdr_f,
})
tbl.to_csv(f'{BASE}/gsea/GSE194151_SexStratified_GSEA.csv', index=False)
print('NES table saved.')

# ── Print concordance summary ─────────────────────────────────────────────────
print('\n=== Concordance summary ===')
print(f'{"Pathway":<22} {"NES_M":>7} {"FDR_M":>7} {"NES_F":>7} {"FDR_F":>7} {"Concordant?"}')
for p, nm, fm, nf, ff in zip(pathways, nes_m, fdr_m, nes_f, fdr_f):
    concordant = 'YES' if np.sign(nm) == np.sign(nf) else 'NO'
    print(f'{p:<22} {nm:>7.3f} {fm:>7.3f} {nf:>7.3f} {ff:>7.3f}  {concordant}')
