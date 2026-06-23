"""
Generate a scree plot (eigenvalue chart) from PLINK PCA output.
Usage: python scripts/plot_eigenvalues.py
Output: report/eigenvalue_scree.png
"""

import os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

EIGENVAL_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data-wes2", "20_pca", "out.eigenval"
)
OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "report", "eigenvalue_scree.png"
)

eigenvalues = np.loadtxt(EIGENVAL_FILE)
n = len(eigenvalues)
pct_variance = eigenvalues / eigenvalues.sum() * 100
cumulative = np.cumsum(pct_variance)
pcs = np.arange(1, n + 1)

fig, ax1 = plt.subplots(figsize=(5.5, 3.5))

ax1.bar(
    pcs, pct_variance, color="steelblue", alpha=0.85, label="Variance explained (%)"
)
ax1.set_xlabel("Principal Component", fontsize=10)
ax1.set_ylabel("Variance Explained (%)", fontsize=10, color="steelblue")
ax1.tick_params(axis="y", labelcolor="steelblue")
ax1.set_xticks(pcs)
ax1.set_ylim(0, pct_variance[0] * 1.3)

ax2 = ax1.twinx()
ax2.plot(
    pcs,
    cumulative,
    color="darkorange",
    marker="o",
    linewidth=1.5,
    markersize=5,
    label="Cumulative (%)",
)
ax2.set_ylabel("Cumulative Variance (%)", fontsize=10, color="darkorange")
ax2.tick_params(axis="y", labelcolor="darkorange")
ax2.set_ylim(0, 105)
ax2.axhline(
    y=cumulative[-1], color="darkorange", linestyle="--", linewidth=0.8, alpha=0.5
)

# Annotate each bar with eigenvalue
for i, (pc, ev, pv) in enumerate(zip(pcs, eigenvalues, pct_variance)):
    ax1.text(
        pc,
        pv + 0.15,
        f"{ev:.2f}",
        ha="center",
        va="bottom",
        fontsize=7,
        color="steelblue",
    )

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper right")

plt.title("Scree Plot: PCA Eigenvalues (10 PCs, 238,500 variant sites)", fontsize=9)
fig.tight_layout()
fig.savefig(OUTPUT_FILE, dpi=200, bbox_inches="tight")
print(f"Saved: {OUTPUT_FILE}")
