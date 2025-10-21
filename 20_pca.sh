BASE_PATH=$1

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 <base_path>"
    exit 1
fi

IN_PATH=$BASE_PATH/02_filtered/data.vcf
OUT_PATH=$BASE_PATH/20_pca/out

# ensure output directory exists
mkdir -p $(dirname $OUT_PATH)

plink --vcf $IN_PATH --pca 10 header --out $OUT_PATH
# ~/Documents/uni/bio/VCF2PCACluster/bin/VCF2PCACluster -InVCF $IN_PATH -OutPut $OUT_PATH -ClusterMethod EM