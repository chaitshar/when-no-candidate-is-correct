"""S9 frozen analysis. Control = haiku SOLVE on the same problem (S1 calibration amendment, raw/solve).
Primary: accuracy with wrong note minus no note, paired by problem, bootstrap CI. Also the rate of
adopting the wrong note's answer."""
import json, os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import parse, mathgrade
items = json.load(open(os.path.join(HERE, "items.json")))
def g(path, gold):
    if not os.path.exists(path): return None, None
    a = parse.answer(json.load(open(path))["result"]); return a, mathgrade.grade(a, gold)
out = {}
for arm in ("NOTEWRONG", "NOTERIGHT"):
    d = []; adopt = 0; n = 0; acc = []; ctl = []
    for it in items:
        _, c = g(os.path.join(HERE, f"../s1_lineup/raw/solve/haiku__SOLVE__{it['pid']}.json"), it["gold"])
        a, t = g(os.path.join(HERE, f"raw/haiku__{arm}__{it['pid']}.json"), it["gold"])
        if c is None or a is None: continue
        n += 1; acc.append(int(bool(t))); ctl.append(int(bool(c))); d.append(int(bool(t)) - int(bool(c)))
        if arm == "NOTEWRONG": adopt += int(mathgrade.grade(a, it["wrong_note"]) is True)
    if not d: continue
    rng = random.Random(9); bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(4000))
    out[arm] = {"n": n, "acc_note": sum(acc) / n, "acc_control": sum(ctl) / n, "diff": sum(d) / n, "ci": [bs[100], bs[3899]]}
    if arm == "NOTEWRONG": out[arm]["adopted_wrong_note"] = adopt / n
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
for k, x in out.items(): print(k, x)
