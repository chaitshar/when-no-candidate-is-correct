#!/usr/bin/env python3
"""Track 1 analysis: Signal Detection Theory (d', c) with Hautus (1995) log-linear
correction and 5,000-resample problem bootstrap CIs, plus non-Claude and non-own-answer
subgroup breakdowns on C3 UNSOLVED pools.

Pure Python 3.9 stdlib only (no numpy, scipy, or sympy).
"""
import csv
import glob
import json
import math
import os
import random
import sys

C3_DIR = "/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar/exps/c3"
REPO_DIR = "/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar"
OUT_DIR = "/Users/chaitanya/research/mas-study/v2-upgrade/results"

sys.path.insert(0, os.path.join(REPO_DIR, "harness"))
import parse  # noqa: E402

B_BOOT = 5000


def norm_ppf(p):
    """Inverse standard normal CDF Phi^-1(p) via Acklam's rational approximation.
    Max relative error < 1.15e-9 for 0 < p < 1.
    """
    if not (0.0 < p < 1.0):
        raise ValueError(f"p must be strictly in (0, 1), got {p}")
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    plow = 0.02425
    phigh = 1.0 - plow
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        return num / den
    if p <= phigh:
        q = p - 0.5
        r = q * q
        num = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
        den = ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0
        return num / den
    q = math.sqrt(-2.0 * math.log(1.0 - p))
    num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
    den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
    return -num / den


def verify_norm_ppf():
    """Verify Acklam Phi^-1 against standard normal quantiles and math.erf."""
    checks = [
        (0.5, 0.0, 1e-12),
        (0.8413447, 1.0, 5e-7),
        (0.8413447460685429, 1.0, 1e-8),
        (0.975, 1.959963984540054, 1e-8),
        (0.025, -1.959963984540054, 1e-8),
        (0.999, 3.090232306167813, 1e-8),
    ]
    results = []
    for p, expected, tol in checks:
        got = norm_ppf(p)
        err = abs(got - expected)
        if err > tol:
            raise AssertionError(f"norm_ppf({p}) = {got}, expected {expected} (err={err})")
        cdf_back = 0.5 * (1.0 + math.erf(got / math.sqrt(2.0)))
        if abs(cdf_back - p) > 1e-8:
            raise AssertionError(f"roundtrip cdf({got}) = {cdf_back}, expected {p}")
        results.append({"p": p, "z": round(got, 9), "expected": expected, "abs_err": err})
    return results


def hautus_sdt(hits, fas):
    """Compute Hautus (1995) log-linear adjusted H, F, d', and c for paired trials."""
    n = len(hits)
    h_raw = sum(hits) / n
    f_raw = sum(fas) / n
    h_adj = (sum(hits) + 0.5) / (n + 1.0)
    f_adj = (sum(fas) + 0.5) / (n + 1.0)
    zh = norm_ppf(h_adj)
    zf = norm_ppf(f_adj)
    d_prime = zh - zf
    c_crit = -0.5 * (zh + zf)
    return {
        "n": n,
        "H_raw": h_raw,
        "F_raw": f_raw,
        "H_adj": h_adj,
        "F_adj": f_adj,
        "zH": zh,
        "zF": zf,
        "d_prime": d_prime,
        "c": c_crit,
    }


def ci95_percentile(sorted_vals):
    """Return 2.5th and 97.5th percentile bounds for sorted bootstrap values."""
    n = len(sorted_vals)
    lo = sorted_vals[int(0.025 * n)]
    hi = sorted_vals[int(0.975 * n) - 1]
    return [lo, hi]


def bootstrap_sdt(hits, fas, seed, n_boot=B_BOOT):
    """Problem-level bootstrap (5,000 resamples) for Hautus d' and c."""
    n = len(hits)
    point = hautus_sdt(hits, fas)
    rng = random.Random(seed)
    dp_draws = []
    c_draws = []
    for _ in range(n_boot):
        idxs = [rng.randrange(n) for _ in range(n)]
        hb = (sum(hits[i] for i in idxs) + 0.5) / (n + 1.0)
        fb = (sum(fas[i] for i in idxs) + 0.5) / (n + 1.0)
        zh = norm_ppf(hb)
        zf = norm_ppf(fb)
        dp_draws.append(zh - zf)
        c_draws.append(-0.5 * (zh + zf))
    dp_draws.sort()
    c_draws.sort()
    point["d_prime_ci95"] = ci95_percentile(dp_draws)
    point["c_ci95"] = ci95_percentile(c_draws)
    return point


