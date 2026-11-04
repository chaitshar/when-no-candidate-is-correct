#!/usr/bin/env python3
"""POST HOC sensitivity for C3 (written 2026-11-04 after round-4 review; not preregistered).
Variants: (a) audited strata: the PI's hand audit of all 90 UNSOLVED problems (audit_unsolved.csv) moves
14 to SOLVED (both replies equivalent to the official answer; both graders missed the form) and 6 to MIXED
(dropped); (b) the preregistered strata excluding 5 problems that duplicate problems used earlier
(duplicates_of_used.json); (c) both. Same definitions as analyze.py (d, h, OLS with competition FE, HC3)."""
import csv, json, os, sys, glob, random
import numpy as np, statsmodels.api as sm
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
TA = {p["pid"]: p for p in json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json"))) if p["kind"] == "TA"}
st = json.load(open(os.path.join(HERE, "strata.json")))
R = {json.load(open(f))["id"]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, "raw/arms/*.json"))}
audit = {r["pid"]: r["audited_stratum"] for r in csv.DictReader(open(os.path.join(HERE, "audit_unsolved.csv")))}
dups = set(json.load(open(os.path.join(HERE, "duplicates_of_used.json"))))
# added after round-7 review: problems whose pools contain official-label errors or garbled answers (candidate_label_audit.csv)
badlab = {r["pid"] for r in csv.DictReader(open(os.path.join(HERE, "candidate_label_audit.csv")))}
def strata(variant):
    s = {pid: st["stratum"][pid] for pid in st["selected"]}
    if variant in ("audited", "both"):
        s = {p: audit.get(p, v) for p, v in s.items()}
    if variant in ("nodup", "both", "all"):
        s = {p: v for p, v in s.items() if p not in dups}
    if variant in ("labels", "all"):
        s = {p: v for p, v in s.items() if p not in badlab}
    if variant == "all":
        s = {p: audit.get(p, v) for p, v in s.items()}
    return {p: v for p, v in s.items() if v in ("SOLVED", "UNSOLVED")}
def rows(m, S):
    out = []
    for pid, s in S.items():
        p = TA[pid]
        v = [parse.verdict(R[f"{m}__ISO__{c['cid']}"]["result"]) if f"{m}__ISO__{c['cid']}" in R else None for c in p["cands"]]
        rp, rf = R.get(f"{m}__PICK__{p['pool']}"), R.get(f"{m}__FORCED__{p['pool']}")
        k = parse.choice(rp["result"], 3) if rp else None; kf = parse.choice(rf["result"], 3) if rf else None
        if None in v: continue
        r = {"comp": p["comp"], "u": int(s == "UNSOLVED")}
        if k is not None: r["d"] = int(k > 0) - int(any(v))
        if kf: r["h"] = int(v[kf - 1]) - sum(int(v[j]) for j in range(3) if j != kf - 1) / 2
        out.append(r)
    return out
def mean_ci(xs, seed):
    rng = random.Random(seed); bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(10000))
    return {"n": len(xs), "mean": sum(xs) / len(xs), "ci95": [bs[250], bs[9749]]}
res = {}
for m in ("haiku", "sonnet"):
    for variant in ("prereg", "audited", "nodup", "both", "labels", "all"):
        S = strata(variant); X = rows(m, S); D = [r for r in X if "d" in r]
        # A competition with one row has leverage 1 and adds nothing to b, but makes HC3 0/0 and platform dependent.
        size = {c: sum(r["comp"] == c for r in D) for c in {r["comp"] for r in D}}
        F = [r for r in D if size[r["comp"]] > 1]
        comps = sorted({r["comp"] for r in F})
        A = np.column_stack([np.ones(len(F)), [r["u"] for r in F]] + [[int(r["comp"] == c) for r in F] for c in comps[1:]])
        fit = sm.OLS(np.array([r["d"] for r in F], float), A).fit(cov_type="HC3")
        b, se = float(fit.params[1]), float(fit.bse[1])
        res[f"{m}_{variant}"] = {"n_solved": sum(1 for r in D if not r["u"]), "n_unsolved": sum(r["u"] for r in D),
            "b": b, "b_ci95": [b - 1.96 * se, b + 1.96 * se], "b_p_one_sided": float(1 - stats.norm.cdf(b / se)),
            "d_unsolved": mean_ci([r["d"] for r in D if r["u"]], 1), "d_solved": mean_ci([r["d"] for r in D if not r["u"]], 2),
            "h_unsolved": mean_ci([r["h"] for r in X if "h" in r and r["u"]], 3), "h_solved": mean_ci([r["h"] for r in X if "h" in r and not r["u"]], 4)}
json.dump(res, open(os.path.join(HERE, "results_sensitivity.json"), "w"), indent=1)
for k, v in res.items():
    print(k, "nS", v["n_solved"], "nU", v["n_unsolved"], "b %+.3f [%+.3f,%+.3f] p %.3f" % (v["b"], *v["b_ci95"], v["b_p_one_sided"]),
          "dU %+.3f %s" % (v["d_unsolved"]["mean"], [round(x, 3) for x in v["d_unsolved"]["ci95"]]),
          "dS %+.3f" % v["d_solved"]["mean"], "hU %+.3f %s" % (v["h_unsolved"]["mean"], [round(x, 3) for x in v["h_unsolved"]["ci95"]]), "hS %+.3f" % v["h_solved"]["mean"])
