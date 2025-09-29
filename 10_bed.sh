BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/03_filtered/data.vcf
OUT_PATH=$BASE_PATH/10_bed/out

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

plink --vcf $IN_PATH --make-bed --out $OUT_PATH