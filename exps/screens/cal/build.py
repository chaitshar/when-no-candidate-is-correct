import json, os, sys
import pyarrow.parquet as pq
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
import lineup_prompts as P
DATA = "/home/user/data/ma"
NOWORK = ("\n\nGive only the final answer, with no working or explanation. Reply with exactly one line: ANSWER: <final answer>")
probs = []
for comp in ("aime_2025", "hmmt_feb_2025"):
    t = pq.read_table(f"{DATA}/{comp}.parquet").to_pandas()
    for _, r in t.iterrows():
        probs.append({"pid": f"{comp}_{r.problem_idx}", "problem": r.problem, "gold": str(r.answer)})
json.dump(probs, open(os.path.join(HERE, "problems.json"), "w"))
jobs, oj = [], []
for m in ("haiku", "sonnet"):
    for p in probs:
        jobs.append({"id": f"{m}__SOLVE__{p['pid']}", "model": m, "timeout": 900, "prompt": P.solve(p["problem"])})
        jobs.append({"id": f"{m}__NOWORK__{p['pid']}", "model": m, "timeout": 300,
                     "prompt": f"Problem:\n{p['problem']}" + NOWORK})
for p in probs[:40]:
    oj.append({"id": f"gemma-4-e4b__SOLVE__{p['pid']}", "model": "gemma-4-e4b", "prompt": P.solve(p["problem"]),
               "max_tokens": 6000, "temperature": 0.7, "seed": 0, "timeout": 1800})
open(os.path.join(HERE, "jobs.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs))
open(os.path.join(HERE, "open_jobs.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in oj))
print(len(probs), len(jobs), len(oj), max(len(j["prompt"]) for j in oj))
