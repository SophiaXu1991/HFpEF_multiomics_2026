"""Process GSE209548: extract TAR -> merge counts -> DESeq2 + GSEA"""
import os, gzip, io, tarfile, warnings, re
warnings.filterwarnings('ignore')
import GEOparse, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import gseapy as gp
import mygene

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))

BASE = BASE_DIR
DATA = _os.path.join(BASE_DIR, 'data'); DEG = f'{BASE}/deg'; GSEA_DIR = f'{BASE}/gsea'
PLTS = f'{BASE}/plots'; TMPD = f'{BASE}/tmp'; os.makedirs(TMPD, exist_ok=True)

MOUSE_GSETS = {
    'FAO_KEGG':        ['Cpt1a','Cpt1b','Cpt2','Slc25a20','Acsl1','Acsl3','Acsl4',
                        'Acadl','Acadm','Acads','Acadvl','Hadha','Hadhb','Hadh','Fabp3'],
    'Ketone_GO':       ['Hmgcs1','Hmgcs2','Hmgcl','Bdh1','Bdh2','Oxct1','Oxct2','Acat1'],
    'PPAR_Signaling':  ['Ppara','Pparg','Rxra','Fabp3','Fabp4','Lpl','Scd1','Acox1'],
    'OxPhos_KEGG':     ['Ndufa1','Ndufb1','Sdha','Sdhb','Uqcrc1','Cox4i1','Atp5a1','Cycs'],
    'Glycolysis_KEGG': ['Hk1','Hk2','Pfkm','Aldoa','Gapdh','Eno1','Pkm','Ldha','Ldhb'],
    'Cardiac_Fibrosis':['Col1a1','Col1a2','Col3a1','Postn','Fn1','Tgfb1','Acta2','Vim','Ctgf'],
    'Insulin_Signaling':['Insr','Irs1','Irs2','Akt1','Akt2','Foxo1','Gsk3b','Slc2a4'],
}

# ── 1. Build count matrix from TAR ───────────────────────────
tar_path = f'{DATA}/GSE209548_RAW.tar'
print('Extracting count matrix from TAR...')
frames = {}
with tarfile.open(tar_path) as tf:
    for m in tf.getmembers():
        match = re.match(r'(GSM\d+)_(\w+)\.tab\.gz', m.name)
        if not match:
            continue
        gsm_id, sname = match.groups()
        fobj = tf.extractfile(m)
        raw = gzip.open(fobj, 'rt', encoding='utf-8', errors='replace').read()
        df = pd.read_csv(io.StringIO(raw), sep='\t', index_col=0, header=0)
        col = df.columns[0]
        frames[gsm_id] = df[col]

counts = pd.DataFrame(frames)
counts.index.name = 'gene'
print(f'Combined matrix: {counts.shape}')
print(f'First genes: {counts.index[:3].tolist()}')
print(f'Samples: {counts.columns.tolist()}')

# ── 2. Sample metadata ────────────────────────────────────────
gse = GEOparse.get_GEO(geo='GSE209548', destdir=DATA, silent=True)
meta_rows = []
for gname, gsm in gse.gsms.items():
    chars = {}
    for c in gsm.metadata.get('characteristics_ch1', []):
        if ':' in c:
            k, v = c.split(':', 1)
            chars[k.strip().lower()] = v.strip().lower()
    gtype = chars.get('genotype', '')
    treat = chars.get('treatment', '')
    meta_rows.append({'sample': gname, 'genotype': gtype, 'treatment': treat})

meta = pd.DataFrame(meta_rows).set_index('sample')
print('\nMetadata:')
print(meta.to_string())

# ── 3. Select WT only, classify groups ───────────────────────
wt = meta[meta['genotype'].str.contains('wt', case=False)].copy()
wt['group'] = wt['treatment'].apply(lambda t:
    'HFpEF' if 'high fat' in t else ('Control' if 'chow' in t else None))
wt = wt.dropna(subset=['group'])
print(f'\nWT samples: {wt["group"].value_counts().to_dict()}')

# ── 4. DESeq2 ─────────────────────────────────────────────────
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats

shared = counts.columns.intersection(wt.index)
ct = counts[shared].T.copy().astype(int)
m  = wt.loc[shared, ['group']].copy()
print(f'\nDESeq2 input: {ct.shape}')

keep = (ct >= 5).sum(axis=0) >= 2
ct = ct.loc[:, keep]
print(f'After filter: {ct.shape[1]} genes')

dds = DeseqDataSet(counts=ct, metadata=m, design_factors='group',
                   ref_level=['group', 'Control'], refit_cooks=True, quiet=True)
dds.deseq2()
st = DeseqStats(dds, quiet=True); st.summary()
res = st.results_df.copy()
res['rank_score'] = np.sign(res['log2FoldChange']) * (-np.log10(res['pvalue'].clip(1e-300)))
res = res.sort_values('rank_score', ascending=False)

sig = (res['padj'] < 0.05).sum()
up  = ((res['padj'] < 0.05) & (res['log2FoldChange'] > 0)).sum()
dn  = ((res['padj'] < 0.05) & (res['log2FoldChange'] < 0)).sum()
print(f'Sig:{sig} (up={up}, dn={dn})')
res.to_csv(f'{DEG}/GSE209548_DEG_all_genes.csv')
print(f'Saved {DEG}/GSE209548_DEG_all_genes.csv')

