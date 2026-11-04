#!/usr/bin/env python3
"""Build C1 pools and jobs from the locked banks. Prints counts only."""
import json, os, random, sys, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import lineup_prompts as P
MODELS = ["haiku", "sonnet", "opus"]
pools = []
for setname, path, cap in (("conf", "confirm_bank.jsonl", None), ("repl", "replication_bank.jsonl", 120)):
    bank = [json.loads(l) for l in open(os.path.join(HERE, "../../banks/locked", path))]
    bank = [b for b in bank if len(b["wrong"]) >= 3]
    if cap:
        bank = [b for b in bank if b["right"]] + [b for b in bank if not b["right"]]
        bank = bank[:cap]
    for b in bank:
        ta = [dict(c, role="wrong", cid=f"{setname}_{b['pid']}_w{i}") for i, c in enumerate(b["wrong"][:3])]
        kinds = [("TA", ta)]
        if b["right"]:
            kinds.append(("TP", ta[:2] + [dict(b["right"][0], role="right", cid=f"{setname}_{b['pid']}_r0")]))
        for kind, cands in kinds:
            cands = list(cands)
            random.Random(f"C1-{b['pid']}-{kind}").shuffle(cands)
            pools.append({"set": setname, "pool": f"{setname}_{b['pid']}_{kind}", "pid": f"{setname}_{b['pid']}",
                          "kind": kind, "problem": b["problem"], "gold": b["gold"], "level": b.get("level"),
                          "roles": [c["role"] for c in cands], "answers": [c["answer"] for c in cands], "cands": cands})
json.dump(pools, open(os.path.join(HERE, "pools.json"), "w"))
jobs = []
for m in MODELS:
    seen = set()
    for q in pools:
        for c in q["cands"]:
            if c["cid"] not in seen:
                seen.add(c["cid"])
                jobs.append({"id": f"{m}__ISO__{c['cid']}", "model": m, "prompt": P.iso(q["problem"], c)})
        jobs.append({"id": f"{m}__PICK__{q['pool']}", "model": m, "prompt": P.pick(q["problem"], q["cands"])})
        for i, j in itertools.permutations(range(len(q["cands"])), 2):
            jobs.append({"id": f"{m}__PAIR__{q['pool']}__{i}{j}", "model": m,
                         "prompt": P.pair(q["problem"], q["cands"][i], q["cands"][j])})
for j in jobs:
    j["timeout"] = 900
with open(os.path.join(HERE, "jobs.jsonl"), "w") as f:
    for j in jobs:
        f.write(json.dumps(j) + "\n")
from collections import Counter
print(Counter((q["set"], q["kind"]) for q in pools), "jobs", len(jobs))