def bootstrap_sdt_diff(pairs_a, pairs_b, seed, n_boot=B_BOOT):
    """Paired problem-level bootstrap for d'_A - d'_B and c_A - c_B."""
    n = len(pairs_a)
    ha = [x[0] for x in pairs_a]
    fa = [x[1] for x in pairs_a]
    hb = [x[0] for x in pairs_b]
    fb = [x[1] for x in pairs_b]
    sa = hautus_sdt(ha, fa)
    sb = hautus_sdt(hb, fb)
    rng = random.Random(seed)
    ddp = []
    dc = []
    for _ in range(n_boot):
        idxs = [rng.randrange(n) for _ in range(n)]
        zha = norm_ppf((sum(ha[i] for i in idxs) + 0.5) / (n + 1.0))
        zfa = norm_ppf((sum(fa[i] for i in idxs) + 0.5) / (n + 1.0))
        zhb = norm_ppf((sum(hb[i] for i in idxs) + 0.5) / (n + 1.0))
        zfb = norm_ppf((sum(fb[i] for i in idxs) + 0.5) / (n + 1.0))
        ddp.append((zha - zfa) - (zhb - zfb))
        dc.append((-0.5 * (zha + zfa)) - (-0.5 * (zhb + zfb)))
    ddp.sort()
    dc.sort()
    return {
        "n": n,
        "d_prime_diff": sa["d_prime"] - sb["d_prime"],
        "d_prime_diff_ci95": ci95_percentile(ddp),
        "c_diff": sa["c"] - sb["c"],
        "c_diff_ci95": ci95_percentile(dc),
    }


def bootstrap_mean(xs, seed, n_boot=B_BOOT):
    """Bootstrap mean and 95% CI for a list of floats."""
    n = len(xs)
    if n == 0:
        return {"n": 0, "mean": None, "ci95": None}
    rng = random.Random(seed)
    draws = []
    for _ in range(n_boot):
        draws.append(sum(rng.choice(xs) for _ in range(n)) / n)
    draws.sort()
    return {"n": n, "mean": sum(xs) / n, "ci95": ci95_percentile(draws)}


def load_c3_data():
    pools = json.load(open(os.path.join(REPO_DIR, "banks/locked_c3/pools.json")))
    ta = {p["pid"]: p for p in pools if p["kind"] == "TA"}
    tp = {p["pid"]: p for p in pools if p["kind"] == "TP"}
    strata = json.load(open(os.path.join(C3_DIR, "strata.json")))
    raw = {}
    for sub in ("arms", "a4"):
        for f in glob.glob(os.path.join(C3_DIR, "raw", sub, "*.json")):
            r = json.load(open(f))
            raw[r["id"]] = r
    audit = {r["pid"]: r["audited_stratum"] for r in csv.DictReader(open(os.path.join(C3_DIR, "audit_unsolved.csv")))}
    dups_raw = json.load(open(os.path.join(C3_DIR, "duplicates_of_used.json")))
    dups = set(dups_raw if isinstance(dups_raw, list) else dups_raw.get("selected_duplicates", dups_raw.get("pids", list(dups_raw))))
    bad = {r["pid"] for r in csv.DictReader(open(os.path.join(C3_DIR, "candidate_label_audit.csv")))}
    own_rows = {}
    for r in csv.DictReader(open(os.path.join(C3_DIR, "own_answer_checks.csv"))):
        pos = [x for x in r["own_answer_candidate_positions"].split(";") if x.strip()]
        own_rows[r["pid"]] = pos
    ref_aligned = json.load(open(os.path.join(C3_DIR, "results_aligned.json")))
    ref_a4 = json.load(open(os.path.join(C3_DIR, "results_a4.json")))
    ref_review = json.load(open(os.path.join(C3_DIR, "results_review.json")))
    return {
        "ta": ta,
        "tp": tp,
        "strata": strata,
        "raw": raw,
        "audit": audit,
        "dups": dups,
        "bad": bad,
        "own_rows": own_rows,
        "ref_aligned": ref_aligned,
        "ref_a4": ref_a4,
        "ref_review": ref_review,
    }


