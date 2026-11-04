#!/usr/bin/env python3
"""POST HOC (2026-11-04, after round-1 review): the solvability split within each source, to
address the confound between solvability and dataset raised by reviewers. Exploratory."""
import json, os, random, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(R, "exps/posthoc"))
import importlib.util
spec = importlib.util.spec_from_file_location("sp", os.path.join(R, "exps/posthoc/solvability_split.py"))
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
out = {}
for src in ("screen", "conf", "repl"):
    for lab, s in (("solved", True), ("unsolved", False)):
        d = [r["d"] for r in sp.rows if r["set"] == src and r["solved"] is s]
        if len(d) < 2:
            out[f"{src}_{lab}"] = {"n": len(d)}; continue
        rng = random.Random(7); bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(10000))
        out[f"{src}_{lab}"] = {"n": len(d), "D": sum(d) / len(d), "ci95": [bs[250], bs[9749]]}
json.dump(out, open(os.path.join(R, "exps/posthoc/solvability_by_source.json"), "w"), indent=1)
for k, v in out.items(): print(k, v)
