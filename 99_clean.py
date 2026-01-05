#!/usr/bin/env python3
import sys
import shutil
import os

# List of subdirectories to remove
dirs_to_remove = [
    "01_merged",
    "02_filtered",
    "03_distribution_analyze",
    "10_kinship",
    "20_pca",
    "21_mds",
    "30_cluster",
    "31_cluster_profile",
    "40_plot",
]


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <base_path>")
        sys.exit(1)

    base_path = sys.argv[1]

    # Remove directories if they exist
    for dir_name in dirs_to_remove:
        full_path = os.path.join(base_path, dir_name)
        if os.path.exists(full_path):
            print(f"Removing: {full_path}")
            shutil.rmtree(full_path)
        else:
            print(f"Skipping (not found): {full_path}")


if __name__ == "__main__":
    main()
