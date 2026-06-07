"""
Query STRING API for key HFpEF metabolic + fibrosis genes → network image.
Species 10090 = mouse (Mus musculus)
"""
import urllib.request, urllib.parse, json, os, pandas as pd

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))

BASE  = BASE_DIR
DEG   = f'{BASE}/deg'
FIGS  = f'{BASE}/figures_r'; os.makedirs(FIGS, exist_ok=True)

# ── key genes: top significant from GSE194151 + pathway genes ─
pathway_genes = [
    # FAO
    'Cpt1a','Cpt1b','Cpt2','Acsl1','Acadl','Acadm','Hadha','Hadhb','Fabp3',
    # Ketone
    'Hmgcs2','Bdh1','Oxct1','Acat1',
    # OxPhos
    'Ndufa1','Sdha','Uqcrc1','Cox4i1','Atp5a1','Cycs',
    # Fibrosis
    'Col1a1','Col1a2','Col3a1','Postn','Fn1','Tgfb1','Acta2','Ctgf',
    # Insulin
    'Insr','Irs1','Akt1','Foxo1','Slc2a4',
    # PPAR
    'Ppara','Pparg','Lpl','Scd1',
]

# Filter to those significantly DE in GSE194151
deg = pd.read_csv(f'{DEG}/GSE194151_DEG_gene_symbols.csv', index_col=0)
sig_mask = (deg['padj'] < 0.05) & (deg['log2FoldChange'].abs() > 0.5)
sig_genes = set(deg[sig_mask].index.tolist())
genes_query = [g for g in pathway_genes if g in sig_genes]
# Always include key fibrosis + metabolic anchors regardless of significance
anchors = ['Tgfb1','Col1a1','Postn','Acta2','Cpt1b','Hmgcs2','Ppara','Acadm','Cycs','Fn1']
genes_query = list(set(genes_query + anchors))
print(f'Querying STRING for {len(genes_query)} genes: {genes_query}')

STRING_API = 'https://string-db.org/api'
species    = 10090  # mouse

# ── 1. Map identifiers ────────────────────────────────────────
params = urllib.parse.urlencode({
    'identifiers': '%0d'.join(genes_query),
    'species': species,
    'limit': 1,
    'echo_query': 1,
    'caller_identity': 'hfpef_analysis'
}).encode()
url_map = f'{STRING_API}/json/get_string_ids'
try:
    req = urllib.request.Request(url_map, data=params)
    with urllib.request.urlopen(req, timeout=30) as r:
        mapped = json.loads(r.read())
    string_ids = [x['stringId'] for x in mapped if 'stringId' in x]
    preferred  = [x.get('preferredName','') for x in mapped]
    print(f'Mapped: {len(string_ids)} / {len(genes_query)}')
    print(f'Identified: {preferred[:10]}...')
except Exception as e:
    print(f'Map error: {e}')
    string_ids = []

if not string_ids:
    print('No STRING IDs — cannot continue')
    exit(1)

# ── 2. Network image (high-res PNG) ───────────────────────────
params_img = urllib.parse.urlencode({
    'identifiers': '%0d'.join(string_ids),
    'species': species,
    'required_score': 700,
    'network_flavor': 'confidence',
    'caller_identity': 'hfpef_analysis',
    'hide_disconnected_nodes': 1,
    'block_structure_pics_in_bubbles': 0,
    'network_type': 'functional',
}).encode()
url_img = f'{STRING_API}/image/network'
try:
    req_img = urllib.request.Request(url_img, data=params_img)
    with urllib.request.urlopen(req_img, timeout=60) as r:
        img_data = r.read()
    out_img = f'{FIGS}/FigS_STRING_network.png'
    with open(out_img, 'wb') as f:
        f.write(img_data)
    print(f'Saved network image: {out_img} ({len(img_data)//1024}KB)')
except Exception as e:
    print(f'Image error: {e}')

# ── 3. Get interaction table for supplementary ────────────────
params_net = urllib.parse.urlencode({
    'identifiers': '%0d'.join(string_ids),
    'species': species,
    'required_score': 700,
    'caller_identity': 'hfpef_analysis',
}).encode()
url_net = f'{STRING_API}/tsv/interaction_partners'
try:
    req_net = urllib.request.Request(url_net, data=params_net)
    with urllib.request.urlopen(req_net, timeout=30) as r:
        tsv = r.read().decode('utf-8')
    lines = [l.split('\t') for l in tsv.strip().split('\n')]
    if len(lines) > 1:
        idf = pd.DataFrame(lines[1:], columns=lines[0])
        print(f'Interactions: {len(idf)} edges')
        print(idf[['preferredName_A','preferredName_B','score']].head(10).to_string())
        idf.to_csv(f'{FIGS}/FigS_STRING_interactions.csv', index=False)
except Exception as e:
    print(f'Interaction error: {e}')
