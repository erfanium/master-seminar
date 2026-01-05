#!/usr/bin/env python3

import sys
import os
import subprocess

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <base_path>")
        sys.exit(1)

    base_path = sys.argv[1]

    in_path = os.path.join(base_path, "02_filtered", "data.vcf")
    out_path = os.path.join(base_path, "10_kinship", "out")

    # ensure output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    log_path = f"{out_path}.log"

    with open(log_path, "w") as log_file:
        subprocess.run(
            [
                "plink",
                "--vcf", in_path,
                "--distance", "ibs", "flat-missing", "square",
                "--out", out_path
            ],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            check=True
        )

if __name__ == "__main__":
    main()
