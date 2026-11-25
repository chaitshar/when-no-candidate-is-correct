#!/usr/bin/env python3
"""Finalisation sensitivity checks added on 22 Nov 2026 (post hoc, not preregistered).

Writes results/final_sensitivity.json and paper/results_extra.tex (keys prefixed x_).
(a) C9: paper-clustered bootstrap (10 papers, 3 negative draws each) for delta c.
(b) H3: out-of-sample prediction of UNSOLVED PICK false choice from the SOLVED delta c.
(c) C7: isolated false acceptance on the 40 problem subset against the full 56 paired problems.
(d) C4: token ratio on TP pools.
Independent of analysis_a.py and analysis_b.py: own parser, stdlib only.
"""
import json, os, random, re
from math import comb
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
ND = NormalDist()
B = 5000


def load(d):
    out = {}
    for f in os.listdir(d):
        if f.endswith(".json"):
            j = json.load(open(os.path.join(d, f)))
            out[j.get("job_id") or j.get("id")] = j
    return out


def choice(t):
    m = re.findall(r"CHOICE:\s*\**\s*(NONE|[1-4])", t or "", re.I)
    if not m:
        return None
    return 0 if m[-1].upper() == "NONE" else int(m[-1])


def verdict(t):
    m = re.findall(r"VERDICT:\s*\**\s*(ACCEPT|REJECT)", t or "", re.I)
    return None if not m else m[-1].upper() == "ACCEPT"


def z(total, n):
    return ND.inv_cdf((total + 0.5) / (n + 1))


def crit(H, F):
    n = len(H)
    return -0.5 * (z(sum(H), n) + z(sum(F), n))


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(p * len(xs))))]


out = {}

# (a) C9 paper-clustered bootstrap
bank = json.load(open(ROOT / "banks/locked_v2/c9_science_pools.json"))["researchbench_pools"]
pools = {p["pool"]: p for p in bank}
items = sorted({p["item"] for p in bank})
paper_of = {p["item"]: p["row"] for p in bank}
c9 = {}
for judge in ["haiku", "gptoss", "gemini", "gemini_low", "hydrogen"]:
    pk = load(ROOT / f"exps/c6_crossvendor/raw_science_{judge}_pick")
    iso = load(ROOT / f"exps/c6_crossvendor/raw_science_{judge}_iso")
    rows = []
    for it in items:
        ta, tp = pools[it + "_TA"], pools[it + "_TP"]
        cta, ctp = choice(pk[f"PICK__{it}_TA"]["text"]), choice(pk[f"PICK__{it}_TP"]["text"])
        vta = [verdict(iso[f"ISO__{c['cid']}"]["text"]) for c in ta["cands"]]
        vtp = [verdict(iso[f"ISO__{c['cid']}"]["text"]) for c in tp["cands"]]
        if cta is None or ctp is None or None in vta or None in vtp:
            continue
        rpos = [i for i, c in enumerate(tp["cands"], 1) if c["role"] == "right"][0]
        k = sum(vtp)
        rows.append(dict(paper=paper_of[it], Fp=int(cta > 0), Hp=int(ctp == rpos),
                         Fi=int(any(vta)), Hi=(1.0 / k if vtp[rpos - 1] else 0.0)))
    dc = crit([r["Hp"] for r in rows], [r["Fp"] for r in rows]) - crit([r["Hi"] for r in rows], [r["Fi"] for r in rows])
    papers = sorted({r["paper"] for r in rows})
    byp = {p: [r for r in rows if r["paper"] == p] for p in papers}
    rng = random.Random(20261122)
    bs = []
    for _ in range(B):
        samp = [r for p in rng.choices(papers, k=len(papers)) for r in byp[p]]
        bs.append(crit([r["Hp"] for r in samp], [r["Fp"] for r in samp]) - crit([r["Hi"] for r in samp], [r["Fi"] for r in samp]))
    gold = {p: verdict(iso[f"ISO__r{p}_gold"]["text"]) for p in papers}
    c9[judge] = dict(n_items=len(rows), n_papers=len(papers), dc=dc, dc_ci=[q(bs, 0.025), q(bs, 0.975)],
                     iso_gold_accepted=sum(1 for v in gold.values() if v),
                     papers_fa_pick=len({r["paper"] for r in rows if r["Fp"]}),
                     papers_fa_iso=len({r["paper"] for r in rows if r["Fi"]}),
                     ta_pick=sum(r["Fp"] for r in rows), ta_iso=sum(r["Fi"] for r in rows),
                     tp_pick=sum(r["Hp"] for r in rows))
out["c9_paper_cluster"] = c9

