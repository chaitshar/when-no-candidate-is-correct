#!/usr/bin/env python3
"""P3 stage B: build TA/TP pools from stage A replies (rule in PREREGISTRATION.md) and judge jobs."""
import glob, json, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import lineup_prompts as P
from analyze import int_answer

probs = json.load(open(os.path.join(HERE, "problems.json")))
ORDER = ([("haiku", s) for s in range(4)] + [("sonnet", s) for s in range(2)] +
         [("haiku", s) for s in range(4, 12)] + [("sonnet", s) for s in range(2, 6)])
pools, stats = [], {"no_pool": 0, "TA": 0, "TP": 0}
for p in probs:
    wrong, right = {}, None
    for m, s in ORDER:
        f = os.path.join(HERE, f"raw/stageA/{m}__GEN__{p['pid']}__{s}.json")
        if not os.path.exists(f):
            continue
        txt = json.load(open(f))["result"] or ""
        a = int_answer(txt)
        if a is None:
            continue
        body = re.sub(r"(?im)^\W*ANSWER\W*:?.*$", "", txt).strip()
        c = {"text": body, "answer": str(a), "gen": f"{m}_{s}"}
        if a == int(p["gold"]):
            right = right or c
        elif str(a) not in wrong:
            wrong[str(a)] = c
    w = list(wrong.values())[:3]
    if len(w) < 3:
        stats["no_pool"] += 1
        continue
    ta = [dict(c, role="wrong", cid=f"{p['pid']}_w{i}") for i, c in enumerate(w)]
    kinds = [("TA", ta)]
    if right:
        kinds.append(("TP", ta[:2] + [dict(right, role="right", cid=f"{p['pid']}_r0")]))
    for kind, cands in kinds:
        cands = list(cands)
        random.Random(f"20261104-{p['pid']}-{kind}").shuffle(cands)
        stats[kind] += 1
        pools.append({"pool": f"{p['pid']}_{kind}", "pid": p["pid"], "kind": kind, "gold": p["gold"],
                      "difficulty": p["difficulty"], "problem": p["problem"], "roles": [c["role"] for c in cands],
                      "answers": [c["answer"] for c in cands], "gens": [c["gen"] for c in cands], "cands": cands})
json.dump(pools, open(os.path.join(HERE, "pools.json"), "w"))
pids = sorted({q["pid"] for q in pools})
jobs = []
def add(model, pid_set, arms):
    seen = set()
    for q in pools:
        if q["pid"] not in pid_set:
            continue
        for c in q["cands"]:
            if "ISO" in arms and c["cid"] not in seen:
                seen.add(c["cid"])
                jobs.append({"id": f"{model}__ISO__{c['cid']}", "prompt": P.iso(q["problem"], c), "model": model})
        if "PICK" in arms and not (model == "fable" and q["kind"] == "TP"):
            jobs.append({"id": f"{model}__PICK__{q['pool']}", "prompt": P.pick(q["problem"], q["cands"]), "model": model})
        if "FORCED" in arms:
            jobs.append({"id": f"{model}__FORCED__{q['pool']}", "prompt": P.forced(q["problem"], q["cands"]), "model": model})
        if "EACH" in arms:
            jobs.append({"id": f"{model}__EACH__{q['pool']}", "prompt": P.each(q["problem"], q["cands"]), "model": model})
        if "SEQ" in arms:
            jobs.append({"id": f"{model}__SEQ__{q['pool']}", "turns": P.seq_turns(q["problem"], q["cands"]), "model": model})
        if "SOLVE" in arms and q["kind"] == "TA":
            jobs.append({"id": f"{model}__SOLVE__{q['pid']}", "prompt": P.solve(q["problem"]), "model": model})
ALL = ["ISO", "PICK", "EACH", "SEQ", "FORCED"]
add("haiku", set(pids), ALL)
add("sonnet", set(pids), ALL)
add("opus", set(pids[:60]), ALL + ["SOLVE"])
add("fable", set(pids[:16]), ["ISO", "PICK"])
for j in jobs:
    j["timeout"] = 900
with open(os.path.join(HERE, "jobs_stageB.jsonl"), "w") as f:
    for j in jobs:
        f.write(json.dumps(j) + "\n")
OPEN = ["smollm2-135m", "qwen2.5-0.5b", "qwen3-0.6b", "qwen2.5-1.5b", "smollm2-1.7b",
        "granite-3.3-2b", "gemma-2-2b", "phi-3.5-mini"]
print(stats, "problems with pools", len(pids), "jobs", len(jobs))
