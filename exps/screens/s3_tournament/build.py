import json, os, sys, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import lineup_prompts as P
pools = json.load(open(os.path.join(HERE, "../s1_lineup/pools.json")))
pids = sorted({p["pid"] for p in pools})[:40]
pools = [p for p in pools if p["pid"] in pids]
json.dump(pools, open(os.path.join(HERE, "pools.json"), "w"))
jobs = [{"id": f"haiku__PAIR__{p['pool']}__{i}{j}", "model": "haiku", "timeout": 900,
         "prompt": P.pair(p["problem"], p["cands"][i], p["cands"][j])}
        for p in pools for i, j in itertools.permutations(range(3), 2)]
open(os.path.join(HERE, "jobs.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs)); print(len(jobs))
