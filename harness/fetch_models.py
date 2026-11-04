#!/usr/bin/env python3
"""Download the open-weight subject models listed in harness/models.json and verify them.

usage: fetch_models.py DEST_DIR [--only name1,name2] [--min-free-gb 6]
Resumable. Verifies sha256 against the pinned value, and stops before filling the disk.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    dest = sys.argv[1]
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    min_free = float(sys.argv[sys.argv.index("--min-free-gb") + 1]) if "--min-free-gb" in sys.argv else 6.0
    os.makedirs(dest, exist_ok=True)
    failed = 0
    for m in sorted(json.load(open(os.path.join(HERE, "models.json"))), key=lambda x: x["size"]):
        if only and m["name"] not in only:
            continue
        path = os.path.join(dest, m["file"])
        if os.path.exists(path) and os.path.getsize(path) == m["size"] and sha256(path) == m["sha256"]:
            print("have", m["name"], flush=True)
            continue
        need = m["size"] - (os.path.getsize(path) if os.path.exists(path) else 0)
        if (shutil.disk_usage(dest).free - need) / 1e9 < min_free:
            print("SKIP low disk", m["name"], flush=True)
            failed += 1
            continue
        url = f"https://huggingface.co/{m['repo']}/resolve/{m['revision']}/{m['file']}"
        rc = subprocess.run(["curl", "-sSL", "--fail", "-C", "-", "-o", path, url]).returncode
        if rc or sha256(path) != m["sha256"]:
            print("FAIL", m["name"], "curl rc", rc, flush=True)
            failed += 1
            continue
        print("ok", m["name"], m["size"], flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
