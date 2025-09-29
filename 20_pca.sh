BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/10_bed/out
OUT_PATH=$BASE_PATH/20_pca/out

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

plink --bfile $IN_PATH --pca 10 header --out $OUT_PATH