import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import lineup_prompts as P
pools = json.load(open(os.path.join(HERE, "../s1_lineup/pools.json")))
items = []
for p in pools:
    if p["kind"] == "TA":
        c = sorted(p["cands"], key=lambda c: c["cid"])[0]; items.append((p, c))
    else:
        c = [c for c in p["cands"] if c["role"] == "right"][0]; items.append((p, c))
json.dump([{"cid": c["cid"], "role": c["role"], "pid": p["pid"]} for p, c in items], open(os.path.join(HERE, "items.json"), "w"))
jobs = []
for p, c in items:
    for lab, src in (("CHECKER", "an automated checker"), ("STUDENT", "another student")):
        jobs.append({"id": f"haiku__CRIT{lab}__{c['cid']}", "model": "haiku", "timeout": 900, "prompt": P.iso_critique(p["problem"], c, src)})
open(os.path.join(HERE, "jobs.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs)); print(len(jobs))
