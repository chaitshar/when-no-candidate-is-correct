#!/usr/bin/env python3
"""Round 2 Autonomous Science Loop Runner (Experiment C7: Compute-Matched Mitigation Matrix)."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")
RUNNER = ROOT / "autoloop" / "runner.py"
C7_DIR = ROOT / "exps" / "c7_mitigation"
LOCK = C7_DIR / "C7_LOCKED.sha256"


def verify_lock():
    res = subprocess.run(
        ["shasum", "-a", "256", "-c", "C7_LOCKED.sha256"],
        cwd=str(C7_DIR),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"C7_LOCKED.sha256 check failed:\n{res.stdout}\n{res.stderr}")
    print("[LOCK] C7 mitigation checksums verified OK.", flush=True)


def run_batch(label, jobs, out_dir, route, model, workers=5, timeout=240):
    t0 = time.time()
    cmd = [
        "caffeinate", "-i",
        sys.executable,
        str(RUNNER),
        "--jobs", str(jobs),
        "--out", str(out_dir),
        "--route", route,
        "--model", model,
        "--workers", str(workers),
        "--timeout", str(timeout),
    ]
    print(f"\n[START] {label} | route={route} model={model} workers={workers}", flush=True)
    res = subprocess.run(cmd)
    dt = time.time() - t0
    print(f"[DONE]  {label} | rc={res.returncode} elapsed={dt:.1f}s", flush=True)
    return res.returncode


def main():
    import os
    ap = argparse.ArgumentParser()
    ap.add_argument("--route-filter", choices=["agy", "claude_cli", "all"], default="all")
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    verify_lock()

    if args.route_filter in ("agy", "all"):
        for tag, model in [
            ("gptoss", "gpt-oss-120b-medium"),
            ("gemini", "gemini-3.8-flash-medium"),
        ]:
            run_batch(
                f"C7 M2 Science ({tag}, 60)",
                C7_DIR / "jobs_science_m2.jsonl",
                C7_DIR / f"raw_science_{tag}_m2",
                "agy",
                model,
                workers=args.workers,
            )
            run_batch(
                f"C7 M2 Math ({tag}, 80)",
                C7_DIR / "jobs_math_cross_m2.jsonl",
                C7_DIR / f"raw_math_{tag}_m2",
                "agy",
                model,
                workers=args.workers,
            )

    if args.route_filter in ("claude_cli", "all"):
        run_batch(
            "C7 M1 Haiku C3 Tie-Breaker (8)",
            C7_DIR / "jobs_math_haiku_c3_m1_tiebreak.jsonl",
            C7_DIR / "raw_math_haiku_m1_tiebreak",
            "claude_cli",
            "haiku",
            workers=args.workers,
        )
        run_batch(
            "C7 M2 Science Haiku (60)",
            C7_DIR / "jobs_science_m2.jsonl",
            C7_DIR / "raw_science_haiku_m2",
            "claude_cli",
            "haiku",
            workers=args.workers,
        )
        run_batch(
            "C7 M2 Math Haiku UNSOLVED (80)",
            C7_DIR / "jobs_math_haiku_m2.jsonl",
            C7_DIR / "raw_math_haiku_m2",
            "claude_cli",
            "haiku",
            workers=args.workers,
        )
        run_batch(
            "C7 M3 Known-Foil Lineup Haiku UNSOLVED (80)",
            C7_DIR / "jobs_math_haiku_m3_foil.jsonl",
            C7_DIR / "raw_math_haiku_m3_foil",
            "claude_cli",
            "haiku",
            workers=args.workers,
        )

    print("\n[ROUND 2 C7 COMPLETE]", flush=True)


if __name__ == "__main__":
    main()
