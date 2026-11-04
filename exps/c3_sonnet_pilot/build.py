import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import lineup_prompts as P
from run_jobs import SYS
SYS2 = SYS + " You have no tools and cannot run code. Reason in plain text and end with the requested final line."
pools = sorted([p for p in json.load(open(os.path.join(HERE, "../screens/s1_lineup/pools.json"))) if p["kind"] == "TA"], key=lambda p: p["pid"])[:15]
jobs = []
for p in pools:
    for c in p["cands"]:
        jobs.append({"id": f"sonnet__ISO__{c['cid']}", "prompt": P.iso(p["problem"], c)})
    jobs.append({"id": f"sonnet__PICK__{p['pool']}", "prompt": P.pick(p["problem"], p["cands"])})
    jobs.append({"id": f"sonnet__FORCED__{p['pool']}", "prompt": P.forced(p["problem"], p["cands"])})
for j in jobs: j.update(model="sonnet", system=SYS2, timeout=900)
open(os.path.join(HERE, "jobs.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs)); print(len(jobs))
