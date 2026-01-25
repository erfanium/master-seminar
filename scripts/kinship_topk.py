import pandas as pd
import numpy as np
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
kinship_input = f"{BASE_PATH}/10_kinship/out.mibs"
kinship_id_input = f"{BASE_PATH}/10_kinship/out.mibs.id"

# ---------------------------
# Load Kinship matrix
# ---------------------------
ids = pd.read_csv(kinship_id_input, sep=r"\s+", header=None)
ids.columns = ["FID", "IID"]
samples = ids["IID"].tolist()
n = len(samples)

triangular_matrix = np.loadtxt(kinship_input)
kinship_matrix = np.zeros((n, n))
for i in range(n):
    kinship_matrix[i, : i + 1] = triangular_matrix[i, : i + 1]
    kinship_matrix[: i + 1, i] = triangular_matrix[i, : i + 1]

# ---------------------------
# Normalize kinship values
# ---------------------------
min_k = kinship_matrix.min()
max_k = kinship_matrix.max()
kinship_matrix = (kinship_matrix - min_k) / (max_k - min_k)

# ---------------------------
# Create pairs
# ---------------------------
pairs = []
for i in range(n):
    for j in range(i + 1, n):
        pairs.append((samples[i], samples[j], kinship_matrix[i, j]))

df_pairs = (
    pd.DataFrame(pairs, columns=["IID1", "IID2", "Kinship"])
    .sort_values(by="Kinship", ascending=False)
    .reset_index(drop=True)
)

top10 = df_pairs.head(10)
bottom10 = df_pairs.tail(10)

print("Top 10 highest-kinship pairs:")
print(top10)

print("\nTop 10 lowest-kinship pairs:")
print(bottom10)
