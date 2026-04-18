#!/usr/bin/env python3
"""
Combined variant filtering in a single pass.

Combines:
1. Custom Python filter function (hardcoded, edit default_filter to customize)
2. Standard bcftools expression-based filtering (VARIANT_FILTER_EXPRESSION)
3. Sample exclusion (SAMPLES_TO_IGNORE)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from cyvcf2 import VCF, Writer


def filter_fn(variant):
    
    print(variant.FILTER == 'PASS')
    # print("variant", variant.CHROM, variant.POS, variant.REF, variant.ALT, variant.INFO)
    
    """
    Custom filter function. Edit this to implement your filtering logic.
    
    Args:
        variant: A cyvcf2 variant object
        
    Returns:
        bool: True if variant should be kept, False otherwise
    """
    # Example: keep only variants with MAF > 0.05
    # maf = variant.INFO.get("MAF")
    # if maf is not None and maf < 0.05:
    #     return False
    
    # Example: filter by call rate
    # if variant.call_rate < 0.95:
    #     return False
    
    # Example: skip multiallelic sites
    # if len(variant.ALT) > 1:
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
    in_path = base_path / "01_merged"
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

    # 4. Check if any filtering is needed
    if False:
        print("No filtering enabled. Creating symlink.")
        rel_in_path = os.path.relpath(in_path, start=base_path)

        if out_path.exists() or out_path.is_symlink():
            if out_path.is_symlink():
                out_path.unlink()
            elif out_path.is_dir():
                shutil.rmtree(out_path)
            else:
                out_path.unlink()

        out_path.symlink_to(rel_in_path)
        sys.exit(0)

    # 5. Perform filtering
    print("Filtering variants...")
    
    out_path.mkdir(parents=True, exist_ok=True)

    # Open input VCF
    vcf = VCF(str(input_vcf))
    
    # Apply sample exclusion to header if needed
    if samples_to_ignore:
        print(f"Ignoring samples: {samples_to_ignore}")
        vcf.set_samples(exclude=samples_to_ignore)
    
    # Open output VCF writer
    writer = Writer(str(output_vcf), vcf)

    kept = 0
    total = 0
    filtered = 0

    for variant in vcf:
        total += 1        
        if not filter_fn(variant):
            filtered += 1
            continue
      
        writer.write_record(variant)
        kept += 1

    writer.close()

    print(f"\nFiltering summary:")
    print(f"  Total variants:       {total}")
    print(f"  filter removed: {filtered}")
    print(f"  Kept:                 {kept} ({100*kept/total:.1f}%)")

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


def _evaluate_bcftools_filter(variant, expression):
    """
    Basic evaluation of bcftools filter expressions.
    Supports common patterns like "MAF>0.05", "AC>=2", etc.
    For complex filters, consider using bcftools directly.
    """
    # Remove spaces
    expression = expression.replace(" ", "")
    
    # Parse simple comparisons
    for op in [">=", "<=", "==", "!=", ">", "<"]:
        if op in expression:
            parts = expression.split(op)
            if len(parts) == 2:
                field, value = parts
                field = field.strip()
                try:
                    value = float(value)
                except ValueError:
                    return True  # Can't evaluate, keep variant
                
                field_value = variant.INFO.get(field)
                if field_value is None:
                    return True  # Field not present, keep variant
                
                # Handle multi-allelic fields
                if isinstance(field_value, (list, tuple)):
                    field_value = field_value[0] if field_value else None
                
                if field_value is None:
                    return True
                
                if op == ">=":
                    return float(field_value) >= value
                elif op == "<=":
                    return float(field_value) <= value
                elif op == ">":
                    return float(field_value) > value
                elif op == "<":
                    return float(field_value) < value
                elif op == "==":
                    return float(field_value) == value
                elif op == "!=":
                    return float(field_value) != value
    
    return True  # Default: keep variant


if __name__ == "__main__":
    main()
