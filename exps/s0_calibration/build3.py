import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../gen"))
import countgen as G
END = "\n\nWork as carefully as you need to. End your reply with exactly one line: ANSWER: <integer>"
jobs, tasks = [], {}
for m, lv, k in (("haiku", ((2000, 2), (20000, 3), (200000, 3), (200000, 4)), 10), ("sonnet", ((20000, 3), (200000, 3), (200000, 4)), 6)):
    for hi, kk in lv:
        for s in range(k):
            t = G.make_task(102000 + s, hi, kk)
            tasks[t["tid"]] = t
            jobs.append({"id": f"{m}__SOLVE__{t['tid']}", "model": m, "timeout": 900, "prompt": G.question(t) + END})
json.dump(tasks, open(os.path.join(HERE, "tasks3.json"), "w"))
open(os.path.join(HERE, "jobs3.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs))
print(len(jobs))
