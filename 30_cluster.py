#!/usr/bin/env python3

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import sys
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
    silhouette_samples,
)
import plotly.express as px

load_dotenv(".env")

positive_wes_set = []

try:
    from sklearn.cluster import HDBSCAN

    HAS_HDBSCAN = True
except ImportError:
    HAS_HDBSCAN = False


# ---------------------------
# Argument parsing
# ---------------------------
if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
    sys.exit(1)

BASE_PATH = sys.argv[1]

# ---------------------------
# Environment variables
# ---------------------------
CLUSTER_ALGO = os.getenv("CLUSTER_ALGO", "hdbscan").lower()

# DBSCAN params
DBSCAN_EPS = float(os.getenv("DBSCAN_EPS", 0.5))
DBSCAN_MIN_SAMPLES = int(os.getenv("DBSCAN_MIN_SAMPLES", 5))

# HDBSCAN params
HDBSCAN_MIN_CLUSTER_SIZE = int(os.getenv("HDBSCAN_MIN_CLUSTER_SIZE", 5))
HDBSCAN_MIN_SAMPLES = int(os.getenv("HDBSCAN_MIN_SAMPLES", 1))

# Partitioning / hierarchical params
CLUSTER_N_CLUSTERS = int(os.getenv("CLUSTER_N_CLUSTERS", 6))
CLUSTER_LINKAGE = os.getenv("CLUSTER_LINKAGE", "ward").lower()
CLUSTER_RANDOM_STATE = int(os.getenv("CLUSTER_RANDOM_STATE", 42))

CLUSTER_LIMIT_PCA = int(os.getenv("CLUSTER_LIMIT_PCA", 0))  # 0 = no limit
CLUSTER_WEIGHT_EIGENVALUES = (
    os.getenv("CLUSTER_WEIGHT_EIGENVALUES", "true").lower() == "true"
)
CLUSTER_TOPK_VARIANT_CALCULATION = (
    os.getenv("SKIP_CLUSTER_TOPK_VARIANT_CALCULATION", "false") == "false"
)

print("[INFO] Clustering configuration:")
print(f"  - algorithm: {CLUSTER_ALGO}")
print(f"  - DBSCAN_EPS: {DBSCAN_EPS}")
print(f"  - DBSCAN_MIN_SAMPLES: {DBSCAN_MIN_SAMPLES}")
print(f"  - HDBSCAN_MIN_CLUSTER_SIZE: {HDBSCAN_MIN_CLUSTER_SIZE}")
print(f"  - HDBSCAN_MIN_SAMPLES: {HDBSCAN_MIN_SAMPLES}")
print(f"  - CLUSTER_N_CLUSTERS: {CLUSTER_N_CLUSTERS}")
print(f"  - CLUSTER_LINKAGE: {CLUSTER_LINKAGE}")
print(f"  - CLUSTER_RANDOM_STATE: {CLUSTER_RANDOM_STATE}")
print(f"  - PCA limit: {CLUSTER_LIMIT_PCA}")
print(f"  - CLUSTER_WEIGHT_EIGENVALUES: {CLUSTER_WEIGHT_EIGENVALUES}")
print(f"  - CLUSTER_TOPK_VARIANT_CALCULATION: {CLUSTER_TOPK_VARIANT_CALCULATION}")


def summarize_cluster_sizes(cluster_labels):
    counts = cluster_labels.value_counts().sort_index()
    return {str(cluster): int(count) for cluster, count in counts.items()}


def relabel_singletons_as_outliers(cluster_labels):
    cluster_labels = cluster_labels.astype(str).copy()
    counts = cluster_labels.value_counts()
    singleton_clusters = {
        cluster
        for cluster, count in counts.items()
        if count == 1 and cluster != "Outlier"
    }
    if singleton_clusters:
        cluster_labels = cluster_labels.apply(
            lambda cluster: "Outlier" if cluster in singleton_clusters else cluster
        )
    return cluster_labels, sorted(singleton_clusters)


