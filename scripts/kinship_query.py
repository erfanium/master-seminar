#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import sys

# ---------------------------
# Argument Parsing
# ---------------------------
if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path> [sample_1] [sample_2]")
    sys.exit(1)

BASE_PATH = sys.argv[1]
sample_name_cli = sys.argv[2] if len(sys.argv) > 2 else None
sample_name_2_cli = sys.argv[3] if len(sys.argv) > 3 else None

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
# Function to get kinship values for a sample (One vs All)
# ---------------------------
def kinship_for_sample(sample_name):
    if sample_name not in samples:
        raise ValueError(f"Sample '{sample_name}' not found in kinship data.")
    idx = samples.index(sample_name)
    kin_values = kinship_matrix[idx, :]
    result = (
        pd.DataFrame({"IID": samples, "Kinship": kin_values})
        .sort_values(by="Kinship", ascending=False)
        .reset_index(drop=True)
    )
    return result


# ---------------------------
# Function to get pairwise kinship (One vs One)
# ---------------------------
def kinship_pair(sample_1, sample_2):
    if sample_1 not in samples:
        raise ValueError(f"Sample '{sample_1}' not found in kinship data.")
    if sample_2 not in samples:
        raise ValueError(f"Sample '{sample_2}' not found in kinship data.")

    idx1 = samples.index(sample_1)
    idx2 = samples.index(sample_2)

    val = kinship_matrix[idx1, idx2]
    return pd.DataFrame(
        {"Sample_1": [sample_1], "Sample_2": [sample_2], "Kinship": [val]}
    )


# ---------------------------
# CLI Output
# ---------------------------
if sample_name_cli:
    pd.set_option("display.max_rows", 50)
    try:
        if sample_name_2_cli:
            df_result = kinship_pair(sample_name_cli, sample_name_2_cli)
            print(df_result.to_string(index=False))
        else:
            df_result = kinship_for_sample(sample_name_cli)
            print(df_result)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
