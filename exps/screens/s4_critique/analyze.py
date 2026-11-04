"""S4 frozen analysis. Control (no critique) = haiku ISO verdicts from S1 for the same candidates.
Benefit = rejection of wrong candidates with a (valid) critique minus control; harm = rejection
of right candidates with an (invalid) critique minus control; per source label; paired bootstrap."""
import json, os, sys, glob, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import parse
items = json.load(open(os.path.join(HERE, "items.json")))
def v(path):
    if not os.path.exists(path): return None
    return parse.verdict(json.load(open(path))["result"])
out = {}
for role in ("wrong", "right"):
    for lab in ("CHECKER", "STUDENT"):
        d = []; acc_c = []; acc_t = []
        for it in items:
            if it["role"] != role: continue
            c = v(os.path.join(HERE, f"../s1_lineup/raw/claude/haiku__ISO__{it['cid']}.json"))
            t = v(os.path.join(HERE, f"raw/haiku__CRIT{lab}__{it['cid']}.json"))
            if c is None or t is None: continue
            acc_c.append(int(c)); acc_t.append(int(t)); d.append(int(t) - int(c))
        if not d: continue
        rng = random.Random(4); B = 4000
        bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(B))
        out[f"{role}_{lab}"] = {"n": len(d), "accept_control": sum(acc_c) / len(d), "accept_critique": sum(acc_t) / len(d),
                                "diff_accept": sum(d) / len(d), "ci": [bs[100], bs[3899]]}
# label effect at fixed validity
for role in ("wrong", "right"):
    a = out.get(f"{role}_CHECKER"); b = out.get(f"{role}_STUDENT")
    if a and b: out[f"{role}_label_effect_checker_minus_student"] = a["accept_critique"] - b["accept_critique"]
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
for k, x in out.items(): print(k, x)
