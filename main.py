#!/usr/bin/env python3
"""
Pipeline orchestrator for VCF analysis.

Usage:
  python main.py <base_path>                  Run full pipeline
  python main.py <base_path> <step_or_verb>   Run a single step (number or verb)

Verbs: clean, index, merge, kinship, pca, mds, cluster, profile, plot-kinship
"""

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
# Each entry: (step_id, description, script_path, verb_name)

PIPELINE = [
    (99, "Cleaning workspace", "./99_clean.py", "clean"),
    (0, "Index VCF files", "./00_index.py", "index"),
    (2, "Merging VCF files", "./02_merge.py", "merge"),
    # (10, "Calculating kinship",  "./10_kinship.py",        "kinship"),
    (20, "Performing PCA", "./20_pca.py", "pca"),
    # (21, "Performing MDS",       "./21_mds.py",            "mds"),
    (30, "Clustering results", "./30_cluster.py", "cluster"),
    (31, "Profile each cluster", "./31_cluster_profile.py", "profile"),
    # (40, "Plot kinship",         "./40_plot_kinship.py",   "plot-kinship"),
]

# Build lookup maps
STEP_MAP = {step_id: (desc, script, verb) for step_id, desc, script, verb in PIPELINE}
VERB_MAP = {verb: (step_id, desc, script) for step_id, desc, script, verb in PIPELINE}


# --- CLI Commands ---


def usage():
    print("Usage:")
    print(f"  {sys.argv[0]} <base_path>                  Run full pipeline")
    print(
        f"  {sys.argv[0]} <base_path> <step_or_verb>   Run a single step (numeric or verb)"
    )
    print()
    print("Available verbs:", ", ".join(sorted(VERB_MAP.keys())))
    print("Available steps:", ", ".join(str(s) for s in sorted(STEP_MAP.keys())))
    sys.exit(1)


def run_step(step_id, base_path):
    """Execute a single pipeline step by its numeric ID."""
    desc, script, _verb = STEP_MAP[step_id]
    Logger.step(desc)

    if step_id == 21 and SKIP_MDS:
        Logger.skip("MDS")
        return
    if step_id == 31 and SKIP_PROFILE:
        Logger.skip("Cluster profiling")
        return

    run_script(script, base_path)


def cmd_full_pipeline(base_path):
    """Run the entire pipeline in order."""
    for step_id, _desc, _script, _verb in PIPELINE:
        run_step(step_id, base_path)


def cmd_verb(base_path, verb):
    """Run a single pipeline step by verb name."""
    if verb not in VERB_MAP:
        print(f"Unknown verb: {verb}")
        print("Available verbs:", ", ".join(sorted(VERB_MAP.keys())))
        sys.exit(1)
    step_id, _desc, _script = VERB_MAP[verb]
    run_step(step_id, base_path)


# --- Main Entry Point ---


def main():
    args = sys.argv[1:]

    if not args:
        usage()

    base_path = args[0]

    if len(args) == 1:
        # python main.py <base_path>
        cmd_full_pipeline(base_path)

    elif len(args) == 2:
        # python main.py <base_path> <step_or_verb>
        arg = args[1]
        # Try numeric step first
        try:
            step_id = int(arg)
            if step_id not in STEP_MAP:
                print(f"Invalid step {step_id}. Valid steps: {sorted(STEP_MAP.keys())}")
                sys.exit(1)
            run_step(step_id, base_path)
        except ValueError:
            # Not a number — treat as verb
            cmd_verb(base_path, arg)

    else:
        usage()


if __name__ == "__main__":
    main()
