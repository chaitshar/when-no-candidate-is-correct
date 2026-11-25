#!/usr/bin/env python3
"""Round 1B: C8 Low-Thinking Sensitivity (gemini-3.8-flash-low) + 4th Judge (gemini-4-hydrogen-medium) on ResearchBench + C7 M2."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")
RUNNER = ROOT / "autoloop" / "runner.py"
C6_DIR = ROOT / "exps" / "c6_crossvendor"
C7_DIR = ROOT / "exps" / "c7_mitigation"


def run_batch(label, jobs, out_dir, model, workers=5, timeout=240):
    t0 = time.time()
    cmd = [
        "caffeinate", "-i",
        sys.executable,
        str(RUNNER),
        "--jobs", str(jobs),
        "--out", str(out_dir),
        "--route", "agy",
        "--model", model,
        "--workers", str(workers),
        "--timeout", str(timeout),
    ]
    print(f"\n[START] {label} | model={model} workers={workers}", flush=True)
    res = subprocess.run(cmd)
    print(f"[DONE]  {label} | rc={res.returncode} elapsed={time.time()-t0:.1f}s", flush=True)
    return res.returncode


def main():
    import os
    if not os.access("/Users/chaitanya/.gemini/antigravity-cli/installation_id", os.R_OK):
        sys.exit("Cannot read agy installation_id inside sandbox.")
    for tag, model in [
        ("gemini_low", "gemini-3.8-flash-low"),
        ("hydrogen", "gemini-4-hydrogen-medium"),
    ]:
        for arm, jname in [
            ("pick", "jobs_science_pick.jsonl"),
            ("iso", "jobs_science_iso.jsonl"),
            ("each", "jobs_science_each.jsonl"),
        ]:
            run_batch(
                f"C8/C9 Science {tag} {arm}",
                C6_DIR / jname,
                C6_DIR / f"raw_science_{tag}_{arm}",
                model,
                workers=5,
            )
        run_batch(
            f"C7 M2 Science {tag}",
            C7_DIR / "jobs_science_m2.jsonl",
            C7_DIR / f"raw_science_{tag}_m2",
            model,
            workers=5,
        )
    print("\n[ROUND 1B COMPLETE]", flush=True)


if __name__ == "__main__":
    main()
