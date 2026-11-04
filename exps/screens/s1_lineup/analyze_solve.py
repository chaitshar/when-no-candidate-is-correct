import json, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import parse, mathgrade
pools = {p["pid"]: p for p in json.load(open(os.path.join(HERE, "pools.json")))}
out = {}
for m in ("haiku", "sonnet"):
    fs = glob.glob(os.path.join(HERE, f"raw/solve/{m}__SOLVE__*.json"))
    g = [mathgrade.grade(parse.answer(json.load(open(f))["result"]), pools[json.load(open(f))["id"].split("__")[2]]["gold"]) for f in fs]
    if fs:
        out[m] = {"n": len(g), "solve": sum(1 for x in g if x) / len(g), "noanswer": sum(1 for x in g if x is None)}
json.dump(out, open(os.path.join(HERE, "results_solve.json"), "w"), indent=1); print(out)
