#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import sys
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score, silhouette_samples
import plotly.express as px

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

CLUSTER_LIMIT_PCA = int(os.getenv("CLUSTER_LIMIT_PCA", 0))  # 0 = no limit
CLUSTER_TOPK_VARIANT_CALCULATION = (
    os.getenv("SKIP_CLUSTER_TOPK_VARIANT_CALCULATION", "false") == "false"
)

print("[INFO] Clustering configuration:")
print(f"  - algorithm: {CLUSTER_ALGO}")
print(f"  - DBSCAN_EPS: {DBSCAN_EPS}")
print(f"  - DBSCAN_MIN_SAMPLES: {DBSCAN_MIN_SAMPLES}")
print(f"  - HDBSCAN_MIN_CLUSTER_SIZE: {HDBSCAN_MIN_CLUSTER_SIZE}")
print(f"  - HDBSCAN_MIN_SAMPLES: {HDBSCAN_MIN_SAMPLES}")
print(f"  - PCA limit: {CLUSTER_LIMIT_PCA}")
print(f"  - CLUSTER_TOPK_VARIANT_CALCULATION: {CLUSTER_TOPK_VARIANT_CALCULATION}")

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

else:
    raise ValueError(f"Unknown CLUSTER_ALGO: {CLUSTER_ALGO}")

labels = clusterer.fit_predict(X_scaled)

# ---------------------------
# Label formatting (MUST come before silhouette output)
# ---------------------------
df_pca["Cluster"] = labels
df_pca["Cluster"] = df_pca["Cluster"].apply(lambda x: f"C{x}" if x != -1 else "Outlier")

# ---------------------------
# Silhouette score
# ---------------------------
mask = labels != -1

if len(set(labels[mask])) > 1:
    sil_score = silhouette_score(X_scaled[mask], labels[mask], metric="euclidean")
    print(f"[INFO] Silhouette score (excluding outliers): {sil_score:.4f}")

    sil_samples = np.full(len(labels), np.nan)
    sil_samples[mask] = silhouette_samples(X_scaled[mask], labels[mask])

    df_pca["Silhouette"] = sil_samples

    df_pca[["FID", "IID", "Cluster", "Silhouette"]].to_csv(
        os.path.join(output_dir, "pca_clusters_silhouette.tsv"),
        sep="\t",
        index=False,
    )
else:
    print(
        "[WARN] Silhouette score not computed: need >=2 clusters (excluding outliers)."
    )
    df_pca["Silhouette"] = np.nan

# ---------------------------
# Cluster statistics
# ---------------------------
n_outliers = (df_pca["Cluster"] == "Outlier").sum()
n_clusters = df_pca["Cluster"].nunique() - (1 if n_outliers > 0 else 0)

print(
    f"[INFO] {CLUSTER_ALGO.upper()} found {n_clusters} clusters and {n_outliers} outliers."
)

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

    print(f"\nCluster: {cluster}")
    print(f"  Size: {count}")
    print(f"  First 20 samples: {sample_names[:20]}")

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
plt.title(f"PCA 2D Plot (Weighted PCs, {CLUSTER_ALGO.upper()}, n={n_clusters})")
plt.legend(fontsize=8)
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "pca_cluster_2d.png"), dpi=300)
plt.close()

# ---------------------------
# 3D plot
# ---------------------------
if "PC3" in df_pca.columns:
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    for label, color in zip(unique_labels, colors):
        mask_plot = labels == label
        name = f"C{label}" if label != -1 else "Outlier"

        ax.scatter(
            df_pca.loc[mask_plot, "PC1"],
            df_pca.loc[mask_plot, "PC2"],
            df_pca.loc[mask_plot, "PC3"],
            c=[color],
            label=name,
            alpha=0.7,
            s=30,
        )

    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_zlabel("PC3")
    ax.set_title(f"PCA 3D Plot (Weighted PCs, {CLUSTER_ALGO.upper()}, n={n_clusters})")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pca_cluster_3d.png"), dpi=300)
    plt.close()

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

        fig = px.scatter_3d(
            df_pca,
            x=pc_x,
            y=pc_y,
            z=pc_z,
            color="Cluster",
            hover_name="FID",
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
