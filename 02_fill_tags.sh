BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/01_merged/data.vcf
OUT_PATH=$BASE_PATH/02_with_tags/data.vcf

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

bcftools +fill-tags $IN_PATH -o $OUT_PATH -- -t AC,AC_Het,F_MISSING,MAF,HWE