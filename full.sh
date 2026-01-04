set -e
BASE_PATH=$1


source ./config.sh

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

python ./clean.py $BASE_PATH

echo "Step 1: Merging VCF fees"
python ./01_merge.py $BASE_PATH


echo "Step 2: Applying filters"
bash ./02_apply_filter.sh $BASE_PATH
# echo "Step 3: Analyzing distribution"
# python ./03_distribution_analyze.py $BASE_PATH
echo "Step 4: Calculating kinship"
bash ./10_kinship.sh $BASE_PATH
echo "Step 5: Performing PCA"
bash ./20_pca.sh $BASE_PATH
echo "Step 6: Performing MDS"
bash ./21_mds.sh $BASE_PATH

echo "Step 7: Clustering results"
python ./30_cluster.py $BASE_PATH

echo "Step 7: Profile each cluster"
python ./31_cluster_profile.py $BASE_PATH

# echo "Step 8: Plotting results"
# python ./40_plot.py $BASE_PATH
