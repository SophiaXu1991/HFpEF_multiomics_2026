"""
HFpEF Multi-omics — Full DEG Pipeline v3 (dataset-specific loaders)
Fixes:
  - GSE194151: Y* column names → positional GSM alignment
  - GSE249409: download count file; keyword "non-failing" → Control
  - GSE209548: download count file; "chow" → Control, "high fat" → HFpEF
  - GSE141910: download count file; exact etiology matching
  - GSE53437:  miRNA float data → quantile-norm + t-test (not DESeq2)
"""

import os, sys, gzip, re, warnings, urllib.request, io
warnings.filterwarnings('ignore')

import GEOparse
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))

BASE  = BASE_DIR
DATA  = _os.path.join(BASE_DIR, 'data')
DEG   = f'{BASE}/deg'
GSEA  = f'{BASE}/gsea'
PLOTS = f'{BASE}/plots'
for d in [DATA, DEG, GSEA, PLOTS]:
    os.makedirs(d, exist_ok=True)

# ─────────────────────────────────────────────
# GENE SETS
# ─────────────────────────────────────────────
MOUSE_GSETS = {
    'FAO_KEGG':        ['Cpt1a','Cpt1b','Cpt2','Slc25a20','Acsl1','Acsl3','Acsl4',
                        'Acadl','Acadm','Acads','Acadvl','Hadha','Hadhb','Hadh',
                        'Echs1','Ehhadh','Acaa2','Fabp3'],
    'Ketone_GO':       ['Hmgcs1','Hmgcs2','Hmgcl','Bdh1','Bdh2','Oxct1','Oxct2','Acat1'],
    'PPAR_Signaling':  ['Ppara','Ppard','Pparg','Rxra','Fabp3','Fabp4','Lpl','Scd1','Acox1','Plin2'],
    'OxPhos_KEGG':     ['Ndufa1','Ndufa2','Ndufb1','Ndufb2','Sdha','Sdhb','Uqcrc1',
                        'Cox4i1','Cox5a','Atp5a1','Atp5b','Cycs'],
    'Glycolysis_KEGG': ['Hk1','Hk2','Pfkm','Aldoa','Gapdh','Pgk1','Eno1','Pkm','Ldha','Ldhb'],
    'Cardiac_Fibrosis':['Col1a1','Col1a2','Col3a1','Postn','Fn1','Tgfb1','Tgfb2',
                        'Acta2','Tagln','Vim','Lox','Ctgf','Thbs1'],
    'Insulin_Signaling':['Insr','Irs1','Irs2','Pik3ca','Akt1','Akt2','Foxo1','Gsk3b','Slc2a4'],
}
HUMAN_GSETS = {
    'FAO_KEGG':        ['CPT1A','CPT1B','CPT2','SLC25A20','ACSL1','ACSL3','ACSL4',
                        'ACADL','ACADM','ACADS','ACADVL','HADHA','HADHB','HADH',
                        'ECHS1','EHHADH','ACAA2','FABP3'],
    'Ketone_GO':       ['HMGCS1','HMGCS2','HMGCL','BDH1','BDH2','OXCT1','OXCT2','ACAT1'],
    'PPAR_Signaling':  ['PPARA','PPARD','PPARG','RXRA','FABP3','FABP4','LPL','SCD','ACOX1'],
    'OxPhos_KEGG':     ['NDUFA1','NDUFA2','NDUFB1','NDUFB2','SDHA','SDHB','UQCRC1',
                        'COX4I1','COX5A','ATP5A1','ATP5B','CYCS'],
    'Glycolysis_KEGG': ['HK1','HK2','PFKM','ALDOA','GAPDH','PGK1','ENO1','PKM','LDHA','LDHB'],
    'Cardiac_Fibrosis':['COL1A1','COL1A2','COL3A1','POSTN','FN1','TGFB1','TGFB2',
                        'ACTA2','TAGLN','VIM','LOX','CTGF','THBS1'],
    'Insulin_Signaling':['INSR','IRS1','IRS2','PIK3CA','AKT1','AKT2','FOXO1','GSK3B','SLC2A4'],
}

