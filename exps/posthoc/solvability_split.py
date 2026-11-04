#!/usr/bin/env python3
"""POST HOC (written 2026-11-04 after C2 results; exploratory, not preregistered for C2).
Hypothesis F5 from the tournament (preregistered in P1/P3, not in C2): the lineup penalty
appears where the judge cannot solve the problem. For claude-haiku-5-5, pool S1 (screen) and
C2 (held-out) TA problems; split by the judge's own SOLVE call (correct vs not); report
PICK minus ISO-any per stratum with problem bootstrap 95% CIs. Also the D2 sensitivity for the
C2 gate (timeouts counted as unsolved)."""
import json, os, sys, random
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(R, "harness"))
import parse, mathgrade
def rec(p):
    return json.load(open(p)) if os.path.exists(p) else None
rows = []
for name, pools_f, raw_iso, raw_solve in (
        ("S1", "exps/screens/s1_lineup/pools.json", "exps/screens/s1_lineup/raw/claude", "exps/screens/s1_lineup/raw/solve"),
        ("C2", "exps/c2_confirm/pools.json", "exps/c2_confirm/raw", "exps/c2_confirm/raw")):
    for p in json.load(open(os.path.join(R, pools_f))):
        if p["kind"] != "TA" or (name == "C2" and False):
            continue
        iv = [rec(os.path.join(R, raw_iso, f"haiku__ISO__{c['cid']}.json")) for c in p["cands"]]
        pk = rec(os.path.join(R, raw_iso, f"haiku__PICK__{p['pool']}.json"))
        sv = rec(os.path.join(R, raw_solve, f"haiku__SOLVE__{p['pid']}.json"))
        if pk is None or any(x is None for x in iv):
            continue
        v = [parse.verdict(x["result"]) for x in iv]; k = parse.choice(pk["result"], 3)
        if k is None or any(x is None for x in v):
            continue
        solved = None if sv is None else bool(mathgrade.grade(parse.answer(sv["result"]), p["gold"]))
        rows.append({"src": name, "set": p.get("set", "screen"), "solved": solved, "d": int(k > 0) - int(any(v)),
                     "pick": int(k > 0), "iso": int(any(v))})
out = {}
for lab, sel in (("solved", lambda r: r["solved"] is True), ("unsolved", lambda r: r["solved"] is False),
                 ("solve_missing", lambda r: r["solved"] is None), ("all", lambda r: True)):
    d = [r["d"] for r in rows if sel(r)]
    if not d: continue
    rng = random.Random(5); bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(10000))
    out[lab] = {"n": len(d), "D": sum(d) / len(d), "ci95": [bs[250], bs[9749]],
                "pick": sum(r["pick"] for r in rows if sel(r)) / len(d), "iso": sum(r["iso"] for r in rows if sel(r)) / len(d)}
s = [r for r in rows if r["src"] == "C2"]
out["c2_gate_sensitivity"] = {"solved": sum(1 for r in s if r["solved"]), "attempted_with_timeouts_as_unsolved": len(s)}
json.dump(out, open(os.path.join(R, "exps/posthoc/solvability_split.json"), "w"), indent=1)
for k, v in out.items(): print(k, v)
