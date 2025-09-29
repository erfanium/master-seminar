BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi
  
IN_PATH=$BASE_PATH/02_with_tags/data.vcf
OUT_PATH=$BASE_PATH/03_filtered/data.vcf

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

bcftools view -i 'F_MISSING>0.25 && MAF>0.001' $IN_PATH -o $OUT_PATH
