import sys
import json
import numpy as np
from scipy.cluster.hierarchy import linkage


def load_input(path: str):
    rows = []
    labels = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.strip().split()
            label = parts[0]
            vec = list(map(float, parts[2:]))
            labels.append(label)
            rows.append(vec)
    return np.array(rows), labels


def build_tree(Z, labels):
    """
    Convert linkage matrix into a *single tree root object* with a 'children' list.
    """
    n = len(labels)
    nodes = {}

    # Initialize leaves
    for i, label in enumerate(labels):
        nodes[i] = {
            "label": label,
            "distance": 0.0,
        }

    # Build internal nodes
    for idx, (c1, c2, dist, _) in enumerate(Z, start=n):
        c1 = int(c1)
        c2 = int(c2)
        nodes[idx] = {"distance": float(dist), "children": [nodes[c1], nodes[c2]]}

    root_index = len(Z) + n - 1
    return nodes[root_index]


def save_nested_json(data: np.ndarray, labels):
    Z = linkage(data, method="ward")
    root = build_tree(Z, labels)

    with open("agnes_tree.json", "w", encoding="utf-8") as f:
        json.dump(root, f, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage: python agnes_plot.py <input_file>")
        sys.exit(1)

    path = sys.argv[1]
    data, labels = load_input(path)
    save_nested_json(data, labels)


if __name__ == "__main__":
    main()
