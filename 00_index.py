#!/usr/bin/env python3
"""
Index VCF files and optionally apply pre-merge filtering.

Compresses raw VCF files from 00_raw_vcf/ and writes indexed files to 01_indexed/.
If PRE_MERGE_FILTER_EXPRESSION is set, applies bcftools filtering.

Environment variables:
- PRE_MERGE_FILTER_EXPRESSION: bcftools filter expression (e.g., "FILTER='PASS'")
- DISABLE_MERGE_CSV: If true, ignore sidecar CSV joins entirely
- MAX_WORKERS: Number of parallel jobs (defaults to CPU count)
"""

import os
import sys
import subprocess
import tempfile
import csv
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


def normalize_chrom_name(chrom):
    mapping = {f"chr{i}": str(i) for i in range(1, 23)}
    mapping.update({"chrX": "X", "chrY": "Y", "chrM": "MT", "chrMT": "MT"})
    if chrom in mapping:
        return mapping[chrom]

    allowed = {str(i) for i in range(1, 23)} | {"X", "Y", "MT"}
    if chrom in allowed:
        return chrom

    return None


def write_normalized_vcf(src_vcf, dst_vcf):
    kept = 0
    with open(src_vcf, "r") as src, open(dst_vcf, "w") as dst:
        for line in src:
            if line.startswith("#"):
                dst.write(line)
                continue

            fields = line.rstrip("\n").split("\t")
            normalized = normalize_chrom_name(fields[0])
            if normalized is None:
                continue

            fields[0] = normalized
            dst.write("\t".join(fields) + "\n")
            kept += 1
    return kept


def find_sidecar_csv(vcf_path):
    candidates = [vcf_path.with_suffix('.csv'), vcf_path.with_name(f"{vcf_path.name}.csv")]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_variant_key(chrom, pos, ref, alt):
    return (str(chrom), str(pos), str(ref), str(alt))


def build_variant_keys(chrom, pos, ref, alt):
    keys = {build_variant_key(chrom, pos, ref, alt)}

    if len(ref) == 1 and len(alt) > 1 and alt.startswith(ref):
        keys.add(build_variant_key(chrom, pos, "-", alt[1:]))

    if len(ref) > 1 and len(alt) == 1 and ref.startswith(alt):
        keys.add(build_variant_key(chrom, pos, ref[1:], "-"))

    return keys


def resolve_csv_columns(fieldnames):
    aliases = {
        "CHROM": ["CHROM", "Chr", "chr", "#CHROM"],
        "POS": ["POS", "Start", "start"],
        "REF": ["REF", "Ref", "ref"],
        "ALT": ["ALT", "Alt", "alt"],
    }
    resolved = {}
    for logical_name, candidates in aliases.items():
        for candidate in candidates:
            if candidate in fieldnames:
                resolved[logical_name] = candidate
                break

    missing = [name for name in aliases if name not in resolved]
    if missing:
        raise ValueError(
            f"CSV sidecar is missing required columns: {', '.join(missing)}"
        )

    return resolved


