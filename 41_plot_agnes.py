import sys
import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram
import matplotlib.pyplot as plt


def load_input(path: str):
    rows = []
    labels = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.strip().split()
            # first two fields are IDs; rest are numeric features
            label = parts[0]
            vec = list(map(float, parts[2:]))
            labels.append(label)
            rows.append(vec)
    return np.array(rows), labels


import mpld3


def plot_agnes(data: np.ndarray, labels):
    # AGNES using Ward linkage (can change to single/complete/average)
    Z = linkage(data, method="ward")

    plt.figure(figsize=(20, 6))
    dendrogram(Z, labels=labels, leaf_rotation=90, leaf_font_size=10)
    plt.title("AGNES Dendrogram")
    plt.tight_layout()
    html = mpld3.fig_to_html(plt.gcf())
    with open("agnes_dendrogram.html", "w", encoding="utf-8") as outf:
        outf.write(html)
    plt.show()


def main():
    if len(sys.argv) < 2:
        print("Usage: python agnes_plot.py <input_file>")
        sys.exit(1)

    path = sys.argv[1]
    data, labels = load_input(path)
    plot_agnes(data, labels)


if __name__ == "__main__":
    main()
