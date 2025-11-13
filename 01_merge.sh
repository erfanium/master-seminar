BASE_PATH=$1
MISSING_TO_REF=${MISSING_TO_REF:-true}


if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/00_raw_vcf/*.vcf
OUT_PATH=$BASE_PATH/01_merged/data.vcf


if [[ "$MISSING_TO_REF" == "true" ]]; then
  FLAGS="--missing-to-ref"
else
  FLAGS=""
fi

echo "Merge flags: $FLAGS"

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

echo "Merging VCF files..."
bcftools merge --force-single --force-no-index $FLAGS $IN_PATH \
  | bcftools norm -m -any - \
  | bcftools annotate --set-id '%CHROM-%POS-%REF-%ALT' \
  | bcftools +fill-tags -o $OUT_PATH -- -t AF,TYPE,AC,AC_Het,F_MISSING,MAF,HWE


echo "Counting variants..."
bcftools +counts $OUT_PATH