#!/usr/bin/env python3
"""P3 stage A: sample solver candidates for hard olympiad problems with integer answers.
Source: KbsdJames/Omni-MATH (GitHub), Omni-Math.jsonl. Keep problems whose answer is an
integer and difficulty >= 4. Seed 20261104 shuffles; first 240 are the P3 pilot set; the
remaining eligible problem indices go to reserved_idx.txt for confirmation (independent agent)."""
import json, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import lineup_prompts as P
SRC = "/home/user/data/Omni-MATH/Omni-Math.jsonl"
R = [json.loads(l) for l in open(SRC)]
elig = [i for i, r in enumerate(R) if re.fullmatch(r"-?\d+", str(r["answer"]).strip().strip("$"))
        and float(r["difficulty"]) >= 4]
rng = random.Random(20261104)
rng.shuffle(elig)
pilot, reserved = elig[:240], elig[240:]
open(os.path.join(HERE, "reserved_idx.txt"), "w").write("\n".join(map(str, reserved)) + "\n")
probs = [{"idx": i, "pid": f"omni_{i}", "problem": R[i]["problem"], "gold": str(R[i]["answer"]).strip().strip("$"),
          "difficulty": R[i]["difficulty"], "source": R[i]["source"], "domain": R[i]["domain"]} for i in pilot]
json.dump(probs, open(os.path.join(HERE, "problems.json"), "w"))
with open(os.path.join(HERE, "jobs_stageA.jsonl"), "w") as f:
    for p in probs:
        for m, k in (("haiku", 4), ("sonnet", 2)):
            for s in range(k):
                f.write(json.dumps({"id": f"{m}__GEN__{p['pid']}__{s}", "model": m, "timeout": 900,
                                    "prompt": P.solve(p["problem"])}) + "\n")
print(len(elig), len(pilot), len(reserved))
