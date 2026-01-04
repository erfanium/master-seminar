BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi
  
IN_PATH=$BASE_PATH/01_merged/data.vcf
OUT_PATH=$BASE_PATH/02_filtered/data.vcf
SNP_FILTER=${SNP_FILTER:-'none'}

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

if [[ "$SNP_FILTER" != "none" ]]; then
  echo "Applying SNP filter: $SNP_FILTER"
  bcftools view -i "$SNP_FILTER" $IN_PATH -o $OUT_PATH

  echo "Counting variants..."
  bcftools +counts $OUT_PATH
else
    echo "No SNP filter applied, creating symlink to input instead of copying."
    ln -s "$IN_PATH" "$OUT_PATH"
fi