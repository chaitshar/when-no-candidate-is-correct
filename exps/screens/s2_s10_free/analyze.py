#!/usr/bin/env python3
"""S2 and S10 (screens prereg v2): free reanalysis of MathArena's officially graded outputs
on the screen split, restricted to MathArena's 2026 model lineup. No subject calls.
Written before running. Scope: MathArena's runs of those models with their configs."""
import json, os, sys, itertools, random
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../banks"))
import matharena_pools as M
COMPS = ["smt_2025", "cmimc_2025", "brumo_2025", "apex_2025", "hmmt_nov_2025", "arxivmath-0626"]


def auroc(pos, neg):
    if not pos or not neg: return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def phi(a, b):
    n11 = sum(x and y for x, y in zip(a, b)); n10 = sum(x and not y for x, y in zip(a, b))
    n01 = sum(y and not x for x, y in zip(a, b)); n00 = len(a) - n11 - n10 - n01
    d = ((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00)) ** 0.5
    return (n11 * n00 - n10 * n01) / d if d else None


# Reads the committed extract data/s2s10_extract.csv.gz (built by data/make_s2s10_extract.py from the
# pinned parquet files, data/matharena_pins.json); changed 2026-11-04 for reproducibility, same rows.
import pandas as pd
T = pd.read_csv(os.path.join(HERE, "../../../data/s2s10_extract.csv.gz"), dtype={"problem_idx": str, "parsed_answer": str}, keep_default_na=False, na_filter=False)
T["correct"] = T.correct.astype(str) == "True"
T["pid"] = T.comp + "_" + T.problem_idx
out = {"S2": {}, "S10": {}}
# S2 per model
for m, g in T.groupby("model_name"):
    pos, neg, una, una_wrong = [], [], 0, 0
    for pid, h in g.groupby("pid"):
        if len(h) < 4: continue
        h = h.sort_values("idx_answer").head(4)
        cnt = h.parsed_answer.astype(str).value_counts()
        mode = cnt.index[0]; share = cnt.iloc[0] / 4
        mode_correct = bool(h[h.parsed_answer.astype(str) == mode].correct.iloc[0])
        (pos if mode_correct else neg).append(share)
        if share == 1.0:
            una += 1; una_wrong += (not mode_correct)
    out["S2"][m] = {"n_problems": len(pos) + len(neg), "modal_correct_rate": len(pos) / max(1, len(pos) + len(neg)),
                    "auroc": auroc(pos, neg), "unanimous": una, "unanimous_wrong": una_wrong,
                    "unanimous_wrong_rate": una_wrong / una if una else None}
# S10
acc = {}
err = defaultdict(dict)  # model -> pid -> list of 0/1 errors by sample
for (m, pid), h in T.groupby(["model_name", "pid"]):
    h = h.sort_values("idx_answer").head(4)
    if len(h) == 4:
        err[m][pid] = [int(not x) for x in h.correct]
models = [m for m in err if len(err[m]) >= 40]
for m in models:
    acc[m] = 1 - sum(sum(v) for v in err[m].values()) / (4 * len(err[m]))
homo = {}
for m in models:
    pids = sorted(err[m]); vals = []
    for i, j in itertools.combinations(range(4), 2):
        p = phi([err[m][q][i] for q in pids], [err[m][q][j] for q in pids])
        if p is not None: vals.append(p)
    homo[m] = sum(vals) / len(vals) if vals else None
hetero = []
for a, b in itertools.combinations(models, 2):
    if abs(acc[a] - acc[b]) > 0.10: continue
    pids = sorted(set(err[a]) & set(err[b]))
    p = phi([err[a][q][0] for q in pids], [err[b][q][0] for q in pids])
    if p is not None and homo[a] is not None and homo[b] is not None:
        hetero.append({"a": a, "b": b, "phi": p, "homo_mean": (homo[a] + homo[b]) / 2})
d = [h["phi"] - h["homo_mean"] for h in hetero]
rng = random.Random(10)
bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(4000)) if d else []
out["S10"] = {"models": {m: {"acc": acc[m], "homo_phi": homo[m]} for m in models},
              "n_matched_pairs": len(hetero), "mean_hetero_phi": sum(h["phi"] for h in hetero) / len(hetero) if hetero else None,
              "mean_homo_phi": sum(h["homo_mean"] for h in hetero) / len(hetero) if hetero else None,
              "diff_hetero_minus_homo": sum(d) / len(d) if d else None,
              "ci_pairs_bootstrap": [bs[100], bs[3899]] if bs else None,
              "note": "bootstrap over model pairs, which share models; CI is descriptive, not a valid test"}
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
for m, v in sorted(out["S2"].items()): print("S2", m, json.dumps(v))
print("S10", json.dumps({k: v for k, v in out["S10"].items() if k != "models"}))
