#!/usr/bin/env python3
import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv(".env")

# --- Configuration & Environment ---
SKIP_PROFILE = os.environ.get("SKIP_CLUSTER_PROFILE", "").lower() == "true"
SKIP_MDS = os.environ.get("SKIP_MDS", "").lower() == "true"
PYTHON_EXE = sys.executable


class Logger:
    """Handles formatted console output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    @staticmethod
    def step(msg):
        print(f"{Logger.GREEN}Step: {msg}{Logger.RESET}")

    @staticmethod
    def skip(msg):
        print(f"{Logger.YELLOW}Skipping: {msg} (per configuration){Logger.RESET}")


def run_script(script_name, base_path):
    """Executes a python script with the provided base_path."""
    # The requirement: run command should not receive python as an arg manually
    subprocess.run([PYTHON_EXE, script_name, base_path], check=True)


# --- Main Logic ---


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <base_path>")
        sys.exit(1)

    base_path = sys.argv[1]

    # Pipeline Execution
    run_script("./99_clean.py", base_path)

    Logger.step("Merging VCF files")
    run_script("./01_merge.py", base_path)

    Logger.step("Applying filters")
    run_script("./02_apply_filter.py", base_path)

    Logger.step("Calculating kinship")
    run_script("./10_kinship.py", base_path)

    Logger.step("Performing PCA")
    run_script("./20_pca.py", base_path)

    Logger.step("Performing MDS")
    if SKIP_MDS:
        Logger.skip("MDS")
    else:
        run_script("./21_mds.py", base_path)

    Logger.step("Clustering results")
    run_script("./30_cluster.py", base_path)

    Logger.step("Profile each cluster")
    if SKIP_PROFILE:
        Logger.skip("Cluster profiling")
    else:
        run_script("./31_cluster_profile.py", base_path)


if __name__ == "__main__":
    main()
