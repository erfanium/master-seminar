#!/usr/bin/env python3

import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
output_dir = f"{BASE_PATH}/40_plot_kinship"

os.makedirs(output_dir, exist_ok=True)

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
# Mask upper triangle + diagonal
# ---------------------------
mask = np.triu(np.ones_like(kinship_matrix, dtype=bool), k=0)
kinship_matrix_masked = np.where(mask, np.nan, kinship_matrix)

# ---------------------------
# Interactive Heatmap (HTML)
# ---------------------------
fig = go.Figure(
    data=go.Heatmap(
        z=kinship_matrix_masked,
        x=samples,
        y=samples,
        colorscale="Viridis",
        colorbar=dict(title="Kinship coefficient"),
        hoverongaps=False,
    )
)
fig.update_layout(
    title="Kinship Matrix (Lower Triangle, Diagonal Removed)",
    xaxis=dict(tickangle=90, type="category"),
    yaxis=dict(autorange="reversed", type="category"),
    width=1200,
    height=1000,
)

output_html = os.path.join(output_dir, "kinship_triangular.html")
fig.write_html(output_html, include_plotlyjs="cdn")

print(f"✅ Interactive HTML plot saved in: {output_html}")
