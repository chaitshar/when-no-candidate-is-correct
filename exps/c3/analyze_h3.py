#!/usr/bin/env python3
"""C3 H3 (amendment A1, written before any arm data): cross-model verification of forced picks."""
import json, os, sys, glob, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
B = 10000
pools = {p["pid"]: p for p in json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json"))) if p["kind"] == "TA"}
st = json.load(open(os.path.join(HERE, "strata.json")))
R = {json.load(open(f))["id"]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, "raw/arms/*.json"))}
def v(m, cid):
    r = R.get(f"{m}__ISO__{cid}"); return None if r is None else parse.verdict(r["result"])
out = {}
for sel, ver_same, ver_cross in (("haiku", "haiku", "sonnet"), ("sonnet", "sonnet", "haiku")):
    d, acc_same, acc_cross, rows = [], [], [], 0
    for pid in st["selected"]:
        p = pools[pid]; rf = R.get(f"{sel}__FORCED__{p['pool']}")
        k = parse.choice(rf["result"], 3) if rf else None
        vs = [v(ver_same, c["cid"]) for c in p["cands"]]; vc = [v(ver_cross, c["cid"]) for c in p["cands"]]
        if not k or any(x is None for x in vs + vc): continue
        i = k - 1; o = [j for j in range(3) if j != i]
        hs = int(vs[i]) - sum(int(vs[j]) for j in o) / 2; hc = int(vc[i]) - sum(int(vc[j]) for j in o) / 2
        d.append(hs - hc); acc_same.append(int(vs[i])); acc_cross.append(int(vc[i]))
    if not d: out[f"select_{sel}"] = None; continue
    rng = random.Random(31); bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(B))
    out[f"select_{sel}"] = {"n": len(d), "mean_hsame_minus_hcross": sum(d) / len(d), "ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]],
                            "p_one_sided": sum(1 for x in bs if x <= 0) / B, f"accept_pick_by_{ver_same}": sum(acc_same) / len(d),
                            f"accept_pick_by_{ver_cross}": sum(acc_cross) / len(d)}
h = out.get("select_haiku")
out["H3_verdict"] = None if not h else ("confirmed" if h["p_one_sided"] < 0.05 else ("refuted" if h["ci95"][1] < 0.05 else "inconclusive"))
json.dump(out, open(os.path.join(HERE, "results_h3.json"), "w"), indent=1); print(json.dumps(out, indent=1))
