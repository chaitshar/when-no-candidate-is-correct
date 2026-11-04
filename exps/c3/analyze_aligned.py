#!/usr/bin/env python3
"""Post hoc, prompted by external review. Gives PICK, EACH and ISO one output space: one candidate or abstain.
EACH and ISO verdicts become a selection by choosing uniformly among accepted candidates, scored in expectation,
so no random draw is needed. Chance for identification given a selection is 1/3, so hit = false-choice/3 for a random
chooser, not hit = false-choice. Reports pre-registered and fully corrected strata."""
import csv, json, os, random, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
P = json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json")))
TA = {p["pid"]: p for p in P if p["kind"] == "TA"}; TP = {p["pid"]: p for p in P if p["kind"] == "TP"}
st = json.load(open(os.path.join(HERE, "strata.json")))
R = {}
for sub in ("arms", "a4"):
    for f in glob.glob(os.path.join(HERE, "raw", sub, "*.json")):
        r = json.load(open(f)); R[r["id"]] = r
audit = {r["pid"]: r["audited_stratum"] for r in csv.DictReader(open(os.path.join(HERE, "audit_unsolved.csv")))}
dups = json.load(open(os.path.join(HERE, "duplicates_of_used.json")))
dups = set(dups if isinstance(dups, list) else dups.get("selected_duplicates", dups.get("pids", list(dups))))
bad = {r["pid"] for r in csv.DictReader(open(os.path.join(HERE, "candidate_label_audit.csv")))}
def strata(kind):
    out = {}
    for x in st["selected"]:
        s = st["stratum"][x]
        if kind == "corrected":
            if x in dups or x in bad: continue
            s = audit.get(x, s)
            if s not in ("SOLVED", "UNSOLVED"): continue
        out[x] = s
    return out
def outcome(m, arm, pool):
    """Returns per-candidate selection probabilities, or None if the reply is missing or unparsed."""
    n = len(pool["cands"])
    if arm == "PICK":
        r = R.get(f"{m}__PICK__{pool['pool']}"); k = parse.choice(r["result"], n) if r else None
        if k is None: return None
        return [float(i == k - 1) for i in range(n)]
    if arm == "EACH":
        r = R.get(f"{m}__EACH__{pool['pool']}"); v = parse.each(r["result"], n) if r else None
        if not v or None in v: return None
    else:
        v = []
        for c in pool["cands"]:
            r = R.get(f"{m}__ISO__{c['cid']}"); x = parse.verdict(r["result"]) if r else None
            if x is None: return None
            v.append(x)
    a = sum(map(int, v))
    return [(1 / a if x else 0.0) for x in v] if a else [0.0] * n
def boot(xs, seed):
    rng = random.Random(seed); b = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(10000))
    return {"n": len(xs), "mean": sum(xs) / len(xs), "ci95": [b[250], b[9749]]}
out = {}
for m in ("haiku", "sonnet"):
    for kind in ("prereg", "corrected"):
        S = strata(kind); res = {}
        for s in ("UNSOLVED", "SOLVED"):
            rows = []
            for x, sx in S.items():
                if sx != s or x not in TP: continue
                row = {}
                for arm in ("PICK", "EACH", "ISO"):
                    a, b = outcome(m, arm, TA[x]), outcome(m, arm, TP[x])
                    if a is None or b is None: continue
                    h = sum(q for q, c in zip(b, TP[x]["cands"]) if c["role"] == "right")
                    w = sum(q for q, c in zip(b, TP[x]["cands"]) if c["role"] != "right")
                    row[arm] = {"F": sum(a), "H": h, "W": w, "A": 1 - h - w}
                rows.append(row)
            d = {}
            for arm in ("PICK", "EACH", "ISO"):
                L = [r[arm] for r in rows if arm in r]; n = len(L)
                f, h, w = (sum(z[k] for z in L) / n for k in "FHW")
                d[arm] = {"n": n, "false_choice": f, "correct": h, "wrong_when_present": w, "abstain_when_present": 1 - h - w,
                          "abstain_when_absent": 1 - f, "correct_given_selection": h / (h + w) if h + w else None,
                          "random_chooser_hit": f / 3, "right_share_of_selections_equal_base": h / (h + w + f) if h + w + f else None}
            for a_, b_ in (("PICK", "ISO"), ("PICK", "EACH"), ("EACH", "ISO")):
                L = [r for r in rows if a_ in r and b_ in r]
                for key, name in (("F", "false"), ("H", "correct")):
                    d[f"{a_}_minus_{b_}_{name}"] = boot([r[a_][key] - r[b_][key] for r in L], 51)
            res[s] = d
        ta = []
        for x, sx in S.items():
            if sx != "UNSOLVED": continue
            a, b = outcome(m, "PICK", TA[x]), outcome(m, "ISO", TA[x])
            if a is not None and b is not None: ta.append((sum(a), sum(b)))
        res["ta_unsolved"] = {"n": len(ta), "pick": sum(t[0] for t in ta) / len(ta), "iso": sum(t[1] for t in ta) / len(ta)}
        out[f"{m}_{kind}"] = res
json.dump(out, open(os.path.join(HERE, "results_aligned.json"), "w"), indent=1)
for k, v in out.items():
    for s in ("UNSOLVED", "SOLVED"):
        for arm in ("PICK", "EACH", "ISO"):
            a = v[s][arm]; print(k, s, arm, a["n"], "F %.2f H %.2f W %.2f A %.2f H|sel %.2f F/3 %.2f right-share %.2f" % (a["false_choice"], a["correct"], a["wrong_when_present"], a["abstain_when_present"], a["correct_given_selection"] or 0, a["random_chooser_hit"], a["right_share_of_selections_equal_base"] or 0))
        for c in ("PICK_minus_ISO", "PICK_minus_EACH", "EACH_minus_ISO"):
            x, y = v[s][c + "_false"], v[s][c + "_correct"]; print("  ", c, "false %+.2f [%+.2f,%+.2f] correct %+.2f [%+.2f,%+.2f]" % (x["mean"], *x["ci95"], y["mean"], *y["ci95"]))