def get_strata_map(data, kind):
    out = {}
    st = data["strata"]
    for pid in st["selected"]:
        s = st["stratum"][pid]
        if kind == "corrected":
            if pid in data["dups"] or pid in data["bad"]:
                continue
            s = data["audit"].get(pid, s)
            if s not in ("SOLVED", "UNSOLVED"):
                continue
        out[pid] = s
    return out


def aligned_outcome(raw, model, arm, pool):
    """Per-candidate selection probabilities matching analyze_aligned.py."""
    n = len(pool["cands"])
    if arm == "PICK":
        r = raw.get(f"{model}__PICK__{pool['pool']}")
        k = parse.choice(r["result"], n) if r else None
        if k is None:
            return None
        return [float(i == k - 1) for i in range(n)]
    if arm == "EACH":
        r = raw.get(f"{model}__EACH__{pool['pool']}")
        v = parse.each(r["result"], n) if r else None
        if not v or None in v:
            return None
    else:
        v = []
        for c in pool["cands"]:
            r = raw.get(f"{model}__ISO__{c['cid']}")
            x = parse.verdict(r["result"]) if r else None
            if x is None:
                return None
            v.append(x)
    a = sum(map(int, v))
    return [(1.0 / a if x else 0.0) for x in v] if a else [0.0] * n


def strict_a4_pair(raw, model, ta_pool, tp_pool, arm):
    """Strict identification hit and FA matching analyze_a4.py."""
    if arm == "PICK":
        a = raw.get(f"{model}__PICK__{ta_pool['pool']}")
        b = raw.get(f"{model}__PICK__{tp_pool['pool']}")
        ka = parse.choice(a["result"], 3) if a else None
        kb = parse.choice(b["result"], 3) if b else None
        if ka is None or kb is None:
            return None
        fa = float(ka > 0)
        hit = float(kb > 0 and tp_pool["cands"][kb - 1]["role"] == "right")
        return hit, fa
    if arm == "EACH":
        a = raw.get(f"{model}__EACH__{ta_pool['pool']}")
        b = raw.get(f"{model}__EACH__{tp_pool['pool']}")
        ea = parse.each(a["result"], 3) if a else None
        eb = parse.each(b["result"], 3) if b else None
        if not ea or not eb or None in ea or None in eb:
            return None
        fa = float(any(ea))
        hit = float(all(v == (c["role"] == "right") for v, c in zip(eb, tp_pool["cands"])))
        return hit, fa
    vta = []
    for c in ta_pool["cands"]:
        r = raw.get(f"{model}__ISO__{c['cid']}")
        x = parse.verdict(r["result"]) if r else None
        if x is None:
            return None
        vta.append(x)
    vtp = []
    for c in tp_pool["cands"]:
        r = raw.get(f"{model}__ISO__{c['cid']}")
        x = parse.verdict(r["result"]) if r else None
        if x is None:
            return None
        vtp.append(x)
    fa = float(any(vta))
    hit = float(all(v == (c["role"] == "right") for v, c in zip(vtp, tp_pool["cands"])))
    return hit, fa


