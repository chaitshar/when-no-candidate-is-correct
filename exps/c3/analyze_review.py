#!/usr/bin/env python3
"""Post hoc checks prompted by external reviews, written after all C3 results were known. No new subject calls.
Candidate position, candidate length, candidate family, the judge's own wrong answer, tokens per procedure,
and a permutation test for the primary coefficient. Exploratory: none of this was pre-registered."""
import csv, glob, json, os, random, statistics, sys
from collections import Counter
import numpy as np
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
P = json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json")))
TA = {p["pid"]: p for p in P if p["kind"] == "TA"}
st = json.load(open(os.path.join(HERE, "strata.json"))); SEL = st["selected"]
R = {}
for sub in ("arms", "a4"):
    for f in glob.glob(os.path.join(HERE, "raw", sub, "*.json")):
        r = json.load(open(f)); R[r["id"]] = r
def fam(gen):
    g = gen.lower()
    for k in ("claude", "deepseek", "qwen", "gemini", "grok", "glm", "gpt", "kimi", "minimax", "llama", "qed"):
        if k in g: return k
    return "other"
def boot(xs, seed=21):
    rng = random.Random(seed); b = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(10000))
    return {"n": len(xs), "mean": sum(xs) / len(xs), "ci95": [b[250], b[9749]]}
def verdicts(m, p):
    out = []
    for c in p["cands"]:
        r = R.get(f"{m}__ISO__{c['cid']}"); out.append(parse.verdict(r["result"]) if r else None)
    return out
def pick(m, arm, p):
    r = R.get(f"{m}__{arm}__{p['pool']}"); return parse.choice(r["result"], 3) if r else None
out = {}
for m in ("haiku", "sonnet"):
    o = {}
    for s in ("UNSOLVED", "SOLVED"):
        L = [TA[x] for x in SEL if st["stratum"][x] == s]; q = {}
        for arm in ("PICK", "FORCED"):
            k = [pick(m, arm, p) for p in L]; k = [x for x in k if x]
            c = [k.count(i) for i in (1, 2, 3)]
            q[f"{arm}_position"] = {"counts": c, "p_uniform": float(stats.chisquare(c).pvalue) if sum(c) else None}
            lg, sh, n = 0, 0, 0
            for p in L:
                x = pick(m, arm, p)
                if not x: continue
                ln = [len(c_["text"]) for c_ in p["cands"]]; n += 1
                lg += ln[x - 1] == max(ln); sh += ln[x - 1] == min(ln)
            q[f"{arm}_longest"] = lg / n if n else None; q[f"{arm}_shortest"] = sh / n if n else None; q[f"{arm}_n"] = n
            obs, exp, n2 = 0, 0.0, 0
            for p in L:
                x = pick(m, arm, p); f = [fam(g) == "claude" for g in p["gens"]]
                if x and 0 < sum(f) < 3: obs += f[x - 1]; exp += sum(f) / 3; n2 += 1
            q[f"{arm}_claude_picks"] = {"n_mixed_pools": n2, "observed": obs, "expected_if_blind": exp,
                                        "p": float(stats.binomtest(obs, n2, exp / n2).pvalue) if n2 else None}
        d = []; a, b = 0, 0
        for p in L:
            v = verdicts(m, p); k = pick(m, "PICK", p)
            if k is not None and None not in v:
                x, y = int(k > 0), int(any(v)); d.append(x - y); a += x > y; b += y > x
        q["d"] = boot(d); q["discordant_pick_only"] = a; q["discordant_iso_only"] = b
        q["sign_test_p"] = float(stats.binomtest(a, a + b, .5).pvalue) if a + b else None
        q["iso_wrong_accept"] = float(np.mean([int(x) for p in L for x in verdicts(m, p) if x is not None]))
        tk = {"ISO": [], "PICK": []}
        for p in L:
            i = [R.get(f"{m}__ISO__{c['cid']}") for c in p["cands"]]; r = R.get(f"{m}__PICK__{p['pool']}")
            if r and all(i):
                tk["ISO"].append(sum(x["usage"]["output_tokens"] for x in i)); tk["PICK"].append(r["usage"]["output_tokens"])
        q["median_output_tokens"] = {a_: statistics.median(b_) for a_, b_ in tk.items() if b_}
        o[s] = q
    gens = Counter(fam(g) for x in SEL for g in TA[x]["gens"])
    o["candidate_families"] = dict(gens); o["claude_candidate_share"] = gens["claude"] / sum(gens.values())
    out[m] = o
