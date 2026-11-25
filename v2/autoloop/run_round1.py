#!/usr/bin/env python3
"""Round 1 Autonomous Science Loop Runner (Pilot Gate -> C5 -> C6 Science -> C4 -> C6 Math)."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")
RUNNER = ROOT / "autoloop" / "runner.py"
LOCK = ROOT / "banks" / "locked_v2" / "LOCKED.sha256"
sys.path.insert(0, str(ROOT / "autoloop"))
import parsers  # noqa: E402


def verify_lock():
    res = subprocess.run(
        ["shasum", "-a", "256", "-c", "LOCKED.sha256"],
        cwd=str(LOCK.parent),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"LOCKED.sha256 check failed:\n{res.stdout}\n{res.stderr}")
    print("[LOCK] All v2 bank checksums verified OK.", flush=True)


def run_batch(label, jobs, out_dir, route, model, workers=6, max_calls=None, timeout=240):
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
    if max_calls is not None:
        cmd += ["--max-calls", str(max_calls)]
    print(f"\n[START] {label} | route={route} model={model} workers={workers} max_calls={max_calls}", flush=True)
    res = subprocess.run(cmd)
    dt = time.time() - t0
    print(f"[DONE]  {label} | rc={res.returncode} elapsed={dt:.1f}s", flush=True)
    return res.returncode


def check_parse_rate(out_dir, arm_type, min_rate=0.80):
    out_p = Path(out_dir)
    if not out_p.exists():
        return 0, 0, 0.0
    files = sorted(f for f in out_p.glob("*.json"))
    ok = 0
    parsed = 0
    for f in files:
        rec = json.loads(f.read_text())
        if rec.get("status") != "ok":
            continue
        ok += 1
        txt = rec.get("text", "")
        if arm_type == "choice2":
            val = parsers.choice(txt, 2)
        elif arm_type == "choice3":
            val = parsers.choice(txt, 3)
        elif arm_type == "choice4":
            val = parsers.choice(txt, 4)
        elif arm_type == "verdict":
            val = parsers.verdict(txt)
        elif arm_type == "each3":
            arr = parsers.each(txt, 3)
            val = arr if all(v is not None for v in arr) else None
        elif arm_type == "each4":
            arr = parsers.each(txt, 4)
            val = arr if all(v is not None for v in arr) else None
        elif arm_type == "answer":
            val = parsers.answer(txt)
        else:
            val = txt.strip() or None
        if val is not None:
            parsed += 1
    rate = (parsed / ok) if ok else 0.0
    print(f"[GATE]  {out_p.name}: ok={ok}/{len(files)} parsed={parsed}/{ok} ({rate:.1%})", flush=True)
    if ok == 0 or rate < min_rate:
        raise RuntimeError(f"Pilot/parse gate failed for {out_p}: ok={ok}, rate={rate:.3f} < {min_rate}")
    return ok, parsed, rate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["pilot", "c5", "science", "c4", "math_gptoss", "math_gemini", "all"], default="all")
    ap.add_argument("--workers-claude", type=int, default=6)
    ap.add_argument("--workers-agy", type=int, default=6)
    args = ap.parse_args()

    verify_lock()

    if args.stage in ("pilot", "all"):
        run_batch("PILOT C5 haiku (8)", ROOT / "exps/c5_removal/jobs_haiku_own_removal.jsonl",
                  ROOT / "exps/c5_removal/raw_own", "claude_cli", "haiku", workers=4, max_calls=8)
        check_parse_rate(ROOT / "exps/c5_removal/raw_own", "choice2", min_rate=0.85)

        run_batch("PILOT Science gpt-oss (8)", ROOT / "exps/c6_crossvendor/jobs_science_pick.jsonl",
                  ROOT / "exps/c6_crossvendor/raw_science_gptoss_pick", "agy", "gpt-oss-120b-medium", workers=4, max_calls=8)
        check_parse_rate(ROOT / "exps/c6_crossvendor/raw_science_gptoss_pick", "choice4", min_rate=0.85)

        run_batch("PILOT Science gemini (8)", ROOT / "exps/c6_crossvendor/jobs_science_pick.jsonl",
                  ROOT / "exps/c6_crossvendor/raw_science_gemini_pick", "agy", "gemini-3.8-flash-medium", workers=4, max_calls=8)
        check_parse_rate(ROOT / "exps/c6_crossvendor/raw_science_gemini_pick", "choice4", min_rate=0.85)
        print("[PILOT] All 3 model families passed live parse gate!", flush=True)

    if args.stage in ("c5", "all"):
        run_batch("C5 Own-Answer Removal (haiku, 38)", ROOT / "exps/c5_removal/jobs_haiku_own_removal.jsonl",
                  ROOT / "exps/c5_removal/raw_own", "claude_cli", "haiku", workers=args.workers_claude)
        check_parse_rate(ROOT / "exps/c5_removal/raw_own", "choice2", min_rate=0.85)

        run_batch("C5 Wells Removal (haiku, 43)", ROOT / "exps/c5_removal/jobs_haiku_wells.jsonl",
                  ROOT / "exps/c5_removal/raw_wells", "claude_cli", "haiku", workers=args.workers_claude)
        check_parse_rate(ROOT / "exps/c5_removal/raw_wells", "choice2", min_rate=0.85)

    if args.stage in ("science", "all"):
        for tag, route, model, w in [
            ("gptoss", "agy", "gpt-oss-120b-medium", args.workers_agy),
            ("gemini", "agy", "gemini-3.8-flash-medium", args.workers_agy),
            ("haiku", "claude_cli", "haiku", args.workers_claude),
        ]:
            for arm, jname, ptype in [
                ("pick", "jobs_science_pick.jsonl", "choice4"),
                ("iso", "jobs_science_iso.jsonl", "verdict"),
                ("each", "jobs_science_each.jsonl", "each4"),
            ]:
                out_d = ROOT / f"exps/c6_crossvendor/raw_science_{tag}_{arm}"
                run_batch(f"C9 Science {tag} {arm}", ROOT / "exps/c6_crossvendor" / jname,
                          out_d, route, model, workers=w)
                check_parse_rate(out_d, ptype, min_rate=0.80)

    if args.stage in ("c4", "all"):
        run_batch("C4 Repeat-PICK 3x (haiku, 372)", ROOT / "exps/c4_compute/jobs_haiku.jsonl",
                  ROOT / "exps/c4_compute/raw_haiku", "claude_cli", "haiku", workers=args.workers_claude)
        check_parse_rate(ROOT / "exps/c4_compute/raw_haiku", "choice3", min_rate=0.85)

    if args.stage in ("math_gptoss", "all"):
        for arm, jname, ptype in [
            ("solve", "jobs_math_solve.jsonl", "answer"),
            ("pick", "jobs_math_pick.jsonl", "choice3"),
            ("iso", "jobs_math_iso.jsonl", "verdict"),
            ("each", "jobs_math_each.jsonl", "each3"),
        ]:
            out_d = ROOT / f"exps/c6_crossvendor/raw_math_gptoss_{arm}"
            run_batch(f"C6 Math gpt-oss {arm}", ROOT / "exps/c6_crossvendor" / jname,
                      out_d, "agy", "gpt-oss-120b-medium", workers=args.workers_agy)
            check_parse_rate(out_d, ptype, min_rate=0.75)

    if args.stage in ("math_gemini", "all"):
        for arm, jname, ptype in [
            ("solve", "jobs_math_solve.jsonl", "answer"),
            ("pick", "jobs_math_pick.jsonl", "choice3"),
            ("iso", "jobs_math_iso.jsonl", "verdict"),
            ("each", "jobs_math_each.jsonl", "each3"),
        ]:
            out_d = ROOT / f"exps/c6_crossvendor/raw_math_gemini_{arm}"
            run_batch(f"C6 Math gemini {arm}", ROOT / "exps/c6_crossvendor" / jname,
                      out_d, "agy", "gemini-3.8-flash-medium", workers=args.workers_agy)
            check_parse_rate(out_d, ptype, min_rate=0.75)

    print("\n[ROUND 1 COMPLETE]", flush=True)


if __name__ == "__main__":
    main()