def compute_sdt_block(data, mode):
    """Compute SDT tables for mode in {'aligned', 'strict_a4'}."""
    out = {}
    ta = data["ta"]
    tp = data["tp"]
    raw = data["raw"]
    for model in ("haiku", "sonnet"):
        for kind in ("prereg", "corrected"):
            s_map = get_strata_map(data, kind)
            key = f"{model}_{kind}"
            out[key] = {}
            for stratum in ("UNSOLVED", "SOLVED"):
                pids = [pid for pid, s in s_map.items() if s == stratum and pid in tp]
                arm_pairs = {arm: {} for arm in ("PICK", "EACH", "ISO")}
                for pid in pids:
                    for arm in ("PICK", "EACH", "ISO"):
                        if mode == "aligned":
                            pa = aligned_outcome(raw, model, arm, ta[pid])
                            pb = aligned_outcome(raw, model, arm, tp[pid])
                            if pa is None or pb is None:
                                continue
                            h_val = sum(q for q, c in zip(pb, tp[pid]["cands"]) if c["role"] == "right")
                            f_val = sum(pa)
                            arm_pairs[arm][pid] = (h_val, f_val)
                        else:
                            pair = strict_a4_pair(raw, model, ta[pid], tp[pid], arm)
                            if pair is not None:
                                arm_pairs[arm][pid] = pair
                # Cross-check raw means against C3 reference files
                if mode == "aligned":
                    ref = data["ref_aligned"][key][stratum]
                    for arm in ("PICK", "EACH", "ISO"):
                        pairs_list = list(arm_pairs[arm].values())
                        h_mean = sum(x[0] for x in pairs_list) / len(pairs_list)
                        f_mean = sum(x[1] for x in pairs_list) / len(pairs_list)
                        if len(pairs_list) != ref[arm]["n"]:
                            raise AssertionError(f"n mismatch {key} {stratum} {arm}")
                        if abs(h_mean - ref[arm]["correct"]) > 1e-9 or abs(f_mean - ref[arm]["false_choice"]) > 1e-9:
                            raise AssertionError(f"aligned mismatch {key} {stratum} {arm}")
                elif kind == "prereg":
                    ref = data["ref_a4"][model][stratum]
                    for arm in ("PICK", "EACH", "ISO"):
                        pairs_list = list(arm_pairs[arm].values())
                        h_mean = sum(x[0] for x in pairs_list) / len(pairs_list)
                        f_mean = sum(x[1] for x in pairs_list) / len(pairs_list)
                        if len(pairs_list) != ref[arm]["n"]:
                            raise AssertionError(f"a4 n mismatch {model} {stratum} {arm}")
                        if abs(h_mean - ref[arm]["hit"]) > 1e-9 or abs(f_mean - ref[arm]["fa"]) > 1e-9:
                            raise AssertionError(f"a4 mismatch {model} {stratum} {arm}")

                res_stratum = {}
                for idx, arm in enumerate(("PICK", "EACH", "ISO")):
                    ordered_pids = [pid for pid in pids if pid in arm_pairs[arm]]
                    hits = [arm_pairs[arm][pid][0] for pid in ordered_pids]
                    fas = [arm_pairs[arm][pid][1] for pid in ordered_pids]
                    seed = 202600 + (0 if model == "haiku" else 1000) + (0 if kind == "prereg" else 500) + (0 if stratum == "UNSOLVED" else 100) + idx
                    res_stratum[arm] = bootstrap_sdt(hits, fas, seed=seed)

                diffs = {}
                for idx, (a_arm, b_arm) in enumerate((("PICK", "ISO"), ("PICK", "EACH"), ("EACH", "ISO"))):
                    shared = [pid for pid in pids if pid in arm_pairs[a_arm] and pid in arm_pairs[b_arm]]
                    pa = [arm_pairs[a_arm][pid] for pid in shared]
                    pb = [arm_pairs[b_arm][pid] for pid in shared]
                    seed = 302600 + (0 if model == "haiku" else 1000) + (0 if kind == "prereg" else 500) + (0 if stratum == "UNSOLVED" else 100) + idx
                    diffs[f"{a_arm}_minus_{b_arm}"] = bootstrap_sdt_diff(pa, pb, seed=seed)
                res_stratum["diffs"] = diffs
                out[key][stratum] = res_stratum
    return out


def has_claude_cand(pool):
    return any("claude" in g.lower() for g in pool["gens"])