# The judge's own wrong answer among the candidates (haiku has SOLVE calls; sonnet does not).
# Matches were read by hand against both SOLVE replies (own_answer_checks.csv): the grader misses forms and can false-match.
own_rows = {r["pid"]: r["own_answer_candidate_positions"].split(";") for r in csv.DictReader(open(os.path.join(HERE, "own_answer_checks.csv")))}
own = {"with": [], "without": [], "pick_matches_own": 0, "pick_n": 0, "forced_matches_own": 0, "forced_n": 0, "pools_with_own": 0, "n": 0}
for x in SEL:
    if st["stratum"][x] != "UNSOLVED": continue
    p = TA[x]; pos = own_rows[x]
    match = [str(i + 1) in pos for i in range(3)]
    has = any(match); own["n"] += 1; own["pools_with_own"] += has
    v = verdicts("haiku", p); k = pick("haiku", "PICK", p)
    if k is not None and None not in v: own["with" if has else "without"].append(int(k > 0) - int(any(v)))
    if has and k: own["pick_n"] += 1; own["pick_matches_own"] += match[k - 1]
    f = pick("haiku", "FORCED", p)
    if has and f: own["forced_n"] += 1; own["forced_matches_own"] += match[f - 1]
g = {True: [], False: []}
for x in SEL:
    if st["stratum"][x] != "UNSOLVED": continue
    p = TA[x]; v = verdicts("sonnet", p); k = pick("sonnet", "PICK", p)
    if k is not None and None not in v: g[own_rows[x] != [""]].append(int(k > 0) - int(any(v)))
own["sonnet_d_with"] = boot(g[True]); own["sonnet_d_without"] = boot(g[False])
own["d_with"] = boot(own.pop("with")); own["d_without"] = boot(own.pop("without")); out["own_answer_haiku_unsolved"] = own
# Permutation test of the primary coefficient: shuffle UNSOLVED within competition, so no standard-error model is needed.
for m in ("haiku", "sonnet"):
    rows = []
    for x in SEL:
        if st["stratum"][x] not in ("SOLVED", "UNSOLVED"): continue
        p = TA[x]; v = verdicts(m, p); k = pick(m, "PICK", p)
        if k is not None and None not in v: rows.append((p["comp"], int(st["stratum"][x] == "UNSOLVED"), int(k > 0) - int(any(v))))
    comps = sorted({r[0] for r in rows}); idx = {c: [i for i, r in enumerate(rows) if r[0] == c] for c in comps}
    y = np.array([r[2] for r in rows], float); u = np.array([r[1] for r in rows], float)
    def stat(u_):
        n, d = 0.0, 0.0
        for c in comps:  # the within-competition OLS slope, which equals the fixed-effects coefficient
            i = idx[c]; a = u_[i] - u_[i].mean(); n += float((a * (y[i] - y[i].mean())).sum()); d += float((a * a).sum())
        return n / d
    obs = stat(u); rng = np.random.default_rng(31); ge = 0
    for _ in range(10000):
        z = u.copy()
        for c in comps: z[idx[c]] = rng.permutation(u[idx[c]])
        ge += stat(z) >= obs
    both = [c for c in comps if u[idx[c]].sum() >= 5 and (1 - u[idx[c]]).sum() >= 5]
    ov = []
    for c in both: ov += [(u[i], y[i]) for i in idx[c]]
    du = [b for a, b in ov if a]; ds = [b for a, b in ov if not a]
    out[f"permutation_{m}"] = {"b": obs, "p_one_sided": (ge + 1) / 10001, "n": len(rows),
                               "overlap_competitions": both, "overlap_unsolved": boot(du) if du else None, "overlap_solved": boot(ds, 22) if ds else None}
json.dump(out, open(os.path.join(HERE, "results_review.json"), "w"), indent=1)
print(json.dumps(out, indent=0))
