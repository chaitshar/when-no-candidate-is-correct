import json, os, sys, glob
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import parse, mathgrade
probs = {p["pid"]: p for p in json.load(open(os.path.join(HERE, "problems.json")))}
res = defaultdict(lambda: {"n": 0, "correct": 0, "noanswer": 0, "cost": 0.0, "ids": set()})
files = glob.glob(os.path.join(HERE, "raw/*.json")) + glob.glob(os.path.join(HERE, "raw/open/*/*.json"))
for f in files:
    r = json.load(open(f)); m, arm, pid = r["id"].split("__")
    g = mathgrade.grade(parse.answer(r["result"]), probs[pid]["gold"])
    k = res[(m, arm)]; k["n"] += 1; k["cost"] += r.get("cost") or 0
    k["ids"] |= set(r.get("model_used") or [r.get("model", "")])
    if g is None: k["noanswer"] += 1
    elif g: k["correct"] += 1
out = {f"{m}_{a}": {"solve": v["correct"] / v["n"], **{x: v[x] for x in ("n", "correct", "noanswer")},
                    "cost": round(v["cost"], 3), "resolved": sorted(v["ids"]),
                    "calibrated": (a == "SOLVE" and 0.2 <= v["correct"] / v["n"] <= 0.8)}
       for (m, a), v in sorted(res.items())}
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
for k, v in out.items(): print(k, v)
