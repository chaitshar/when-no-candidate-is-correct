import json, os, sys, glob, re
from collections import defaultdict
from math import sqrt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import parse
def wilson(k, n, z=1.96):
    if n == 0: return (None, None)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)
def intans(text):
    a = parse.answer(text)
    if a is None: return None
    a = re.sub(r"[^\d-]", "", a)
    try: return int(a)
    except ValueError: return None
tasks = json.load(open(os.path.join(HERE, "tasks.json")))
res = defaultdict(lambda: [0, 0, 0, 0.0])
for f in glob.glob(os.path.join(HERE, "raw/*.json")):
    r = json.load(open(f)); m, _, tid = r["id"].split("__"); t = tasks[tid]
    a = intans(r["result"]); key = (m, t["iterations"])
    res[key][1] += 1; res[key][3] += r.get("cost") or 0
    if a is None: res[key][2] += 1
    elif a == t["answer"]: res[key][0] += 1
out = {}
for (m, l), (k, n, pf, c) in sorted(res.items()):
    out[f"{m}_{l}"] = {"solve": k / n, "k": k, "n": n, "wilson": wilson(k, n), "parse_fail": pf, "cost": round(c, 4)}
    print(m, l, out[f"{m}_{l}"])
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
