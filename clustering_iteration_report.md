# Clustering Iteration Report

## Goal

Target clustering behavior:

- avoid large clusters
- prefer many small clusters
- ideally most clusters have `<= 5` members

## Baseline

Initial strong-separation configuration produced a few very large clusters:

- max cluster size: `93`
- non-outlier clusters: `5`
- clusters with size `<= 5`: `2`
- silhouette: `0.8798`

This had strong separation, but it did **not** satisfy the small-cluster goal.

## Clustering-Only Iterations

Saved under `data-wes2/30_cluster_iterations/`.

| Iteration | Max Cluster Size | Clusters > 5 | Clusters <= 5 | Outliers | Silhouette |
|---|---:|---:|---:|---:|---:|
| `agg_25` | 24 | 10 | 5 | 10 | 0.2197 |
| `agg_40` | 12 | 14 | 12 | 14 | 0.2477 |
| `kmeans_40` | 12 | 15 | 8 | 17 | 0.2146 |
| `hdbscan_dense` | 93 | 3 | 2 | 10 | 0.8798 |

Best result from this sweep for the stated goal was `agg_40`.

## PCA + Clustering Iterations

Saved under `data-wes2/30_cluster_iterations_pca/`.

| Iteration | PCA_COUNT | CLUSTER_LIMIT_PCA | Algo | N Clusters | Max Cluster Size | Clusters > 5 | Clusters <= 5 | Outliers | Silhouette |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `pca4_lim2_agg40` | 4 | 2 | agglomerative | 40 | 12 | 12 | 17 | 11 | 0.4316 |
| `pca4_lim4_agg40` | 4 | 4 | agglomerative | 40 | 12 | 14 | 12 | 14 | 0.2477 |
| `pca6_lim3_agg40` | 6 | 3 | agglomerative | 40 | 11 | 12 | 16 | 12 | 0.3009 |
| `pca6_lim4_agg40` | 6 | 4 | agglomerative | 40 | 12 | 14 | 12 | 14 | 0.2477 |
| `pca8_lim3_agg50` | 8 | 3 | agglomerative | 50 | 8 | 9 | 24 | 17 | 0.3159 |
| `pca10_lim2_agg50` | 10 | 2 | agglomerative | 50 | 10 | 8 | 28 | 14 | 0.4405 |

## Best Findings

### Best for Strict Small-Cluster Objective

`pca8_lim3_agg50`

- max cluster size: `8`
- non-outlier clusters: `33`
- clusters with size `<= 5`: `24`
- outliers: `17`
- silhouette: `0.3159`

Why it stands out:

- smallest maximum cluster size found so far
- much closer to the desired “all clusters small” behavior

### Best Balanced Candidate

`pca10_lim2_agg50`

- max cluster size: `10`
- non-outlier clusters: `36`
- clusters with size `<= 5`: `28`
- outliers: `14`
- silhouette: `0.4405`

Why it stands out:

- more small clusters overall than `pca8_lim3_agg50`
- better silhouette and Davies-Bouldin than the stricter candidate
- still keeps large clusters much smaller than the original baseline

## Recommendation

If optimizing **strictly for smallest cluster sizes**, prefer:

- `pca8_lim3_agg50`

If optimizing for a **better balance of small clusters and clustering quality**, prefer:

- `pca10_lim2_agg50`

## Current Limitations

Even the best runs are still not fully at the ideal target.

- some clusters are still size `6–10`
- ideal target of mostly `<= 5` has not been fully achieved yet

## Suggested Next Iteration

To push closer to the ideal target, next sweep should try:

- `CLUSTER_N_CLUSTERS=60..80`
- low `CLUSTER_LIMIT_PCA` values like `2` or `3`
- possibly recursive splitting of clusters larger than `5`

## Saved Comparison Files

- `data-wes2/30_cluster_iterations/comparison.json`
- `data-wes2/30_cluster_iterations_pca/comparison.json`
