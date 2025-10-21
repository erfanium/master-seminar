import os
import sys
from cyvcf2 import VCF
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


if len(sys.argv) < 2:
    print(f"Usage: {os.path.basename(sys.argv[0])} <base_path>")
    sys.exit(1)

BASE_PATH = sys.argv[1]

# BASE_PATH = "data"

# File paths
before_filter = f"{BASE_PATH}/01_merged"
after_filter = f"{BASE_PATH}/02_filtered"
output_dir = f"{BASE_PATH}/03_distribution_analyze"

os.makedirs(output_dir, exist_ok=True)


def process_vcf(vcf_path, output_prefix):

    # Load VCF
    vcf = VCF(vcf_path)

    # Collect INFO fields
    data = []
    for variant in vcf:
        data.append(
            {
                "F_MISSING": variant.INFO.get("F_MISSING"),
                "MAF": variant.INFO.get("MAF"),
                "AC_Het": variant.INFO.get("AC_Het"),
                "HWE": variant.INFO.get("HWE"),
            }
        )

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df = df.apply(pd.to_numeric, errors="coerce")

    # Print summary statistics
    print(df.describe())

    # Plot distributions
    sns.set(style="whitegrid")
    fields = ["F_MISSING", "MAF", "AC_Het", "HWE"]
    plt.figure(figsize=(16, 4))
    for i, field in enumerate(fields, 1):
        plt.subplot(1, 4, i)
        sns.histplot(df[field].dropna(), kde=True, bins=20)
        plt.title(f"{field} Distribution")
        plt.xlabel(field)
        plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{output_prefix}_distribution.png")


process_vcf(f"{before_filter}/data.vcf", "before")
process_vcf(f"{after_filter}/data.vcf", "after")
