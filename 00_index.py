#!/usr/bin/env python3
"""
Index VCF files and optionally apply pre-merge filtering.

Compresses raw VCF files from 00_raw_vcf/ and writes indexed files to 01_indexed/.
If PRE_MERGE_FILTER_EXPRESSION is set, applies bcftools filtering.

Environment variables:
- PRE_MERGE_FILTER_EXPRESSION: bcftools filter expression (e.g., "FILTER='PASS'")
- MAX_WORKERS: Number of parallel jobs (defaults to CPU count)
"""

import os
import sys
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def run(cmd, stdout=None):
    """Run a command and fail hard if it errors."""
    # When stdout is redirected to a file, don't capture it
    capture = stdout is None
    result = subprocess.run(cmd, stdout=stdout, capture_output=capture, text=True)
    if result.returncode != 0:
        err_msg = result.stderr if capture else "Check output for errors"
        print(f"Command failed: {' '.join(cmd)}\nError: {err_msg}", file=sys.stderr)
        sys.exit(result.returncode)


def count_variants(vcf_path):
    """Count the number of variants in a VCF file using bcftools."""
    # First try the fast +counts plugin
    try:
        result = subprocess.run(
            ["bcftools", "+counts", str(vcf_path)],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.splitlines():
            if 'Number of sites:' in line or 'number of records' in line.lower():
                return int(line.split()[-1])
    except subprocess.CalledProcessError:
        pass # Plugin might be missing or file might be corrupted, fall through to fallback
    
    # Fallback: Count lines without headers (slower but 100% reliable)
    try:
        p1 = subprocess.Popen(["bcftools", "view", "-H", str(vcf_path)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        p2 = subprocess.Popen(["wc", "-l"], stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        p1.stdout.close()
        out, _ = p2.communicate()
        if p2.returncode == 0:
            return int(out.strip())
    except Exception as e:
        print(f"  Warning: Could not count variants for {vcf_path.name}: {e}")
        
    return None


def process_vcf(vcf, out_path, pre_merge_filter):
    """Worker function to process a single VCF file."""
    if vcf.name.startswith("_"):
        return f"Skipping {vcf.name} (starts with '_')"

    out_file = out_path / f"{vcf.name}.gz"
    logs = [f"\nProcessing {vcf.name}"]

    # Count variants before filtering (directly from raw file)
    variants_before = count_variants(vcf)
    logs.append(f"  Variants before filter: {variants_before}")

    if pre_merge_filter != "none":
        logs.append(f"  Applying filter: {pre_merge_filter}")
        # Single-pass: filter raw VCF and output directly to compressed target
        cmd = ["bcftools", "view", "-i", pre_merge_filter, "-Oz", "-o", str(out_file), str(vcf)]
        run(cmd)
    else:
        # Just compress
        with open(out_file, "wb") as f_out:
            run(["bgzip", "-c", str(vcf)], stdout=f_out)

    # Index compressed file
    run(["bcftools", "index", "-t", str(out_file)])
    
    # If filtered, count variants again and calculate diff
    if pre_merge_filter != "none":
        variants_after = count_variants(out_file)
        logs.append(f"  Variants after filter:  {variants_after}")
        if variants_before is not None and variants_after is not None:
            removed = variants_before - variants_after
            pct = (100 * removed / variants_before) if variants_before > 0 else 0
            logs.append(f"  Removed: {removed} ({pct:.1f}%)")

    return "\n".join(logs)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <base_path>")
        sys.exit(1)

    base_path = Path(sys.argv[1])
    in_path = base_path / "00_raw_vcf"
    out_path = base_path / "01_indexed"

    if not in_path.exists():
        print(f"Input directory does not exist: {in_path}")
        sys.exit(1)

    out_path.mkdir(parents=True, exist_ok=True)

    pre_merge_filter = os.environ.get("PRE_MERGE_FILTER_EXPRESSION", "none")
    if pre_merge_filter != "none":
        print(f"Pre-merge filter enabled: {pre_merge_filter}")

    vcfs = sorted(in_path.glob("*.vcf"))
    if not vcfs:
        print(f"No VCF files found in {in_path}")
        sys.exit(1)

    print(f"Found {len(vcfs)} VCF files")

    # Use max_workers from environment, default to CPU count
    workers = int(os.environ.get("MAX_WORKERS", os.cpu_count() or 4))
    print(f"Processing with {workers} concurrent workers...")

    processed_count = 0

    # Run in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_vcf, vcf, out_path, pre_merge_filter): vcf 
            for vcf in vcfs
        }
        
        for future in as_completed(futures):
            # Print the grouped log output for each file as it completes
            print(future.result())
            vcf_path = futures[future]
            if not vcf_path.name.startswith("_"):
                processed_count += 1

    print(f"\nAll {processed_count} files processed successfully.")


if __name__ == "__main__":
    main()
