BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi
  
IN_PATH=$BASE_PATH/01_merged/data.vcf
OUT_PATH=$BASE_PATH/02_filtered/data.vcf

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

bcftools view -i 'MAF<0.05' $IN_PATH -o $OUT_PATH

echo "Counting variants..."
bcftools +counts $OUT_PATH