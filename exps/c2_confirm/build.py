"""Build C2 jobs from the locked pools. Prints counts only."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import lineup_prompts as P
L = os.path.join(HERE, "../../banks/locked_ma")
pools = []
for st, f in (("conf", "confirm_pools.json"), ("repl", "replication_pools.json")):
    for p in json.load(open(os.path.join(L, f))):
        p["set"] = st; pools.append(p)
json.dump(pools, open(os.path.join(HERE, "pools.json"), "w"))
jobs = []
for m, sets in (("haiku", ("conf", "repl")), ("sonnet", ("conf",))):
    seen, solved = set(), set()
    for q in pools:
        if q["set"] not in sets: continue
        for c in q["cands"]:
            if c["cid"] not in seen:
                seen.add(c["cid"]); jobs.append({"id": f"{m}__ISO__{c['cid']}", "model": m, "prompt": P.iso(q["problem"], c)})
        jobs.append({"id": f"{m}__PICK__{q['pool']}", "model": m, "prompt": P.pick(q["problem"], q["cands"])})
        if q["kind"] == "TA":
            jobs.append({"id": f"{m}__FORCED__{q['pool']}", "model": m, "prompt": P.forced(q["problem"], q["cands"])})
        if q["pid"] not in solved:
            solved.add(q["pid"]); jobs.append({"id": f"{m}__SOLVE__{q['pid']}", "model": m, "prompt": P.solve(q["problem"])})
for j in jobs: j["timeout"] = 900
for m in ("haiku", "sonnet"):
    open(os.path.join(HERE, f"jobs_{m}.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs if j["model"] == m))
from collections import Counter
print(Counter((j["model"], j["id"].split("__")[1]) for j in jobs))
