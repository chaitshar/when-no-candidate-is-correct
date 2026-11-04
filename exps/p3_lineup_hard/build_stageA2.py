#!/usr/bin/env python3
"""P3 stage A2 top-up (AMENDMENTS.md A2)."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import lineup_prompts as P
from analyze import int_answer, GOLD
probs = json.load(open(os.path.join(HERE, "problems.json")))
out = []
for p in probs:
    wrong, bad = set(), 0
    for f in glob.glob(os.path.join(HERE, f"raw/stageA/*__GEN__{p['pid']}__*.json")):
        a = int_answer(json.load(open(f))["result"])
        if a is None:
            bad += 1
        elif a != GOLD[p["pid"]]:
            wrong.add(a)
    if (wrong or bad) and len(wrong) < 3:
        for m, ks in (("haiku", range(4, 12)), ("sonnet", range(2, 6))):
            for k in ks:
                out.append({"id": f"{m}__GEN__{p['pid']}__{k}", "model": m, "timeout": 900, "prompt": P.solve(p["problem"])})
with open(os.path.join(HERE, "jobs_stageA2.jsonl"), "w") as f:
    for j in out:
        f.write(json.dumps(j) + "\n")
print(len(out), len(out) // 12)
