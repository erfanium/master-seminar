#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import sys
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import HDBSCAN  # use the sklearn implementation
import plotly.express as px

# Argument parsing
if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
    sys.exit(1)

BASE_PATH = sys.argv[1]
HDB_MIN_CLUSTER_SIZE = int(os.getenv("HDB_MIN_CLUSTER_SIZE", 2))
HDB_MIN_SAMPLES = os.getenv("HDB_MIN_SAMPLES", 1)
HDB_MIN_SAMPLES = int(HDB_MIN_SAMPLES) if HDB_MIN_SAMPLES is not None else None
CLUSTER_LIMIT_PCA = int(os.getenv("CLUSTER_LIMIT_PCA", 0))  # 0 means no limit
CLUSTER_TOPK_VARIANT_CALCULATION = (
    os.getenv("SKIP_CLUSTER_TOPK_VARIANT_CALCULATION", "false") == "false"
)

print("[INFO] HDBSCAN parameters:")
print(f"  - min_cluster_size: {HDB_MIN_CLUSTER_SIZE}")
print(f"  - min_samples: {HDB_MIN_SAMPLES}")
print(f"  - pca count limit: {CLUSTER_LIMIT_PCA}")
print(f"  - CLUSTER_TOPK_VARIANT_CALCULATION: {CLUSTER_TOPK_VARIANT_CALCULATION}")

# File paths
pca_input = f"{BASE_PATH}/20_pca/out.eigenvec"
eigenval_input = f"{BASE_PATH}/20_pca/out.eigenval"
output_dir = f"{BASE_PATH}/30_cluster"
os.makedirs(output_dir, exist_ok=True)

# Load PCA data
print(f"[INFO] Loading PCA data from: {pca_input}")
df_pca = pd.read_csv(pca_input, sep="\\s+", header=0)
pca_columns = [col for col in df_pca.columns if col.startswith("PC")]


X = df_pca[pca_columns].copy()

# keep only first x pca
if CLUSTER_LIMIT_PCA:
    X = X[pca_columns[:CLUSTER_LIMIT_PCA]]

eigenvalues = np.loadtxt(eigenval_input)
eigenvalues = eigenvalues[:CLUSTER_LIMIT_PCA]


cumulative = np.cumsum(eigenvalues / np.sum(eigenvalues))


X_scaled = StandardScaler().fit_transform(X)
X_scaled = X_scaled * eigenvalues

# Fit HDBSCAN
clusterer = HDBSCAN(
    min_cluster_size=HDB_MIN_CLUSTER_SIZE,
    min_samples=HDB_MIN_SAMPLES,
    metric="euclidean",  # you can change metric if needed
    algorithm="auto",
)
labels = clusterer.fit_predict(X_scaled)
df_pca["Cluster"] = labels
df_pca["Cluster"] = df_pca["Cluster"].apply(lambda x: f"C{x}" if x != -1 else "Outlier")

n_outliers = len(df_pca[df_pca["Cluster"] == "Outlier"])
n_clusters = df_pca["Cluster"].nunique() - (1 if n_outliers > 0 else 0)

print(f"[INFO] HDBSCAN found {n_clusters} clusters and {n_outliers} outliers.")

# ----- Cluster Summary -----
print("\n[INFO] Cluster Summary")
clusters = df_pca["Cluster"].unique()

for cluster in clusters:
    cluster_df = df_pca[df_pca["Cluster"] == cluster]
    count = len(cluster_df)

    # extract sample names (adjust column name if needed)
    if "IID" in cluster_df.columns:
        sample_names = cluster_df["IID"].tolist()
    else:
        # fallback to index
        sample_names = cluster_df.index.tolist()

    first_20 = sample_names[:20]

    print(f"\nCluster: {cluster}")
    print(f"  Size: {count}")
    print(f"  First 20 samples: {first_20}")


# 2D Plot
plt.figure(figsize=(10, 8))
unique_labels = set(labels)
colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))
for label, color in zip(unique_labels, colors):
    mask = labels == label
    name = f"C{label}" if label != -1 else "Outlier"
    plt.scatter(
        df_pca.loc[mask, "PC1"],
        df_pca.loc[mask, "PC2"],
        c=[color],
        label=name,
        alpha=0.7,
        edgecolors="w",
        s=60,
    )
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.title(f"PCA 2D Plot (Weighted PCs, HDBSCAN, n={n_clusters})")
plt.legend(fontsize=8)
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "pca_hdbscan_2d.png"), dpi=300)
plt.close()

# 3D Plot (if PC3 exists)
if "PC3" in df_pca.columns:
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    for label, color in zip(unique_labels, colors):
        mask = labels == label
        name = f"C{label}" if label != -1 else "Outlier"
        ax.scatter(
            df_pca.loc[mask, "PC1"],
            df_pca.loc[mask, "PC2"],
            df_pca.loc[mask, "PC3"],
            c=[color],
            label=name,
            alpha=0.7,
            s=30,
        )
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_zlabel("PC3")
    ax.set_title(f"PCA 3D Plot (Weighted PCs, HDBSCAN, n={n_clusters})")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "pca_hdbscan_3d.png"), dpi=300)
    plt.close()


# Interactive 3D plot with Plotly
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

    # Generate color map for clusters
    color_map = {}
    for i, cluster in enumerate(unique_clusters):
        if cluster == "Outlier":
            color_map[cluster] = "#808080"
        else:
            color_map[cluster] = colors[i % len(colors)]

    # Determine number of PCs available
    num_pcs = len([col for col in df_pca.columns if col.startswith("PC")])

    # Sliding window of 3 PCs (PC1-3, PC2-4, ..., PC(n-2)-PCn)
    for start_pc in range(1, num_pcs - 2 + 1):  # up to PC8 if PC10 exists
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

        # Save each plot with PC range in the filename
        plot_filename = f"pca_hdbscan_3d_{start_pc}.html"
        interactive_plot_path = os.path.join(output_dir, plot_filename)

        fig.write_html(interactive_plot_path)

        print(f"[INFO] Saved: {interactive_plot_path}")


# Save full PCA data with cluster labels
cluster_output = os.path.join(output_dir, "pca_hdbscan_clusters.tsv")
df_pca.to_csv(cluster_output, sep="\t", index=False)
print(f"[INFO] Clustered PCA data saved to: {cluster_output}")

# Save plink compatible clusters result (FID, IID, Cluster)
cluster_output = os.path.join(output_dir, "pca_hdbscan_clusters_plink.tsv")
df_pca[["FID", "IID", "Cluster"]].to_csv(cluster_output, sep="\t", index=False)
print(f"[INFO] Clustered PCA data saved to: {cluster_output}")
