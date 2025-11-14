from cyvcf2 import VCF
import os
import sys
import pandas as pd
from core.cluster_profiler import ClusterProfiler
import json

if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
    sys.exit(1)

BASE_PATH = sys.argv[1]

# File paths
vcf_path = f"{BASE_PATH}/01_merged/data.vcf"
cluster_path = f"{BASE_PATH}/30_cluster/pca_hdbscan_clusters_plink.tsv"
cluster_profile_dir = f"{BASE_PATH}/31_cluster_profile"

os.makedirs(cluster_profile_dir, exist_ok=True)

# Load cluster assignment table
clusters = pd.read_csv(cluster_path, sep="\t")

# Separate out outliers
outlier_samples = clusters.loc[clusters["Cluster"] == "Outlier", "IID"].tolist()
clusters = clusters.loc[clusters["Cluster"] != "Outlier"]

unq_cluster_names = clusters["Cluster"].unique()
print(f"Found clusters: {unq_cluster_names}")
print(f"Found outlier samples: {outlier_samples}")

# Load VCF
vcf = VCF(vcf_path)
sample_names = list(vcf.samples)
sample_name_to_index = {s: i for i, s in enumerate(sample_names)}
index_to_sample_name = {v: k for k, v in sample_name_to_index.items()}

# Create ClusterProfiler objects for each cluster
profilers = {}
for cluster_name in unq_cluster_names:
    cluster_samples = clusters.loc[clusters["Cluster"] == cluster_name, "IID"].tolist()
    cluster_indices = [
        sample_name_to_index[s] for s in cluster_samples if s in sample_name_to_index
    ]
    if not cluster_indices:
        print(
            f"⚠️ Warning: Cluster {cluster_name} has no matching VCF samples, skipping."
        )
        continue
    profilers[cluster_name] = ClusterProfiler(
        name=str(cluster_name), idx=cluster_indices, k=20
    )

# Create dedicated profilers for each outlier
outlier_profilers = {}
for outlier in outlier_samples:
    if outlier not in sample_name_to_index:
        print(f"⚠️ Warning: Outlier {outlier} not found in VCF, skipping.")
        continue
    outlier_idx = [sample_name_to_index[outlier]]
    outlier_profilers[outlier] = ClusterProfiler(name=outlier, idx=outlier_idx, k=100)

print(
    f"Created {len(profilers)} cluster profilers and {len(outlier_profilers)} outlier profilers."
)

# Process each variant and feed to all profilers
for i, variant in enumerate(vcf):
    if i % 1000 == 0:
        print(f"Processing variant {i}...")
    for profiler in list(profilers.values()) + list(outlier_profilers.values()):
        profiler.process_variant(variant)

print("Finished processing all variants.\n")

# Compile results
results = {"clusters": {}, "outliers": {}}

for name, profiler in profilers.items():
    top_variants = profiler.get_topk()
    cluster_data = {
        "samples": [index_to_sample_name[i] for i in profiler.idx],
        "top_variants": [],
    }
    for entry in top_variants:
        var = entry["variant"]
        chrom = var.CHROM
        pos = var.POS
        ref = var.REF
        alt = ",".join(var.ALT) if isinstance(var.ALT, (list, tuple)) else var.ALT
        cluster_data["top_variants"].append(
            {
                "chr": chrom,
                "pos": pos,
                "ref": ref,
                "alt": alt,
                "in_cluster_avg": entry["in_cluster_avg"],
                "out_cluster_avg": entry["out_cluster_avg"],
                "score": entry["score"],
            }
        )
    results["clusters"][name] = cluster_data

for name, profiler in outlier_profilers.items():
    top_variants = profiler.get_topk()
    outlier_data = {
        "samples": [index_to_sample_name[i] for i in profiler.idx],
        "top_variants": [],
    }
    for entry in top_variants:
        var = entry["variant"]
        chrom = var.CHROM
        pos = var.POS
        ref = var.REF
        alt = ",".join(var.ALT) if isinstance(var.ALT, (list, tuple)) else var.ALT
        outlier_data["top_variants"].append(
            {
                "chr": chrom,
                "pos": pos,
                "ref": ref,
                "alt": alt,
                "in_cluster_avg": entry["in_cluster_avg"],
                "out_cluster_avg": entry["out_cluster_avg"],
                "score": entry["score"],
            }
        )
    results["outliers"][name] = outlier_data

# Save to a JSON file
with open(f"{cluster_profile_dir}/result.json", "w") as f:
    json.dump(results, f, indent=4)

print(f"Results saved to {cluster_profile_dir}/result.json")
