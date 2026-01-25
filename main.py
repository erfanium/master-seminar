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
    subprocess.run([PYTHON_EXE, script_name, base_path], check=True)


# --- Pipeline Definition ---

PIPELINE = [
    (99, "Cleaning workspace", "./99_clean.py"),
    (1, "Merging VCF files", "./01_merge.py"),
    (2, "Applying filters", "./02_apply_filter.py"),
    (10, "Calculating kinship", "./10_kinship.py"),
    (20, "Performing PCA", "./20_pca.py"),
    (21, "Performing MDS", "./21_mds.py"),
    (30, "Clustering results", "./30_cluster.py"),
    (31, "Profile each cluster", "./31_cluster_profile.py"),
]


# --- Main Logic ---


def main():
    if len(sys.argv) not in (2, 3):
        print(f"Usage: {sys.argv[0]} <base_path> [step]")
        sys.exit(1)

    base_path = sys.argv[1]
    requested_step = int(sys.argv[2]) if len(sys.argv) == 3 else None

    valid_steps = {step for step, _, _ in PIPELINE}
    if requested_step is not None and requested_step not in valid_steps:
        print(f"Invalid step {requested_step}. Valid steps: {sorted(valid_steps)}")
        sys.exit(1)

    for step_id, description, script in PIPELINE:

        if requested_step is not None and step_id != requested_step:
            continue

        Logger.step(description)

        if step_id == 21 and SKIP_MDS:
            Logger.skip("MDS")
            continue

        if step_id == 31 and SKIP_PROFILE:
            Logger.skip("Cluster profiling")
            continue

        run_script(script, base_path)


if __name__ == "__main__":
    main()
