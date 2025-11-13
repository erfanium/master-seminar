#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import sys

# ---------------------------
# Argument Parsing
# ---------------------------
if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
    sys.exit(1)

BASE_PATH = sys.argv[1]

# ---------------------------
# File Paths
# ---------------------------
pca_input = f"{BASE_PATH}/20_pca/out.eigenvec"
mds_input = f"{BASE_PATH}/21_mds/out.mds"
kinship_input = f"{BASE_PATH}/10_kinship/out.mibs"
kinship_id_input = f"{BASE_PATH}/10_kinship/out.mibs.id"
output_dir = f"{BASE_PATH}/40_plot"

os.makedirs(output_dir, exist_ok=True)

# ---------------------------
# Load PCA data
# ---------------------------
df_pca = pd.read_csv(pca_input, sep="\\s+", header=0)


# --- 2D PCA Plot ---
plt.figure(figsize=(10, 8))
plt.scatter(df_pca["PC1"], df_pca["PC2"], c="blue", alpha=0.6, edgecolors="w")
for i, fid in enumerate(df_pca["FID"]):
    plt.text(df_pca["PC1"][i], df_pca["PC2"][i], str(fid), fontsize=6, alpha=0.7)
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.title("PCA 2D Plot (PC1 vs PC2)")
plt.grid(True)
plt.savefig(os.path.join(output_dir, "pca_2d.png"), dpi=300)
plt.close()

# --- 3D PCA Plot ---
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(df_pca["PC1"], df_pca["PC2"], df_pca["PC3"], c="red", alpha=0.6)
for i, fid in enumerate(df_pca["FID"]):
    ax.text(
        df_pca["PC1"][i],
        df_pca["PC2"][i],
        df_pca["PC3"][i],
        str(fid),
        fontsize=6,
        alpha=0.7,
    )
ax.set_xlabel("PC1")
ax.set_ylabel("PC2")
ax.set_zlabel("PC3")
ax.set_title("PCA 3D Plot (PC1 vs PC2 vs PC3)")
plt.savefig(os.path.join(output_dir, "pca_3d.png"), dpi=300)
plt.close()

# ---------------------------
# Load and Plot MDS Data
# ---------------------------
if os.path.exists(mds_input):
    df_mds = pd.read_csv(mds_input, sep="\\s+")

    # --- 2D MDS Plot (C1 vs C2) ---
    plt.figure(figsize=(10, 8))
    plt.scatter(df_mds["C1"], df_mds["C2"], c="green", alpha=0.6, edgecolors="w")
    for i, fid in enumerate(df_mds["FID"]):
        plt.text(df_mds["C1"][i], df_mds["C2"][i], str(fid), fontsize=6, alpha=0.7)
    plt.xlabel("MDS Dimension 1")
    plt.ylabel("MDS Dimension 2")
    plt.title("MDS 2D Plot (C1 vs C2)")
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "mds_2d.png"), dpi=300)
    plt.close()

    # --- 3D MDS Plot (C1 vs C2 vs C3) ---
    if "C3" in df_mds.columns:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")
        ax.scatter(df_mds["C1"], df_mds["C2"], df_mds["C3"], c="orange", alpha=0.6)
        for i, fid in enumerate(df_mds["FID"]):
            ax.text(
                df_mds["C1"][i],
                df_mds["C2"][i],
                df_mds["C3"][i],
                str(fid),
                fontsize=6,
                alpha=0.7,
            )
        ax.set_xlabel("MDS Dim 1")
        ax.set_ylabel("MDS Dim 2")
        ax.set_zlabel("MDS Dim 3")
        ax.set_title("MDS 3D Plot (C1 vs C2 vs C3)")
        plt.savefig(os.path.join(output_dir, "mds_3d.png"), dpi=300)
        plt.close()
else:
    print(f"[Warning] MDS file not found at {mds_input}, skipping MDS plots.")

# ---------------------------
# Load Kinship matrix
# ---------------------------
ids = pd.read_csv(kinship_id_input, sep="\\s+", header=None)
ids.columns = ["FID", "IID"]
samples = ids["IID"].tolist()
n = len(samples)

triangular_matrix = np.loadtxt(kinship_input)
kinship_matrix = np.zeros((n, n))
for i in range(n):
    kinship_matrix[i, : i + 1] = triangular_matrix[i, : i + 1]
    kinship_matrix[: i + 1, i] = triangular_matrix[i, : i + 1]

# ---------------------------
# Plot triangular kinship heatmap
# ---------------------------
plt.figure(figsize=(10, 8))
mask = np.triu(np.ones_like(kinship_matrix, dtype=bool), k=0)
kinship_tri = np.ma.array(kinship_matrix, mask=mask)

im = plt.imshow(kinship_tri, cmap=plt.cm.viridis, interpolation="nearest")
plt.colorbar(im, label="Kinship coefficient")
plt.xticks(range(n), samples, rotation=90, fontsize=6)
plt.yticks(range(n), samples, fontsize=6)
plt.title("Kinship Matrix (Lower Triangle, Diagonal Removed)")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "kinship_triangular.png"), dpi=300)
plt.close()

print(f"✅ Plots saved in: {output_dir}")
