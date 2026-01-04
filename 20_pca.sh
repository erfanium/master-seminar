BASE_PATH=$1
PCA_COUNT=${PCA_COUNT:-10}

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/02_filtered/data.vcf
OUT_PATH=$BASE_PATH/20_pca/out

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

plink --vcf $IN_PATH --cluster --pca $PCA_COUNT var-wts header --out $OUT_PATH > $OUT_PATH.log

python3 tools/var-wts-topk.py $OUT_PATH.eigenvec.var > $OUT_PATH.eigenvec.var.topk.json