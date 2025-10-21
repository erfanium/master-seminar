BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/00_raw_vcf/*
OUT_PATH=$BASE_PATH/01_merged/data.vcf
FLAGS="--missing-to-ref"
# FLAGS=""

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

echo "Merging VCF files..."
bcftools merge  --force-no-index $FLAGS $IN_PATH | bcftools +fill-tags -o $OUT_PATH -- -t TYPE,AC,AC_Het,F_MISSING,MAF,HWE

echo "Counting variants..."
bcftools +counts $OUT_PATH