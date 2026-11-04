#!/usr/bin/env python3
"""Fetch the MathArena parquet files this project used and verify their sha256 against
data/matharena_pins.json (hashes of the files fetched on 2026-11-03).
Source: https://huggingface.co/api/datasets/MathArena/<name>/parquet/default/train/0.parquet
(the Hugging Face parquet conversion). Licence CC BY-NC-SA 4.0.
usage: fetch_matharena.py DEST_DIR [name ...]   (default: all pinned names)
Exits nonzero if any hash differs (the conversion can change if MathArena updates a dataset)."""
import hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
pins = json.load(open(os.path.join(HERE, "matharena_pins.json")))
dest = sys.argv[1]; names = sys.argv[2:] or sorted(pins)
os.makedirs(dest, exist_ok=True); bad = 0
for n in names:
    f = os.path.join(dest, f"{n}.parquet")
    if not os.path.exists(f):
        url = f"https://huggingface.co/api/datasets/MathArena/{n}/parquet/default/train/0.parquet"
        subprocess.run(["curl", "-sSL", "--fail", "-m", "600", "-o", f, url], check=False)
    h = hashlib.sha256(open(f, "rb").read()).hexdigest() if os.path.exists(f) else None
    ok = h == pins[n]["sha256_local"]
    bad += not ok
    print("ok " if ok else "MISMATCH ", n, h)
sys.exit(1 if bad else 0)
