#!/usr/bin/env python3
"""Write data/s2s10_extract.csv.gz: the columns S2/S10 need (problem_idx, model_name, idx_answer,
parsed_answer, correct, comp) for the six screen competitions, restricted to MathArena's 2026
lineup, plus data/current_models.json. Lets claims_reproduce run without the 1 GB parquet files."""
import json, os, sys
import pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, "banks"))
import matharena_pools as M
import pyarrow.parquet as pq
cur = sorted(M.current_models())
json.dump(cur, open(os.path.join(R, "data/current_models.json"), "w"), indent=1)
rows = []
for c in ["smt_2025", "cmimc_2025", "brumo_2025", "apex_2025", "hmmt_nov_2025", "arxivmath-0626"]:
    t = pq.read_table(f"{M.DATA}/{c}_outputs.parquet", columns=["problem_idx", "model_name", "idx_answer", "parsed_answer", "correct"]).to_pandas()
    t = t[t.model_name.isin(cur)].copy(); t["comp"] = c
    t["parsed_answer"] = t.parsed_answer.astype(str); t["problem_idx"] = t.problem_idx.astype(str)
    rows.append(t)
pd.concat(rows).to_csv(os.path.join(R, "data/s2s10_extract.csv.gz"), index=False)
print("rows", sum(len(r) for r in rows))