def load_variant_rows(csv_path):
    with open(csv_path, newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        column_map = resolve_csv_columns(fieldnames)

        rows = {}
        for row in reader:
            chrom = normalize_chrom_name(row[column_map["CHROM"]])
            if chrom is None:
                continue
            key = build_variant_key(
                chrom,
                row[column_map["POS"]],
                row[column_map["REF"]],
                row[column_map["ALT"]],
            )
            rows[key] = row

    return fieldnames, column_map, rows


def augment_vcf_with_csv(src_vcf, dst_vcf, csv_path):
    fieldnames, column_map, rows_by_variant = load_variant_rows(csv_path)
    join_columns = set(column_map.values())
    extra_fields = [name for name in fieldnames if name not in join_columns]
    missing_count = 0
    kept = 0
    header_seen = False

    with open(src_vcf, "r") as src, open(dst_vcf, "w") as dst:
        for line in src:
            if line.startswith("##"):
                dst.write(line)
                continue

            if line.startswith("#CHROM"):
                for field in extra_fields:
                    dst.write(
                        f'##INFO=<ID=CSV_{field},Number=.,Type=String,Description="Joined from sidecar CSV column {field}">\n'
                    )
                dst.write(line)
                header_seen = True
                continue

            fields = line.rstrip("\n").split("\t")
            normalized = normalize_chrom_name(fields[0])
            if normalized is None:
                continue

            fields[0] = normalized
            joined_rows = []
            missing_alts = []
            for alt in fields[4].split(","):
                row = None
                for key in build_variant_keys(fields[0], fields[1], fields[3], alt):
                    row = rows_by_variant.get(key)
                    if row is not None:
                        break
                if row is None:
                    missing_alts.append(alt)
                else:
                    joined_rows.append(row)

            if missing_alts:
                print(
                    f"No CSV row found for {fields[0]}:{fields[1]} {fields[3]}>{','.join(missing_alts)} in {csv_path.name}",
                    file=sys.stderr,
                )
                missing_count += len(missing_alts)

            if joined_rows and extra_fields:
                joined_info = []
                for field in extra_fields:
                    values = []
                    for row in joined_rows:
                        value = row.get(field, "")
                        if value not in ("", None):
                            values.append(str(value).replace(";", ","))
                    if values:
                        joined_info.append(f"CSV_{field}={'|'.join(values)}")

                if joined_info:
                    if fields[7] == ".":
                        fields[7] = ";".join(joined_info)
                    else:
                        fields[7] = fields[7] + ";" + ";".join(joined_info)

            dst.write("\t".join(fields) + "\n")
            kept += 1

    if not header_seen:
        raise ValueError(f"Invalid VCF header in {src_vcf}")

    return kept, missing_count


def count_variants(vcf_path):
    """Count the number of variants in a VCF file using bcftools."""
    # First try the fast +counts plugin
    try:
        result = subprocess.run(
            ["bcftools", "+counts", str(vcf_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if "Number of sites:" in line or "number of records" in line.lower():
                return int(line.split()[-1])
    except subprocess.CalledProcessError:
        pass  # Plugin might be missing or file might be corrupted, fall through to fallback

    # Fallback: Count lines without headers (slower but 100% reliable)
    try:
        p1 = subprocess.Popen(
            ["bcftools", "view", "-H", str(vcf_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        p2 = subprocess.Popen(
            ["wc", "-l"],
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        p1.stdout.close()
        out, _ = p2.communicate()
        if p2.returncode == 0:
            return int(out.strip())
    except Exception as e:
        print(f"  Warning: Could not count variants for {vcf_path.name}: {e}")

    return None


def process_vcf(vcf, out_path, pre_merge_filter):
    """Worker function to process a single VCF file.
    Returns a dict with keys: name, skipped, variants_before, variants_after.
    """
    if vcf.name.startswith("_"):
        return {
            "name": vcf.name,
            "skipped": True,
            "variants_before": None,
            "variants_after": None,
        }

    out_file = out_path / f"{vcf.name}.gz"
    disable_merge_csv = os.environ.get("DISABLE_MERGE_CSV", "").lower() in (
        "1",
        "true",
        "yes",
    )
    sidecar_csv = None if disable_merge_csv else find_sidecar_csv(vcf)

    # Count variants before filtering (directly from raw file)
    variants_before = count_variants(vcf)

    try:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".vcf") as temp_vcf:
            temp_vcf_path = Path(temp_vcf.name)

        missing_join_rows = 0
        if sidecar_csv is None:
            write_normalized_vcf(vcf, temp_vcf_path)
        else:
            _, missing_join_rows = augment_vcf_with_csv(vcf, temp_vcf_path, sidecar_csv)

        cmd = ["bcftools", "view"]
        if pre_merge_filter != "none":
            cmd.extend(["-i", pre_merge_filter])
        cmd.extend(["-Oz", "-o", str(out_file), str(temp_vcf_path)])
        run(cmd)
    finally:
        if "temp_vcf_path" in locals():
            temp_vcf_path.unlink(missing_ok=True)

    # Index compressed file
    run(["bcftools", "index", "-t", str(out_file)])

    variants_after = count_variants(out_file)

    return {
        "name": vcf.name,
        "skipped": False,
        "variants_before": variants_before,
        "variants_after": variants_after,
        "sidecar_csv": sidecar_csv.name if sidecar_csv else None,
        "missing_join_rows": missing_join_rows,
    }


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
    results = []
    total_files = len(vcfs)

    # Run in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_vcf, vcf, out_path, pre_merge_filter): vcf
            for vcf in vcfs
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            processed_count += 1
            stat = "skipped"
            if not result["skipped"]:
                stat = f"bef={result['variants_before']}, aft={result['variants_after']}"
                if result.get("sidecar_csv"):
                    stat += (
                        f", csv={result['sidecar_csv']}, missing_rows={result.get('missing_join_rows', 0)}"
                    )
            print(f"  [{processed_count}/{total_files}] {result['name']} ({stat})")

    # ── Summary statistics ──────────────────────────────────────────
    total_files = len(vcfs)
    processed = [r for r in results if not r["skipped"]]
    total_before = sum(
        r["variants_before"] for r in processed if r["variants_before"] is not None
    )
    total_after = sum(
        r["variants_after"] for r in processed if r["variants_after"] is not None
    )

    filter_used = pre_merge_filter if pre_merge_filter != "none" else "none"

    print(f"\n{'='*60}")
    print(f"  Summary")
    print(f"{'='*60}")
    print(f"  Total VCF files                : {total_files}")
    print(f"  Total variants before filtering: {total_before:,}")
    print(f"  Filter expression              : {filter_used}")
    print(f"  Total variants after filtering : {total_after:,}")
    if total_before > 0:
        removed = total_before - total_after
        pct = 100 * removed / total_before
        print(f"  Total removed                  : {removed:,} ({pct:.1f}%)")
    print(f"{'='*60}")
    # ─────────────────────────────────────────────────────────────────

    print(f"\nAll {len(processed)} files processed successfully.")


if __name__ == "__main__":
    main()