# ─────────────────────────────────────────────
# UTILITY
# ─────────────────────────────────────────────
def dl(url, dest):
    if os.path.exists(dest):
        return True
    print(f'    Downloading {os.path.basename(dest)}...')
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f'    Failed: {e}')
        return False

def read_tsv(path, **kwargs):
    op  = gzip.open if path.endswith('.gz') else open
    sep = kwargs.pop('sep', '\t')
    with op(path, 'rt', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    skip = sum(1 for l in lines if l.startswith('!') or l.startswith('#'))
    content = ''.join(lines[skip:])
    return pd.read_csv(io.StringIO(content), sep=sep, index_col=0, **kwargs)

def run_gsea(results_df, gene_sets, dataset_id):
    import gseapy as gp
    ranked = (results_df['rank_score']
              .dropna().drop_duplicates()
              .sort_values(ascending=False))
    rnk = pd.DataFrame({'gene': ranked.index, 'score': ranked.values})
    try:
        pre = gp.prerank(rnk=rnk, gene_sets=gene_sets, min_size=5, max_size=500,
                         permutation_num=1000, outdir=None, seed=42, verbose=False)
        res = pre.res2d.rename(columns={'NOM p-val':'pval','FDR q-val':'FDR'})
        res['dataset'] = dataset_id
        print(f'  GSEA {dataset_id}:')
        for idx, row in res.iterrows():
            try:
                print(f'    {str(idx):<25} NES={float(row["NES"]):+.3f}  FDR={float(row["FDR"]):.4f}')
            except Exception:
                pass
        return res
    except Exception as e:
        print(f'  GSEA error: {e}')
        return pd.DataFrame()

def plot_volcano(res, dataset_id, title, highlight=None):
    if 'padj' not in res.columns or 'log2FoldChange' not in res.columns:
        return
    df  = res.dropna(subset=['log2FoldChange','padj']).copy()
    df['nlp'] = -np.log10(df['padj'].clip(1e-300))
    up   = (df.padj < 0.05) & (df.log2FoldChange >  0.5)
    down = (df.padj < 0.05) & (df.log2FoldChange < -0.5)
    ns   = ~(up | down)
    fig, ax = plt.subplots(figsize=(6,5))
    ax.scatter(df.loc[ns,'log2FoldChange'],   df.loc[ns,'nlp'],   c='#CCCCCC', s=3,  alpha=0.4, lw=0, rasterized=True)
    ax.scatter(df.loc[down,'log2FoldChange'], df.loc[down,'nlp'], c='#2166AC', s=6,  alpha=0.7, lw=0, rasterized=True)
    ax.scatter(df.loc[up,'log2FoldChange'],   df.loc[up,'nlp'],   c='#D6604D', s=6,  alpha=0.7, lw=0, rasterized=True)
    if highlight:
        for g in highlight:
            if g in df.index:
                r = df.loc[g]
                ax.scatter(r.log2FoldChange, r.nlp, c='gold', s=55, zorder=6, edgecolors='black', lw=0.6)
                ax.annotate(g,(r.log2FoldChange,r.nlp),fontsize=7,xytext=(5,3),textcoords='offset points',fontweight='bold')
    ax.axhline(-np.log10(0.05), color='gray', lw=0.7, ls='--')
    ax.axvline(0.5,  color='gray', lw=0.4, ls=':')
    ax.axvline(-0.5, color='gray', lw=0.4, ls=':')
    ax.text(0.98,0.98,f'Up: {up.sum()}',   transform=ax.transAxes,ha='right',va='top',color='#D6604D',fontsize=8,fontweight='bold')
    ax.text(0.02,0.98,f'Down: {down.sum()}',transform=ax.transAxes,ha='left', va='top',color='#2166AC',fontsize=8,fontweight='bold')
    ax.set_xlabel(r'$log_2$ Fold Change',fontsize=9)
    ax.set_ylabel(r'$-log_{10}$(padj)',fontsize=9)
    ax.set_title(title,fontsize=10,fontweight='bold')
    ax.spines[['top','right']].set_visible(False)
    plt.tight_layout()
    out = f'{PLOTS}/volcano_{dataset_id}.pdf'
    fig.savefig(out, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f'  Volcano: {out}')


# ═══════════════════════════════════════════════════════════════
# DATASET 1: GSE194151  Mouse whole-heart HFD+L-NAME vs Control
# Count columns: Y1..Y30  ←→  GSM metadata order
# ═══════════════════════════════════════════════════════════════
def process_GSE194151():
    print('\n' + '='*60 + '\nGSE194151 (mouse HFD+L-NAME)\n' + '='*60)
    gse_id = 'GSE194151'

    # Load count matrix
    count_file = f'{DATA}/{gse_id}_GSE194151_HFpEF_B6.mm10_Ensembl97.kallisto_counts.txt.gz'
    if not os.path.exists(count_file):
        url = ('https://ftp.ncbi.nlm.nih.gov/geo/series/GSE194nnn/GSE194151/suppl/'
               'GSE194151_GSE194151_HFpEF_B6.mm10_Ensembl97.kallisto_counts.txt.gz')
        if not dl(url, count_file):
            return None

    counts = read_tsv(count_file)
    counts = counts.select_dtypes(include=[np.number])
    # Round to integer (kallisto TPM → nearest int for DESeq2)
    counts = counts.round(0).astype(int)
    counts = counts[(counts > 0).any(axis=1)]
    print(f'  Count matrix: {counts.shape}  cols={list(counts.columns[:5])}...')

    # Build metadata from GEO — positional alignment (30 cols = 30 GSMs)
    gse = GEOparse.get_GEO(geo=gse_id, destdir=DATA, silent=True)
    gsm_order = list(gse.gsms.keys())
    assert len(gsm_order) == counts.shape[1], \
        f'Sample count mismatch: {len(gsm_order)} GSMs vs {counts.shape[1]} cols'

    # Map column → GSM
    col_to_gsm = dict(zip(counts.columns, gsm_order))
    counts.columns = [col_to_gsm[c] for c in counts.columns]

    # Build metadata
    rows = []
    for gsm_name, gsm in gse.gsms.items():
        chars = ' '.join(gsm.metadata.get('characteristics_ch1', [])).lower()
        title = gsm.metadata.get('title', [''])[0].lower()
        if 'hfd' in chars or 'l-name' in chars or 'hfpef' in chars or 'hfpef' in title:
            group = 'HFpEF'
        elif 'control diet' in chars or 'control' in chars or 'ctrl' in chars:
            group = 'Control'
        else:
            group = None
        rows.append({'sample': gsm_name, 'group': group})
    meta = pd.DataFrame(rows).dropna(subset=['group']).set_index('sample')[['group']]
    print(f'  Groups: {meta["group"].value_counts().to_dict()}')

    # Keep common samples
    shared = counts.columns.intersection(meta.index)
    counts = counts[shared]
    meta   = meta.loc[shared]

    return run_deseq2_standard(counts, meta, gse_id,
                               highlight=['Cpt1b','Cpt2','Hadha','Acadm','Hadhb','Hmgcs2','Irs1'],
                               gsets=MOUSE_GSETS)


# ═══════════════════════════════════════════════════════════════
# DATASET 2: GSE249409  Mouse whole-heart HFD+mTAC vs Control
# ═══════════════════════════════════════════════════════════════
def process_GSE249409():
    print('\n' + '='*60 + '\nGSE249409 (mouse HFD+mTAC)\n' + '='*60)
    gse_id = 'GSE249409'

    # Try multiple possible filenames for supplementary count file
    candidates = [
        ('https://ftp.ncbi.nlm.nih.gov/geo/series/GSE249nnn/GSE249409/suppl/'
         'GSE249409_raw_counts.txt.gz',
         f'{DATA}/{gse_id}_raw_counts.txt.gz'),
        ('https://ftp.ncbi.nlm.nih.gov/geo/series/GSE249nnn/GSE249409/suppl/'
         'GSE249409_counts.txt.gz',
         f'{DATA}/{gse_id}_counts.txt.gz'),
    ]

    # Scan NCBI FTP directory for actual filenames
    import urllib.request
    try:
        ftp_index = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE249nnn/GSE249409/suppl/'
        with urllib.request.urlopen(ftp_index, timeout=15) as r:
            html = r.read().decode('utf-8', errors='replace')
        links = re.findall(r'href="([^"]+\.(?:txt|csv|tsv)(?:\.gz)?)"', html)
        for lnk in links:
            fname = os.path.basename(lnk)
            candidates.insert(0, (ftp_index + fname, f'{DATA}/{gse_id}_{fname}'))
    except Exception as e:
        print(f'  FTP scan failed: {e}')

    count_file = None
    for url, dest in candidates:
        if os.path.exists(dest):
            count_file = dest; break
        if dl(url, dest):
            count_file = dest; break

    gse = GEOparse.get_GEO(geo=gse_id, destdir=DATA, silent=True)

    if count_file is None:
        # Try pivot from SOFT (may work for some datasets)
        print('  No count file — trying SOFT VALUE pivot')
        try:
            counts = gse.pivot_samples('VALUE')
            if counts is not None and not counts.empty:
                counts = counts.fillna(0).round(0).astype(int)
                count_file = 'from_soft'
            else:
                print('  SKIP: no count data available')
                return None
        except Exception:
            print('  SKIP: no count data available')
            return None
    else:
        counts = read_tsv(count_file)
        counts = counts.select_dtypes(include=[np.number]).round(0).astype(int)
        counts = counts[(counts > 0).any(axis=1)]

    print(f'  Count matrix: {counts.shape}')

    rows = []
    for gsm_name, gsm in gse.gsms.items():
        chars = ' '.join(gsm.metadata.get('characteristics_ch1', [])).lower()
        title = gsm.metadata.get('title', [''])[0].lower()
        info  = chars + ' ' + title
        if 'non-failing' in info or 'control' in info or 'vehicle' in info or 'sham' in info:
            group = 'Control'
        elif 'hfpef' in info or 'tac' in info or 'hfd' in info or 'failing' in info:
            group = 'HFpEF'
        else:
            group = None
        rows.append({'sample': gsm_name, 'title': title, 'group': group})

    meta = pd.DataFrame(rows).dropna(subset=['group']).set_index('sample')[['group']]
    print(f'  Groups: {meta["group"].value_counts().to_dict()}')

    # Positional alignment if needed
    if counts.columns.intersection(meta.index).empty:
        gsm_list = [r['sample'] for r in rows if r['group'] is not None]
        if len(gsm_list) == counts.shape[1]:
            counts.columns = gsm_list
        else:
            # Use all GSMs in order
            all_gsm = list(gse.gsms.keys())
            if len(all_gsm) == counts.shape[1]:
                counts.columns = all_gsm

    shared = counts.columns.intersection(meta.index)
    if len(shared) < 4:
        print(f'  SKIP: only {len(shared)} aligned samples')
        return None

    counts = counts[shared]
    meta   = meta.loc[shared]

    return run_deseq2_standard(counts, meta, gse_id,
                               highlight=['Cpt1b','Hmgcs2','Irs1','Hadha','Acadm'],
                               gsets=MOUSE_GSETS)


# ═══════════════════════════════════════════════════════════════
# DATASET 3: GSE209548  Mouse cardiomyocyte HFD vs Chow
# ═══════════════════════════════════════════════════════════════
def process_GSE209548():
    print('\n' + '='*60 + '\nGSE209548 (mouse CM HFD)\n' + '='*60)
    gse_id = 'GSE209548'

    gse = GEOparse.get_GEO(geo=gse_id, destdir=DATA, silent=True)

    # Try FTP
    candidates = []
    try:
        ftp_index = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE209nnn/GSE209548/suppl/'
        with urllib.request.urlopen(ftp_index, timeout=15) as r:
            html = r.read().decode('utf-8', errors='replace')
        links = re.findall(r'href="([^"]+\.(?:txt|csv|tsv)(?:\.gz)?)"', html)
        for lnk in links:
            fname = os.path.basename(lnk)
            candidates.append((ftp_index + fname, f'{DATA}/{gse_id}_{fname}'))
    except Exception as e:
        print(f'  FTP scan: {e}')

    count_file = None
    for url, dest in candidates:
        if os.path.exists(dest):
            count_file = dest; break
        if dl(url, dest):
            count_file = dest; break

    if count_file is None:
        # Try pivot
        print('  No suppl file — trying SOFT VALUE pivot')
        for attr in ['VALUE','COUNT','READS']:
            try:
                counts = gse.pivot_samples(attr)
                if counts is not None and not counts.empty and counts.shape[0] > 100:
                    counts = counts.fillna(0).round(0).astype(int)
                    break
            except Exception:
                counts = None
        if counts is None:
            print('  SKIP')
            return None
    else:
        counts = read_tsv(count_file)
        counts = counts.select_dtypes(include=[np.number]).round(0).astype(int)
        counts = counts[(counts > 0).any(axis=1)]

    print(f'  Count matrix: {counts.shape}')

    rows = []
    for gsm_name, gsm in gse.gsms.items():
        chars = ' '.join(gsm.metadata.get('characteristics_ch1', [])).lower()
        title = gsm.metadata.get('title', [''])[0].lower()
        info  = chars + ' ' + title
        if 'chow' in info or ' cd' in info or 'control' in info or 'normal' in info:
            group = 'Control'
        elif 'high fat' in info or 'hfd' in info or 'hf diet' in info:
            group = 'HFpEF'
        else:
            group = None
        rows.append({'sample': gsm_name, 'group': group})

    meta = pd.DataFrame(rows).dropna(subset=['group']).set_index('sample')[['group']]
    print(f'  Groups: {meta["group"].value_counts().to_dict()}')

    # Positional alignment
    if counts.columns.intersection(meta.index).empty:
        gsm_order = [r['sample'] for _, r in
                     pd.DataFrame(rows).dropna(subset=['group']).iterrows()]
        all_gsm = list(gse.gsms.keys())
        if len(all_gsm) == counts.shape[1]:
            counts.columns = all_gsm
        elif len(gsm_order) == counts.shape[1]:
            counts.columns = gsm_order

    shared = counts.columns.intersection(meta.index)
    if len(shared) < 4:
        print(f'  SKIP: {len(shared)} aligned samples only')
        return None
    counts = counts[shared]
    meta   = meta.loc[shared]

    return run_deseq2_standard(counts, meta, gse_id,
                               highlight=['Cpt1b','Cpt1a','Hadha','Acadm'],
                               gsets=MOUSE_GSETS)


# ═══════════════════════════════════════════════════════════════
# DATASET 4: GSE141910  Human DCM vs Non-Failing
# ═══════════════════════════════════════════════════════════════
def process_GSE141910():
    print('\n' + '='*60 + '\nGSE141910 (human DCM)\n' + '='*60)
    gse_id = 'GSE141910'

    gse = GEOparse.get_GEO(geo=gse_id, destdir=DATA, silent=True)

    candidates = []
    try:
        ftp_index = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE141nnn/GSE141910/suppl/'
        with urllib.request.urlopen(ftp_index, timeout=15) as r:
            html = r.read().decode('utf-8', errors='replace')
        links = re.findall(r'href="([^"]+\.(?:txt|csv|tsv)(?:\.gz)?)"', html)
        for lnk in links:
            fname = os.path.basename(lnk)
            candidates.append((ftp_index + fname, f'{DATA}/{gse_id}_{fname}'))
    except Exception as e:
        print(f'  FTP scan: {e}')

    count_file = None
    for url, dest in sorted(candidates, key=lambda x: (
            'count' not in x[0].lower(), 'raw' not in x[0].lower())):
        if os.path.exists(dest):
            count_file = dest; break
        if dl(url, dest):
            count_file = dest; break

    if count_file is None:
        print('  SKIP: no count file')
        return None

    counts = read_tsv(count_file)
    counts = counts.select_dtypes(include=[np.number]).round(0).astype(int)
    counts = counts[(counts > 0).any(axis=1)]
    print(f'  Count matrix: {counts.shape}')

    rows = []
    for gsm_name, gsm in gse.gsms.items():
        chars = ' '.join(gsm.metadata.get('characteristics_ch1', [])).lower()
        # MUST check non-failing before failing to avoid substring match
        if 'non-failing' in chars or 'non failing' in chars or 'donor' in chars:
            group = 'Control'
        elif 'dcm' in chars or 'dilated' in chars or ('failing' in chars and 'non' not in chars):
            group = 'HFpEF'   # DCM in this context
        else:
            group = None
        rows.append({'sample': gsm_name, 'group': group})

    meta = pd.DataFrame(rows).dropna(subset=['group']).set_index('sample')[['group']]
    print(f'  Groups: {meta["group"].value_counts().to_dict()}')

    shared = counts.columns.intersection(meta.index)
    if len(shared) < 10:
        # Try positional
        all_gsm = list(gse.gsms.keys())
        if len(all_gsm) == counts.shape[1]:
            counts.columns = all_gsm
            shared = counts.columns.intersection(meta.index)

    if len(shared) < 10:
        print(f'  SKIP: {len(shared)} aligned samples')
        return None

    counts = counts[shared]
    meta   = meta.loc[shared]

    return run_deseq2_standard(counts, meta, gse_id,
                               highlight=['HMGCS2','ACADM','POSTN','COL1A1','ACTA2'],
                               gsets=HUMAN_GSETS)


# ═══════════════════════════════════════════════════════════════
# DATASET 5: GSE53437  Human circulating miRNA (microarray)
# NOTE: this dataset has hfREF + hfpEF groups — use fold-change + t-test
# ═══════════════════════════════════════════════════════════════
def process_GSE53437():
    print('\n' + '='*60 + '\nGSE53437 (human miRNA microarray)\n' + '='*60)
    gse_id = 'GSE53437'

    gse = GEOparse.get_GEO(geo=gse_id, destdir=DATA, silent=True)

    # Download all set files
    set_files = []
    try:
        ftp_index = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE53nnn/GSE53437/suppl/'
        with urllib.request.urlopen(ftp_index, timeout=15) as r:
            html = r.read().decode('utf-8', errors='replace')
        links = re.findall(r'href="([^"]+\.(?:txt|csv|tsv)(?:\.gz)?)"', html)
        for lnk in links:
            fname = os.path.basename(lnk)
            dest  = f'{DATA}/{gse_id}_{fname}'
            if os.path.exists(dest) or dl(ftp_index + fname, dest):
                set_files.append(dest)
    except Exception as e:
        print(f'  FTP scan: {e}')

    # Use already-cached file if scan fails
    cached = [f'{DATA}/{f}' for f in os.listdir(DATA)
              if f.startswith(gse_id) and f.endswith('.gz')]
    for c in cached:
        if c not in set_files:
            set_files.append(c)

    if not set_files:
        print('  SKIP: no data files')
        return None

    # Load and merge all sets; keep only miRNA probe rows (not mRNA)
    dfs = []
    for sf in set_files:
        if 'family' in sf or 'soft' in sf.lower():
            continue
        try:
            df = read_tsv(sf)
            # Drop 'Name' column if present (non-numeric)
            df = df.select_dtypes(include=[np.number])
            if df.shape[0] > 100:
                dfs.append(df)
                print(f'  Loaded: {os.path.basename(sf)} → {df.shape}')
        except Exception as e:
            print(f'  Skip {os.path.basename(sf)}: {e}')

    if not dfs:
        print('  SKIP: could not load any expression matrices')
        return None

    # Merge sets by common probes
    expr = dfs[0]
    for other in dfs[1:]:
        common_idx = expr.index.intersection(other.index)
        if len(common_idx) > 100:
            expr = pd.concat([expr.loc[common_idx], other.loc[common_idx]], axis=1)
    print(f'  Combined matrix: {expr.shape}')

    # Quantile normalise (log2 transform first)
    expr_log = np.log2(expr.replace(0, np.nan).fillna(np.nanmin(expr.values[expr.values > 0])))

    def quantile_normalize(df):
        rank_mean = df.stack().groupby(
            df.rank(method='first').stack().astype(int)).mean()
        return df.rank(method='min').stack().astype(int).map(rank_mean).unstack()

    expr_norm = quantile_normalize(expr_log)

    # Assign groups from column names
    def col_group(c):
        cl = c.lower()
        if 'hfpef' in cl or 'hfpef' in cl:
            return 'HFpEF'
        elif 'control' in cl or 'ctrl' in cl or 'normal' in cl:
            return 'Control'
        elif 'hfref' in cl or 'ref' in cl:
            return 'hfREF'   # separate group
        return None

    col_groups = {c: col_group(c) for c in expr_norm.columns}
    print(f'  Column groups: { {v: sum(1 for x in col_groups.values() if x==v) for v in set(col_groups.values())} }')

    # Use hfpEF vs Control if available; else hfREF vs Control as proxy
    hfpef_cols = [c for c, g in col_groups.items() if g == 'HFpEF']
    ref_cols   = [c for c, g in col_groups.items() if g == 'hfREF']
    ctrl_cols  = [c for c, g in col_groups.items() if g == 'Control']

    if len(hfpef_cols) >= 3 and len(ctrl_cols) >= 3:
        case_cols = hfpef_cols
        case_label = 'HFpEF'
    elif len(ref_cols) >= 3 and len(ctrl_cols) >= 3:
        case_cols = ref_cols
        case_label = 'hfREF'
        print('  NOTE: No hfpEF samples found — using hfREF vs Control as proxy')
    else:
        print('  SKIP: insufficient grouped samples')
        return None

    print(f'  Analysis: {case_label} (n={len(case_cols)}) vs Control (n={len(ctrl_cols)})')

    case_data = expr_norm[case_cols]
    ctrl_data = expr_norm[ctrl_cols]

    # T-test for each probe
    rows = []
    for probe in expr_norm.index:
        g1 = case_data.loc[probe].dropna().values
        g2 = ctrl_data.loc[probe].dropna().values
        if len(g1) < 3 or len(g2) < 3:
            continue
        lfc = g1.mean() - g2.mean()
        _, pval = stats.ttest_ind(g1, g2, equal_var=False)
        rows.append({'probe': probe, 'log2FoldChange': lfc, 'pvalue': pval,
                     'baseMean': expr_norm.loc[probe].mean()})

    res = pd.DataFrame(rows).set_index('probe')
    # BH correction
    from statsmodels.stats.multitest import multipletests
    _, res['padj'], _, _ = multipletests(res['pvalue'].fillna(1), method='fdr_bh')
    res['rank_score'] = np.sign(res['log2FoldChange']) * (-np.log10(res['pvalue'].clip(1e-300)))
    res = res.sort_values('rank_score', ascending=False)

    n_sig = (res['padj'] < 0.05).sum()
    print(f'  T-test done. Significant (padj<0.05): {n_sig}')

    out_csv = f'{DEG}/{gse_id}_DEG_all_genes.csv'
    res.to_csv(out_csv)
    print(f'  Saved: {out_csv}')

    # Volcano
    plot_volcano(res, gse_id, f'{gse_id} — {case_label} vs Control (miRNA)',
                 highlight=['hsa-miR-33a-5p','hsa-miR-181a-5p','hsa-miR-146a-5p'])

    return res


# ═══════════════════════════════════════════════════════════════
# SHARED DESeq2 RUNNER
# ═══════════════════════════════════════════════════════════════
def run_deseq2_standard(counts, meta, dataset_id, highlight=None, gsets=None):
    from pydeseq2.dds import DeseqDataSet
    from pydeseq2.ds import DeseqStats

    print(f'  DESeq2: {counts.shape[0]} genes × {counts.shape[1]} samples')

    counts_t = counts.T.copy()
    counts_t.index = counts_t.index.astype(str)
    meta = meta.loc[counts_t.index].copy()

    # Filter low-count genes
    keep = (counts_t >= 5).sum(axis=0) >= max(2, int(counts_t.shape[0] * 0.15))
    counts_t = counts_t.loc[:, keep]
    counts_t = counts_t.round(0).astype(int)

    dds = DeseqDataSet(
        counts=counts_t,
        metadata=meta,
        design_factors='group',
        ref_level=['group', 'Control'],
        refit_cooks=True,
        quiet=True,
    )
    dds.deseq2()
    stat = DeseqStats(dds, quiet=True)
    stat.summary()
    res = stat.results_df.copy()
    res['rank_score'] = np.sign(res['log2FoldChange']) * (-np.log10(res['pvalue'].clip(1e-300)))
    res = res.sort_values('rank_score', ascending=False)

    sig = (res['padj'] < 0.05).sum()
    up  = ((res['padj'] < 0.05) & (res['log2FoldChange'] > 0)).sum()
    dn  = ((res['padj'] < 0.05) & (res['log2FoldChange'] < 0)).sum()
    print(f'  Sig: {sig}  (up={up}, down={dn})')

    out_csv = f'{DEG}/{dataset_id}_DEG_all_genes.csv'
    res.to_csv(out_csv)
    print(f'  Saved: {out_csv}')

    if gsets:
        gsea_res = run_gsea(res, gsets, dataset_id)
        if not gsea_res.empty:
            gsea_res.to_csv(f'{GSEA}/{dataset_id}_GSEA.csv')

    plot_volcano(res, dataset_id,
                 f'{dataset_id} — HFpEF vs Control',
                 highlight=highlight)
    return res


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
all_results = {}

for fn, label in [
    (process_GSE194151, 'GSE194151'),
    (process_GSE249409, 'GSE249409'),
    (process_GSE209548, 'GSE209548'),
    (process_GSE141910, 'GSE141910'),
    (process_GSE53437,  'GSE53437'),
]:
    try:
        res = fn()
        if res is not None:
            all_results[label] = res
    except Exception as e:
        import traceback
        print(f'\nERROR in {label}: {e}')
        traceback.print_exc()

# ─── SUMMARY ──────────────────────────────────────────────────
print('\n' + '='*60 + '\nSUMMARY\n' + '='*60)
for gid, res in all_results.items():
    sig  = (res['padj'] < 0.05).sum()
    up   = ((res['padj'] < 0.05) & (res['log2FoldChange'] > 0)).sum()
    dn   = ((res['padj'] < 0.05) & (res['log2FoldChange'] < 0)).sum()
    print(f'{gid:12s}: {len(res):6d} genes | sig={sig} (up={up}, down={dn})')

print('\nOutput:')
for d in [DEG, GSEA, PLOTS]:
    for f in sorted(os.listdir(d)):
        sz = os.path.getsize(f'{d}/{f}') // 1024
        print(f'  {f}  ({sz} KB)')
