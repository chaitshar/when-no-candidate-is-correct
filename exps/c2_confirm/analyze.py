"""C2 frozen analysis (written before data). Reads raw/*.json, writes results.json and results.txt."""
import json, os, sys, glob, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import parse, mathgrade
B = 10000
pools = json.load(open(os.path.join(HERE, "pools.json")))
R = {}
for f in glob.glob(os.path.join(HERE, "raw/*.json")):
    r = json.load(open(f)); R[r["id"]] = r


def boot(d, seed):
    rng = random.Random(seed)
    bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(B))
    return bs


def analyze(m, sets):
    P = [p for p in pools if p["set"] in sets]
    out = {"sets": sets, "cost": 0.0, "calls": 0, "parse_fail": {}, "resolved": set()}
    for k, r in R.items():
        if k.startswith(m + "__") and any(r["id"].endswith(p["pool"]) or p["pid"] in r["id"] or any(c["cid"] in r["id"] for c in p["cands"]) for p in P[:0]):
            pass
    iso, pf = {}, {"ISO": 0, "PICK": 0, "FORCED": 0, "SOLVE": 0}
    def rec(key, arm):
        r = R.get(key)
        if r is not None:
            out["cost"] += r.get("cost") or 0; out["calls"] += 1; out["resolved"] |= set(r.get("model_used") or [])
        return r
    for p in P:
        for c in p["cands"]:
            if c["cid"] in iso: continue
            r = rec(f"{m}__ISO__{c['cid']}", "ISO")
            if r is None: continue
            v = parse.verdict(r["result"])
            if v is None: pf["ISO"] += 1
            iso[c["cid"]] = (v, c["role"])
    solved = {}
    for pid in sorted({p["pid"] for p in P}):
        r = rec(f"{m}__SOLVE__{pid}", "SOLVE")
        if r is None: continue
        gold = next(p["gold"] for p in P if p["pid"] == pid)
        g = mathgrade.grade(parse.answer(r["result"]), gold)
        if g is None: pf["SOLVE"] += 1
        solved[pid] = bool(g)
    w = [v for v, ro in iso.values() if ro == "wrong" and v is not None]
    rt = [v for v, ro in iso.values() if ro == "right" and v is not None]
    n_iso = len(iso)
    gate = {"solve_rate": sum(solved.values()) / len(solved) if solved else None,
            "iso_parse": 1 - pf["ISO"] / n_iso if n_iso else None,
            "iso_acc_wrong": sum(w) / len(w) if w else None, "iso_acc_right": sum(rt) / len(rt) if rt else None}
    gate["passed"] = bool(gate["solve_rate"] is not None and 0.2 <= gate["solve_rate"] <= 0.8 and gate["iso_parse"] >= 0.9
                          and gate["iso_acc_right"] - gate["iso_acc_wrong"] >= 0.10 and gate["iso_acc_wrong"] > 0)
    out["gate"] = gate
    h1, h2, tp = [], [], {"hit": 0, "false": 0, "none": 0, "n": 0}
    arms = {"ISO": [], "PICK": []}
    for p in P:
        r = rec(f"{m}__PICK__{p['pool']}", "PICK")
        k = parse.choice(r["result"], len(p["cands"])) if r else None
        if r is not None and k is None: pf["PICK"] += 1
        if p["kind"] == "TP" and k is not None:
            tp["n"] += 1
            if k == 0: tp["none"] += 1
            elif p["roles"][k - 1] == "right": tp["hit"] += 1
            else: tp["false"] += 1
        if p["kind"] != "TA": continue
        iv = [iso.get(c["cid"], (None,))[0] for c in p["cands"]]
        if k is not None and all(v is not None for v in iv):
            h1.append(int(k > 0) - int(any(iv)))
            arms["PICK"].append(int(k > 0)); arms["ISO"].append(int(any(iv)))
        rf = rec(f"{m}__FORCED__{p['pool']}", "FORCED")
        kf = parse.choice(rf["result"], len(p["cands"])) if rf else None
        if rf is not None and not kf: pf["FORCED"] += 1
        if kf and all(v is not None for v in iv):
            others = [int(iv[j]) for j in range(len(iv)) if j != kf - 1]
            h2.append(int(iv[kf - 1]) - sum(others) / len(others))
    if h1:
        bs = boot(h1, 1)
        out["H1"] = {"n": len(h1), "D": sum(h1) / len(h1), "ci90": [bs[int(.05 * B)], bs[int(.95 * B) - 1]],
                     "ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]],
                     "p_tost": max(sum(x >= 0.10 for x in bs) / B, sum(x <= -0.10 for x in bs) / B),
                     "p_one_sided_D_gt_0": sum(x <= 0 for x in bs) / B}
        out["H1"]["equivalent"] = -0.10 < out["H1"]["ci90"][0] and out["H1"]["ci90"][1] < 0.10
    if h2:
        bs = boot(h2, 2)
        out["H2"] = {"n": len(h2), "diff": sum(h2) / len(h2), "ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]],
                     "p_one_sided": sum(x <= 0 for x in bs) / B}
    out["arms_TA"] = {a: [sum(v) / len(v), len(v)] for a, v in arms.items() if v}
    out["TP_pick"] = {k: (v / tp["n"] if k != "n" and tp["n"] else v) for k, v in tp.items()}
    out["parse_fail"] = pf; out["resolved"] = sorted(out["resolved"]); out["cost"] = round(out["cost"], 3)
    return out


res = {"haiku_all": analyze("haiku", ("conf", "repl")), "haiku_conf": analyze("haiku", ("conf",)),
       "haiku_repl": analyze("haiku", ("repl",)), "sonnet_conf": analyze("sonnet", ("conf",))}
prim = [("haiku_H1", res["haiku_all"].get("H1", {}).get("p_tost")), ("haiku_H2", res["haiku_all"].get("H2", {}).get("p_one_sided")),
        ("sonnet_H1", res["sonnet_conf"].get("H1", {}).get("p_tost")), ("sonnet_H2", res["sonnet_conf"].get("H2", {}).get("p_one_sided"))]
prim = sorted([x for x in prim if x[1] is not None], key=lambda x: x[1])
holm, prev = {}, 0.0
for i, (k, p) in enumerate(prim):
    prev = max(prev, min(1.0, (len(prim) - i) * p)); holm[k] = prev
res["holm"] = holm
json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
txt = "\n".join(f"== {k}: {json.dumps(v, default=str)}" for k, v in res.items())
open(os.path.join(HERE, "results.txt"), "w").write(txt + "\n"); print(txt)
