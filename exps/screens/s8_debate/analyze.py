"""S8 frozen analysis: TA NEITHER rate and wrong-pick rate; TP accuracy (picked the right side), NEITHER rate."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
pairs = json.load(open(os.path.join(HERE, "pairs.json")))
out = {"TA": {"n": 0, "neither": 0, "pick": 0, "unparsed": 0}, "TP": {"n": 0, "neither": 0, "right": 0, "wrong": 0, "unparsed": 0}}
for q in pairs:
    f = os.path.join(HERE, "raw", f"haiku__JUDGE__{q['pair']}.json")
    if not os.path.exists(f): continue
    m = re.findall(r"^\W*DECISION\W*:\W*(A|B|NEITHER)\b", json.load(open(f))["result"], re.M | re.I)
    k = out[q["kind"]]; k["n"] += 1
    if not m: k["unparsed"] += 1; continue
    d = m[-1].upper()
    if d == "NEITHER": k["neither"] += 1
    elif q["kind"] == "TA": k["pick"] += 1
    else: k["right" if q["role" + d] == "right" else "wrong"] += 1
for k in out.values():
    if k["n"]: k.update({x + "_rate": k[x] / k["n"] for x in list(k) if x != "n"})
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1); print(out)
