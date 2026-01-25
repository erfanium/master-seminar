#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path


def run(cmd, log_file=None):
    if log_file:
        with open(log_file, "w") as f:
            subprocess.run(cmd, check=True, stdout=f, stderr=subprocess.STDOUT)
    else:
        subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <base_path>")
        sys.exit(1)

    base_path = Path(sys.argv[1])
    pca_count = int(os.environ.get("PCA_COUNT", 10))

    in_path = base_path / "02_filtered" / "data.vcf"
    out_path = base_path / "21_mds" / "out"

    # ensure output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "plink",
        "--vcf",
        str(in_path),
        "--cluster",
        "--mds-plot",
        str(pca_count),
        "--out",
        str(out_path),
    ]

    log_file = f"{out_path}.log"
    run(cmd, log_file=log_file)


if __name__ == "__main__":
    main()
