import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import sys

if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
    sys.exit(1)

BASE_PATH = sys.argv[1]

# File paths
input_file = f"{BASE_PATH}/20_pca/out.eigenvec"
output_dir = f"{BASE_PATH}/40_plot"

os.makedirs(output_dir, exist_ok=True)

# Load data with header from the file
df = pd.read_csv(input_file, delim_whitespace=True, header=0)

# --- 2D Plot (PC1 vs PC2) with FID labels ---
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

# --- 3D Plot (PC1 vs PC2 vs PC3) with FID labels ---
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

print(f"Plots with FID labels saved in {output_dir}")
