"""S1 calibration on its own problems (amendment A2): one SOLVE call per problem per judge."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import lineup_prompts as P
pools = {p["pid"]: p for p in json.load(open(os.path.join(HERE, "pools.json")))}
jobs = []
for m, f in (("haiku", "jobs_haiku.jsonl"), ("sonnet", "jobs_sonnet.jsonl")):
    pids = sorted({json.loads(l)["id"].split("__")[2].rsplit("_", 1)[0] for l in open(os.path.join(HERE, f)) if "__PICK__" in l})
    for pid in pids:
        jobs.append({"id": f"{m}__SOLVE__{pid}", "model": m, "timeout": 900, "prompt": P.solve(pools[pid]["problem"])})
open(os.path.join(HERE, "jobs_solve.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs))
print(len(jobs))
