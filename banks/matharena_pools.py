#!/usr/bin/env python3
"""Build candidate pools from MathArena (Dekoninck et al., matharena.ai) final-answer
competitions and their published, officially graded model outputs.

Source: Hugging Face datasets MathArena/<comp> and MathArena/<comp>_outputs, parquet
conversion, fetched 2026-11-03 into DATA_DIR (/home/user/data/ma). Licence CC BY-NC-SA 4.0
(research use, attribution). Items and answers are used verbatim; nothing is edited.

Candidate generators: models listed in MathArena's 2026 runs (the union of model_name in
hmmt_feb_2026_outputs and aime_2026_outputs), i.e. MathArena's own current lineup.
A candidate is one output row of such a model with a final assistant message of at least
300 characters (so the judge sees reasoning, not only a boxed answer). It is WRONG iff
MathArena's official grading marks it incorrect (column `correct`), RIGHT iff marked
correct. Wrong candidates are deduplicated by parsed answer string (first row in file order
after sorting by model_name, then idx_answer).

Option MA_ALL_MODELS=1 (added 2026-11-03 after the replication lock came out empty, before any
use of held-out data): generators are all models MathArena ran on that competition. Used for the
monthly arxivmath sets, which MathArena ran on a different, 2026-era model list.

Pools: TA = first 3 distinct wrong answers; TP = first 2 of those + first right candidate.

usage: matharena_pools.py COMP[,COMP...] OUT.json
"""
import json
import os
import sys

import pyarrow.parquet as pq

DATA = os.environ.get("MA_DATA", "/home/user/data/ma")


def current_models():
    s = set()
    for c in ("hmmt_feb_2026", "aime_2026"):
        s |= set(pq.read_table(f"{DATA}/{c}_outputs.parquet", columns=["model_name"]).to_pandas().model_name)
    return s


def final_text(raw):
    msgs = json.loads(raw)
    a = [m for m in msgs if m.get("role") == "assistant"]
    if not a:
        return ""
    c = a[-1].get("content")
    return c if isinstance(c, str) else ""


def build(comps):
    cur = current_models()
    pools = []
    for comp in comps:
        probs = pq.read_table(f"{DATA}/{comp}.parquet").to_pandas()
        out = pq.read_table(f"{DATA}/{comp}_outputs.parquet",
                            columns=["problem_idx", "model_name", "idx_answer", "all_messages",
                                     "parsed_answer", "correct", "gold_answer"]).to_pandas()
        if os.environ.get("MA_ALL_MODELS") != "1":
            out = out[out.model_name.isin(cur)]
        out = out.sort_values(["problem_idx", "model_name", "idx_answer"])
        for pidx, g in out.groupby("problem_idx"):
            prow = probs[probs.problem_idx.astype(str) == str(pidx)]
            if prow.empty:
                continue
            problem, gold = prow.iloc[0]["problem"], str(prow.iloc[0]["answer"])
            wrong, right = {}, None
            for _, r in g.iterrows():
                txt = final_text(r.all_messages)
                if len(txt) < 300:
                    continue
                c = {"text": txt, "answer": str(r.parsed_answer), "gen": f"{r.model_name}#{r.idx_answer}"}
                if bool(r.correct):
                    right = right or c
                elif c["answer"] not in wrong and c["answer"] not in ("None", "", "nan"):
                    wrong[c["answer"]] = c
            w = list(wrong.values())[:3]
            if len(w) < 3:
                continue
            pid = f"{comp}_{pidx}"
            ta = [dict(c, role="wrong", cid=f"{pid}_w{i}") for i, c in enumerate(w)]
            kinds = [("TA", ta)]
            if right:
                kinds.append(("TP", ta[:2] + [dict(right, role="right", cid=f"{pid}_r0")]))
            for kind, cands in kinds:
                import random
                cands = list(cands)
                random.Random(f"MA-{pid}-{kind}").shuffle(cands)
                pools.append({"pool": f"{pid}_{kind}", "pid": pid, "comp": comp, "kind": kind,
                              "problem": problem, "gold": gold, "roles": [c["role"] for c in cands],
                              "answers": [c["answer"] for c in cands], "gens": [c["gen"] for c in cands],
                              "cands": cands})
    return pools


if __name__ == "__main__":
    pools = build(sys.argv[1].split(","))
    json.dump(pools, open(sys.argv[2], "w"))
    from collections import Counter
    print(Counter((p["comp"], p["kind"]) for p in pools))
