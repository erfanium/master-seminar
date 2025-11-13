set -e
BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

rm -rf ./$BASE_PATH/01_merged ./$BASE_PATH/02_filtered ./$BASE_PATH/03_distribution_analyze ./$BASE_PATH/10_kinship ./$BASE_PATH/20_pca ./$BASE_PATH/21_mds ./$BASE_PATH/30_cluster ./$BASE_PATH/40_plot
# rm -rf ./$BASE_PATH/02_filtered ./$BASE_PATH/03_distribution_analyze ./$BASE_PATH/10_kinship ./$BASE_PATH/20_pca ./$BASE_PATH/21_mds ./$BASE_PATH/30_cluster ./$BASE_PATH/40_plot