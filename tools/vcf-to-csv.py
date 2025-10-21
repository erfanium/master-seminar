#!/usr/bin/env python3
import sys
from cyvcf2 import VCF
import pandas as pd


def process_vcf(vcf_path):
    """Process a VCF and return a DataFrame with variant info."""
    vcf = VCF(vcf_path)
    data = []
    for variant in vcf:
        data.append(
            {
                "CHROM": variant.CHROM,
                "POS": variant.POS,
                "ID": variant.ID,
                "F_MISSING": variant.INFO.get("F_MISSING"),
                "MAF": variant.INFO.get("MAF"),
                "AC_Het": variant.INFO.get("AC_Het"),
                "HWE": variant.INFO.get("HWE"),
            }
        )
    df = pd.DataFrame(data)
    df = df.apply(pd.to_numeric, errors="ignore", downcast="float")
    return df


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} in.vcf", file=sys.stderr)
        sys.exit(1)

    vcf_path = sys.argv[1]
    df = process_vcf(vcf_path)
    df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
