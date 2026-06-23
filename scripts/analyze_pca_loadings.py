"""
Analyze PCA variant loadings from PLINK eigenvec.var output.

For each principal component, prints the top N variants by absolute loading value.
Also reports the overlap between PC2 top-loading sites and C2 cluster-discriminative
variants, providing cross-validation that PC2 captures the C2 population axis.

Usage: python scripts/analyze_pca_loadings.py
"""

import json
import pandas as pd

EIGENVEC_VAR = "data-wes2/20_pca/out.eigenvec.var"
CLUSTER_PROFILE = "data-wes2/31_cluster_profile/result.json"
TOP_N = 3
PC2_OVERLAP_N = 20  # how many PC2 top sites to check for C2 overlap

df = pd.read_csv(EIGENVEC_VAR, sep=r"\s+")
pc_cols = [c for c in df.columns if c.startswith("PC")]

print(f"Loaded {len(df):,} variant sites, {len(pc_cols)} PCs\n")

# --- Top N loadings per PC --------------------------------------------------
for pc in pc_cols:
    top = df.reindex(df[pc].abs().nlargest(TOP_N).index)
    print(f"{pc}:")
    for _, r in top.iterrows():
        parts = r["VAR"].split("-", 3)
        pos = parts[1] if len(parts) >= 2 else "?"
        ref = parts[2][:8] if len(parts) >= 3 else "?"
        alt = parts[3][:8] if len(parts) >= 4 else "?"
        print(f"  chr{r['CHR']}:{pos}  {ref}>{alt}  {r[pc]:+.4f}")
    print()

# --- PC2 / C2 cluster overlap -----------------------------------------------
with open(CLUSTER_PROFILE) as fh:
    profile = json.load(fh)

c2_positions = {str(v["pos"]) for v in profile["clusters"]["C2"]["top_variants"]}
pc2_top = df.reindex(df["PC2"].abs().nlargest(PC2_OVERLAP_N).index)

overlap = []
for _, r in pc2_top.iterrows():
    pos = r["VAR"].split("-")[1]
    if pos in c2_positions:
        overlap.append(f"chr{r['CHR']}:{pos}  PC2_loading={r['PC2']:+.4f}")

print(
    f"PC2 top-{PC2_OVERLAP_N} positions that overlap C2 cluster-discriminative variants "
    f"({len(overlap)} found):"
)
for o in overlap:
    print(" ", o)