# ── 5. Gene symbol mapping ────────────────────────────────────
print('\nMapping Ensembl -> symbol...')
mg = mygene.MyGeneInfo()
ids = res.index.str.split('.').str[0].tolist()
q = mg.querymany(ids, scopes='ensembl.gene', fields='symbol', species='mouse', verbose=False)
imap = {h['query']: h['symbol'] for h in q if 'symbol' in h}
res2 = res.copy()
res2.index = [imap.get(e.split('.')[0], None) for e in res.index]
res2 = res2[res2.index.notna() & ~res2.index.duplicated()]
print(f'Mapped: {len(res2)}/{len(res)}')
res2.to_csv(f'{DEG}/GSE209548_DEG_gene_symbols.csv')

# ── 6. GSEA ───────────────────────────────────────────────────
ranked = res2['rank_score'].dropna().drop_duplicates().sort_values(ascending=False)
rnk = pd.DataFrame({'gene': ranked.index, 'score': ranked.values})
print('\nGSEA:')
try:
    pre = gp.prerank(rnk=rnk, gene_sets=MOUSE_GSETS, min_size=5, max_size=500,
                     permutation_num=1000, outdir=TMPD, seed=42, verbose=False, no_plot=True)
    r = pre.res2d.copy()
    r['dataset'] = 'GSE209548'
    for idx, row in r.iterrows():
        nes = row.get('nes', row.get('NES', '?'))
        fdr = row.get('fdr', row.get('FDR', '?'))
        try:
            print(f'  {str(idx):<25} NES={float(nes):+.3f}  FDR={float(fdr):.4f}')
        except Exception:
            pass
    r.to_csv(f'{GSEA_DIR}/GSE209548_GSEA.csv')
    print('  Saved GSE209548_GSEA.csv')
except Exception as e:
    print(f'  GSEA error: {e}')

# ── 7. Volcano ────────────────────────────────────────────────
df = res2.dropna(subset=['log2FoldChange', 'padj']).copy()
df['nlp'] = -np.log10(df['padj'].clip(1e-300))
up_m = (df.padj < 0.05) & (df.log2FoldChange > 0.5)
dn_m = (df.padj < 0.05) & (df.log2FoldChange < -0.5)
ns_m = ~(up_m | dn_m)
fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(df.loc[ns_m, 'log2FoldChange'], df.loc[ns_m, 'nlp'],    c='#CCCCCC', s=3, alpha=0.4, lw=0, rasterized=True)
ax.scatter(df.loc[dn_m, 'log2FoldChange'], df.loc[dn_m, 'nlp'],    c='#2166AC', s=6, alpha=0.7, lw=0, rasterized=True)
ax.scatter(df.loc[up_m, 'log2FoldChange'], df.loc[up_m, 'nlp'],    c='#D6604D', s=6, alpha=0.7, lw=0, rasterized=True)
for g in ['Cpt1b', 'Cpt1a', 'Hadha', 'Acadm', 'Col1a1', 'Tgfb1']:
    if g in df.index:
        r2 = df.loc[g]
        ax.scatter(r2.log2FoldChange, r2.nlp, c='gold', s=55, zorder=6, edgecolors='black', lw=0.6)
        ax.annotate(g, (r2.log2FoldChange, r2.nlp), fontsize=7,
                    xytext=(5, 3), textcoords='offset points', fontweight='bold')
ax.axhline(-np.log10(0.05), color='gray', lw=0.7, ls='--')
ax.axvline(0.5, color='gray', lw=0.4, ls=':')
ax.axvline(-0.5, color='gray', lw=0.4, ls=':')
ax.text(0.98, 0.98, f'Up:{up_m.sum()}', transform=ax.transAxes, ha='right', va='top',
        color='#D6604D', fontsize=8, fontweight='bold')
ax.text(0.02, 0.98, f'Down:{dn_m.sum()}', transform=ax.transAxes, ha='left', va='top',
        color='#2166AC', fontsize=8, fontweight='bold')
ax.set_xlabel(r'$log_2$ Fold Change', fontsize=9)
ax.set_ylabel(r'$-log_{10}$(padj)', fontsize=9)
ax.set_title('GSE209548 HFD vs Chow (WT mouse cardiomyocytes)', fontsize=9, fontweight='bold')
ax.spines[['top', 'right']].set_visible(False)
plt.tight_layout()
out = f'{PLTS}/volcano_GSE209548.pdf'
fig.savefig(out, bbox_inches='tight', dpi=150)
plt.close(fig)
print(f'\nVolcano: {out}')

# ── Summary ───────────────────────────────────────────────────
print('\n' + '='*50 + '\nOUTPUT FILES\n' + '='*50)
for d, lbl in [(DEG, 'DEG'), (GSEA_DIR, 'GSEA'), (PLTS, 'Plots')]:
    fl = sorted(os.listdir(d))
    if fl:
        print(f'\n{lbl}:')
        for f in fl:
            sz = os.path.getsize(f'{d}/{f}') // 1024
            print(f'  {f}  ({sz}KB)')