def compute_cluster_metrics(features, cluster_labels):
    cluster_labels = cluster_labels.astype(str)
    outlier_mask = cluster_labels == "Outlier"
    non_outlier_mask = ~outlier_mask

    metrics = {
        "samples_total": int(len(cluster_labels)),
        "samples_non_outlier": int(non_outlier_mask.sum()),
        "samples_outlier": int(outlier_mask.sum()),
        "outlier_fraction": float(outlier_mask.mean()),
        "cluster_count_total": int(cluster_labels.nunique()),
        "cluster_count_non_outlier": int(cluster_labels[non_outlier_mask].nunique()),
        "cluster_sizes": summarize_cluster_sizes(cluster_labels),
    }

    valid_labels = cluster_labels[non_outlier_mask]
    valid_features = features[non_outlier_mask]

    if len(valid_labels) == 0:
        metrics["warning"] = "No non-outlier samples available for unsupervised metrics"
        return metrics, np.full(len(cluster_labels), np.nan), pd.DataFrame(
            columns=["Cluster", "Size", "MeanSilhouette", "MinSilhouette", "MaxSilhouette"]
        )

    if valid_labels.nunique() < 2:
        metrics["warning"] = "Need at least 2 non-outlier clusters for unsupervised metrics"
        return metrics, np.full(len(cluster_labels), np.nan), pd.DataFrame(
            columns=["Cluster", "Size", "MeanSilhouette", "MinSilhouette", "MaxSilhouette"]
        )

    sample_silhouette = np.full(len(cluster_labels), np.nan)
    sample_silhouette[non_outlier_mask] = silhouette_samples(valid_features, valid_labels)

    metrics["silhouette_score"] = float(silhouette_score(valid_features, valid_labels))
    metrics["calinski_harabasz_score"] = float(
        calinski_harabasz_score(valid_features, valid_labels)
    )
    metrics["davies_bouldin_score"] = float(
        davies_bouldin_score(valid_features, valid_labels)
    )

    silhouette_df = pd.DataFrame(
        {
            "Cluster": valid_labels.to_numpy(),
            "Silhouette": sample_silhouette[non_outlier_mask],
        }
    )
    cluster_silhouette = (
        silhouette_df.groupby("Cluster", as_index=False)
        .agg(
            Size=("Silhouette", "size"),
            MeanSilhouette=("Silhouette", "mean"),
            MinSilhouette=("Silhouette", "min"),
            MaxSilhouette=("Silhouette", "max"),
        )
        .sort_values("Cluster")
    )

    return metrics, sample_silhouette, cluster_silhouette

# ---------------------------
# File paths
# ---------------------------
pca_input = f"{BASE_PATH}/20_pca/out.eigenvec"
eigenval_input = f"{BASE_PATH}/20_pca/out.eigenval"
output_dir = f"{BASE_PATH}/30_cluster"
os.makedirs(output_dir, exist_ok=True)

# ---------------------------
# Load PCA data
# ---------------------------
print(f"[INFO] Loading PCA data from: {pca_input}")
df_pca = pd.read_csv(pca_input, sep="\\s+", header=0)
pca_columns = [col for col in df_pca.columns if col.startswith("PC")]

X = df_pca[pca_columns].copy()

if CLUSTER_LIMIT_PCA:
    X = X[pca_columns[:CLUSTER_LIMIT_PCA]]

eigenvalues = np.loadtxt(eigenval_input)
if CLUSTER_LIMIT_PCA:
    eigenvalues = eigenvalues[:CLUSTER_LIMIT_PCA]

# ---------------------------
# Scaling + eigenvalue weighting
# ---------------------------
X_scaled = StandardScaler().fit_transform(X)
if CLUSTER_WEIGHT_EIGENVALUES:
    X_scaled = X_scaled * eigenvalues

# ---------------------------
# Clustering backend
# ---------------------------
if CLUSTER_ALGO == "hdbscan":
    if not HAS_HDBSCAN:
        raise ImportError(
            "HDBSCAN not installed. Install hdbscan or use CLUSTER_ALGO=dbscan"
        )

    clusterer = HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
    )

