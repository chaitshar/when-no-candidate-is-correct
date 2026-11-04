"""S5 frozen analysis: agent and step accuracy vs human labels, Wilson CIs, per subset and model,
with two baselines: always the most frequent labelled agent (in-sample, optimistic) and a uniformly
random step. Unparseable replies count as wrong and are reported."""
import json, os, sys, glob, re
from math import sqrt
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
def wilson(k, n, z=1.96):
    if not n: return [None, None]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [(c - h) / d, (c + h) / d]
def last(pat, t):
    m = re.findall(pat, t or "", re.I | re.M); return m[-1].strip() if m else None
items = {it["iid"]: it for it in json.load(open(os.path.join(HERE, "items.json")))}
R = {json.load(open(f))["id"]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, "raw/*.json"))}
out = {}
for m in ("haiku", "sonnet"):
    for sub in ("algo", "hand", "all"):
        n = ka = ks = ks1 = unp = 0; cost = 0.0; ids = set()
        for iid, it in items.items():
            if sub != "all" and it["subset"] != sub: continue
            r = R.get(f"{m}__ATTR__{iid}")
            if r is None: continue
            n += 1; cost += r.get("cost") or 0; ids |= set(r.get("model_used") or [])
            a = last(r"^\W*AGENT\W*:\s*(.+)$", r["result"]); s = last(r"^\W*STEP\W*:\s*(\d+)", r["result"])
            if a is None or s is None: unp += 1
            ka += int(a is not None and a.strip("*` ").lower() == it["agent"].lower())
            ks += int(s is not None and int(s) == it["step"])
            ks1 += int(s is not None and abs(int(s) - it["step"]) <= 1)
        if not n: continue
        sel = [it for it in items.values() if sub == "all" or it["subset"] == sub]
        maj = Counter(it["agent"] for it in sel).most_common(1)[0][1] / len(sel)
        rnd = sum(1 / it["n_steps"] for it in sel) / len(sel)
        out[f"{m}_{sub}"] = {"n": n, "agent_acc": ka / n, "agent_ci": wilson(ka, n), "step_acc": ks / n,
                             "step_ci": wilson(ks, n), "step_acc_pm1": ks1 / n, "unparsed": unp,
                             "baseline_majority_agent": maj, "baseline_random_step": rnd, "cost": round(cost, 3),
                             "resolved": sorted(ids)}
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
for k, v in out.items(): print(k, v)
