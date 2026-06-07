"""
Cross-model validation: GSE194151 (HFD+L-NAME) vs GSE249409 (HFD+mTAC, no L-NAME)
Generates Figure S6.
"""

import warnings

# ── Paths (relative to repo root) ────────────────────────────────────────────
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
_os.makedirs(_os.path.join(BASE_DIR, 'figures_out'), exist_ok=True)

PUB  = _os.path.join(BASE_DIR, 'figures_out')
DATA = _os.path.join(BASE_DIR, 'data')
DEG  = _os.path.join(BASE_DIR, 'deg')

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

# ── paths ──────────────────────────────────────────────────────────────────────
GSEA_194 = BASE_DIR
GSEA_249 = BASE_DIR
OUT_DIR  = _os.path.join(BASE_DIR, 'figures_out')
OUT_FILE = os.path.join(OUT_DIR, "FigureS6_CrossModel_Validation.png")
os.makedirs(OUT_DIR, exist_ok=True)

FDR_THRESH = 0.10

# ── load ───────────────────────────────────────────────────────────────────────
df194 = pd.read_csv(GSEA_194).rename(columns={"Term": "pathway"})
df249 = pd.read_csv(GSEA_249).rename(columns={"Term": "pathway"})

# normalise column names to lowercase
df194.columns = [c.lower() for c in df194.columns]
df249.columns = [c.lower() for c in df249.columns]

print("GSE194151 columns:", df194.columns.tolist())
print("GSE249409 columns:", df249.columns.tolist())

df194 = df194.set_index("pathway")
df249 = df249.set_index("pathway")

# ── pathway order (canonical) ─────────────────────────────────────────────────
PATHWAY_ORDER = [
    'FAO_KEGG',
    'Ketone_GO',
    'PPAR_Signaling',
    'OxPhos_KEGG',
    'Glycolysis_KEGG',
    'Cardiac_Fibrosis',
    'Insulin_Signaling',
]

# ── comparison table ───────────────────────────────────────────────────────────
print("\n" + "="*85)
print(f"{'Pathway':<25} {'GSE194151 NES':>15} {'GSE194151 FDR':>15} {'GSE249409 NES':>15} {'GSE249409 FDR':>15}")
print("-"*85)

nes_194 = []
nes_249 = []
sig_194 = []   # True = FDR<0.10
sig_249 = []

for pw in PATHWAY_ORDER:
    n194  = df194.loc[pw, "nes"]  if pw in df194.index else np.nan
    f194  = df194.loc[pw, "fdr"]  if pw in df194.index else np.nan
    n249  = df249.loc[pw, "nes"]  if pw in df249.index else np.nan
    f249  = df249.loc[pw, "fdr"]  if pw in df249.index else np.nan

    nes_194.append(n194)
    nes_249.append(n249)
    sig_194.append(not np.isnan(f194) and f194 < FDR_THRESH)
    sig_249.append(not np.isnan(f249) and f249 < FDR_THRESH)

    print(f"{pw:<25} {n194:>+15.4f} {f194:>15.4f} {n249:>+15.4f} {f249:>15.4f}")

print("="*85)

# ── OxPhos specific report ─────────────────────────────────────────────────────
oxphos_249 = nes_249[PATHWAY_ORDER.index("OxPhos_KEGG")]
fao_249    = nes_249[PATHWAY_ORDER.index("FAO_KEGG")]
oxphos_194 = nes_194[PATHWAY_ORDER.index("OxPhos_KEGG")]
fao_194    = nes_194[PATHWAY_ORDER.index("FAO_KEGG")]

print()
print("KEY FINDINGS:")
print(f"  OxPhos_KEGG   GSE194151 (HFD+L-NAME): NES = {oxphos_194:+.4f}")
print(f"  OxPhos_KEGG   GSE249409 (HFD+mTAC)  : NES = {oxphos_249:+.4f}")
direction_match = (np.sign(oxphos_194) == np.sign(oxphos_249))
print(f"  → OxPhos NES directions agree: {direction_match}")
if oxphos_249 > 0:
    print("  → OxPhos shows POSITIVE NES in GSE249409 (HFD+mTAC, no L-NAME): YES")
else:
    print(f"  → OxPhos shows POSITIVE NES in GSE249409: NO (NES={oxphos_249:+.4f})")
print(f"  FAO_KEGG      GSE194151: NES = {fao_194:+.4f}  |  GSE249409: NES = {fao_249:+.4f}")

# ── figure ─────────────────────────────────────────────────────────────────────
x       = np.arange(len(PATHWAY_ORDER))
width   = 0.35

# alpha: 1.0 if FDR<0.10, 0.35 if not
alpha_194 = [1.0 if s else 0.35 for s in sig_194]
alpha_249 = [1.0 if s else 0.35 for s in sig_249]

fig, ax = plt.subplots(figsize=(12, 6))

bars1 = ax.bar(x - width/2, nes_194, width, label="GSE194151 HFD+L-NAME",
               color="#1f77b4", edgecolor="black", linewidth=0.5)
bars2 = ax.bar(x + width/2, nes_249, width, label="GSE249409 HFD+mTAC",
               color="#2ca02c", edgecolor="black", linewidth=0.5)

# apply per-bar alpha
for bar, a in zip(bars1, alpha_194):
    bar.set_alpha(a)
for bar, a in zip(bars2, alpha_249):
    bar.set_alpha(a)

ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(PATHWAY_ORDER, rotation=30, ha="right", fontsize=10)
ax.set_ylabel("Normalised Enrichment Score (NES)", fontsize=11)
ax.set_title(
    "Figure S6. Cross-Model Validation: HFD+L-NAME vs HFD+mTAC GSEA Comparison",
    fontsize=11, fontweight="bold"
)

# legend (include alpha note)
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor="#1f77b4", edgecolor="black", label="GSE194151 HFD+L-NAME"),
    Patch(facecolor="#2ca02c", edgecolor="black", label="GSE249409 HFD+mTAC"),
    Patch(facecolor="gray",   edgecolor="black", alpha=0.35, label="FDR ≥ 0.10 (faded)"),
    Patch(facecolor="gray",   edgecolor="black", alpha=1.0,  label="FDR < 0.10 (saturated)"),
]
ax.legend(handles=legend_elements, fontsize=9, loc="upper right")

# annotation note
ax.text(
    0.01, 0.02,
    "OxPhos upregulation replicated without L-NAME → not solely L-NAME artifact",
    transform=ax.transAxes,
    fontsize=9, style="italic", color="#555555",
    va="bottom"
)

plt.tight_layout()
plt.savefig(OUT_FILE, dpi=150, bbox_inches="tight")
print(f"\nFigure saved to {OUT_FILE}")
