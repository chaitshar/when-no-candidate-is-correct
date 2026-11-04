"""S5: Who&When failure attribution, all-at-once setting with the ground-truth answer given.
Data: HF Kevin355/Who_and_When at commit 59b9fcba1aaed7bbf206b5f4d3c68b8face2f49c, used verbatim.
Steps are numbered from 0 (index into history), which matches the labels."""
import json, os
import pyarrow.parquet as pq
HERE = os.path.dirname(os.path.abspath(__file__))
D = "/home/user/data/ww"
items = []
for sub, f in (("algo", "Algorithm-Generated.parquet"), ("hand", "Hand-Crafted.parquet")):
    t = pq.read_table(f"{D}/{f}").to_pandas()
    for i, r in t.iterrows():
        hist = list(r.history)
        gt = r.ground_truth if "ground_truth" in t.columns else r.groundtruth
        steps = "\n\n".join(f"Step {k} | {h.get('name') or h.get('role')}:\n{h.get('content')}" for k, h in enumerate(hist))
        agents = sorted({str(h.get('name') or h.get('role')) for h in hist})
        prompt = ("Below is the log of a multi-agent system that tried to solve a task and failed. "
                  "Identify the agent whose mistake was decisive for the failure, and the step at which "
                  "that decisive mistake was made.\n\n"
                  f"Task:\n{r.question}\n\nCorrect answer to the task: {gt}\n\n"
                  f"Agents in the log: {', '.join(agents)}\n\nLog (steps numbered from 0):\n\n{steps}\n\n"
                  "End your reply with exactly two lines:\nAGENT: <agent name as written in the log>\nSTEP: <step number>")
        items.append({"iid": f"{sub}_{i}", "subset": sub, "agent": str(r.mistake_agent), "step": int(r.mistake_step),
                      "n_steps": len(hist), "agents": agents, "prompt": prompt})
json.dump([{k: v for k, v in it.items() if k != "prompt"} for it in items], open(os.path.join(HERE, "items.json"), "w"))
jobs = [{"id": f"{m}__ATTR__{it['iid']}", "model": m, "timeout": 900, "prompt": it["prompt"]}
        for m in ("haiku", "sonnet") for it in items]
open(os.path.join(HERE, "jobs.jsonl"), "w").write("".join(json.dumps(j) + "\n" for j in jobs))
print(len(items), len(jobs), sum(len(j["prompt"]) for j in jobs) // 4, "approx tokens")