elif CLUSTER_ALGO == "dbscan":
    clusterer = DBSCAN(
        eps=DBSCAN_EPS,
        min_samples=DBSCAN_MIN_SAMPLES,
        metric="euclidean",
        n_jobs=-1,
    )

elif CLUSTER_ALGO == "kmeans":
    clusterer = KMeans(
        n_clusters=CLUSTER_N_CLUSTERS,
        n_init="auto",
        random_state=CLUSTER_RANDOM_STATE,
    )

elif CLUSTER_ALGO == "agglomerative":
    clusterer = AgglomerativeClustering(
        n_clusters=CLUSTER_N_CLUSTERS,
        linkage=CLUSTER_LINKAGE,
    )

else:
    raise ValueError(f"Unknown CLUSTER_ALGO: {CLUSTER_ALGO}")

labels = clusterer.fit_predict(X_scaled)

# ---------------------------
# Label formatting (MUST come before silhouette output)
# ---------------------------
df_pca["Cluster"] = labels
df_pca["Cluster"] = df_pca["Cluster"].apply(lambda x: f"C{x}" if x != -1 else "Outlier")
df_pca["Cluster"], singleton_clusters = relabel_singletons_as_outliers(df_pca["Cluster"])

# ---------------------------
# Silhouette score
# ---------------------------
metrics, sil_samples, cluster_silhouette = compute_cluster_metrics(
    X_scaled, df_pca["Cluster"]
)
metrics["singleton_clusters_promoted_to_outlier"] = singleton_clusters
df_pca["Silhouette"] = sil_samples

if "warning" in metrics:
    print(f"[WARN] {metrics['warning']}")
else:
    print(f"[INFO] Silhouette score (excluding outliers): {metrics['silhouette_score']:.4f}")
    print(f"[INFO] Calinski-Harabasz score: {metrics['calinski_harabasz_score']:.4f}")
    print(f"[INFO] Davies-Bouldin score: {metrics['davies_bouldin_score']:.4f}")

df_pca[["FID", "IID", "Cluster", "Silhouette"]].to_csv(
    os.path.join(output_dir, "pca_clusters_silhouette.tsv"),
    sep="\t",
    index=False,
)

cluster_silhouette.to_csv(
    os.path.join(output_dir, "cluster_metrics.tsv"),
    sep="\t",
    index=False,
)

with open(os.path.join(output_dir, "summary.json"), "w") as handle:
    json.dump(metrics, handle, indent=2)

# ---------------------------
# Cluster statistics
# ---------------------------
n_outliers = (df_pca["Cluster"] == "Outlier").sum()
n_clusters = df_pca["Cluster"].nunique() - (1 if n_outliers > 0 else 0)

print(
    f"[INFO] {CLUSTER_ALGO.upper()} found {n_clusters} clusters and {n_outliers} outliers."
)

if singleton_clusters:
    print(
        f"[INFO] Singleton clusters promoted to outliers: {', '.join(singleton_clusters)}"
    )

if not cluster_silhouette.empty:
    print("\n[INFO] Per-cluster silhouette summary")
    print(cluster_silhouette.to_string(index=False))

# ---------------------------
# Cluster summary
# ---------------------------
print("\n[INFO] Cluster Summary")
clusters = df_pca["Cluster"].unique()


for cluster in clusters:
    cluster_df = df_pca[df_pca["Cluster"] == cluster]
    count = len(cluster_df)

    if "IID" in cluster_df.columns:
        sample_names = cluster_df["IID"].tolist()
    else:
        sample_names = cluster_df.index.tolist()

    # annotate with (POS) if in positive_wes
    annotated_names = [
        f"{name} (POS)" if str(name) in positive_wes_set else name
        for name in sample_names
    ]

    print(f"\nCluster: {cluster}")
    print(f"  Size: {count}")
    print(f"  First 20 samples: {annotated_names[:20]}")

# ---------------------------
# 2D plot
# ---------------------------
plt.figure(figsize=(10, 8))
unique_labels = set(labels)
colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

