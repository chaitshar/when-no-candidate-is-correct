#!/usr/bin/env python3
"""C3 stage 1: grade the two SOLVE replies per problem with grader A and grader B; list
disagreements (disagreements.csv) for hand checking; apply hand_checks.csv; assign strata;
sample at most 150 per stratum with random.Random(3). Writes strata.json and solve_summary.json."""
import csv, json, os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import parse, mathgrade
from grader_b import grade_b
pools = json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json")))
TA = {p["pid"]: p for p in pools if p["kind"] == "TA"}
hand = {}
hp = os.path.join(HERE, "hand_checks.csv")
if os.path.exists(hp):
    for r in csv.DictReader(open(hp)):
        hand[r["id"]] = r["decision"].strip().lower() == "correct"
grades, dis, missing = {}, [], 0
for pid, p in sorted(TA.items()):
    for k in (0, 1):
        jid = f"haiku__SOLVE__{pid}__{k}"
        f = os.path.join(HERE, "raw/solve", jid + ".json")
        if not os.path.exists(f):
            missing += 1; continue
        txt = json.load(open(f))["result"] or ""
        a = mathgrade.grade(parse.answer(txt), p["gold"]); b = grade_b(txt, p["gold"])
        a, b = bool(a), bool(b)
        if a != b:
            dis.append({"id": jid, "grader_a": a, "grader_b": b, "extracted_a": parse.answer(txt), "gold": p["gold"]})
            g = hand.get(jid)
        else:
            g = a
        grades[jid] = g
with open(os.path.join(HERE, "disagreements.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "grader_a", "grader_b", "extracted_a", "gold"]); w.writeheader(); w.writerows(dis)
stratum, unresolved = {}, 0
for pid in sorted(TA):
    g = [grades.get(f"haiku__SOLVE__{pid}__{k}") for k in (0, 1)]
    if any(x is None for x in g):
        unresolved += 1; stratum[pid] = "UNRESOLVED"; continue
    stratum[pid] = "SOLVED" if all(g) else ("UNSOLVED" if not any(g) else "MIXED")
sel = []
for s in ("SOLVED", "UNSOLVED"):
    ids = sorted(p for p, v in stratum.items() if v == s)
    if len(ids) > 150:
        random.Random(3).shuffle(ids); ids = sorted(ids[:150])
    sel += ids
from collections import Counter
summ = {"counts": dict(Counter(stratum.values())), "selected": len(sel), "disagreements": len(dis),
        "hand_checked": sum(1 for d in dis if d["id"] in hand), "missing_replies": missing, "unresolved": unresolved}
json.dump({"stratum": stratum, "selected": sel}, open(os.path.join(HERE, "strata.json"), "w"), indent=1)
json.dump(summ, open(os.path.join(HERE, "solve_summary.json"), "w"), indent=1); print(summ)
