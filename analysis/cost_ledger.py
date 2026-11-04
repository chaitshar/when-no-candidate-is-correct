#!/usr/bin/env python3
"""Rebuild results/cost_ledger.csv from every raw subject record (total_cost_usd per call),
plus the orchestrator and agent estimates kept in results/agent_cost_estimates.csv."""
import csv, glob, json, os
from collections import defaultdict
rows = defaultdict(lambda: [0, 0.0, set()])
for f in glob.glob("exps/**/*.json", recursive=True):
    if "/raw" not in f or "/open/" in f:
        continue
    try:
        r = json.load(open(f))
    except Exception:
        continue
    if "id" not in r or "__" not in r["id"]:
        continue
    exp = f.split("/raw")[0].replace("exps/", "")
    m, arm = r["id"].split("__")[:2]
    k = rows[(exp, m, arm)]
    k[0] += 1; k[1] += r.get("cost") or 0; k[2] |= set(r.get("model_used") or [])
with open("results/cost_ledger.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["exp", "model_alias", "resolved_model_id", "arm_or_purpose", "calls", "cost_usd"])
    for (e, m, a), (n, c, ids) in sorted(rows.items()):
        w.writerow([e, m, "|".join(sorted(ids)), a, n, round(c, 4)])
    sub = sum(v[1] for v in rows.values())
    agent = 0.0
    if os.path.exists("results/agent_cost_estimates.csv"):
        for r in csv.DictReader(open("results/agent_cost_estimates.csv")):
            agent += float(r["est_usd"])
    w.writerow(["TOTAL_SUBJECTS", "", "", "", sum(v[0] for v in rows.values()), round(sub, 2)])
    w.writerow(["TOTAL_AGENTS_EST", "", "", "see results/agent_cost_estimates.csv", "", round(agent, 2)])
print("subjects", round(sub, 2), "agents est", round(agent, 2))
