import os
import sys
import subprocess

# 1. Check arguments (Equivalent to if [ -z "$BASE_PATH" ])
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <base_path>")
    sys.exit(1)

base_path = sys.argv[1]

# 2. Define paths
in_path = os.path.join(base_path, "01_merged", "data.vcf")
out_path = os.path.join(base_path, "02_filtered", "data.vcf")

# 3. Get Environment Variable (Equivalent to SNP_FILTER=${SNP_FILTER:-'none'})
snp_filter = os.environ.get("SNP_FILTER", "none")

# 4. Ensure output directory exists (Equivalent to mkdir -p)
out_dir = os.path.dirname(out_path)
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# 5. Conditional Logic
if snp_filter != "none":
    print(f"Applying SNP filter: {snp_filter}")

    # Run bcftools view -i "$SNP_FILTER" $IN_PATH -o $OUT_PATH
    subprocess.run(
        ["bcftools", "view", "-i", snp_filter, in_path, "-o", out_path], check=True
    )

    print("Counting variants...")
    # Run bcftools +counts $OUT_PATH
    subprocess.run(["bcftools", "+counts", out_path], check=True)

else:
    print("No SNP filter applied, creating symlink to input instead of copying.")

    rel_in_path = os.path.relpath(in_path, start=out_dir)

    if os.path.exists(out_path) or os.path.islink(out_path):
        os.remove(out_path)

    os.symlink(rel_in_path, out_path)
