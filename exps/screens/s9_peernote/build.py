import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import lineup_prompts as P
pools = json.load(open(os.path.join(HERE, "../s1_lineup/pools.json")))
ta = {p["pid"]: p for p in pools if p["kind"] == "TA"}
jobs, items = [], []
for pid, p in sorted(ta.items()):
    wrong = sorted(p["cands"], key=lambda c: c["cid"])[0]["answer"]
    items.append({"pid": pid, "gold": p["gold"], "wrong_note": wrong})
    jobs.append({"id": f"haiku__NOTEWRONG__{pid}", "model": "haiku", "timeout": 900, "prompt": P.solve_with_note(p["problem"], wrong)})
    jobs.append({"id": f"haiku__NOTERIGHT__{pid}", "model": "haiku", "timeout": 900, "prompt": P.solve_with_note(p["problem"], p["gold"])})
json.dump(items, open(os.path.join(HERE, "items.json"), "w"))
open(os.path.join(HERE, "jobs.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs)); print(len(jobs))
