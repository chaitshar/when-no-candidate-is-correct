#!/usr/bin/env python3
"""POST HOC (2026-11-04, after round-5 review): A4 quantities on the audited strata with duplicates
removed (same variant 'both' as analyze_sensitivity.py). Same definitions as analyze_a4.py."""
import csv, json, os, sys, glob, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
pools = json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json")))
TA = {p["pid"]: p for p in pools if p["kind"] == "TA"}; TP = {p["pid"]: p for p in pools if p["kind"] == "TP"}
st = json.load(open(os.path.join(HERE, "strata.json")))
audit = {r["pid"]: r["audited_stratum"] for r in csv.DictReader(open(os.path.join(HERE, "audit_unsolved.csv")))}
dups = set(json.load(open(os.path.join(HERE, "duplicates_of_used.json"))))
badlab = {r["pid"] for r in csv.DictReader(open(os.path.join(HERE, "candidate_label_audit.csv")))}
S = {p: audit.get(p, st["stratum"][p]) for p in st["selected"] if p not in dups and p not in badlab}  # 'all' variant (labels excluded added after round 7)
R = {}
for f in glob.glob(os.path.join(HERE, "raw/arms/*.json")) + glob.glob(os.path.join(HERE, "raw/a4/*.json")):
    r = json.load(open(f)); R[r["id"]] = r
def iso(m, cid):
    r = R.get(f"{m}__ISO__{cid}"); return None if r is None else parse.verdict(r["result"])
out = {}
for m in ("haiku", "sonnet"):
    res = {}
    for s in ("SOLVED", "UNSOLVED"):
        rows = []
        for pid, ss in S.items():
            if ss != s or pid not in TP: continue
            ta, tp = TA[pid], TP[pid]
            vta = [iso(m, c["cid"]) for c in ta["cands"]]; vtp = [iso(m, c["cid"]) for c in tp["cands"]]
            a = R.get(f"{m}__PICK__{ta['pool']}"); b = R.get(f"{m}__PICK__{tp['pool']}")
            ka = parse.choice(a["result"], 3) if a else None; kb = parse.choice(b["result"], 3) if b else None
            if None in vta + vtp or ka is None or kb is None: continue
            jp = int(kb > 0 and tp["cands"][kb - 1]["role"] == "right") - int(ka > 0)
            ji = int(all(v == (c["role"] == "right") for v, c in zip(vtp, tp["cands"]))) - int(any(vta))
            hp = int(kb > 0 and tp["cands"][kb - 1]["role"] == "right") - int(all(v == (c["role"] == "right") for v, c in zip(vtp, tp["cands"])))
            rows.append((jp, ji, hp))
        if not rows: continue
        d = [a - b for a, b, _ in rows]; rng = random.Random(51)
        bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(10000))
        res[s] = {"n": len(rows), "J_PICK": sum(r[0] for r in rows) / len(rows), "J_ISO": sum(r[1] for r in rows) / len(rows),
                  "dJ": sum(d) / len(d), "dJ_ci95": [bs[250], bs[9749]], "dhit": sum(r[2] for r in rows) / len(rows)}
    out[m] = res
json.dump(out, open(os.path.join(HERE, "results_a4_sensitivity.json"), "w"), indent=1); print(json.dumps(out, indent=1))
