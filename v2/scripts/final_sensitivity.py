#!/usr/bin/env python3
"""Finalisation sensitivity checks added on 22 Nov 2026 (post hoc, not preregistered).

Writes results/final_sensitivity.json and paper/results_extra.tex (keys prefixed x_).
(a) C9: paper-clustered bootstrap (10 papers, 3 negative draws each) for delta c.
(b) H3: out-of-sample prediction of UNSOLVED PICK false choice from the SOLVED delta c.
(c) C7: isolated false acceptance on the 40 problem subset against the full 56 paired problems.
(d) C4: token ratio on TP pools.
Added 26 Nov 2026, also post hoc:
(e) C4 and C5 main contrasts with and without the pools whose "Final answer:" line did not match the boxed answer
    (pool list read from audit/extractor_audit_report.md).
(f) Holm adjustment for the planned C4 family of three tests.
(g) First-study confidence curves (amendment A5 of the first study: H6 and H7), copied from its results file.
Independent of analysis_a.py and analysis_b.py: own parser, stdlib only.
"""
import json, os, random, re
from math import comb
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
# The first-study archive: a sibling folder on the author's machine, the parent folder in the public archive.
_sib = ROOT.parent / "when-no-candidate-is-correct-chaitshar"
V1ROOT = _sib if _sib.is_dir() else ROOT.parent
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
v1 = V1ROOT / "exps/c3/raw/arms"
fa = lambda pid: any(verdict(json.load(open(v1 / f"haiku__ISO__{c['cid']}.json")).get("result")) for c in by[pid]["TA"]["cands"])
s1 = json.load(open(ROOT / "exps/c7_mitigation/m1_stage1_math_haiku_c3.json"))
sel = {p["pool"][:-3] for p in s1["pools"]}
K, N, k = sum(fa(p) for p in paired), len(paired), sum(fa(p) for p in sel)
tail = sum(comb(K, i) * comb(N - K, 40 - i) for i in range(k + 1)) / comb(N, 40)
out["c7_subset"] = dict(full_k=K, full_n=N, sub_k=k, sub_n=len(sel), rest_k=K - k, rest_n=N - len(sel), hypergeom_tail=tail)

# (d) C4 token ratio on TP pools
ra = json.load(open(ROOT / "results/results_a.json"))
out["c4_tok_ratio_tp"] = ra["c4_compute"]["token_ratio"]["tp"]["median_ratio"]

# (e) main contrasts with and without the pools that showed a mismatched "Final answer:" line
def affected(section):
    txt = (ROOT / "audit/extractor_audit_report.md").read_text()
    part = txt.split("## " + section, 1)[1].split("\n## ", 1)[0]
    return set(re.findall(r"^\| `([^`]+)` \|", part, re.M))


def iso_res(cid):
    return verdict(json.load(open(v1 / f"haiku__ISO__{cid}.json")).get("result"))


def contrast(rows, seed):
    """rows: list of (pick_wrong, iso_wrong) 0/1 pairs. Returns rates, difference, bootstrap range and one-sided p."""
    n = len(rows)
    fp, fi = sum(r[0] for r in rows) / n, sum(r[1] for r in rows) / n
    rng = random.Random(seed)
    bs = []
    for _ in range(B):
        smp = rng.choices(rows, k=n)
        bs.append(sum(r[0] - r[1] for r in smp) / n)
    return dict(n=n, pick=fp, iso=fi, diff=fp - fi, ci=[q(bs, 0.025), q(bs, 0.975)], p=sum(b <= 0 for b in bs) / B)


def maj3(cs):
    for v in set(cs):
        if cs.count(v) >= 2:
            return v
    return 0


fal = {}
bad4, bad5 = affected("c4_haiku_compute"), affected("c5_haiku_removal")
c4raw = load(ROOT / "exps/c4_compute/raw_haiku")
rows4 = []
for p in b4:
    if p["kind"] != "TA":
        continue
    cs = [choice(c4raw[f"haiku__PICK__{p['pool']}__rep{r}"]["text"]) for r in range(3)]
    vs = [iso_res(c["cid"]) for c in p["cands"]]
    if None in cs or None in vs:
        continue
    rows4.append((p["pool"], int(maj3(cs) > 0), int(any(vs))))
fal["c4"] = dict(n_affected=len([r for r in rows4 if r[0] in bad4]),
                 all=contrast([r[1:] for r in rows4], 1), clean=contrast([r[1:] for r in rows4 if r[0] not in bad4], 2))