def compute_subgroups(data):
    ta = data["ta"]
    raw = data["raw"]
    own_rows = data["own_rows"]
    subgroups_spec = [
        ("all_unsolved", "All UNSOLVED TA pools", lambda p, has_cl, has_own: True),
        ("no_claude_and_no_own", "0 Claude candidates AND no own answer", lambda p, has_cl, has_own: (not has_cl) and (not has_own)),
        ("no_claude", "0 Claude candidates", lambda p, has_cl, has_own: not has_cl),
        ("has_claude", ">=1 Claude candidate", lambda p, has_cl, has_own: has_cl),
        ("no_own", "No own answer", lambda p, has_cl, has_own: not has_own),
        ("has_own", "Has own answer (reference)", lambda p, has_cl, has_own: has_own),
    ]
    out = {}
    for kind in ("prereg", "corrected"):
        s_map = get_strata_map(data, kind)
        uns_pids = [pid for pid, s in s_map.items() if s == "UNSOLVED"]
        out[kind] = {"n_unsolved_ta": len(uns_pids), "models": {}}
        for model in ("haiku", "sonnet"):
            m_res = {}
            for s_idx, (sg_key, sg_label, pred) in enumerate(subgroups_spec):
                pick_vals = []
                iso_vals = []
                d_vals = []
                sg_pids = []
                for pid in uns_pids:
                    pool = ta[pid]
                    has_cl = has_claude_cand(pool)
                    has_own = len(own_rows.get(pid, [])) > 0
                    if not pred(pool, has_cl, has_own):
                        continue
                    p_out = aligned_outcome(raw, model, "PICK", pool)
                    i_out = aligned_outcome(raw, model, "ISO", pool)
                    if p_out is None or i_out is None:
                        continue
                    pv = float(sum(p_out))
                    iv = float(sum(i_out))
                    pick_vals.append(pv)
                    iso_vals.append(iv)
                    d_vals.append(pv - iv)
                    sg_pids.append(pid)
                seed_base = 402600 + (0 if kind == "prereg" else 500) + (0 if model == "haiku" else 100) + s_idx * 10
                b_pick = bootstrap_mean(pick_vals, seed=seed_base + 1)
                b_iso = bootstrap_mean(iso_vals, seed=seed_base + 2)
                b_d = bootstrap_mean(d_vals, seed=seed_base + 3)
                m_res[sg_key] = {
                    "label": sg_label,
                    "n": len(sg_pids),
                    "pids": sg_pids,
                    "pick": b_pick["mean"],
                    "pick_ci95": b_pick["ci95"],
                    "iso_any": b_iso["mean"],
                    "iso_any_ci95": b_iso["ci95"],
                    "d": b_d["mean"],
                    "d_ci95": b_d["ci95"],
                }
            # Cross-check against results_review.json on prereg
            if kind == "prereg":
                ref_rev = data["ref_review"]["own_answer_haiku_unsolved"]
                if model == "haiku":
                    assert abs(m_res["has_own"]["d"] - ref_rev["d_with"]["mean"]) < 1e-12
                    assert abs(m_res["no_own"]["d"] - ref_rev["d_without"]["mean"]) < 1e-12
                else:
                    assert abs(m_res["has_own"]["d"] - ref_rev["sonnet_d_with"]["mean"]) < 1e-12
                    assert abs(m_res["no_own"]["d"] - ref_rev["sonnet_d_without"]["mean"]) < 1e-12
            out[kind]["models"][model] = m_res
    return out


def fmt_ci(val, ci):
    if val is None or ci is None:
        return "NA"
    return f"{val:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}]"


def fmt_rate(val):
    return "NA" if val is None else f"{val:.3f}"


