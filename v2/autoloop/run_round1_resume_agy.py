#!/usr/bin/env python3
"""Resume remaining agy runs: C6 Math (gpt-oss + gemini-3.8-flash) and remaining 50 C7 M2 hydrogen calls."""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")
RUNNER = ROOT / "autoloop" / "runner.py"
C6_DIR = ROOT / "exps" / "c6_crossvendor"
C7_DIR = ROOT / "exps" / "c7_mitigation"


def run_batch(label, jobs, out_dir, model, workers=6, timeout=180):
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
    if not os.access("/Users/chaitanya/.gemini/antigravity-cli/installation_id", os.R_OK):
        sys.exit("Cannot read agy installation_id inside sandbox.")

    # 1. Finish remaining 50 C7 M2 hydrogen Science calls (fast, ~3 min)
    run_batch("C7 M2 Science hydrogen (resume 50)", C7_DIR / "jobs_science_m2.jsonl",
              C7_DIR / "raw_science_hydrogen_m2", "gemini-4-hydrogen-medium", workers=4)

    # 2. Resume C6 Math gpt-oss (100 balanced judge-family-free problems)
    for arm, jname in [
        ("pick", "jobs_math_pick.jsonl"),
        ("iso", "jobs_math_iso.jsonl"),
        ("each", "jobs_math_each.jsonl"),
    ]:
        run_batch(f"C6 Math gpt-oss {arm}", C6_DIR / jname,
                  C6_DIR / f"raw_math_gptoss_{arm}", "gpt-oss-120b-medium", workers=6)

    # 3. Run C6 Math gemini-3.8-flash (100 balanced judge-family-free problems)
    for arm, jname in [
        ("solve", "jobs_math_solve.jsonl"),
        ("pick", "jobs_math_pick.jsonl"),
        ("iso", "jobs_math_iso.jsonl"),
        ("each", "jobs_math_each.jsonl"),
    ]:
        run_batch(f"C6 Math gemini {arm}", C6_DIR / jname,
                  C6_DIR / f"raw_math_gemini_{arm}", "gemini-3.8-flash-medium", workers=12)

    print("\n[AGY RESUME COMPLETE]", flush=True)


if __name__ == "__main__":
    main()
