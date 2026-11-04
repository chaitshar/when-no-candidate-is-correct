import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import lineup_prompts as P
pools = json.load(open(os.path.join(HERE, "pools.json")))
pids = sorted({p["pid"] for p in pools if p["kind"] == "TP"})  # problems with both pools
import random
random.Random(11).shuffle(pids)
HAIKU = set(pids[:60]); SONNET = set(pids[:25])
pools = [p for p in pools if p["pid"] in HAIKU]
json.dump(pools, open(os.path.join(HERE, "pools.json"), "w"))
jobs = []
for m, sel in (("haiku", HAIKU), ("sonnet", SONNET)):
    seen = set()
    for q in pools:
        if q["pid"] not in sel: continue
        for c in q["cands"]:
            if c["cid"] not in seen:
                seen.add(c["cid"]); jobs.append({"id": f"{m}__ISO__{c['cid']}", "model": m, "prompt": P.iso(q["problem"], c)})
        jobs.append({"id": f"{m}__PICK__{q['pool']}", "model": m, "prompt": P.pick(q["problem"], q["cands"])})
        jobs.append({"id": f"{m}__FORCED__{q['pool']}", "model": m, "prompt": P.forced(q["problem"], q["cands"])})
        jobs.append({"id": f"{m}__EACH__{q['pool']}", "model": m, "prompt": P.each(q["problem"], q["cands"])})
for j in jobs: j["timeout"] = 900
# haiku first so a sonnet run can be held back by the gate in the prereg
jobs.sort(key=lambda j: j["model"] != "haiku")
open(os.path.join(HERE, "jobs_haiku.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs if j["model"] == "haiku"))
open(os.path.join(HERE, "jobs_sonnet.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs if j["model"] == "sonnet"))
from collections import Counter
print(Counter((j["model"], j["id"].split("__")[1]) for j in jobs), sum(len(j["prompt"]) for j in jobs) // 4, "approx input tokens")
