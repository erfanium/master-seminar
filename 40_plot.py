import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import sys

if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
    sys.exit(1)

BASE_PATH = sys.argv[1]

# File paths
pca_input = f"{BASE_PATH}/20_pca/out.eigenvec"
kinship_input = f"{BASE_PATH}/10_kinship/out.mibs"
kinship_id_input = f"{BASE_PATH}/10_kinship/out.mibs.id"
output_dir = f"{BASE_PATH}/40_plot"

os.makedirs(output_dir, exist_ok=True)

# ---------------------------
# Load PCA data
# ---------------------------
df = pd.read_csv(pca_input, delim_whitespace=True, header=0)

# --- 2D PCA Plot ---
plt.figure(figsize=(10, 8))
plt.scatter(df["PC1"], df["PC2"], c="blue", alpha=0.6, edgecolors="w")
for i, fid in enumerate(df["FID"]):
    plt.text(df["PC1"][i], df["PC2"][i], str(fid), fontsize=6, alpha=0.7)
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.title("PCA 2D Plot (PC1 vs PC2)")
plt.grid(True)
plt.savefig(os.path.join(output_dir, "pca_2d.png"), dpi=300)
plt.close()

# --- 3D PCA Plot ---
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(df["PC1"], df["PC2"], df["PC3"], c="red", alpha=0.6)
for i, fid in enumerate(df["FID"]):
    ax.text(df["PC1"][i], df["PC2"][i], df["PC3"][i], str(fid), fontsize=6, alpha=0.7)
ax.set_xlabel("PC1")
ax.set_ylabel("PC2")
ax.set_zlabel("PC3")
ax.set_title("PCA 3D Plot (PC1 vs PC2 vs PC3)")
plt.savefig(os.path.join(output_dir, "pca_3d.png"), dpi=300)
plt.close()

# ---------------------------
# Load Kinship matrix
# ---------------------------
# Load IDs
ids = pd.read_csv(kinship_id_input, delim_whitespace=True, header=None)
ids.columns = ["FID", "IID"]
samples = ids["IID"].tolist()
n = len(samples)

# Load triangular kinship matrix
triangular_matrix = np.loadtxt(kinship_input)

# Fill into a square matrix
kinship_matrix = np.zeros((n, n))
for i in range(n):
    kinship_matrix[i, : i + 1] = triangular_matrix[i, : i + 1]
    kinship_matrix[: i + 1, i] = triangular_matrix[i, : i + 1]

# ---------------------------
# Plot triangular heatmap (only lower triangle)
# ---------------------------
plt.figure(figsize=(10, 8))

# Mask the upper triangle AND the diagonal
mask = np.triu(np.ones_like(kinship_matrix, dtype=bool), k=0)
kinship_tri = np.ma.array(kinship_matrix, mask=mask)

cmap = plt.cm.viridis
im = plt.imshow(kinship_tri, cmap=cmap, interpolation="nearest")

plt.colorbar(im, label="Kinship coefficient")
plt.xticks(range(n), samples, rotation=90, fontsize=6)
plt.yticks(range(n), samples, fontsize=6)
plt.title("Kinship Matrix (Lower Triangle, Diagonal Removed)")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "kinship_triangular.png"), dpi=300)
plt.close()
