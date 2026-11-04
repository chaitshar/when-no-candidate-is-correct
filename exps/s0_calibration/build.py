import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../gen"))
import progtrace as G
END = "\n\nWork as carefully as you need to. End your reply with exactly one line: ANSWER: <integer>"
jobs, tasks = [], {}
for m, k in (("haiku", 16), ("sonnet", 10)):
    for lvl in (4, 8, 12, 18, 26):
        for s in range(k):
            t = G.make_task(100000 + lvl * 50 + s, lvl, 3, 3)
            tasks[t["tid"]] = t
            jobs.append({"id": f"{m}__SOLVE__{t['tid']}", "model": m, "timeout": 600, "prompt": G.question(t) + END})
json.dump(tasks, open(os.path.join(HERE, "tasks.json"), "w"))
open(os.path.join(HERE, "jobs.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs))
print(len(jobs))
