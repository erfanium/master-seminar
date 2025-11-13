BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/02_filtered/data.vcf
OUT_PATH=$BASE_PATH/10_kinship/out

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

plink --vcf $IN_PATH --distance ibs flat-missing square --out $OUT_PATH > $OUT_PATH.log