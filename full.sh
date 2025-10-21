set -e
BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

bash ./01_merge.sh $BASE_PATH
bash ./02_apply_filter.sh $BASE_PATH
python ./03_distribution_analyze.py $BASE_PATH
bash ./10_kinship.sh $BASE_PATH
bash ./20_pca.sh $BASE_PATH
python ./40_plot.py $BASE_PATH
