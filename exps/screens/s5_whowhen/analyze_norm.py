"""S5 sensitivity (amendment A3, written after seeing that hand-crafted labels use base names):
agent names are compared after removing a trailing parenthetical, e.g. 'Orchestrator (thought)'
-> 'Orchestrator', and lowercasing. Strict scoring in analyze.py stays primary."""
import json, os, glob, re
from math import sqrt
HERE = os.path.dirname(os.path.abspath(__file__))
def base(s): return re.sub(r"\s*\(.*\)\s*$", "", s.strip("*` ")).strip().lower()
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [(c - h) / d, (c + h) / d]
items = {it["iid"]: it for it in json.load(open(os.path.join(HERE, "items.json")))}
out = {}
for m in ("haiku", "sonnet"):
    for sub in ("algo", "hand", "all"):
        n = k = 0
        for f in glob.glob(os.path.join(HERE, f"raw/{m}__ATTR__*.json")):
            r = json.load(open(f)); it = items[r["id"].split("__")[2]]
            if sub != "all" and it["subset"] != sub: continue
            a = re.findall(r"^\W*AGENT\W*:\s*(.+)$", r["result"], re.M | re.I)
            n += 1; k += int(bool(a) and base(a[-1]) == base(it["agent"]))
        out[f"{m}_{sub}"] = {"n": n, "agent_acc_norm": k / n, "ci": wilson(k, n)}
json.dump(out, open(os.path.join(HERE, "results_norm.json"), "w"), indent=1)
for k, v in out.items(): print(k, v)
