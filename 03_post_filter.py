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
import atexit
from pathlib import Path
from cyvcf2 import VCF, Writer
import pandas as pd
from sortedcontainers import SortedDict

count = {
    "total": 0,
    "exact_match": 0,
    "prefix_match": 0,
    "not_found": 0,
}

NOT_FOUND_LOG_FILE = Path("not_found_variants.log")
_not_found_log_handle = None


def _get_not_found_log_handle():
    global _not_found_log_handle
    if _not_found_log_handle is None or _not_found_log_handle.closed:
        _not_found_log_handle = NOT_FOUND_LOG_FILE.open("a")
    return _not_found_log_handle


@atexit.register
def _close_not_found_log_handle():
    global _not_found_log_handle
    if _not_found_log_handle is not None and not _not_found_log_handle.closed:
        _not_found_log_handle.close()


def log_not_found_variant_to_file(variant, sample_names, iranom_index=None):
    """Log variants not found in Iranom AF data to a file for later analysis."""
    key = to_iranom_variant_key_format(
        variant.CHROM, variant.POS, variant.REF, (variant.ALT)[0]
    )
    variant_sample_names = [
        sample_name
        for sample_name, genotype in zip(sample_names, variant.genotypes)
        if genotype[0] != 0 or genotype[1] != 0
    ]
    log_handle = _get_not_found_log_handle()
    log_handle.write(f"{key} ({', '.join(variant_sample_names)})\n")


def to_iranom_variant_key_format(chrom, pos, ref, alt):
    """Coverts standard VCF variant key format to Iranom AF CSV format. e.g. X-153056311-C-CAG to X-153056311---AG"""

    # remove common prefix from ref and alt
    while ref and alt and ref[0] == alt[0]:
        ref = ref[1:]
        alt = alt[1:]

    # if empty use -
    if not ref:
        ref = "-"
    if not alt:
        alt = "-"

    return f"{chrom}-{pos}-{ref}-{alt}"


def filter_fn(variant, iranom_index=None, sample_names=None):
    count["total"] += 1
    # return True

    key = to_iranom_variant_key_format(
        variant.CHROM, variant.POS, variant.REF, (variant.ALT)[0]
    )

    row = iranom_index.get(key)
    if row:
        count["exact_match"] += 1
        return True
        # iranome_af: str = row["Iranome_AF"]
        # if iranome_af != ".":
        #     af_value = float(iranome_af)
        #     if af_value > 0.02:
        #         return False  # Filter out common variants
        #     else:
        #         return True
        # print(f"Variant {key} found in Iranom AF data: {row}")
    else:
        pass
        prefix = f"{variant.CHROM}-{variant.POS}"
        row = get_by_prefix(iranom_index, prefix)
        if row:
            count["prefix_match"] += 1
            print(
                f"Variant {key} found but not exact match in Iranom AF data. Matching prefix: {prefix} to keys {list(row.keys())}"
            )
        else:
            count["not_found"] += 1
            log_not_found_variant_to_file(variant, sample_names or [], iranom_index)

    return True


def get_by_prefix(iranom_index, prefix):
    """Get all rows matching a prefix using B-tree range query."""
    if not iranom_index:
        return {}
    # irange returns keys in [prefix, prefix + chr(max_unicode))
    # Build dict by mapping keys to their values
    return {k: iranom_index[k] for k in iranom_index.irange(prefix, prefix + "\uffff")}


def main():
    # 1. Check arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <base_path>")
        print(f"Environment variables:")
        print(
            f"  POST_FILTER_SYMLINK_ONLY=1: Skip filtering and create symlink to merged VCF"
        )
        sys.exit(1)

    base_path = Path(sys.argv[1])
    POST_FILTER_SYMLINK_ONLY = os.environ.get(
        "POST_FILTER_SYMLINK_ONLY", ""
    ).lower() in ("1", "true", "yes")

    # 2. Define paths
    in_path = base_path / "02_merged"
    out_path = base_path / "03_filtered"
    iranom_path = base_path / "00_iranom_af" / "data.csv"

    input_vcf = in_path / "data.vcf.gz"
    output_vcf = out_path / "data.vcf.gz"

    if not input_vcf.exists():
        print(f"Error: Input VCF not found: {input_vcf}")
        sys.exit(1)

    # 3. Read environment variables
    # samples_env = os.environ.get("SAMPLES_TO_IGNORE", "").strip()
    # samples_to_ignore = []
    # if samples_env:
    #     samples_to_ignore = [s.strip() for s in samples_env.split(",") if s.strip()]

    # 4. Create output directory
    out_path.mkdir(parents=True, exist_ok=True)

    # 4a. Handle symlink-only mode
    if POST_FILTER_SYMLINK_ONLY:
        print("Symlink-only mode: Creating symlink to merged VCF...")
        if output_vcf.exists() or output_vcf.is_symlink():
            output_vcf.unlink()

        # Use relative path for symlink (from output dir to input file)
        rel_path = os.path.relpath(input_vcf, output_vcf.parent)
        output_vcf.symlink_to(rel_path)

        # Also create symlink for the index if it exists
        input_vcf_idx = Path(str(input_vcf) + ".tbi")
        output_vcf_idx = Path(str(output_vcf) + ".tbi")
        if input_vcf_idx.exists():
            if output_vcf_idx.exists() or output_vcf_idx.is_symlink():
                output_vcf_idx.unlink()
            rel_idx_path = os.path.relpath(input_vcf_idx, output_vcf_idx.parent)
            output_vcf_idx.symlink_to(rel_idx_path)

        print(f"✓ Created symlink: {output_vcf} -> {rel_path}")
        return

    # 5. Perform filtering
    print("Applying post-merge filter...")

    # Open input VCF
    vcf = VCF(str(input_vcf))
    sample_names = list(vcf.samples)

    # Apply sample exclusion if needed
    # if samples_to_ignore:
    #     print(f"Excluding samples: {samples_to_ignore}")
    #     vcf.set_samples(exclude=samples_to_ignore)

    # Open output VCF writer
    writer = Writer(str(output_vcf), vcf)

    kept = 0
    total = 0
    filtered = 0

    # 2. Load Iranom AF CSV and create B-tree index
    print("Loading Iranom AF data...")
    if not iranom_path.exists():
        print(f"Warning: Iranom AF file not found: {iranom_path}")
        iranom_index = SortedDict()
    else:
        df = pd.read_csv(iranom_path)
        # Create B-tree index: Variant -> entire row (dict of column values)
        # SortedDict maintains sorted order for range/prefix queries
        iranom_index = SortedDict(df.set_index("Variant").to_dict("index"))
        print(f"Loaded {len(iranom_index)} variants from Iranom AF data")

    for variant in vcf:
        total += 1

        try:
            if not filter_fn(variant, iranom_index, sample_names):
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

    print(f"\nIranom AF matching summary:")
    print(f"  Total variants:    {count['total']}")
    print(
        f"  Exact matches:     {count['exact_match']} ({100*count['exact_match']/count['total']:.1f}%)"
    )
    print(
        f"  Prefix matches:    {count['prefix_match']} ({100*count['prefix_match']/count['total']:.1f}%)"
    )
    print(
        f"  Not found:         {count['not_found']} ({100*count['not_found']/count['total']:.1f}%)"
    )

    print("\nIndexing compressed VCF...")
    subprocess.run(["bcftools", "index", "-t", str(output_vcf)], check=True)

    print("Counting variants...")
    subprocess.run(["bcftools", "+counts", str(output_vcf)], check=True)


if __name__ == "__main__":
    main()
