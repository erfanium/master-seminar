BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/00_raw_vcf/*
OUT_PATH=$BASE_PATH/01_merged/data.vcf
# FLAGS="--missing-to-ref"
FLAGS="+"

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

bcftools merge --force-no-index $FLAGS -o $OUT_PATH $IN_PATH