# (b) H3 out-of-sample prediction, from the published macros
res = {}
for l in open(ROOT / "paper/results.tex"):
    m = re.match(r"\\expandafter\\def\\csname res@(.+?)\\endcsname\{(.*)\}\s*$", l)
    if m:
        res[m.group(1)] = m.group(2)
num = lambda k: float(res[k])
ci = lambda k: [float(x) for x in res[k].strip("[]").split(",")]
h3 = {}
for tag, pre in [("gptoss", "c6_gptoss"), ("gemini", "c6_gemini"), ("haiku_v1", "c3hc"), ("sonnet_v1", "c3sc")]:
    dp, c, dcs = num(f"{pre}_u_iso_dp"), num(f"{pre}_u_iso_c"), num(f"{pre}_s_pi_dc")
    pred = 1 - ND.cdf(dp / 2 + c + dcs)
    obs, lohi = num(f"{pre}_u_pick_f"), None
    if f"{pre}_u_pick_f_ci" in res and "NA" not in res[f"{pre}_u_pick_f_ci"]:
        lohi = ci(f"{pre}_u_pick_f_ci")
    h3[tag] = dict(pred=pred, obs=obs, obs_ci=lohi, n=int(res[f"{pre}_u_pi_n"]),
                   inside=(None if lohi is None else lohi[0] <= pred <= lohi[1]))
out["h3"] = h3

# (c) C7 subset baseline
b4 = json.load(open(ROOT / "banks/locked_v2/c4_haiku_compute.json"))["pools"]
by = {}
for p in b4:
    by.setdefault(p["pid"], {})[p["kind"]] = p
paired = [k for k, v in by.items() if "TA" in v and "TP" in v]
v1 = ROOT.parent / "when-no-candidate-is-correct-chaitshar/exps/c3/raw/arms"
fa = lambda pid: any(verdict(json.load(open(v1 / f"haiku__ISO__{c['cid']}.json")).get("result")) for c in by[pid]["TA"]["cands"])
s1 = json.load(open(ROOT / "exps/c7_mitigation/m1_stage1_math_haiku_c3.json"))
sel = {p["pool"][:-3] for p in s1["pools"]}
K, N, k = sum(fa(p) for p in paired), len(paired), sum(fa(p) for p in sel)
tail = sum(comb(K, i) * comb(N - K, 40 - i) for i in range(k + 1)) / comb(N, 40)
out["c7_subset"] = dict(full_k=K, full_n=N, sub_k=k, sub_n=len(sel), rest_k=K - k, rest_n=N - len(sel), hypergeom_tail=tail)

# (d) C4 token ratio on TP pools
ra = json.load(open(ROOT / "results/results_a.json"))
out["c4_tok_ratio_tp"] = ra["c4_compute"]["token_ratio"]["tp"]["median_ratio"]

json.dump(out, open(ROOT / "results/final_sensitivity.json", "w"), indent=1)
sg = lambda x: f"{x:+.3f}"
M = {}
names = {"haiku": "haiku", "gptoss": "gptoss", "gemini": "gemini", "gemini_low": "gemlow", "hydrogen": "hydro"}
for j, d in c9.items():
    a = names[j]
    M[f"x_c9_{a}_dc"] = sg(d["dc"])
    M[f"x_c9_{a}_dc_ci"] = f"[{sg(d['dc_ci'][0])}, {sg(d['dc_ci'][1])}]"
    M[f"x_c9_{a}_gold"] = str(d["iso_gold_accepted"])
    M[f"x_c9_{a}_pfa_pick"] = str(d["papers_fa_pick"])
    M[f"x_c9_{a}_pfa_iso"] = str(d["papers_fa_iso"])
for t, d in h3.items():
    M[f"x_h3_{t}_pred"] = f"{d['pred']:.3f}"
M.update({"x_c7_full_k": str(K), "x_c7_full_n": str(N), "x_c7_full_f": f"{K/N:.3f}", "x_c7_sub_k": str(k),
          "x_c7_rest_k": str(K - k), "x_c7_rest_n": str(N - len(sel)), "x_c7_tail": f"{tail:.4f}",
          "x_c4_tok_ratio_tp": f"{out['c4_tok_ratio_tp']:.3f}"})
with open(ROOT / "paper/results_extra.tex", "w") as f:
    f.write("% Auto-generated by scripts/final_sensitivity.py. Do not hand-edit.\n")
    for k_, v in sorted(M.items()):
        f.write(f"\\expandafter\\def\\csname res@{k_}\\endcsname{{{v}}}\n")
print(json.dumps(out, indent=1))
