import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../gen"))
import progtrace2 as G
END = "\n\nWork as carefully as you need to. End your reply with exactly one line: ANSWER: <integer>"
jobs, tasks = [], {}
for m, lv, k in (("haiku", (10, 20, 40, 80), 10), ("sonnet", (20, 40, 80), 6)):
    for lvl in lv:
        for s in range(k):
            t = G.make_task(101000 + lvl * 50 + s, lvl, 4, 4)
            tasks[t["tid"]] = t
            jobs.append({"id": f"{m}__SOLVE__{t['tid']}", "model": m, "timeout": 900, "prompt": G.question(t) + END})
json.dump(tasks, open(os.path.join(HERE, "tasks2.json"), "w"))
open(os.path.join(HERE, "jobs2.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs))
print(len(jobs))
