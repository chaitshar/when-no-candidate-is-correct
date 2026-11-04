#!/usr/bin/env python3
"""C3 frozen analysis (written before any arm data). Reads strata.json and raw/arms/*.json.
Writes results.json and results.txt."""
import json, os, sys, glob, random
from collections import defaultdict
import numpy as np
import statsmodels.api as sm
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import parse
B = 10000
pools = json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json")))
TA = {p["pid"]: p for p in pools if p["kind"] == "TA"}
TP = {p["pid"]: p for p in pools if p["kind"] == "TP"}
st = json.load(open(os.path.join(HERE, "strata.json")))
R = {}
for f in glob.glob(os.path.join(HERE, "raw/arms/*.json")):
    r = json.load(open(f)); R[r["id"]] = r
cost = defaultdict(float); calls = defaultdict(int); ids = set()
for k, r in R.items():
    if not k.startswith("haiku__"): continue  # amendment A2: tally only this model's records (descriptive fields)
    arm = k.split("__")[1]; cost[arm] += r.get("cost") or 0; calls[arm] += 1; ids |= set(r.get("model_used") or [])
def verdict(cid):
    r = R.get(f"haiku__ISO__{cid}"); return None if r is None else parse.verdict(r["result"])
n_iso = n_iso_ok = 0; wrong_v, right_v = [], []
rows = []
for pid in st["selected"]:
    p = TA[pid]
    v = [verdict(c["cid"]) for c in p["cands"]]
    for x in v:
        if R.get("x") is None: pass
    for c, x in zip(p["cands"], v):
        if f"haiku__ISO__{c['cid']}" in R:
            n_iso += 1; n_iso_ok += x is not None
            if x is not None: wrong_v.append(int(x))
    if pid in TP:
        rc = [c for c in TP[pid]["cands"] if c["role"] == "right"][0]
        if f"haiku__ISO__{rc['cid']}" in R:
            x = verdict(rc["cid"]); n_iso += 1; n_iso_ok += x is not None
            if x is not None: right_v.append(int(x))
    rp = R.get(f"haiku__PICK__{p['pool']}"); rf = R.get(f"haiku__FORCED__{p['pool']}")
    k = parse.choice(rp["result"], 3) if rp else None
    kf = parse.choice(rf["result"], 3) if rf else None
    row = {"pid": pid, "comp": p["comp"], "family": "arxiv" if p["comp"].startswith("arxivmath") else "contest",
           "unsolved": int(st["stratum"][pid] == "UNSOLVED"), "d": None, "h": None,
           "pick_missing": rp is None, "pick_unparsed": rp is not None and k is None,
           "forced_unparsed": rf is not None and not kf}
    if k is not None and all(x is not None for x in v):
        row["d"] = int(k > 0) - int(any(v)); row["pick"] = int(k > 0); row["iso"] = int(any(v))
    if kf and all(x is not None for x in v):
        o = [int(v[j]) for j in range(3) if j != kf - 1]; row["h"] = int(v[kf - 1]) - sum(o) / 2
    rows.append(row)
S = [r for r in rows if not r["unsolved"]]; U = [r for r in rows if r["unsolved"]]
gate = {"iso_parse": n_iso_ok / n_iso if n_iso else None, "iso_acc_wrong": float(np.mean(wrong_v)) if wrong_v else None,
        "iso_acc_right": float(np.mean(right_v)) if right_v else None, "n_solved": len(S), "n_unsolved": len(U)}
gate["passed"] = bool(gate["iso_parse"] is not None and gate["iso_parse"] >= 0.90 and gate["iso_acc_wrong"] is not None
                      and gate["iso_acc_right"] is not None and gate["iso_acc_right"] - gate["iso_acc_wrong"] >= 0.10
                      and gate["iso_acc_wrong"] > 0 and len(S) >= 40 and len(U) >= 40)
def boot(xs, seed):
    rng = random.Random(seed); return sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(B))
def one_mean(xs, seed):
    if not xs: return None
    bs = boot(xs, seed)
    return {"n": len(xs), "mean": sum(xs) / len(xs), "ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]],
            "p_one_sided": sum(1 for x in bs if x <= 0) / B}
