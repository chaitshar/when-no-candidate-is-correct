#!/usr/bin/env python3
"""Pilot P2 (branch B2): round-robin pairwise tournaments on the P1 pilot pools.
Every unordered pair is judged in both orders (A/B swapped), one fresh call each."""
import json, os, sys, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import lineup_prompts as P
pools = json.load(open(os.path.join(HERE, "../p1_lineup_math/pools.json")))
jobs = []
for m in ("haiku", "sonnet"):
    for p in pools:
        for i, j in itertools.permutations(range(len(p["cands"])), 2):
            jobs.append({"id": f"{m}__PAIR__{p['pool']}__{i}{j}", "model": m, "timeout": 600,
                         "prompt": P.pair(p["problem"], p["cands"][i], p["cands"][j])})
with open(os.path.join(HERE, "jobs.jsonl"), "w") as f:
    for j in jobs:
        f.write(json.dumps(j) + "\n")
print(len(jobs))
