set -e
BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

bash ./01_merge.sh $BASE_PATH
bash ./02_bed.sh $BASE_PATH
bash ./03_pca.sh $BASE_PATH
python ./04_plot.py $BASE_PATH
