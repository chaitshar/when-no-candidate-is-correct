#!/usr/bin/env python3
"""Build pilot P1 jobs (B1 lineup on real math). Deterministic: seed 20261103.

Selection: problems in banks/prm_bank.jsonl with >= 3 wrong and >= 1 right candidate.
40 sampled for the pilot; the remaining ids are written to reserved_ids.txt and must
not be used for anything but confirmation (built by an independent agent).
TA pool: 3 wrong candidates. TP pool: the first 2 of those wrong + 1 right.
Candidate order within a pool is shuffled once per pool and shared by every arm.
"""
import json, random, sys, os, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../harness"))
import lineup_prompts as P

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20261103
CLAUDE = {"haiku": 40, "sonnet": 40, "opus": 40}   # problems per model
FABLE_TA = 16                                       # fable: TA pools, ISO + PICK only
OPEN = ["smollm2-135m", "qwen2.5-0.5b", "qwen3-0.6b", "qwen2.5-1.5b", "smollm2-1.7b",
        "granite-3.3-2b", "gemma-2-2b", "phi-3.5-mini"]

bank = [json.loads(l) for l in open(os.path.join(HERE, "../../banks/prm_bank.jsonl"))]
elig = [b for b in bank if len(b["wrong"]) >= 3 and b["right"]]
rng = random.Random(SEED)
rng.shuffle(elig)
pilot, reserved = elig[:40], elig[40:]
open(os.path.join(HERE, "reserved_ids.txt"), "w").write("\n".join(b["pid"] for b in reserved) + "\n")

pools = []
for b in pilot:
    w = b["wrong"][:3]
    r = b["right"][0]
    ta = [dict(c, role="wrong", cid=f"{b['pid']}_w{i}") for i, c in enumerate(w)]
    tp = ta[:2] + [dict(r, role="right", cid=f"{b['pid']}_r0")]
    rr = random.Random(f"{SEED}-{b['pid']}")
    rr.shuffle(ta); rr.shuffle(tp)
    for kind, cands in (("TA", ta), ("TP", tp)):
        pools.append({"pool": f"{b['pid']}_{kind}", "pid": b["pid"], "kind": kind, "level": b["level"],
                      "subject": b["subject"], "gold": b["gold"], "problem": b["problem"],
                      "order": [c["cid"] for c in cands], "roles": [c["role"] for c in cands],
                      "answers": [c["answer"] for c in cands], "cands": cands})
json.dump(pools, open(os.path.join(HERE, "pools.json"), "w"))

def jobs_for(model, pids, arms, prefix="", extra=None, for_open=False):
    out = []
    seen_iso = set()
    for p in pools:
        if p["pid"] not in pids:
            continue
        for c in p["cands"]:
            if "ISO" in arms and c["cid"] not in seen_iso:
                seen_iso.add(c["cid"])
                out.append({"id": f"{model}__ISO__{c['cid']}", "prompt": P.iso(p["problem"], c)})
        if "PICK" in arms:
            out.append({"id": f"{model}__PICK__{p['pool']}", "prompt": P.pick(p["problem"], p["cands"])})
        if "BASE" in arms:
            out.append({"id": f"{model}__BASE__{p['pool']}", "prompt": P.pick(p["problem"], p["cands"], True)})
        if "EACH" in arms:
            out.append({"id": f"{model}__EACH__{p['pool']}", "prompt": P.each(p["problem"], p["cands"])})
        if "SEQ" in arms and not for_open:
            out.append({"id": f"{model}__SEQ__{p['pool']}", "turns": P.seq_turns(p["problem"], p["cands"])})
        if "SOLVE" in arms and p["kind"] == "TA":
            out.append({"id": f"{model}__SOLVE__{p['pid']}", "prompt": P.solve(p["problem"])})
    for j in out:
        j["model"] = model
        if extra:
            j.update(extra)
    return out

ALL = ["ISO", "PICK", "BASE", "EACH", "SEQ", "SOLVE"]
jobs = []
for m, k in CLAUDE.items():
    jobs += jobs_for(m, {b["pid"] for b in pilot[:k]}, ALL, extra={"timeout": 600})
fable_pids = {b["pid"] for b in pilot[:FABLE_TA]}
jobs += [j for j in jobs_for("fable", fable_pids, ["ISO", "PICK"], extra={"timeout": 900})
         if "__PICK__" not in j["id"] or j["id"].endswith("_TA") ]
with open(os.path.join(HERE, "jobs.jsonl"), "w") as f:
    for j in jobs:
        f.write(json.dumps(j) + "\n")

oj = []
for m in OPEN:
    for j in jobs_for(m, {b["pid"] for b in pilot}, ["ISO", "PICK", "EACH", "SOLVE"], for_open=True):
        if m == "qwen3-0.6b":
            j["prompt"] += " /no_think"
        j.update({"seed": 0, "temperature": 0.7, "max_tokens": 1024, "timeout": 900})
        oj.append(j)
with open(os.path.join(HERE, "open_jobs.jsonl"), "w") as f:
    for j in oj:
        f.write(json.dumps(j) + "\n")
from collections import Counter
print("claude jobs", len(jobs), Counter((j["model"], j["id"].split("__")[1]) for j in jobs))
print("open jobs", len(oj))
print("reserved", len(reserved))
