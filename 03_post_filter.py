#!/usr/bin/env python3
"""
Post-merge filtering: Apply custom Python-based filter to merged VCF.

Reads merged VCF from 02_merged/ and writes filtered VCF to 03_filtered/.
This filter is applied AFTER merging on the single merged VCF file.

Edit the filter_fn() function to customize filtering logic.
"""

import os
import sys
import subprocess
from pathlib import Path
from cyvcf2 import VCF, Writer


def filter_fn(variant):
    """
    Custom post-merge filter function. Edit this to implement your filtering logic.
    
    Args:
        variant: A cyvcf2 variant object with properties like:
            - variant.CHROM: chromosome
            - variant.POS: position
            - variant.REF: reference allele
            - variant.ALT: alternate alleles (list)
            - variant.ID: variant ID (CHROM-POS-REF-ALT)
            - variant.FILTER: filter status
            - variant.INFO: dictionary of INFO fields (MAF, AC, AN, etc.)
            - variant.call_rate: proportion of non-missing genotypes
        
    Returns:
        bool: True if variant should be kept, False otherwise
    """
    
    # Example filters (uncomment to enable):
    
    # Keep only PASS variants
    # if variant.FILTER != 'PASS':
    #     return False
    
    # Filter by Minor Allele Frequency
    # maf = variant.INFO.get("MAF")
    # if maf is not None and maf < 0.01:
    #     return False
    
    # Filter by call rate
    # if variant.call_rate < 0.95:
    #     return False
    
    # Skip multiallelic sites
    # if len(variant.ALT) > 1:
    #     return False
    
    # Filter by Hardy-Weinberg Equilibrium
    # hwe = variant.INFO.get("HWE")
    # if hwe is not None and hwe < 1e-6:
    #     return False
    
    # Default: keep all variants
    return True


def main():
    # 1. Check arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <base_path>")
        sys.exit(1)

    base_path = Path(sys.argv[1])

    # 2. Define paths
    in_path = base_path / "02_merged"
    out_path = base_path / "03_filtered"

    input_vcf = in_path / "data.vcf.gz"
    output_vcf = out_path / "data.vcf.gz"

    if not input_vcf.exists():
        print(f"Error: Input VCF not found: {input_vcf}")
        sys.exit(1)

    # 3. Read environment variables
    samples_env = os.environ.get("SAMPLES_TO_IGNORE", "").strip()
    samples_to_ignore = []
    if samples_env:
        samples_to_ignore = [s.strip() for s in samples_env.split(",") if s.strip()]

    # 4. Create output directory
    out_path.mkdir(parents=True, exist_ok=True)

    # 5. Perform filtering
    print("Applying post-merge filter...")
    
    # Open input VCF
    vcf = VCF(str(input_vcf))
    
    # Apply sample exclusion if needed
    if samples_to_ignore:
        print(f"Excluding samples: {samples_to_ignore}")
        vcf.set_samples(exclude=samples_to_ignore)
    
    # Open output VCF writer
    writer = Writer(str(output_vcf), vcf)

    kept = 0
    total = 0
    filtered = 0

    for variant in vcf:
        total += 1
        
        try:
            if not filter_fn(variant):
                filtered += 1
                continue
        except Exception as e:
            print(f"Error processing variant {variant.CHROM}:{variant.POS}: {e}")
            raise
        
        writer.write_record(variant)
        kept += 1

    writer.close()

    print(f"\nPost-merge filtering summary:")
    print(f"  Total variants:    {total}")
    print(f"  Filtered out:      {filtered}")
    print(f"  Kept:              {kept} ({100*kept/total:.1f}%)")

    print("\nIndexing compressed VCF...")
    subprocess.run(
        ["bcftools", "index", "-t", str(output_vcf)],
        check=True
    )

    print("Counting variants...")
    subprocess.run(
        ["bcftools", "+counts", str(output_vcf)],
        check=True
    )


if __name__ == "__main__":
    main()
