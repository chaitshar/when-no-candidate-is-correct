#!/usr/bin/env python3
"""C3 amendment A5 analysis (written before any A5 call): lineup ROC (H6) and base-rate manipulation (H7)."""
import csv, json, os, sys, glob, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
B = 10000
pools = json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json")))
TA = {p["pid"]: p for p in pools if p["kind"] == "TA"}; TP = {p["pid"]: p for p in pools if p["kind"] == "TP"}
st = json.load(open(os.path.join(HERE, "strata.json")))
R = {}
for f in glob.glob(os.path.join(HERE, "raw/arms/*.json")) + glob.glob(os.path.join(HERE, "raw/a4/*.json")) + glob.glob(os.path.join(HERE, "raw/a5/*.json")):
    r = json.load(open(f)); R[r["id"]] = r
def unit(pid):
    ta, tp = TA[pid], TP.get(pid)
    if tp is None: return None
    u = {}
    a, b = R.get(f"haiku__PICKC__{ta['pool']}"), R.get(f"haiku__PICKC__{tp['pool']}")
    if a and b:
        ka, kb = parse.choice(a["result"], 3), parse.choice(b["result"], 3)
        ca, cb = parse.confidence(a["result"]), parse.confidence(b["result"])
        if None not in (ka, kb, ca, cb):
            u["pick_fa"] = ca if ka > 0 else 0  # 0 = no identification
            u["pick_hit"] = cb if (kb > 0 and tp["cands"][kb - 1]["role"] == "right") else 0
    def isoproc(pool):
        sc = []
        for c in pool["cands"]:
            r = R.get(f"haiku__ISOC__{c['cid']}")
            if r is None: return None
            v, cf = parse.verdict(r["result"]), parse.confidence(r["result"])
            if v is None or cf is None: return None
            sc.append((cf if v else -cf, c["role"]))
        top = max(x for x, _ in sc)
        if top <= 0 or [x for x, _ in sc].count(top) > 1: return (0, None)
        return (top, [ro for x, ro in sc if x == top][0])
    x, y = isoproc(ta), isoproc(tp)
    if x is not None and y is not None:
        u["iso_fa"] = x[0]; u["iso_hit"] = y[0] if y[1] == "right" else 0
    a, b = R.get(f"haiku__BASE__{ta['pool']}"), R.get(f"haiku__BASE__{tp['pool']}")
    if a and b:
        ka, kb = parse.choice(a["result"], 3), parse.choice(b["result"], 3)
        if ka is not None and kb is not None:
            u["base_fa"] = int(ka > 0); u["base_hit"] = int(kb > 0 and tp["cands"][kb - 1]["role"] == "right")
    a, b = R.get(f"haiku__PICK__{ta['pool']}"), R.get(f"haiku__PICK__{tp['pool']}")
    if a and b:
        ka, kb = parse.choice(a["result"], 3), parse.choice(b["result"], 3)
        if ka is not None and kb is not None:
            u["p_fa"] = int(ka > 0); u["p_hit"] = int(kb > 0 and tp["cands"][kb - 1]["role"] == "right")
    return u
def roc(us, kh, kf):
    pts = [(0.0, 0.0)]
    for t in (5, 4, 3, 2, 1):
        pts.append((sum(u[kf] >= t for u in us) / len(us), sum(u[kh] >= t for u in us) / len(us)))
    return pts
def pauc(pts, xmax):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 >= xmax: break
        if x1 > xmax:
            y1 = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0) if x1 > x0 else y1; x1 = xmax
        a += (x1 - x0) * (y0 + y1) / 2
    return a
def h6(us):
    rp, ri = roc(us, "pick_hit", "pick_fa"), roc(us, "iso_hit", "iso_fa")
    xmax = min(rp[-1][0], ri[-1][0])
    return pauc(rp, xmax) - pauc(ri, xmax), rp, ri, xmax
def load(strata):
    return {s: [u for u in (unit(p) for p in st["selected"] if strata.get(p) == s) if u] for s in ("SOLVED", "UNSOLVED")}
def run(strata, tag):
    out = {}
    U = load(strata)
    for s, us in U.items():
        r6 = [u for u in us if all(k in u for k in ("pick_hit", "pick_fa", "iso_hit", "iso_fa"))]
        res = {"n_roc": len(r6)}
        if r6:
            d, rp, ri, xmax = h6(r6)
            rng = random.Random(61); bs = sorted(h6([rng.choice(r6) for _ in r6])[0] for _ in range(B))
            res.update({"pAUC_diff": d, "ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]], "p_one_sided_lt0": sum(1 for x in bs if x >= 0) / B,
                        "roc_pick": rp, "roc_iso": ri, "fa_max": xmax})
        r7 = [u for u in us if "base_fa" in u and "p_fa" in u]
        if r7:
            dd = [u["base_fa"] - u["p_fa"] for u in r7]; dh = [u["base_hit"] - u["p_hit"] for u in r7]
            rng = random.Random(71); bs = sorted(sum(rng.choice(dd) for _ in dd) / len(dd) for _ in range(B))
            rng = random.Random(72); bh = sorted(sum(rng.choice(dh) for _ in dh) / len(dh) for _ in range(B))
            res.update({"n_base": len(r7), "fa_base": sum(u["base_fa"] for u in r7) / len(r7), "fa_pick": sum(u["p_fa"] for u in r7) / len(r7),
                        "dfa": sum(dd) / len(dd), "dfa_ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]], "dfa_p_one_sided_lt0": sum(1 for x in bs if x >= 0) / B,
                        "hit_base": sum(u["base_hit"] for u in r7) / len(r7), "hit_pick": sum(u["p_hit"] for u in r7) / len(r7),
                        "dhit": sum(dh) / len(dh), "dhit_ci95": [bh[int(.025 * B)], bh[int(.975 * B) - 1]]})
        out[s] = res
    if tag == "prereg":
        u = out.get("UNSOLVED", {})
        ps = sorted([(k, u[pk]) for k, pk in (("H6", "p_one_sided_lt0"), ("H7", "dfa_p_one_sided_lt0")) if pk in u], key=lambda x: x[1])
        holm, prev = {}, 0.0
        for i, (k, p) in enumerate(ps):
            prev = max(prev, min(1.0, (len(ps) - i) * p)); holm[k] = prev
        out["holm"] = holm; out["verdicts"] = {k: ("confirmed" if v < 0.05 else "not confirmed") for k, v in holm.items()}
    return out
pre = {p: st["stratum"][p] for p in st["selected"]}
audit = {r["pid"]: r["audited_stratum"] for r in csv.DictReader(open(os.path.join(HERE, "audit_unsolved.csv")))}
dups = set(json.load(open(os.path.join(HERE, "duplicates_of_used.json"))))
aud = {p: audit.get(p, v) for p, v in pre.items() if p not in dups}
res = {"prereg": run(pre, "prereg"), "audited_sensitivity": run(aud, "aud")}
json.dump(res, open(os.path.join(HERE, "results_a5.json"), "w"), indent=1)
for k in ("prereg", "audited_sensitivity"):
    for s in ("SOLVED", "UNSOLVED"):
        x = res[k].get(s, {}); print(k, s, {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in x.items() if not kk.startswith("roc")})
print(res["prereg"].get("holm"), res["prereg"].get("verdicts"))