def write_markdown(payload, md_path):
    lines = [
        "# Track 1: SDT (d', c) and Subgroup Breakdowns on C3",
        "",
        "Pure Python 3.9 stdlib recomputation from `exps/c3` raw replies, `banks/locked_c3/pools.json`, `results_aligned.json`, `results_a4.json`, `results_review.json`, and `own_answer_checks.csv`.",
        "Hautus (1995) log-linear correction: `H_adj = (sum(H) + 0.5) / (n + 1)`, `F_adj = (sum(F) + 0.5) / (n + 1)`.",
        "Bootstrap: 5,000 problem resamples (percentile 95% CI). Positive `d'` indicates signal sensitivity; negative `c` indicates liberal choosing bias (low abstention threshold).",
        "",
        "## 1. Signal Detection Theory (Aligned Output Space: Primary)",
        "",
        "Hit rate `H` and false-alarm rate `F` match `results_aligned.json` (EACH and ISO choose uniformly among accepted candidates on TP; `F` is any non-abstention on TA).",
        "",
        "| Model & Stratum Set | Stratum | Arm | N | H_raw | F_raw | d' [95% CI] | c [95% CI] |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    sdt_al = payload["sdt_aligned"]
    for key in ("haiku_prereg", "haiku_corrected", "sonnet_prereg", "sonnet_corrected"):
        for stratum in ("UNSOLVED", "SOLVED"):
            for arm in ("PICK", "EACH", "ISO"):
                r = sdt_al[key][stratum][arm]
                lines.append(
                    f"| {key} | {stratum} | {arm} | {r['n']} | {r['H_raw']:.3f} | {r['F_raw']:.3f} | "
                    f"{fmt_ci(r['d_prime'], r['d_prime_ci95'])} | {fmt_ci(r['c'], r['c_ci95'])} |"
                )

    lines.extend([
        "",
        "### Paired SDT Contrasts (Aligned Output Space)",
        "",
        "| Model & Stratum Set | Stratum | Contrast | N | delta d' [95% CI] | delta c [95% CI] |",
        "|---|---|---|---:|---|---|",
    ])
    for key in ("haiku_prereg", "haiku_corrected", "sonnet_prereg", "sonnet_corrected"):
        for stratum in ("UNSOLVED", "SOLVED"):
            for cname in ("PICK_minus_ISO", "PICK_minus_EACH", "EACH_minus_ISO"):
                d = sdt_al[key][stratum]["diffs"][cname]
                lines.append(
                    f"| {key} | {stratum} | {cname} | {d['n']} | "
                    f"{fmt_ci(d['d_prime_diff'], d['d_prime_diff_ci95'])} | {fmt_ci(d['c_diff'], d['c_diff_ci95'])} |"
                )

    lines.extend([
        "",
        "## 2. Signal Detection Theory (Strict A4 Identification Sensitivity)",
        "",
        "In `results_a4.json`, strict identification requires EACH and ISO to accept the right candidate and reject both wrong candidates on TP.",
        "",
        "| Model & Stratum Set | Stratum | Arm | N | hit_raw | fa_raw | d' [95% CI] | c [95% CI] |",
        "|---|---|---|---:|---:|---:|---|---|",
    ])
    sdt_a4 = payload["sdt_strict_a4"]
    for key in ("haiku_prereg", "haiku_corrected", "sonnet_prereg", "sonnet_corrected"):
        for stratum in ("UNSOLVED", "SOLVED"):
            for arm in ("PICK", "EACH", "ISO"):
                r = sdt_a4[key][stratum][arm]
                lines.append(
                    f"| {key} | {stratum} | {arm} | {r['n']} | {r['H_raw']:.3f} | {r['F_raw']:.3f} | "
                    f"{fmt_ci(r['d_prime'], r['d_prime_ci95'])} | {fmt_ci(r['c'], r['c_ci95'])} |"
                )

    lines.extend([
        "",
        "## 3. Non-Claude and Non-Own-Answer Subgroups (UNSOLVED TA Pools)",
        "",
        "Note: `own_answer_checks.csv` records whether Haiku's wrong SOLVE answer appears among the 3 TA candidates (Sonnet had no SOLVE calls in C3).",
        "",
    ])
    for kind in ("prereg", "corrected"):
        lines.extend([
            f"### {kind.capitalize()} UNSOLVED TA Pools (N={payload['subgroups'][kind]['n_unsolved_ta']})",
            "",
            "| Model | Subgroup | N | PICK | ISO-any | d (PICK minus ISO-any) [95% CI] |",
            "|---|---|---:|---:|---:|---|",
        ])
        for model in ("haiku", "sonnet"):
            m_res = payload["subgroups"][kind]["models"][model]
            for sg_key in ("all_unsolved", "no_claude_and_no_own", "no_claude", "has_claude", "no_own", "has_own"):
                r = m_res[sg_key]
                lines.append(
                    f"| {model} | {r['label']} | {r['n']} | {fmt_rate(r['pick'])} | {fmt_rate(r['iso_any'])} | "
                    f"{fmt_ci(r['d'], r['d_ci95'])} |"
                )
        lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ppf_checks = verify_norm_ppf()
    data = load_c3_data()
    sdt_aligned = compute_sdt_block(data, "aligned")
    sdt_strict = compute_sdt_block(data, "strict_a4")
    subgroups = compute_subgroups(data)

    payload = {
        "meta": {
            "bootstrap_resamples": B_BOOT,
            "hautus_correction": "H_adj = (sum(H) + 0.5) / (n + 1), F_adj = (sum(F) + 0.5) / (n + 1)",
            "ppf_verification": ppf_checks,
            "note_own_answer": "own_answer_checks.csv reflects Haiku SOLVE answers; Sonnet had no SOLVE calls in C3.",
        },
        "sdt_aligned": sdt_aligned,
        "sdt_strict_a4": sdt_strict,
        "subgroups": subgroups,
    }

    json_path = os.path.join(OUT_DIR, "sdt_and_subgroups.json")
    md_path = os.path.join(OUT_DIR, "SDT_AND_SUBGROUPS.md")
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    write_markdown(payload, md_path)
    print(f"Wrote {json_path} and {md_path}")


if __name__ == "__main__":
    main()