out = {"gate": gate, "cost": {k: round(v, 3) for k, v in cost.items()}, "calls": dict(calls), "resolved": sorted(ids)}
D = [r for r in rows if r["d"] is not None]
# H1: OLS with competition fixed effects, HC3
y = np.array([r["d"] for r in D], float)
comps = sorted({r["comp"] for r in D})
X = np.column_stack([np.ones(len(D)), [r["unsolved"] for r in D]] + [[int(r["comp"] == c) for r in D] for c in comps[1:]])
fit = sm.OLS(y, X).fit(cov_type="HC3")
b, se = float(fit.params[1]), float(fit.bse[1])
from scipy import stats
out["H1"] = {"b": b, "se_hc3": se, "ci95": [b - 1.96 * se, b + 1.96 * se], "p_one_sided": float(1 - stats.norm.cdf(b / se)) if se > 0 else None,
             "n": len(D), "n_comps": len(comps)}
du = [r["d"] for r in D if r["unsolved"]]; ds = [r["d"] for r in D if not r["unsolved"]]
out["D_unsolved"] = one_mean(du, 11); out["D_solved"] = one_mean(ds, 12)
if du and ds:
    rng = random.Random(13); diffs = sorted(sum(rng.choice(du) for _ in du) / len(du) - sum(rng.choice(ds) for _ in ds) / len(ds) for _ in range(B))
    out["H1_unadjusted"] = {"diff": sum(du) / len(du) - sum(ds) / len(ds), "ci95": [diffs[int(.025 * B)], diffs[int(.975 * B) - 1]]}
for fam in ("contest", "arxiv"):
    Df = [r for r in D if r["family"] == fam]
    if len({r["unsolved"] for r in Df}) == 2 and len(Df) > 5:
        cf = sorted({r["comp"] for r in Df})
        Xf = np.column_stack([np.ones(len(Df)), [r["unsolved"] for r in Df]] + [[int(r["comp"] == c) for r in Df] for c in cf[1:]])
        ff = sm.OLS(np.array([r["d"] for r in Df], float), Xf).fit(cov_type="HC3")
        out[f"H1_family_{fam}"] = {"b": float(ff.params[1]), "se_hc3": float(ff.bse[1]), "n": len(Df),
                                    "n_unsolved": sum(r["unsolved"] for r in Df)}
    else:
        out[f"H1_family_{fam}"] = {"n": len(Df), "n_unsolved": sum(r["unsolved"] for r in Df), "note": "one stratum only"}
out["arms"] = {s: {"pick": float(np.mean([r["pick"] for r in D if r["unsolved"] == u])) if any(r["unsolved"] == u for r in D) else None,
                   "iso_any": float(np.mean([r["iso"] for r in D if r["unsolved"] == u])) if any(r["unsolved"] == u for r in D) else None}
               for s, u in (("SOLVED", 0), ("UNSOLVED", 1))}
out["H2s"] = one_mean([r["h"] for r in rows if r["h"] is not None and not r["unsolved"]], 21)
out["H2u"] = one_mean([r["h"] for r in rows if r["h"] is not None and r["unsolved"]], 22)
out["missing"] = {"pick_missing": sum(r["pick_missing"] for r in rows), "pick_unparsed": sum(r["pick_unparsed"] for r in rows),
                  "forced_unparsed": sum(r["forced_unparsed"] for r in rows), "d_missing": sum(r["d"] is None for r in rows)}
ps = [("H1", out["H1"]["p_one_sided"]), ("H1u", (out["D_unsolved"] or {}).get("p_one_sided")),
      ("H2s", (out["H2s"] or {}).get("p_one_sided")), ("H2u", (out["H2u"] or {}).get("p_one_sided"))]
ps = sorted([x for x in ps if x[1] is not None], key=lambda x: x[1]); holm, prev = {}, 0.0
for i, (k, p) in enumerate(ps):
    prev = max(prev, min(1.0, (len(ps) - i) * p)); holm[k] = prev
out["holm"] = holm
def verdict_of(name, ci_upper, est, thr):
    if not gate["passed"]: return "not interpretable (gate failed)"
    if holm.get(name, 1) < 0.05: return "confirmed"
    if ci_upper is not None and ci_upper < thr and (name != "H1" or est <= 0): return "refuted"
    return "inconclusive"
out["verdicts"] = {"H1": verdict_of("H1", out["H1"]["ci95"][1], b, 0.10)}
for k, key in (("H1u", "D_unsolved"), ("H2s", "H2s"), ("H2u", "H2u")):
    o = out[key]; out["verdicts"][k] = verdict_of(k, o["ci95"][1] if o else None, o["mean"] if o else None, 0.05) if o else "no data"
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
txt = "\n".join(f"{k}: {json.dumps(v)}" for k, v in out.items()); open(os.path.join(HERE, "results.txt"), "w").write(txt + "\n"); print(txt)