b5 = json.load(open(ROOT / "banks/locked_v2/c5_haiku_removal.json"))
for tag, key, rawdir, pre in [("c5_own", "own_answer_removal", "raw_own", "haiku__PICK2_OWN__"),
                              ("c5_first", "wells_removal", "raw_wells", "haiku__PICK2_WELLS__")]:
    raw5 = load(ROOT / "exps/c5_removal" / rawdir)
    rows5 = []
    for p in b5[key]:
        c = choice(raw5[pre + p["pool"]]["text"])
        vs = [iso_res(cid) for cid in p["retained_cids"]]
        if c is None or None in vs:
            continue
        rows5.append((p["pool"], int(c > 0), int(any(vs))))
    fal[tag] = dict(n_affected=len([r for r in rows5 if r[0] in bad5]),
                    all=contrast([r[1:] for r in rows5], 3), clean=contrast([r[1:] for r in rows5 if r[0] not in bad5], 4))
out["final_answer_line"] = fal

# (f) Holm adjustment for the planned C4 family (H_C4a, H_C4b, H_C4c)
rb = json.load(open(ROOT / "results/results_b.json"))["c4_compute"]
fam = {"a": rb["ta_contrasts"]["PICK_MAJ3_minus_ISO_any"]["p_one_sided_gt0"],
       "b": rb["ta_contrasts"]["PICK_ANY3_minus_ISO_any"]["p_one_sided_gt0"],
       "c": rb["sdt_diffs"]["PICK_MAJ3_minus_ISO"]["d_prime_diff_p_one_sided_lt0"]}
fam = {k_: max(v, 1.0 / B) for k_, v in fam.items()}  # a bootstrap p of 0 means below 1/B
order = sorted(fam, key=fam.get)
holm, run = {}, 0.0
for i, k_ in enumerate(order):
    run = max(run, min(1.0, (len(order) - i) * fam[k_]))
    holm[k_] = run
out["holm_c4"] = dict(raw=fam, adjusted=holm)

# (g) first-study confidence curves (amendment A5: H6 partial area under the curve, H7 base-rate instruction)
a5 = json.load(open(V1ROOT / "exps/c3/results_a5.json"))["prereg"]
out["v1_a5"] = {s_: {k_: a5[s_][k_] for k_ in ("n_roc", "pAUC_diff", "ci95", "fa_base", "fa_pick", "dfa", "dfa_ci95")}
                for s_ in ("UNSOLVED", "SOLVED")}

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
rng2 = lambda c_: f"[{sg(c_[0])}, {sg(c_[1])}]"
pfmt = lambda v: "$<0.001$" if v < 0.001 else f"{v:.3f}"
for tag, d in fal.items():
    M[f"x_fal_{tag}_naff"] = str(d["n_affected"])
    for w in ("all", "clean"):
        M[f"x_fal_{tag}_{w}_n"] = str(d[w]["n"])
        M[f"x_fal_{tag}_{w}_pick"] = f"{d[w]['pick']:.3f}"
        M[f"x_fal_{tag}_{w}_iso"] = f"{d[w]['iso']:.3f}"
        M[f"x_fal_{tag}_{w}_diff"] = sg(d[w]["diff"])
        M[f"x_fal_{tag}_{w}_ci"] = rng2(d[w]["ci"])
for k_, v in holm.items():
    M[f"x_holm_c4{k_}"] = pfmt(v)
for s_, a in (("UNSOLVED", "u"), ("SOLVED", "s")):
    d = out["v1_a5"][s_]
    M[f"x_a5_{a}_n"] = str(d["n_roc"])
    M[f"x_a5_{a}_pauc"] = sg(d["pAUC_diff"])
    M[f"x_a5_{a}_pauc_ci"] = rng2(d["ci95"])
    M[f"x_a5_{a}_fa_base"] = f"{d['fa_base']:.3f}"
    M[f"x_a5_{a}_fa_pick"] = f"{d['fa_pick']:.3f}"
with open(ROOT / "paper/results_extra.tex", "w") as f:
    f.write("% Auto-generated by scripts/final_sensitivity.py. Do not hand-edit.\n")
    for k_, v in sorted(M.items()):
        f.write(f"\\expandafter\\def\\csname res@{k_}\\endcsname{{{v}}}\n")
print(json.dumps(out, indent=1))
