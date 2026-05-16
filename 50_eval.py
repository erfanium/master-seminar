#!/usr/bin/env python3

import os
import sys

import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import (
    adjusted_mutual_info_score,
    adjusted_rand_score,
    classification_report,
    confusion_matrix,
    f1_score,
    homogeneity_completeness_v_measure,
)


def resolve_actual_cluster(labels_df, sample_id):
    matches = labels_df[
        labels_df["path"].str.contains(sample_id, na=False, regex=False)
    ]

    if matches.empty:
        raise ValueError(
            f"Could not find actual cluster label for sampleId '{sample_id}' in 00_labels/data.csv"
        )

    unique_clusters = matches["cluster"].dropna().unique()
    if len(unique_clusters) != 1:
        raise ValueError(
            f"Found conflicting actual cluster labels for sampleId '{sample_id}': {list(unique_clusters)}"
        )

    return unique_clusters[0]


def align_predicted_clusters(y_true, y_pred):
    contingency = pd.crosstab(y_true, y_pred)
    cost_matrix = -contingency.to_numpy()
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    mapping = {
        contingency.columns[col_index]: contingency.index[row_index]
        for row_index, col_index in zip(row_ind, col_ind)
    }

    aligned_pred = y_pred.map(mapping).fillna(y_pred)
    return aligned_pred, mapping


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
        sys.exit(1)

    base_path = sys.argv[1]
    predicted_path = os.path.join(base_path, "30_cluster", "pca_clusters.tsv")
    actual_labels_path = os.path.join(base_path, "00_labels", "data.csv")

    print(f"[INFO] Loading predicted clusters from: {predicted_path}")
    predicted_df = pd.read_csv(predicted_path, sep="\t")

    print(f"[INFO] Loading actual labels from: {actual_labels_path}")
    actual_df = pd.read_csv(actual_labels_path)
    actual_df = actual_df.dropna(subset=["path", "cluster"])

    if "IID" not in predicted_df.columns or "Cluster" not in predicted_df.columns:
        raise ValueError(
            "Predicted clusters file must contain 'IID' and 'Cluster' columns"
        )

    eval_df = predicted_df[["IID", "Cluster"]].copy()
    eval_df["ActualCluster"] = (
        eval_df["IID"]
        .astype(str)
        .apply(lambda sample_id: resolve_actual_cluster(actual_df, sample_id))
    )

    y_true = eval_df["ActualCluster"]
    y_pred = eval_df["Cluster"]

    print("\n[INFO] Evaluation summary")
    print(f"Samples evaluated: {len(eval_df)}")
    print(f"Actual labels: {sorted(y_true.unique())}")
    print(f"Predicted labels: {sorted(y_pred.unique())}")

    ari = adjusted_rand_score(y_true, y_pred)
    ami = adjusted_mutual_info_score(y_true, y_pred)
    homogeneity, completeness, v_measure = homogeneity_completeness_v_measure(
        y_true, y_pred
    )
    aligned_pred, label_mapping = align_predicted_clusters(y_true, y_pred)
    macro_f1 = f1_score(y_true, aligned_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, aligned_pred, average="weighted", zero_division=0)

    print("\n[INFO] Standard metrics")
    print(f"Adjusted Rand Index: {ari:.4f}")
    print(f"Adjusted Mutual Information: {ami:.4f}")
    print(f"Homogeneity: {homogeneity:.4f}")
    print(f"Completeness: {completeness:.4f}")
    print(f"V-measure: {v_measure:.4f}")
    print(f"Aligned label mapping: {label_mapping}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")

    labels = sorted(set(y_true.unique()) | set(aligned_pred.unique()))
    conf_mat = confusion_matrix(y_true, aligned_pred, labels=labels)
    conf_mat_df = pd.DataFrame(conf_mat, index=labels, columns=labels)

    print("\n[INFO] Confusion matrix (after label alignment)")
    print(conf_mat_df.to_string())

    print("\n[INFO] Classification report (after label alignment)")
    print(classification_report(y_true, aligned_pred, zero_division=0))


if __name__ == "__main__":
    main()
