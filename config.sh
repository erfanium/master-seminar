# Configuration file for the pipeline

export MISSING_TO_REF=true

export SNP_FILTER='none'
# export SNP_FILTER='MAF<0.10 && MAF>0'
# export SNP_FILTER='MAF>(1/490)'


export PCA_COUNT=40


# The minimum number of points required for a group of points to be considered a cluster.
export HDB_MIN_SAMPLES=2

# The number of points in a neighborhood around a point required for it to be considered a core point. Essentially controls how conservative the algorithm is about identifying dense regions.
export HDB_MIN_CLUSTER_SIZE=2


export CLUSTER_LIMIT_PCA=40

# skip topk calculation for variants of each cluster
export SKIP_CLUSTER_TOPK_VARIANT_CALCULATION=false


# export SNP_FILTER='none'