for label, color in zip(unique_labels, colors):
    mask_plot = labels == label
    name = f"C{label}" if label != -1 else "Outlier"

    plt.scatter(
        df_pca.loc[mask_plot, "PC1"],
        df_pca.loc[mask_plot, "PC2"],
        c=[color],
        label=name,
        alpha=0.7,
        edgecolors="w",
        s=60,
    )

plt.xlabel("PC1")
plt.ylabel("PC2")
plot_mode = "Weighted PCs" if CLUSTER_WEIGHT_EIGENVALUES else "Scaled PCs"
plt.title(f"PCA 2D Plot ({plot_mode}, {CLUSTER_ALGO.upper()}, n={n_clusters})")
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "pca_cluster_2d.png"), dpi=300)
plt.close()

# ---------------------------
# 3D plot
# ---------------------------
# if "PC3" in df_pca.columns:
#     fig = plt.figure(figsize=(10, 8))
#     ax = fig.add_subplot(111, projection="3d")

#     for label, color in zip(unique_labels, colors):
#         mask_plot = labels == label
#         name = f"C{label}" if label != -1 else "Outlier"

#         ax.scatter(
#             df_pca.loc[mask_plot, "PC1"],
#             df_pca.loc[mask_plot, "PC2"],
#             df_pca.loc[mask_plot, "PC3"],
#             c=[color],
#             label=name,
#             alpha=0.7,
#             s=30,
#         )

#     ax.set_xlabel("PC1")
#     ax.set_ylabel("PC2")
#     ax.set_zlabel("PC3")
#     ax.set_title(f"PCA 3D Plot (Weighted PCs, {CLUSTER_ALGO.upper()}, n={n_clusters})")
#     ax.legend(fontsize=8)
#     plt.tight_layout()
#     plt.savefig(os.path.join(output_dir, "pca_cluster_3d.png"), dpi=300)
#     plt.close()

# ---------------------------
# Interactive 3D plot
# ---------------------------
if "PC3" in df_pca.columns:
    unique_clusters = df_pca["Cluster"].unique()

    colors = [
        "#e10000",
        "#00C200",
        "#2d2d86",
        "#ecf800",
        "#0068D0",
        "#660000",
        "#773c00",
        "#000098",
        "#2f4f4f",
        "#3b3b3b",
    ]

    color_map = {}
    for i, cluster in enumerate(unique_clusters):
        if cluster == "Outlier":
            color_map[cluster] = "#808080"
        else:
            color_map[cluster] = colors[i % len(colors)]

    num_pcs = len([c for c in df_pca.columns if c.startswith("PC")])

    for start_pc in range(1, num_pcs - 1):
        pc_x = f"PC{start_pc}"
        pc_y = f"PC{start_pc + 1}"
        pc_z = f"PC{start_pc + 2}"

        # create hover text with POS annotation
        df_pca["hover_text"] = (
            df_pca["FID"]
            .astype(str)
            .apply(lambda x: f"{x} (POS)" if str(x) in positive_wes_set else x)
        )

        # define marker shape per sample
        df_pca["marker_symbol"] = df_pca["IID"].apply(
            lambda x: "triangle-up" if str(x) in positive_wes_set else "circle"
        )

        fig = px.scatter_3d(
            df_pca,
            x=pc_x,
            y=pc_y,
            z=pc_z,
            color="Cluster",
            symbol="marker_symbol",
            hover_name="hover_text",  # show POS in hover
            title=f"PCA 3D Interactive Plot ({pc_x}, {pc_y}, {pc_z})",
            opacity=0.7,
            color_discrete_map=color_map,
        )

        fig.update_traces(marker=dict(size=4))
        fig.update_layout(legend_title_text="Cluster ID")

        fig.write_html(os.path.join(output_dir, f"pca_cluster_3d_{start_pc}.html"))

# ---------------------------
# Save outputs
# ---------------------------
df_pca.to_csv(
    os.path.join(output_dir, "pca_clusters.tsv"),
    sep="\t",
    index=False,
)

df_pca[["FID", "IID", "Cluster"]].to_csv(
    os.path.join(output_dir, "pca_clusters_plink.tsv"),
    sep="\t",
    index=False,
)
