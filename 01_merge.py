#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path


def run(cmd, stdin=None, stdout=None):
    """Run a command and fail hard if it errors."""
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, stdin=stdin, stdout=stdout, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)
    return result


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <base_path>")
        sys.exit(1)

    base_path = Path(sys.argv[1])
    missing_to_ref = os.environ.get("MISSING_TO_REF", "true").lower() == "true"

    in_path = base_path / "00_raw_vcf"
    out_path = base_path / "01_merged" / "data.vcf"

    vcfs = sorted(in_path.glob("*.vcf"))
    if not vcfs:
        print(f"No VCFs found in {in_path}")
        sys.exit(1)

    flags = ["--missing-to-ref"] if missing_to_ref else []
    print(f"Merge flags: {' '.join(flags) if flags else '(none)'}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Merging VCF files...")

    p1 = subprocess.Popen(
        [
            "bcftools",
            "merge",
            "--force-single",
            "--force-no-index",
            *flags,
            *map(str, vcfs),
        ],
        stdout=subprocess.PIPE,
    )

    p2 = subprocess.Popen(
        ["bcftools", "norm", "-m", "-any", "-"], stdin=p1.stdout, stdout=subprocess.PIPE
    )

    p3 = subprocess.Popen(
        ["bcftools", "annotate", "--set-id", "%CHROM-%POS-%REF-%ALT"],
        stdin=p2.stdout,
        stdout=subprocess.PIPE,
    )

    p4 = subprocess.Popen(
        [
            "bcftools",
            "+fill-tags",
            "-o",
            str(out_path),
            "--",
            "-t",
            "AF,TYPE,AC,AC_Het,F_MISSING,MAF,HWE",
        ],
        stdin=p3.stdout,
    )

    for p in (p1, p2, p3, p4):
        if p.wait() != 0:
            sys.exit(1)

    print("Counting variants...")
    run(["bcftools", "+counts", str(out_path)])


if __name__ == "__main__":
    main()
