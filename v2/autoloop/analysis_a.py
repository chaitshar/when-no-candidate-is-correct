#!/usr/bin/env python3
"""Independent dual-script analysis (analysis_a.py) for Lineups Without a Culprit v2.

Pure Python 3.9 stdlib only. Implements Hautus (1995) log-linear SDT with an
accurate Acklam plus Halley-refined inverse normal CDF and paired problem-level
bootstrap (5,000 resamples, independent seed 20261120).
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import statistics
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import parsers_extended as parsers  # noqa: E402


DEFAULT_ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")
DEFAULT_V1_ROOT = Path("/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar")
DEFAULT_BOOT_N = 5000
DEFAULT_SEED = 20261120


# ---------------------------------------------------------------------------
# Mathematical and statistical primitives (pure stdlib)
# ---------------------------------------------------------------------------

def norm_cdf(z: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def norm_pdf(z: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def norm_ppf(p: float) -> float:
    """Inverse standard normal CDF using Acklam rational approximation plus one Newton step."""
    if not (0.0 < p < 1.0):
        raise ValueError(f"norm_ppf requires 0 < p < 1, got {p!r}")

    a = (
        -3.969683028665376e+01,
        2.209460984245205e+02,
        -2.759285104469687e+02,
        1.383577518672690e+02,
        -3.066479806614716e+01,
        2.506628277459239e+00,
    )
    b = (
        -5.447609879822406e+01,
        1.615858368580409e+02,
        -1.556989798598866e+02,
        6.680131188771972e+01,
        -1.328068155288572e+01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e+00,
        -2.549732539343734e+00,
        4.374664141464968e+00,
        2.938163982698783e+00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e+00,
        3.754408661907416e+00,
    )

    p_low = 0.02425
    p_high = 1.0 - p_low

    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        z = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        z = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
            ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0
        )
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        z = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )

    # Single Newton refinement step for full float64 accuracy.
    err = norm_cdf(z) - p
    pdf = norm_pdf(z)
    if pdf > 0.0:
        z = z - err / pdf
    return z


def percentile(sorted_vals: Sequence[float], q: float) -> float:
    """Linearly interpolated percentile on an already sorted non-empty sequence."""
    n = len(sorted_vals)
    if n == 1:
        return float(sorted_vals[0])
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_vals[lo])
    frac = pos - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def ci95_from_samples(samples: Sequence[float]) -> List[float]:
    ordered = sorted(samples)
    return [percentile(ordered, 0.025), percentile(ordered, 0.975)]


def hautus_sdt_point(h_vals: Sequence[float], f_vals: Sequence[float]) -> Dict[str, float]:
    """Compute Hautus (1995) log-linear SDT statistics for paired hit and FA arrays."""
    n = len(h_vals)
    if n == 0 or len(f_vals) != n:
        raise ValueError("hautus_sdt_point requires equal non-empty sequences")
    sum_h = sum(h_vals)
    sum_f = sum(f_vals)
    h_raw = sum_h / n
    f_raw = sum_f / n
    h_adj = (sum_h + 0.5) / (n + 1.0)
    f_adj = (sum_f + 0.5) / (n + 1.0)
    zh = norm_ppf(h_adj)
    zf = norm_ppf(f_adj)
    d_prime = zh - zf
    c_val = -0.5 * (zh + zf)
    return {
        "n": n,
        "H_raw": h_raw,
        "F_raw": f_raw,
        "H_adj": h_adj,
        "F_adj": f_adj,
        "zH": zh,
        "zF": zf,
        "d_prime": d_prime,
        "c": c_val,
    }


def boot_rate_summary(vals: Sequence[float], rng: random.Random, n_boot: int) -> Dict[str, Any]:
    """Bootstrap summary for a 1D per-item sequence (rates or paired differences)."""
    n = len(vals)
    if n == 0:
        return {
            "n": 0,
            "mean": None,
            "ci95": None,
            "p_one_sided_gt0": None,
            "p_one_sided_lt0": None,
        }
    mean_val = sum(vals) / n
    draws: List[float] = []
    le0 = 0
    ge0 = 0
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += vals[rng.randrange(n)]
        m = s / n
        draws.append(m)
        if m <= 0.0:
            le0 += 1
        if m >= 0.0:
            ge0 += 1
    return {
        "n": n,
        "mean": mean_val,
        "ci95": ci95_from_samples(draws),
        "p_one_sided_gt0": le0 / n_boot,
        "p_one_sided_lt0": ge0 / n_boot,
    }


def boot_sdt_summary(
    h_vals: Sequence[float],
    f_vals: Sequence[float],
    rng: random.Random,
    n_boot: int,
) -> Optional[Dict[str, Any]]:
    """Hautus SDT point estimate plus paired problem-level bootstrap 95% CIs."""
    n = len(h_vals)
    if n == 0:
        return None
    pt = hautus_sdt_point(h_vals, f_vals)
    d_draws: List[float] = []
    c_draws: List[float] = []
    h_draws: List[float] = []
    f_draws: List[float] = []
    inv_n = 1.0 / n
    denom = n + 1.0
    for _ in range(n_boot):
        sh = 0.0
        sf = 0.0
        for _ in range(n):
            idx = rng.randrange(n)
            sh += h_vals[idx]
            sf += f_vals[idx]
        h_draws.append(sh * inv_n)
        f_draws.append(sf * inv_n)
        zh = norm_ppf((sh + 0.5) / denom)
        zf = norm_ppf((sf + 0.5) / denom)
        d_draws.append(zh - zf)
        c_draws.append(-0.5 * (zh + zf))
    out: Dict[str, Any] = dict(pt)
    out["d_prime_ci95"] = ci95_from_samples(d_draws)
    out["c_ci95"] = ci95_from_samples(c_draws)
    out["H_raw_ci95"] = ci95_from_samples(h_draws)
    out["F_raw_ci95"] = ci95_from_samples(f_draws)
    return out


def boot_sdt_diff(
    ha_vals: Sequence[float],
    fa_vals: Sequence[float],
    hb_vals: Sequence[float],
    fb_vals: Sequence[float],
    rng: random.Random,
    n_boot: int,
) -> Optional[Dict[str, Any]]:
    """Paired bootstrap difference between Arm A and Arm B (A minus B) SDT metrics."""
    n = len(ha_vals)
    if n == 0:
        return None
    pt_a = hautus_sdt_point(ha_vals, fa_vals)
    pt_b = hautus_sdt_point(hb_vals, fb_vals)

    d_diff = pt_a["d_prime"] - pt_b["d_prime"]
    c_diff = pt_a["c"] - pt_b["c"]
    h_diff = pt_a["H_raw"] - pt_b["H_raw"]
    f_diff = pt_a["F_raw"] - pt_b["F_raw"]

    d_draws: List[float] = []
    c_draws: List[float] = []
    h_draws: List[float] = []
    f_draws: List[float] = []

    d_ge0 = 0
    d_le0 = 0
    c_le0 = 0
    c_ge0 = 0
    h_ge0 = 0
    f_ge0 = 0

    inv_n = 1.0 / n
    denom = n + 1.0

    for _ in range(n_boot):
        sha = 0.0
        sfa = 0.0
        shb = 0.0
        sfb = 0.0
        for _ in range(n):
            idx = rng.randrange(n)
            sha += ha_vals[idx]
            sfa += fa_vals[idx]
            shb += hb_vals[idx]
            sfb += fb_vals[idx]
        zha = norm_ppf((sha + 0.5) / denom)
        zfa = norm_ppf((sfa + 0.5) / denom)
        zhb = norm_ppf((shb + 0.5) / denom)
        zfb = norm_ppf((sfb + 0.5) / denom)

        dd = (zha - zfa) - (zhb - zfb)
        cd = (-0.5 * (zha + zfa)) - (-0.5 * (zhb + zfb))
        hd = (sha - shb) * inv_n
        fd = (sfa - sfb) * inv_n

        d_draws.append(dd)
        c_draws.append(cd)
        h_draws.append(hd)
        f_draws.append(fd)

        if dd >= 0.0:
            d_ge0 += 1
        if dd <= 0.0:
            d_le0 += 1
        if cd <= 0.0:
            c_le0 += 1
        if cd >= 0.0:
            c_ge0 += 1
        if hd >= 0.0:
            h_ge0 += 1
        if fd >= 0.0:
            f_ge0 += 1

    return {
        "n": n,
        "d_prime_diff": d_diff,
        "d_prime_diff_ci95": ci95_from_samples(d_draws),
        "d_prime_diff_p_one_sided_lt0": d_ge0 / n_boot,
        "d_prime_diff_p_one_sided_gt0": d_le0 / n_boot,
        "c_diff": c_diff,
        "c_diff_ci95": ci95_from_samples(c_draws),
        "c_diff_p_one_sided_gt0": c_le0 / n_boot,
        "c_diff_p_one_sided_lt0": c_ge0 / n_boot,
        "H_diff": h_diff,
        "H_diff_ci95": ci95_from_samples(h_draws),
        "H_diff_p_one_sided_lt0": h_ge0 / n_boot,
        "F_diff": f_diff,
        "F_diff_ci95": ci95_from_samples(f_draws),
        "F_diff_p_one_sided_lt0": f_ge0 / n_boot,
    }


# ---------------------------------------------------------------------------
# IO helpers for raw JSON files (v2 and v1 C3)
# ---------------------------------------------------------------------------

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s:
            rows.append(json.loads(s))
    return rows


def read_v2_record(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        obj = load_json(path)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def is_v2_ok(rec: Optional[Dict[str, Any]]) -> bool:
    return rec is not None and rec.get("status") == "ok"


def read_v1_c3_text(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    try:
        obj = load_json(path)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    if obj.get("rc") not in (0, None):
        return None
    txt = obj.get("result")
    return txt if isinstance(txt, str) else None


def read_v1_c3_output_tokens(path: Path) -> Optional[int]:
    if not path.is_file():
        return None
    try:
        obj = load_json(path)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    usage = obj.get("usage")
    if isinstance(usage, dict) and isinstance(usage.get("output_tokens"), (int, float)):
        return int(usage["output_tokens"])
    return None


def v1_haiku_pick_choice(v1_root: Path, pool_id: str, kind: str, n_cands: int = 3) -> Optional[int]:
    if kind == "TA":
        p = v1_root / "exps" / "c3" / "raw" / "arms" / f"haiku__PICK__{pool_id}.json"
    else:
        p = v1_root / "exps" / "c3" / "raw" / "a4" / f"haiku__PICK__{pool_id}.json"
    txt = read_v1_c3_text(p)
    return parsers.choice(txt, n_cands) if txt is not None else None


def v1_haiku_iso_verdict(v1_root: Path, cid: str) -> Optional[bool]:
    p = v1_root / "exps" / "c3" / "raw" / "arms" / f"haiku__ISO__{cid}.json"
    txt = read_v1_c3_text(p)
    return parsers.verdict(txt) if txt is not None else None


def arm_status_label(n_ok: int, n_expected: int) -> str:
    if n_ok == 0:
        return "pending"
    if n_ok >= n_expected:
        return "complete"
    return "partial"


def right_pos_1idx(pool: Dict[str, Any]) -> Optional[int]:
    roles = pool.get("roles") or []
    for idx, role in enumerate(roles, 1):
        if role == "right":
            return idx
    cands = pool.get("cands") or []
    for idx, c in enumerate(cands, 1):
        if isinstance(c, dict) and c.get("role") == "right":
            return idx
    return None


def aligned_from_verdicts(verdicts: Sequence[Optional[bool]], right_pos: Optional[int], is_tp: bool) -> Optional[float]:
    if any(v is None for v in verdicts):
        return None
    accepted = [idx for idx, v in enumerate(verdicts, 1) if v is True]
    if not is_tp:
        return 1.0 if accepted else 0.0
    if right_pos is None:
        return None
    return (1.0 / len(accepted)) if right_pos in accepted else 0.0


def strict_from_verdicts(verdicts: Sequence[Optional[bool]], right_pos: Optional[int]) -> Optional[float]:
    if any(v is None for v in verdicts) or right_pos is None:
        return None
    accepted = [idx for idx, v in enumerate(verdicts, 1) if v is True]
    return 1.0 if accepted == [right_pos] else 0.0


def criterion_recovery(
    sdt_arm: Optional[Dict[str, Any]],
    sdt_pick: Optional[Dict[str, Any]],
    sdt_iso: Optional[Dict[str, Any]],
) -> Optional[float]:
    if sdt_arm is None or sdt_pick is None or sdt_iso is None:
        return None
    denom = sdt_iso["c"] - sdt_pick["c"]
    if abs(denom) < 1e-12:
        return None
    return (sdt_arm["c"] - sdt_pick["c"]) / denom


# ---------------------------------------------------------------------------
# Section 1: C5 Own-Answer Removal
# ---------------------------------------------------------------------------

def _c5_own_subset_stats(
    rows: Sequence[Dict[str, Any]],
    rng: random.Random,
    n_boot: int,
    include_subgroups: bool,
) -> Dict[str, Any]:
    analyzed = [r for r in rows if r["ok_all"]]
    pids = [r["pid"] for r in rows]
    n_bank = len(rows)
    n_an = len(analyzed)

    fa_pick2_arr = [r["fa_pick2"] for r in analyzed]
    fa_iso2_arr = [r["fa_iso2"] for r in analyzed]
    d_c5_arr = [r["fa_pick2"] - r["fa_iso2"] for r in analyzed]
    fa_pick3_arr = [r["fa_pick3"] for r in analyzed]
    fa_iso3_arr = [r["fa_iso3"] for r in analyzed]
    d_c3_arr = [r["fa_pick3"] - r["fa_iso3"] for r in analyzed]
    red_arr = [(r["fa_pick3"] - r["fa_iso3"]) - (r["fa_pick2"] - r["fa_iso2"]) for r in analyzed]

    s_pick2 = boot_rate_summary(fa_pick2_arr, rng, n_boot)
    s_iso2 = boot_rate_summary(fa_iso2_arr, rng, n_boot)
    s_dc5 = boot_rate_summary(d_c5_arr, rng, n_boot)
    s_dc3 = boot_rate_summary(d_c3_arr, rng, n_boot)
    s_red = boot_rate_summary(red_arr, rng, n_boot)

    fa_pick3_mean = (sum(fa_pick3_arr) / n_an) if n_an else None
    fa_iso3_mean = (sum(fa_iso3_arr) / n_an) if n_an else None

    kill_flag = False
    if s_dc5["p_one_sided_gt0"] is not None and s_dc5["ci95"] is not None:
        kill_flag = (s_dc5["p_one_sided_gt0"] >= 0.05) and (s_dc5["ci95"][1] < 0.10)

    out: Dict[str, Any] = {
        "n_bank": n_bank,
        "n_analyzed": n_an,
        "pids": pids,
        "fa_pick2": s_pick2["mean"],
        "fa_pick2_ci95": s_pick2["ci95"],
        "fa_iso2": s_iso2["mean"],
        "fa_iso2_ci95": s_iso2["ci95"],
        "d_c5": s_dc5["mean"],
        "d_c5_ci95": s_dc5["ci95"],
        "d_c5_p_one_sided": s_dc5["p_one_sided_gt0"],
        "fa_pick3_c3": fa_pick3_mean,
        "fa_iso3_c3": fa_iso3_mean,
        "d_c3": s_dc3["mean"],
        "d_c3_ci95": s_dc3["ci95"],
        "effect_reduction_d_c3_minus_d_c5": s_red["mean"],
        "effect_reduction_ci95": s_red["ci95"],
        "kill_own_sole_driver": kill_flag,
    }
    if include_subgroups:
        zero_cl = [r for r in rows if not r["has_claude_retained"]]
        ge1_cl = [r for r in rows if r["has_claude_retained"]]
        out["claude_candidate_subgroups"] = {
            "zero_claude": _c5_own_subset_stats(zero_cl, rng, n_boot, include_subgroups=False),
            "ge1_claude": _c5_own_subset_stats(ge1_cl, rng, n_boot, include_subgroups=False),
        }
    return out


def analyze_c5_own_removal(
    root: Path,
    v1_root: Path,
    rng: random.Random,
    n_boot: int,
) -> Dict[str, Any]:
    bank = load_json(root / "banks" / "locked_v2" / "c5_haiku_removal.json")
    pools = bank["own_answer_removal"]
    raw_dir = root / "exps" / "c5_removal" / "raw_own"

    n_expected = len(pools)
    n_files = 0
    n_ok = 0
    n_parsed = 0
    records: List[Dict[str, Any]] = []

    for pool in pools:
        pool_id = pool["pool"]
        pid = pool["pid"]
        fp = raw_dir / f"haiku__PICK2_OWN__{pool_id}.json"
        rec = read_v2_record(fp)
        if rec is not None:
            n_files += 1
        pick2_val: Optional[int] = None
        if is_v2_ok(rec):
            n_ok += 1
            pick2_val = parsers.choice(rec.get("text"), 2)
            if pick2_val is not None:
                n_parsed += 1

        retained_cids = list(pool["retained_cids"])
        removed_cid = pool["removed_cid"]
        iso_ret = [v1_haiku_iso_verdict(v1_root, cid) for cid in retained_cids]
        iso_rem = v1_haiku_iso_verdict(v1_root, removed_cid)
        pick3_c3 = v1_haiku_pick_choice(v1_root, pool_id, "TA", 3)

        ok_all = (
            pick2_val is not None
            and all(v is not None for v in iso_ret)
            and iso_rem is not None
            and pick3_c3 is not None
        )
        fa_pick2 = (1.0 if pick2_val > 0 else 0.0) if pick2_val is not None else None
        fa_iso2 = (1.0 if any(v is True for v in iso_ret) else 0.0) if all(v is not None for v in iso_ret) else None
        fa_pick3 = (1.0 if pick3_c3 > 0 else 0.0) if pick3_c3 is not None else None
        fa_iso3 = (
            (1.0 if (any(v is True for v in iso_ret) or iso_rem is True) else 0.0)
            if (all(v is not None for v in iso_ret) and iso_rem is not None)
            else None
        )

        vendors = [str(v).lower() for v in (pool.get("vendors") or [])]
        records.append(
            {
                "pid": pid,
                "pool": pool_id,
                "is_corrected_unsolved": bool(pool.get("is_corrected_unsolved")),
                "has_claude_retained": "claude" in vendors,
                "ok_all": ok_all,
                "fa_pick2": fa_pick2,
                "fa_iso2": fa_iso2,
                "fa_pick3": fa_pick3,
                "fa_iso3": fa_iso3,
            }
        )

    parse_rate = (n_parsed / n_ok) if n_ok > 0 else None
    corr_rows = [r for r in records if r["is_corrected_unsolved"]]

    return {
        "status": arm_status_label(n_ok, n_expected),
        "n_expected": n_expected,
        "n_files": n_files,
        "n_ok": n_ok,
        "n_parsed": n_parsed,
        "parse_rate": parse_rate,
        "subsets": {
            "all_38": _c5_own_subset_stats(records, rng, n_boot, include_subgroups=True),
            "corrected_33": _c5_own_subset_stats(corr_rows, rng, n_boot, include_subgroups=True),
        },
    }


# ---------------------------------------------------------------------------
# Section 2: C5 Wells Removal
# ---------------------------------------------------------------------------

def analyze_c5_wells_removal(
    root: Path,
    v1_root: Path,
    rng: random.Random,
    n_boot: int,
) -> Dict[str, Any]:
    bank = load_json(root / "banks" / "locked_v2" / "c5_haiku_removal.json")
    meta = bank["meta"]
    pools = bank["wells_removal"]
    raw_dir = root / "exps" / "c5_removal" / "raw_wells"

    n_expected = len(pools)
    n_files = 0
    n_ok = 0
    n_parsed = 0

    pick2_vals: List[float] = []
    iso2_vals: List[float] = []
    diff_vals: List[float] = []
    iso_rem_vals: List[float] = []
    iso3_vals: List[float] = []

    for pool in pools:
        pool_id = pool["pool"]
        fp = raw_dir / f"haiku__PICK2_WELLS__{pool_id}.json"
        rec = read_v2_record(fp)
        if rec is not None:
            n_files += 1
        ch: Optional[int] = None
        if is_v2_ok(rec):
            n_ok += 1
            ch = parsers.choice(rec.get("text"), 2)
            if ch is not None:
                n_parsed += 1

        retained_cids = list(pool["retained_cids"])
        removed_cid = pool["removed_cid"]
        iso_ret = [v1_haiku_iso_verdict(v1_root, cid) for cid in retained_cids]
        iso_rem = v1_haiku_iso_verdict(v1_root, removed_cid)

        if ch is not None and all(v is not None for v in iso_ret) and iso_rem is not None:
            p2 = 1.0 if ch > 0 else 0.0
            i2 = 1.0 if any(v is True for v in iso_ret) else 0.0
            ir = 1.0 if iso_rem is True else 0.0
            i3 = 1.0 if (i2 > 0.0 or ir > 0.0) else 0.0
            pick2_vals.append(p2)
            iso2_vals.append(i2)
            diff_vals.append(p2 - i2)
            iso_rem_vals.append(ir)
            iso3_vals.append(i3)

    parse_rate = (n_parsed / n_ok) if n_ok > 0 else None
    n_an = len(pick2_vals)
    s_pick2 = boot_rate_summary(pick2_vals, rng, n_boot)
    s_iso2 = boot_rate_summary(iso2_vals, rng, n_boot)
    s_diff = boot_rate_summary(diff_vals, rng, n_boot)

    n_src = int(meta["n_wells_source_pools"])
    c3_pick3_rate = len(pools) / n_src if n_src > 0 else None
    prop_2_of_3 = (2.0 / 3.0) * c3_pick3_rate if c3_pick3_rate is not None else None
    indep_2_of_3 = (1.0 - (1.0 - c3_pick3_rate) ** (2.0 / 3.0)) if c3_pick3_rate is not None else None
    diff_vs_prop = (
        (s_pick2["mean"] - prop_2_of_3)
        if (s_pick2["mean"] is not None and prop_2_of_3 is not None)
        else None
    )

    return {
        "status": arm_status_label(n_ok, n_expected),
        "n_expected": n_expected,
        "n_files": n_files,
        "n_ok": n_ok,
        "n_parsed": n_parsed,
        "parse_rate": parse_rate,
        "n_analyzed": n_an,
        "choosing_rate_pick2": s_pick2["mean"],
        "choosing_rate_pick2_ci95": s_pick2["ci95"],
        "abstain_rate_pick2": (1.0 - s_pick2["mean"]) if s_pick2["mean"] is not None else None,
        "fa_iso2_c3": s_iso2["mean"],
        "fa_iso2_c3_ci95": s_iso2["ci95"],
        "diff_pick2_minus_iso2": s_diff["mean"],
        "diff_pick2_minus_iso2_ci95": s_diff["ci95"],
        "diff_pick2_minus_iso2_p_one_sided": s_diff["p_one_sided_gt0"],
        "c3_pick3_rate_all_source": c3_pick3_rate,
        "proportional_2_of_3_baseline": prop_2_of_3,
        "indep_2_of_3_baseline": indep_2_of_3,
        "diff_vs_proportional_2_of_3": diff_vs_prop,
        "c3_iso_removed_accept_rate": (sum(iso_rem_vals) / n_an) if n_an else None,
        "c3_iso3_accept_rate_on_analyzed": (sum(iso3_vals) / n_an) if n_an else None,
    }


# ---------------------------------------------------------------------------
# Section 3: C4 Compute-Matched 3x PICK
# ---------------------------------------------------------------------------

def _agg_c4_ta(ks: Sequence[int]) -> Dict[str, float]:
    counts = Counter(ks)
    maj_choice = 0
    for val, cnt in counts.items():
        if cnt >= 2:
            maj_choice = val
            break
    maj_fa = 1.0 if maj_choice > 0 else 0.0
    if any(cnt >= 2 for cnt in counts.values()):
        tieunif_fa = maj_fa
    else:
        tieunif_fa = sum(1.0 for k in ks if k > 0) / 3.0
    any_fa = 1.0 if any(k > 0 for k in ks) else 0.0
    return {
        "PICK_MAJ3": maj_fa,
        "PICK_MAJ3_TIEUNIF": tieunif_fa,
        "PICK_ANY3": any_fa,
    }


def _agg_c4_tp(ks: Sequence[int], right_pos: int) -> Dict[str, float]:
    counts = Counter(ks)
    maj_choice = 0
    for val, cnt in counts.items():
        if cnt >= 2:
            maj_choice = val
            break
    maj_h = 1.0 if maj_choice == right_pos else 0.0
    if any(cnt >= 2 for cnt in counts.values()):
        tieunif_h = maj_h
    else:
        tieunif_h = sum(1.0 for k in ks if k == right_pos) / 3.0
    uniq_picks = set(k for k in ks if k > 0)
    any_h_aligned = (1.0 / len(uniq_picks)) if right_pos in uniq_picks else 0.0
    any_h_strict = 1.0 if uniq_picks == {right_pos} else 0.0
    return {
        "PICK_MAJ3": maj_h,
        "PICK_MAJ3_TIEUNIF": tieunif_h,
        "PICK_ANY3": any_h_aligned,
        "PICK_MAJ3_strict": maj_h,
        "PICK_ANY3_strict": any_h_strict,
    }


def _token_ratio_block(pick_toks: Sequence[float], iso_toks: Sequence[float]) -> Dict[str, Any]:
    n = len(pick_toks)
    if n == 0:
        return {
            "n_pools": 0,
            "pick_3x_median_tokens": None,
            "iso_3x_median_tokens": None,
            "median_ratio": None,
            "per_pool_ratio_median": None,
            "gate_090_to_110": False,
        }
    p_med = float(statistics.median(pick_toks))
    i_med = float(statistics.median(iso_toks))
    med_ratio = (p_med / i_med) if i_med > 0 else None
    per_pool = [p / i for p, i in zip(pick_toks, iso_toks) if i > 0]
    per_med = float(statistics.median(per_pool)) if per_pool else None
    gate = bool(med_ratio is not None and 0.90 <= med_ratio <= 1.10)
    return {
        "n_pools": n,
        "pick_3x_median_tokens": p_med,
        "iso_3x_median_tokens": i_med,
        "median_ratio": med_ratio,
        "per_pool_ratio_median": per_med,
        "gate_090_to_110": gate,
    }


def analyze_c4_compute(
    root: Path,
    v1_root: Path,
    rng: random.Random,
    n_boot: int,
) -> Dict[str, Any]:
    bank = load_json(root / "banks" / "locked_v2" / "c4_haiku_compute.json")
    pools = bank["pools"]
    raw_dir = root / "exps" / "c4_compute" / "raw_haiku"
    repeats = int(bank["meta"].get("repeats_per_pool", 3))

    n_expected_calls = len(pools) * repeats
    n_files = 0
    n_ok = 0
    n_parsed_calls = 0

    ta_by_pid: Dict[str, Dict[str, float]] = {}
    tp_by_pid: Dict[str, Dict[str, float]] = {}
    tok_ta_pick: List[float] = []
    tok_ta_iso: List[float] = []
    tok_tp_pick: List[float] = []
    tok_tp_iso: List[float] = []

    for pool in pools:
        pool_id = pool["pool"]
        pid = pool["pid"]
        kind = pool["kind"]
        rpos = right_pos_1idx(pool)

        ks: List[Optional[int]] = []
        p_tok_sum = 0
        p_tok_ok = True
        for rep in range(repeats):
            fp = raw_dir / f"haiku__PICK__{pool_id}__rep{rep}.json"
            rec = read_v2_record(fp)
            if rec is not None:
                n_files += 1
            if is_v2_ok(rec):
                n_ok += 1
                ch = parsers.choice(rec.get("text"), 3)
                if ch is not None:
                    n_parsed_calls += 1
                ks.append(ch)
                ot = rec.get("output_tokens")
                if isinstance(ot, (int, float)):
                    p_tok_sum += int(ot)
                else:
                    p_tok_ok = False
            else:
                ks.append(None)
                p_tok_ok = False

        cids = [c["cid"] for c in pool["cands"]]
        iso_v = [v1_haiku_iso_verdict(v1_root, cid) for cid in cids]
        iso_toks = [
            read_v1_c3_output_tokens(v1_root / "exps" / "c3" / "raw" / "arms" / f"haiku__ISO__{cid}.json")
            for cid in cids
        ]
        if p_tok_ok and all(t is not None for t in iso_toks):
            iso_tok_sum = float(sum(int(t) for t in iso_toks if t is not None))
            if kind == "TA":
                tok_ta_pick.append(float(p_tok_sum))
                tok_ta_iso.append(iso_tok_sum)
            else:
                tok_tp_pick.append(float(p_tok_sum))
                tok_tp_iso.append(iso_tok_sum)

        pick1x = v1_haiku_pick_choice(v1_root, pool_id, kind, 3)

        if all(k is not None for k in ks) and all(v is not None for v in iso_v) and pick1x is not None:
            ks_clean = [int(k) for k in ks if k is not None]
            if kind == "TA":
                row = _agg_c4_ta(ks_clean)
                row["ISO_any"] = 1.0 if any(v is True for v in iso_v) else 0.0
                row["ISO"] = row["ISO_any"]
                row["PICK_1X"] = 1.0 if pick1x > 0 else 0.0
                ta_by_pid[pid] = row
            elif kind == "TP" and rpos is not None:
                row = _agg_c4_tp(ks_clean, rpos)
                iso_h = aligned_from_verdicts(iso_v, rpos, is_tp=True)
                iso_strict = strict_from_verdicts(iso_v, rpos)
                if iso_h is not None and iso_strict is not None:
                    row["ISO"] = iso_h
                    row["ISO_strict"] = iso_strict
                    row["PICK_1X"] = 1.0 if pick1x == rpos else 0.0
                    row["PICK_1X_strict"] = row["PICK_1X"]
                    tp_by_pid[pid] = row

    ta_pids = sorted(ta_by_pid.keys())
    paired_pids = sorted(set(ta_by_pid.keys()) & set(tp_by_pid.keys()))

    ta_arm_keys = ("PICK_MAJ3", "PICK_MAJ3_TIEUNIF", "PICK_ANY3", "ISO_any", "PICK_1X")
    ta_rates = {
        k: boot_rate_summary([ta_by_pid[p][k] for p in ta_pids], rng, n_boot)
        for k in ta_arm_keys
    }

    ta_contrast_specs = (
        ("PICK_MAJ3_minus_ISO_any", "PICK_MAJ3", "ISO_any"),
        ("PICK_ANY3_minus_ISO_any", "PICK_ANY3", "ISO_any"),
        ("PICK_MAJ3_TIEUNIF_minus_ISO_any", "PICK_MAJ3_TIEUNIF", "ISO_any"),
        ("PICK_MAJ3_minus_PICK_1X", "PICK_MAJ3", "PICK_1X"),
    )
    ta_contrasts = {
        name: boot_rate_summary([ta_by_pid[p][a] - ta_by_pid[p][b] for p in ta_pids], rng, n_boot)
        for name, a, b in ta_contrast_specs
    }

    sdt_arm_keys = ("PICK_MAJ3", "PICK_MAJ3_TIEUNIF", "PICK_ANY3", "ISO", "PICK_1X")
    sdt_aligned = {
        k: boot_sdt_summary(
            [tp_by_pid[p][k] for p in paired_pids],
            [ta_by_pid[p][k] for p in paired_pids],
            rng,
            n_boot,
        )
        for k in sdt_arm_keys
    }

    sdt_diff_specs = (
        ("PICK_MAJ3_minus_ISO", "PICK_MAJ3", "ISO"),
        ("PICK_ANY3_minus_ISO", "PICK_ANY3", "ISO"),
        ("PICK_MAJ3_TIEUNIF_minus_ISO", "PICK_MAJ3_TIEUNIF", "ISO"),
        ("PICK_MAJ3_minus_PICK_1X", "PICK_MAJ3", "PICK_1X"),
    )
    sdt_diffs = {
        name: boot_sdt_diff(
            [tp_by_pid[p][a] for p in paired_pids],
            [ta_by_pid[p][a] for p in paired_pids],
            [tp_by_pid[p][b] for p in paired_pids],
            [ta_by_pid[p][b] for p in paired_pids],
            rng,
            n_boot,
        )
        for name, a, b in sdt_diff_specs
    }

    strict_specs = (
        ("PICK_MAJ3", "PICK_MAJ3_strict"),
        ("PICK_ANY3", "PICK_ANY3_strict"),
        ("ISO", "ISO_strict"),
        ("PICK_1X", "PICK_1X_strict"),
    )
    strict_tp_hits = {
        name: boot_rate_summary([tp_by_pid[p][key] for p in paired_pids], rng, n_boot)
        for name, key in strict_specs
    }

    parse_rate_calls = (n_parsed_calls / n_ok) if n_ok > 0 else None

    return {
        "status": arm_status_label(n_ok, n_expected_calls),
        "n_expected_calls": n_expected_calls,
        "n_files": n_files,
        "n_ok": n_ok,
        "n_parsed_calls": n_parsed_calls,
        "parse_rate_calls": parse_rate_calls,
        "n_ta_analyzed": len(ta_pids),
        "n_tp_paired_analyzed": len(paired_pids),
        "ta_rates": ta_rates,
        "ta_contrasts": ta_contrasts,
        "sdt_aligned": sdt_aligned,
        "sdt_diffs": sdt_diffs,
        "strict_tp_hits": strict_tp_hits,
        "token_ratio": {
            "ta": _token_ratio_block(tok_ta_pick, tok_ta_iso),
            "tp": _token_ratio_block(tok_tp_pick, tok_tp_iso),
            "all": _token_ratio_block(tok_ta_pick + tok_tp_pick, tok_ta_iso + tok_tp_iso),
        },
    }


# ---------------------------------------------------------------------------
# Shared multi-arm evaluation block (for c9_science and c6_math)
# ---------------------------------------------------------------------------

def _m1_from_iso_and_pick(
    iso_verdicts: Sequence[Optional[bool]],
    pick_choice: Optional[int],
    right_pos: Optional[int],
    is_tp: bool,
) -> Dict[str, Optional[float]]:
    if any(v is None for v in iso_verdicts):
        return {
            "M1_unif_aligned": None,
            "M1_unif_strict": None,
            "M1_pick_tiebreak_aligned": None,
            "M1_pick_tiebreak_strict": None,
            "M1_pick_or_abstain_aligned": None,
            "M1_pick_or_abstain_strict": None,
        }
    accepted = [idx for idx, v in enumerate(iso_verdicts, 1) if v is True]
    k = len(accepted)

    if k == 0:
        return {
            "M1_unif_aligned": 0.0,
            "M1_unif_strict": 0.0,
            "M1_pick_tiebreak_aligned": 0.0,
            "M1_pick_tiebreak_strict": 0.0,
            "M1_pick_or_abstain_aligned": 0.0,
            "M1_pick_or_abstain_strict": 0.0,
        }
    if k == 1:
        sole = accepted[0]
        if not is_tp:
            return {
                "M1_unif_aligned": 1.0,
                "M1_unif_strict": 1.0,
                "M1_pick_tiebreak_aligned": 1.0,
                "M1_pick_tiebreak_strict": 1.0,
                "M1_pick_or_abstain_aligned": 1.0,
                "M1_pick_or_abstain_strict": 1.0,
            }
        hit = 1.0 if sole == right_pos else 0.0
        return {
            "M1_unif_aligned": hit,
            "M1_unif_strict": hit,
            "M1_pick_tiebreak_aligned": hit,
            "M1_pick_tiebreak_strict": hit,
            "M1_pick_or_abstain_aligned": hit,
            "M1_pick_or_abstain_strict": hit,
        }

    # k >= 2
    if not is_tp:
        unif_val = 1.0
        if pick_choice is None:
            tb_val = None
            poa_val = None
        else:
            tb_val = 1.0
            poa_val = 1.0 if pick_choice in accepted else 0.0
        return {
            "M1_unif_aligned": unif_val,
            "M1_unif_strict": unif_val,
            "M1_pick_tiebreak_aligned": tb_val,
            "M1_pick_tiebreak_strict": tb_val,
            "M1_pick_or_abstain_aligned": poa_val,
            "M1_pick_or_abstain_strict": poa_val,
        }

    # k >= 2 and TP
    unif_aligned = (1.0 / k) if right_pos in accepted else 0.0
    unif_strict = unif_aligned
    if pick_choice is None:
        tb_aligned = None
        tb_strict = None
        poa_aligned = None
        poa_strict = None
    else:
        if pick_choice in accepted:
            tb_aligned = 1.0 if pick_choice == right_pos else 0.0
            tb_strict = tb_aligned
            poa_aligned = tb_aligned
            poa_strict = tb_aligned
        else:
            tb_aligned = unif_aligned
            tb_strict = 0.0
            poa_aligned = 0.0
            poa_strict = 0.0
    return {
        "M1_unif_aligned": unif_aligned,
        "M1_unif_strict": unif_strict,
        "M1_pick_tiebreak_aligned": tb_aligned,
        "M1_pick_tiebreak_strict": tb_strict,
        "M1_pick_or_abstain_aligned": poa_aligned,
        "M1_pick_or_abstain_strict": poa_strict,
    }


def _compute_panel_metrics(
    item_ids: Sequence[str],
    ta_map: Dict[str, Dict[str, Optional[float]]],
    tp_aligned_map: Dict[str, Dict[str, Optional[float]]],
    tp_strict_map: Dict[str, Dict[str, Optional[float]]],
    tp_chose_map: Dict[str, Dict[str, Optional[bool]]],
    arm_names: Sequence[str],
    diff_specs: Sequence[Tuple[str, str, str]],
    rng: random.Random,
    n_boot: int,
) -> Dict[str, Any]:
    ta_false_choice: Dict[str, Any] = {}
    tp_hit_aligned: Dict[str, Any] = {}
    tp_hit_strict: Dict[str, Any] = {}
    sdt: Dict[str, Any] = {}

    for arm in arm_names:
        ta_vals = [float(ta_map[i][arm]) for i in item_ids if ta_map[i].get(arm) is not None]
        tp_al_vals = [float(tp_aligned_map[i][arm]) for i in item_ids if tp_aligned_map[i].get(arm) is not None]
        tp_st_vals = [float(tp_strict_map[i][arm]) for i in item_ids if tp_strict_map[i].get(arm) is not None]

        ta_false_choice[arm] = boot_rate_summary(ta_vals, rng, n_boot)
        tp_hit_aligned[arm] = boot_rate_summary(tp_al_vals, rng, n_boot)
        tp_hit_strict[arm] = boot_rate_summary(tp_st_vals, rng, n_boot)

        paired_ids = [
            i for i in item_ids
            if ta_map[i].get(arm) is not None and tp_aligned_map[i].get(arm) is not None
        ]
        sdt[arm] = boot_sdt_summary(
            [float(tp_aligned_map[i][arm]) for i in paired_ids],
            [float(ta_map[i][arm]) for i in paired_ids],
            rng,
            n_boot,
        )

    rg_pick = [
        float(tp_aligned_map[i]["PICK"])
        for i in item_ids
        if tp_chose_map[i].get("PICK") is True and tp_aligned_map[i].get("PICK") is not None
    ]
    rg_each = [
        float(tp_aligned_map[i]["EACH"])
        for i in item_ids
        if tp_chose_map[i].get("EACH") is True and tp_aligned_map[i].get("EACH") is not None
    ]
    rg_iso = [
        float(tp_aligned_map[i]["ISO"])
        for i in item_ids
        if tp_chose_map[i].get("ISO") is True and tp_aligned_map[i].get("ISO") is not None
    ]

    sdt_diffs: Dict[str, Any] = {}
    for diff_name, a, b in diff_specs:
        both_ids = [
            i for i in item_ids
            if (
                ta_map[i].get(a) is not None
                and tp_aligned_map[i].get(a) is not None
                and ta_map[i].get(b) is not None
                and tp_aligned_map[i].get(b) is not None
            )
        ]
        sdt_diffs[diff_name] = boot_sdt_diff(
            [float(tp_aligned_map[i][a]) for i in both_ids],
            [float(ta_map[i][a]) for i in both_ids],
            [float(tp_aligned_map[i][b]) for i in both_ids],
            [float(ta_map[i][b]) for i in both_ids],
            rng,
            n_boot,
        )

    return {
        "n_items": len(item_ids),
        "ta_false_choice": ta_false_choice,
        "tp_hit_aligned": tp_hit_aligned,
        "tp_hit_strict": tp_hit_strict,
        "right_given_pick": boot_rate_summary(rg_pick, rng, n_boot),
        "right_given_each": boot_rate_summary(rg_each, rng, n_boot),
        "right_given_iso": boot_rate_summary(rg_iso, rng, n_boot),
        "sdt": sdt,
        "sdt_diffs": sdt_diffs,
    }


# ---------------------------------------------------------------------------
# Section 4: C9 Science (ResearchBench)
# ---------------------------------------------------------------------------

def _load_science_model_data(
    root: Path,
    rb_pools: Sequence[Dict[str, Any]],
    model: str,
) -> Dict[str, Any]:
    base = root / "exps" / "c6_crossvendor"
    pick_dir = base / f"raw_science_{model}_pick"
    iso_dir = base / f"raw_science_{model}_iso"
    each_dir = base / f"raw_science_{model}_each"

    unique_cands: Dict[str, str] = {}
    for p in rb_pools:
        for c in p["cands"]:
            unique_cands[c["cid"]] = c["role"]

    iso_ok = 0
    iso_parsed = 0
    iso_map: Dict[str, Optional[bool]] = {}
    for cid in sorted(unique_cands.keys()):
        rec = read_v2_record(iso_dir / f"ISO__{cid}.json")
        if is_v2_ok(rec):
            iso_ok += 1
            v = parsers.verdict(rec.get("text"))
            if v is not None:
                iso_parsed += 1
            iso_map[cid] = v
        else:
            iso_map[cid] = None

    pick_ok = 0
    pick_parsed = 0
    each_ok = 0
    each_parsed = 0
    pick_map: Dict[str, Optional[int]] = {}
    each_map: Dict[str, List[Optional[bool]]] = {}

    for p in rb_pools:
        pool_id = p["pool"]
        n_cands = len(p["cands"])
        rec_p = read_v2_record(pick_dir / f"PICK__{pool_id}.json")
        if is_v2_ok(rec_p):
            pick_ok += 1
            ch = parsers.choice(rec_p.get("text"), n_cands)
            if ch is not None:
                pick_parsed += 1
            pick_map[pool_id] = ch
        else:
            pick_map[pool_id] = None

        rec_e = read_v2_record(each_dir / f"EACH__{pool_id}.json")
        if is_v2_ok(rec_e):
            each_ok += 1
            ev = parsers.each(rec_e.get("text"), n_cands)
            if all(v is not None for v in ev):
                each_parsed += 1
            each_map[pool_id] = ev
        else:
            each_map[pool_id] = [None] * n_cands

    return {
        "unique_cands": unique_cands,
        "iso_map": iso_map,
        "pick_map": pick_map,
        "each_map": each_map,
        "counts": {
            "pick_ok": pick_ok,
            "pick_parsed": pick_parsed,
            "iso_ok": iso_ok,
            "iso_parsed": iso_parsed,
            "each_ok": each_ok,
            "each_parsed": each_parsed,
        },
    }


def analyze_c9_science(
    root: Path,
    rng: random.Random,
    n_boot: int,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    bank = load_json(root / "banks" / "locked_v2" / "c9_science_pools.json")
    rb_pools = bank["researchbench_pools"]
    items = sorted({p["item"] for p in rb_pools})
    pools_by_item_kind = {(p["item"], p["kind"]): p for p in rb_pools}
    unique_cids = {c["cid"] for p in rb_pools for c in p["cands"]}
    n_unique_cands = len(unique_cids)
    n_pools = len(rb_pools)

    science_models = ("gptoss", "gemini", "gemini_low", "hydrogen", "haiku")
    models_out: Dict[str, Any] = {}
    science_cache: Dict[str, Dict[str, Any]] = {}

    arm_names = ("PICK", "EACH", "ISO", "M1_unif", "M1_pick_tiebreak", "M1_pick_or_abstain")
    diff_specs = (
        ("PICK_minus_ISO", "PICK", "ISO"),
        ("EACH_minus_ISO", "EACH", "ISO"),
        ("PICK_minus_EACH", "PICK", "EACH"),
        ("M1_pick_tiebreak_minus_PICK", "M1_pick_tiebreak", "PICK"),
        ("M1_pick_or_abstain_minus_PICK", "M1_pick_or_abstain", "PICK"),
        ("M1_unif_minus_PICK", "M1_unif", "PICK"),
    )

    for model in science_models:
        mdata = _load_science_model_data(root, rb_pools, model)
        science_cache[model] = mdata
        cnt = mdata["counts"]
        unique_cands = mdata["unique_cands"]
        iso_map = mdata["iso_map"]
        pick_map = mdata["pick_map"]
        each_map = mdata["each_map"]

        total_ok = cnt["pick_ok"] + cnt["iso_ok"] + cnt["each_ok"]
        total_parsed = cnt["pick_parsed"] + cnt["iso_parsed"] + cnt["each_parsed"]
        pr_pick = (cnt["pick_parsed"] / cnt["pick_ok"]) if cnt["pick_ok"] > 0 else None
        pr_iso = (cnt["iso_parsed"] / cnt["iso_ok"]) if cnt["iso_ok"] > 0 else None
        pr_each = (cnt["each_parsed"] / cnt["each_ok"]) if cnt["each_ok"] > 0 else None
        pr_tot = (total_parsed / total_ok) if total_ok > 0 else None

        right_vals = [1.0 if iso_map[cid] is True else 0.0 for cid, role in unique_cands.items() if role == "right" and iso_map[cid] is not None]
        wrong_vals = [1.0 if iso_map[cid] is True else 0.0 for cid, role in unique_cands.items() if role != "right" and iso_map[cid] is not None]
        iso_right = (sum(right_vals) / len(right_vals)) if right_vals else None
        iso_wrong = (sum(wrong_vals) / len(wrong_vals)) if wrong_vals else None
        iso_diff = (iso_right - iso_wrong) if (iso_right is not None and iso_wrong is not None) else None
        gate_pass = bool(
            pr_iso is not None
            and pr_iso >= 0.90
            and iso_diff is not None
            and iso_diff >= 0.10
            and iso_wrong is not None
            and iso_wrong > 0.0
        )

        ta_map: Dict[str, Dict[str, Optional[float]]] = {}
        tp_al_map: Dict[str, Dict[str, Optional[float]]] = {}
        tp_st_map: Dict[str, Dict[str, Optional[float]]] = {}
        tp_ch_map: Dict[str, Dict[str, Optional[bool]]] = {}

        for item in items:
            p_ta = pools_by_item_kind[(item, "TA")]
            p_tp = pools_by_item_kind[(item, "TP")]
            rpos = right_pos_1idx(p_tp)

            pick_ta = pick_map[p_ta["pool"]]
            pick_tp = pick_map[p_tp["pool"]]
            each_ta = each_map[p_ta["pool"]]
            each_tp = each_map[p_tp["pool"]]
            iso_ta = [iso_map[c["cid"]] for c in p_ta["cands"]]
            iso_tp = [iso_map[c["cid"]] for c in p_tp["cands"]]

            m1_ta = _m1_from_iso_and_pick(iso_ta, pick_ta, None, is_tp=False)
            m1_tp = _m1_from_iso_and_pick(iso_tp, pick_tp, rpos, is_tp=True)
            pick_paired_ok = (pick_ta is not None) and (pick_tp is not None)

            ta_map[item] = {
                "PICK": (1.0 if pick_ta > 0 else 0.0) if pick_ta is not None else None,
                "EACH": aligned_from_verdicts(each_ta, None, is_tp=False),
                "ISO": aligned_from_verdicts(iso_ta, None, is_tp=False),
                "M1_unif": m1_ta["M1_unif_aligned"],
                "M1_pick_tiebreak": m1_ta["M1_pick_tiebreak_aligned"] if pick_paired_ok else None,
                "M1_pick_or_abstain": m1_ta["M1_pick_or_abstain_aligned"] if pick_paired_ok else None,
            }
            tp_al_map[item] = {
                "PICK": (1.0 if pick_tp == rpos else 0.0) if (pick_tp is not None and rpos is not None) else None,
                "EACH": aligned_from_verdicts(each_tp, rpos, is_tp=True),
                "ISO": aligned_from_verdicts(iso_tp, rpos, is_tp=True),
                "M1_unif": m1_tp["M1_unif_aligned"],
                "M1_pick_tiebreak": m1_tp["M1_pick_tiebreak_aligned"] if pick_paired_ok else None,
                "M1_pick_or_abstain": m1_tp["M1_pick_or_abstain_aligned"] if pick_paired_ok else None,
            }
            tp_st_map[item] = {
                "PICK": tp_al_map[item]["PICK"],
                "EACH": strict_from_verdicts(each_tp, rpos),
                "ISO": strict_from_verdicts(iso_tp, rpos),
                "M1_unif": m1_tp["M1_unif_strict"],
                "M1_pick_tiebreak": m1_tp["M1_pick_tiebreak_strict"] if pick_paired_ok else None,
                "M1_pick_or_abstain": m1_tp["M1_pick_or_abstain_strict"] if pick_paired_ok else None,
            }
            tp_ch_map[item] = {
                "PICK": (pick_tp > 0) if pick_tp is not None else None,
                "EACH": any(v is True for v in each_tp) if all(v is not None for v in each_tp) else None,
                "ISO": any(v is True for v in iso_tp) if all(v is not None for v in iso_tp) else None,
            }

        metrics = _compute_panel_metrics(
            items, ta_map, tp_al_map, tp_st_map, tp_ch_map, arm_names, diff_specs, rng, n_boot
        )
        raw_exact = _science_raw_counts_and_exact_tests(items, ta_map, tp_al_map, tp_st_map)
        models_out[model] = {
            "arm_statuses": {
                "pick": arm_status_label(cnt["pick_ok"], n_pools),
                "iso": arm_status_label(cnt["iso_ok"], n_unique_cands),
                "each": arm_status_label(cnt["each_ok"], n_pools),
            },
            "n_ok": {
                "pick": cnt["pick_ok"],
                "iso": cnt["iso_ok"],
                "each": cnt["each_ok"],
                "total": total_ok,
            },
            "n_parsed": {
                "pick": cnt["pick_parsed"],
                "iso": cnt["iso_parsed"],
                "each": cnt["each_parsed"],
                "total": total_parsed,
            },
            "parse_rates": {
                "pick": pr_pick,
                "iso": pr_iso,
                "each": pr_each,
                "total": pr_tot,
            },
            "calibration": {
                "n_iso_right": len(right_vals),
                "n_iso_wrong": len(wrong_vals),
                "iso_right": iso_right,
                "iso_wrong": iso_wrong,
                "iso_right_minus_wrong": iso_diff,
                "gate_pass": gate_pass,
            },
            "metrics": metrics,
            "raw_counts_and_exact_tests": raw_exact,
        }

    section = {
        "n_items": len(items),
        "n_unique_cands": n_unique_cands,
        "models": models_out,
    }
    return section, science_cache


# ---------------------------------------------------------------------------
# Section 5: C6 Cross-Vendor Math
# ---------------------------------------------------------------------------

def _load_math_model_data(
    root: Path,
    math_pools: Sequence[Dict[str, Any]],
    model: str,
) -> Dict[str, Any]:
    base = root / "exps" / "c6_crossvendor"
    solve_dir = base / f"raw_math_{model}_solve"
    pick_dir = base / f"raw_math_{model}_pick"
    iso_dir = base / f"raw_math_{model}_iso"
    each_dir = base / f"raw_math_{model}_each"

    pids_gold: Dict[str, str] = {}
    unique_cands: Dict[str, str] = {}
    for p in math_pools:
        pids_gold[p["pid"]] = p["gold"]
        for c in p["cands"]:
            unique_cands[c["cid"]] = c["role"]

    solve_ok = 0
    solve_parsed = 0
    unparsed_solve = 0
    solve_grades: Dict[str, List[Optional[bool]]] = {}
    for pid in sorted(pids_gold.keys()):
        gold = pids_gold[pid]
        grades: List[Optional[bool]] = []
        for att in (0, 1):
            rec = read_v2_record(solve_dir / f"SOLVE__{pid}__{att}.json")
            if is_v2_ok(rec):
                solve_ok += 1
                ans = parsers.answer(rec.get("text"))
                if ans is not None:
                    solve_parsed += 1
                    grades.append(parsers.grade_answer(ans, gold))
                else:
                    unparsed_solve += 1
                    grades.append(None)
            else:
                grades.append(None)
        solve_grades[pid] = grades

    iso_ok = 0
    iso_parsed = 0
    iso_map: Dict[str, Optional[bool]] = {}
    for cid in sorted(unique_cands.keys()):
        rec = read_v2_record(iso_dir / f"ISO__{cid}.json")
        if is_v2_ok(rec):
            iso_ok += 1
            v = parsers.verdict(rec.get("text"))
            if v is not None:
                iso_parsed += 1
            iso_map[cid] = v
        else:
            iso_map[cid] = None

    pick_ok = 0
    pick_parsed = 0
    each_ok = 0
    each_parsed = 0
    pick_map: Dict[str, Optional[int]] = {}
    each_map: Dict[str, List[Optional[bool]]] = {}
    for p in math_pools:
        pool_id = p["pool"]
        n_cands = len(p["cands"])
        rec_p = read_v2_record(pick_dir / f"PICK__{pool_id}.json")
        if is_v2_ok(rec_p):
            pick_ok += 1
            ch = parsers.choice(rec_p.get("text"), n_cands)
            if ch is not None:
                pick_parsed += 1
            pick_map[pool_id] = ch
        else:
            pick_map[pool_id] = None

        rec_e = read_v2_record(each_dir / f"EACH__{pool_id}.json")
        if is_v2_ok(rec_e):
            each_ok += 1
            ev = parsers.each(rec_e.get("text"), n_cands)
            if all(v is not None for v in ev):
                each_parsed += 1
            each_map[pool_id] = ev
        else:
            each_map[pool_id] = [None] * n_cands

    return {
        "unique_cands": unique_cands,
        "solve_grades": solve_grades,
        "iso_map": iso_map,
        "pick_map": pick_map,
        "each_map": each_map,
        "counts": {
            "solve_ok": solve_ok,
            "solve_parsed": solve_parsed,
            "unparsed_solve": unparsed_solve,
            "pick_ok": pick_ok,
            "pick_parsed": pick_parsed,
            "iso_ok": iso_ok,
            "iso_parsed": iso_parsed,
            "each_ok": each_ok,
            "each_parsed": each_parsed,
        },
    }


def analyze_c6_math(
    root: Path,
    rng: random.Random,
    n_boot: int,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    bank = load_json(root / "banks" / "locked_v2" / "c6_crossvendor_math.json")
    math_pools = bank["pools"]
    pids = sorted({p["pid"] for p in math_pools})
    pools_by_pid_kind = {(p["pid"], p["kind"]): p for p in math_pools}
    source_by_pid = {p["pid"]: p["source"] for p in math_pools}
    unique_cids = {c["cid"] for p in math_pools for c in p["cands"]}

    n_problems = len(pids)
    n_pools = len(math_pools)
    n_unique_cands = len(unique_cids)
    n_solve_exp = 2 * n_problems

    math_models = ("gptoss", "gemini")
    models_out: Dict[str, Any] = {}
    math_cache: Dict[str, Dict[str, Any]] = {}

    arm_names = ("PICK", "EACH", "ISO")
    diff_specs = (
        ("PICK_minus_ISO", "PICK", "ISO"),
        ("EACH_minus_ISO", "EACH", "ISO"),
        ("PICK_minus_EACH", "PICK", "EACH"),
    )

    for model in math_models:
        mdata = _load_math_model_data(root, math_pools, model)
        math_cache[model] = mdata
        cnt = mdata["counts"]
        unique_cands = mdata["unique_cands"]
        solve_grades = mdata["solve_grades"]
        iso_map = mdata["iso_map"]
        pick_map = mdata["pick_map"]
        each_map = mdata["each_map"]

        total_ok = cnt["solve_ok"] + cnt["pick_ok"] + cnt["iso_ok"] + cnt["each_ok"]
        total_parsed = cnt["solve_parsed"] + cnt["pick_parsed"] + cnt["iso_parsed"] + cnt["each_parsed"]

        pr_solve = (cnt["solve_parsed"] / cnt["solve_ok"]) if cnt["solve_ok"] > 0 else None
        pr_pick = (cnt["pick_parsed"] / cnt["pick_ok"]) if cnt["pick_ok"] > 0 else None
        pr_iso = (cnt["iso_parsed"] / cnt["iso_ok"]) if cnt["iso_ok"] > 0 else None
        pr_each = (cnt["each_parsed"] / cnt["each_ok"]) if cnt["each_ok"] > 0 else None
        pr_tot = (total_parsed / total_ok) if total_ok > 0 else None

        stratum_pids: Dict[str, List[str]] = {
            "ALL": list(pids),
            "SOLVED_M": [],
            "UNSOLVED_M": [],
            "MIXED_M": [],
        }
        for pid in pids:
            g0, g1 = solve_grades[pid]
            if g0 is True and g1 is True:
                stratum_pids["SOLVED_M"].append(pid)
            elif g0 is False and g1 is False:
                stratum_pids["UNSOLVED_M"].append(pid)
            elif (g0 is True and g1 is False) or (g0 is False and g1 is True):
                stratum_pids["MIXED_M"].append(pid)

        stratum_counts = {
            st: {
                "all": len(st_pids),
                "contest": sum(1 for p in st_pids if source_by_pid[p] == "contest"),
                "arxivmath": sum(1 for p in st_pids if source_by_pid[p] == "arxivmath"),
            }
            for st, st_pids in stratum_pids.items()
        }

        right_vals = [1.0 if iso_map[cid] is True else 0.0 for cid, role in unique_cands.items() if role == "right" and iso_map[cid] is not None]
        wrong_vals = [1.0 if iso_map[cid] is True else 0.0 for cid, role in unique_cands.items() if role != "right" and iso_map[cid] is not None]
        iso_right = (sum(right_vals) / len(right_vals)) if right_vals else None
        iso_wrong = (sum(wrong_vals) / len(wrong_vals)) if wrong_vals else None
        iso_diff = (iso_right - iso_wrong) if (iso_right is not None and iso_wrong is not None) else None
        gate_pass = bool(
            pr_iso is not None
            and pr_iso >= 0.90
            and iso_diff is not None
            and iso_diff >= 0.10
            and iso_wrong is not None
            and iso_wrong > 0.0
            and len(stratum_pids["SOLVED_M"]) >= 25
            and len(stratum_pids["UNSOLVED_M"]) >= 25
        )

        ta_map: Dict[str, Dict[str, Optional[float]]] = {}
        tp_al_map: Dict[str, Dict[str, Optional[float]]] = {}
        tp_st_map: Dict[str, Dict[str, Optional[float]]] = {}
        tp_ch_map: Dict[str, Dict[str, Optional[bool]]] = {}
        for pid in pids:
            p_ta = pools_by_pid_kind[(pid, "TA")]
            p_tp = pools_by_pid_kind[(pid, "TP")]
            rpos = right_pos_1idx(p_tp)
            pick_ta = pick_map[p_ta["pool"]]
            pick_tp = pick_map[p_tp["pool"]]
            each_ta = each_map[p_ta["pool"]]
            each_tp = each_map[p_tp["pool"]]
            iso_ta = [iso_map[c["cid"]] for c in p_ta["cands"]]
            iso_tp = [iso_map[c["cid"]] for c in p_tp["cands"]]

            ta_map[pid] = {
                "PICK": (1.0 if pick_ta > 0 else 0.0) if pick_ta is not None else None,
                "EACH": aligned_from_verdicts(each_ta, None, is_tp=False),
                "ISO": aligned_from_verdicts(iso_ta, None, is_tp=False),
            }
            tp_al_map[pid] = {
                "PICK": (1.0 if pick_tp == rpos else 0.0) if (pick_tp is not None and rpos is not None) else None,
                "EACH": aligned_from_verdicts(each_tp, rpos, is_tp=True),
                "ISO": aligned_from_verdicts(iso_tp, rpos, is_tp=True),
            }
            tp_st_map[pid] = {
                "PICK": tp_al_map[pid]["PICK"],
                "EACH": strict_from_verdicts(each_tp, rpos),
                "ISO": strict_from_verdicts(iso_tp, rpos),
            }
            tp_ch_map[pid] = {
                "PICK": (pick_tp > 0) if pick_tp is not None else None,
                "EACH": any(v is True for v in each_tp) if all(v is not None for v in each_tp) else None,
                "ISO": any(v is True for v in iso_tp) if all(v is not None for v in iso_tp) else None,
            }

        strata_out: Dict[str, Any] = {}
        for st, st_pids in stratum_pids.items():
            strata_out[st] = {
                "all": _compute_panel_metrics(
                    st_pids, ta_map, tp_al_map, tp_st_map, tp_ch_map, arm_names, diff_specs, rng, n_boot
                ),
                "contest": _compute_panel_metrics(
                    [p for p in st_pids if source_by_pid[p] == "contest"],
                    ta_map, tp_al_map, tp_st_map, tp_ch_map, arm_names, diff_specs, rng, n_boot,
                ),
                "arxivmath": _compute_panel_metrics(
                    [p for p in st_pids if source_by_pid[p] == "arxivmath"],
                    ta_map, tp_al_map, tp_st_map, tp_ch_map, arm_names, diff_specs, rng, n_boot,
                ),
            }

        models_out[model] = {
            "arm_statuses": {
                "solve": arm_status_label(cnt["solve_ok"], n_solve_exp),
                "pick": arm_status_label(cnt["pick_ok"], n_pools),
                "iso": arm_status_label(cnt["iso_ok"], n_unique_cands),
                "each": arm_status_label(cnt["each_ok"], n_pools),
            },
            "n_ok": {
                "solve": cnt["solve_ok"],
                "pick": cnt["pick_ok"],
                "iso": cnt["iso_ok"],
                "each": cnt["each_ok"],
                "total": total_ok,
            },
            "n_parsed": {
                "solve": cnt["solve_parsed"],
                "pick": cnt["pick_parsed"],
                "iso": cnt["iso_parsed"],
                "each": cnt["each_parsed"],
                "total": total_parsed,
            },
            "parse_rates": {
                "solve": pr_solve,
                "pick": pr_pick,
                "iso": pr_iso,
                "each": pr_each,
                "total": pr_tot,
            },
            "n_unparsed_solve_attempts": cnt["unparsed_solve"],
            "stratum_counts": stratum_counts,
            "calibration": {
                "n_iso_right": len(right_vals),
                "n_iso_wrong": len(wrong_vals),
                "iso_right": iso_right,
                "iso_wrong": iso_wrong,
                "iso_right_minus_wrong": iso_diff,
                "gate_pass": gate_pass,
            },
            "strata": strata_out,
            "h3_out_of_sample_prediction": {
                "status": "pending",
            },
        }

    section = {
        "n_problems": n_problems,
        "n_unique_cands": n_unique_cands,
        "models": models_out,
    }
    return section, math_cache


# ---------------------------------------------------------------------------
# Section 6: C7 Mitigation Matrix
# ---------------------------------------------------------------------------

def _analyze_m2_panel(
    jobs: Sequence[Dict[str, Any]],
    raw_dir: Path,
    id_field: str,
    baseline_pick_fn: Callable[[Dict[str, Any]], Optional[int]],
    baseline_iso_fn: Callable[[Dict[str, Any]], List[Optional[bool]]],
    rng: random.Random,
    n_boot: int,
) -> Dict[str, Any]:
    n_expected = len(jobs)
    n_files = 0
    n_ok = 0
    n_parsed_choice = 0
    n_parsed_conf = 0
    n_parsed_both = 0

    conf_hist = {
        "ta": {str(i): 0 for i in range(1, 6)},
        "tp": {str(i): 0 for i in range(1, 6)},
    }

    jobs_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    items: List[str] = []
    seen_items = set()
    for job in jobs:
        iid = str(job[id_field])
        kind = str(job["kind"])
        jobs_by_key[(iid, kind)] = job
        if iid not in seen_items:
            seen_items.add(iid)
            items.append(iid)
    items.sort()

    ta_vals: Dict[str, Dict[str, Optional[float]]] = {i: {} for i in items}
    tp_vals: Dict[str, Dict[str, Optional[float]]] = {i: {} for i in items}

    for job in jobs:
        iid = str(job[id_field])
        kind = str(job["kind"])
        n_cands = int(job["n_cands"])
        rpos = job.get("right_pos_1idx")
        tau = int(job.get("conf_threshold", 4))

        fp = raw_dir / f"{job['id']}.json"
        rec = read_v2_record(fp)
        if rec is not None:
            n_files += 1
        ch: Optional[int] = None
        cf: Optional[int] = None
        if is_v2_ok(rec):
            n_ok += 1
            txt = rec.get("text")
            ch = parsers.choice(txt, n_cands)
            cf = parsers.confidence(txt)
            if ch is not None:
                n_parsed_choice += 1
            if cf is not None:
                n_parsed_conf += 1
                conf_hist[kind.lower()][str(cf)] += 1
            if ch is not None and cf is not None:
                n_parsed_both += 1

        ch_gate4: Optional[int] = None
        if ch is not None and cf is not None:
            ch_gate4 = ch if cf >= tau else 0

        b_pick = baseline_pick_fn(job)
        b_iso = baseline_iso_fn(job)

        if kind == "TA":
            ta_vals[iid]["M2_raw"] = (1.0 if ch > 0 else 0.0) if ch is not None else None
            ta_vals[iid]["M2_gate4"] = (1.0 if ch_gate4 > 0 else 0.0) if ch_gate4 is not None else None
            ta_vals[iid]["PICK"] = (1.0 if b_pick > 0 else 0.0) if b_pick is not None else None
            ta_vals[iid]["ISO"] = aligned_from_verdicts(b_iso, None, is_tp=False)
        else:
            tp_vals[iid]["M2_raw"] = (1.0 if ch == rpos else 0.0) if (ch is not None and rpos is not None) else None
            tp_vals[iid]["M2_gate4"] = (1.0 if ch_gate4 == rpos else 0.0) if (ch_gate4 is not None and rpos is not None) else None
            tp_vals[iid]["PICK"] = (1.0 if b_pick == rpos else 0.0) if (b_pick is not None and rpos is not None) else None
            tp_vals[iid]["ISO"] = aligned_from_verdicts(b_iso, rpos, is_tp=True)

    arms = ("M2_raw", "M2_gate4", "PICK", "ISO")
    paired_by_arm: Dict[str, List[str]] = {
        a: [i for i in items if ta_vals[i].get(a) is not None and tp_vals[i].get(a) is not None]
        for a in arms
    }
    ta_fc = {
        a: boot_rate_summary([float(ta_vals[i][a]) for i in paired_by_arm[a]], rng, n_boot)
        for a in arms
    }
    tp_hit = {
        a: boot_rate_summary([float(tp_vals[i][a]) for i in paired_by_arm[a]], rng, n_boot)
        for a in arms
    }
    sdt = {
        a: boot_sdt_summary(
            [float(tp_vals[i][a]) for i in paired_by_arm[a]],
            [float(ta_vals[i][a]) for i in paired_by_arm[a]],
            rng,
            n_boot,
        )
        for a in arms
    }

    diff_specs = (
        ("M2_raw_minus_PICK", "M2_raw", "PICK"),
        ("M2_raw_minus_ISO", "M2_raw", "ISO"),
        ("M2_gate4_minus_PICK", "M2_gate4", "PICK"),
        ("M2_gate4_minus_ISO", "M2_gate4", "ISO"),
        ("M2_gate4_minus_M2_raw", "M2_gate4", "M2_raw"),
        ("PICK_minus_ISO", "PICK", "ISO"),
    )
    sdt_diffs: Dict[str, Any] = {}
    for dname, a, b in diff_specs:
        both = [
            i for i in items
            if (
                ta_vals[i].get(a) is not None
                and tp_vals[i].get(a) is not None
                and ta_vals[i].get(b) is not None
                and tp_vals[i].get(b) is not None
            )
        ]
        sdt_diffs[dname] = boot_sdt_diff(
            [float(tp_vals[i][a]) for i in both],
            [float(ta_vals[i][a]) for i in both],
            [float(tp_vals[i][b]) for i in both],
            [float(ta_vals[i][b]) for i in both],
            rng,
            n_boot,
        )

    return {
        "status": arm_status_label(n_ok, n_expected),
        "n_expected_calls": n_expected,
        "n_files": n_files,
        "n_ok": n_ok,
        "n_parsed_choice": n_parsed_choice,
        "n_parsed_conf": n_parsed_conf,
        "n_parsed_both": n_parsed_both,
        "parse_rate_choice": (n_parsed_choice / n_ok) if n_ok > 0 else None,
        "parse_rate_conf": (n_parsed_conf / n_ok) if n_ok > 0 else None,
        "n_paired_m2_raw": len(paired_by_arm["M2_raw"]),
        "n_paired_m2_gate4": len(paired_by_arm["M2_gate4"]),
        "n_matched_pick": len(paired_by_arm["PICK"]),
        "n_matched_iso": len(paired_by_arm["ISO"]),
        "confidence_hist": conf_hist,
        "criterion_recovery_frac": {
            "M2_raw": criterion_recovery(sdt["M2_raw"], sdt["PICK"], sdt["ISO"]),
            "M2_gate4": criterion_recovery(sdt["M2_gate4"], sdt["PICK"], sdt["ISO"]),
        },
        "ta_false_choice": ta_fc,
        "tp_hit_aligned": tp_hit,
        "sdt": sdt,
        "sdt_diffs": sdt_diffs,
    }


def _analyze_math_haiku_m1(
    root: Path,
    v1_root: Path,
    rng: random.Random,
    n_boot: int,
) -> Dict[str, Any]:
    c7_dir = root / "exps" / "c7_mitigation"
    m2_haiku_jobs = load_jsonl(c7_dir / "jobs_math_haiku_m2.jsonl")
    tb_jobs = load_jsonl(c7_dir / "jobs_math_haiku_c3_m1_tiebreak.jsonl")
    tb_by_pool = {j["pool"]: j for j in tb_jobs}
    tb_raw_dir = c7_dir / "raw_math_haiku_m1_tiebreak"

    pids = sorted({j["pid"] for j in m2_haiku_jobs})
    n_problems = len(pids)
    n_pools = len(m2_haiku_jobs)

    stage1_counts: Dict[str, int] = {"k_0": 0, "k_1": 0, "k_2": 0}
    n_tb_expected = len(tb_jobs)
    n_tb_files = 0
    n_tb_ok = 0
    n_tb_parsed = 0
    tb_none_count = 0

    tb_choices: Dict[str, Optional[int]] = {}
    for tbj in tb_jobs:
        fp = tb_raw_dir / f"{tbj['id']}.json"
        rec = read_v2_record(fp)
        if rec is not None:
            n_tb_files += 1
        ch: Optional[int] = None
        if is_v2_ok(rec):
            n_tb_ok += 1
            ch = parsers.choice(rec.get("text"), int(tbj["n_cands"]))
            if ch is not None:
                n_tb_parsed += 1
                if ch == 0:
                    tb_none_count += 1
        tb_choices[tbj["pool"]] = ch

    ta_vals: Dict[str, Dict[str, Optional[float]]] = {p: {} for p in pids}
    tp_vals: Dict[str, Dict[str, Optional[float]]] = {p: {} for p in pids}

    for job in m2_haiku_jobs:
        pid = job["pid"]
        pool_id = job["pool"]
        kind = job["kind"]
        rpos = job.get("right_pos_1idx")
        cids = list(job["cids"])

        iso_v = [v1_haiku_iso_verdict(v1_root, cid) for cid in cids]
        pick_v = v1_haiku_pick_choice(v1_root, pool_id, kind, 3)

        m1_choice: Optional[int] = None
        if all(v is not None for v in iso_v):
            accepted = [idx for idx, v in enumerate(iso_v, 1) if v is True]
            k = len(accepted)
            k_key = f"k_{k}"
            stage1_counts[k_key] = stage1_counts.get(k_key, 0) + 1
            if k == 0:
                m1_choice = 0
            elif k == 1:
                m1_choice = accepted[0]
            else:
                tbj = tb_by_pool.get(pool_id)
                tb_ch = tb_choices.get(pool_id)
                if tbj is not None and tb_ch is not None:
                    if tb_ch == 0:
                        m1_choice = 0
                    else:
                        orig_positions = tbj["accepted_orig_positions_1idx"]
                        m1_choice = int(orig_positions[tb_ch - 1])

        if kind == "TA":
            ta_vals[pid]["M1"] = (1.0 if m1_choice > 0 else 0.0) if m1_choice is not None else None
            ta_vals[pid]["PICK"] = (1.0 if pick_v > 0 else 0.0) if pick_v is not None else None
            ta_vals[pid]["ISO"] = aligned_from_verdicts(iso_v, None, is_tp=False)
        else:
            tp_vals[pid]["M1"] = (1.0 if m1_choice == rpos else 0.0) if (m1_choice is not None and rpos is not None) else None
            tp_vals[pid]["PICK"] = (1.0 if pick_v == rpos else 0.0) if (pick_v is not None and rpos is not None) else None
            tp_vals[pid]["ISO"] = aligned_from_verdicts(iso_v, rpos, is_tp=True)

    arms = ("M1", "PICK", "ISO")
    ta_fc = {
        a: boot_rate_summary([float(ta_vals[p][a]) for p in pids if ta_vals[p].get(a) is not None], rng, n_boot)
        for a in arms
    }
    tp_hit = {
        a: boot_rate_summary([float(tp_vals[p][a]) for p in pids if tp_vals[p].get(a) is not None], rng, n_boot)
        for a in arms
    }
    paired_by_arm = {
        a: [p for p in pids if ta_vals[p].get(a) is not None and tp_vals[p].get(a) is not None]
        for a in arms
    }
    sdt = {
        a: boot_sdt_summary(
            [float(tp_vals[p][a]) for p in paired_by_arm[a]],
            [float(ta_vals[p][a]) for p in paired_by_arm[a]],
            rng,
            n_boot,
        )
        for a in arms
    }
    diff_specs = (
        ("M1_minus_PICK", "M1", "PICK"),
        ("M1_minus_ISO", "M1", "ISO"),
        ("PICK_minus_ISO", "PICK", "ISO"),
    )
    sdt_diffs: Dict[str, Any] = {}
    for dname, a, b in diff_specs:
        both = [
            p for p in pids
            if (
                ta_vals[p].get(a) is not None
                and tp_vals[p].get(a) is not None
                and ta_vals[p].get(b) is not None
                and tp_vals[p].get(b) is not None
            )
        ]
        sdt_diffs[dname] = boot_sdt_diff(
            [float(tp_vals[p][a]) for p in both],
            [float(ta_vals[p][a]) for p in both],
            [float(tp_vals[p][b]) for p in both],
            [float(ta_vals[p][b]) for p in both],
            rng,
            n_boot,
        )

    return {
        "status": arm_status_label(n_tb_ok, n_tb_expected) if n_tb_expected > 0 else "complete",
        "n_problems": n_problems,
        "stage1_counts": stage1_counts,
        "n_tiebreak_expected": n_tb_expected,
        "n_tiebreak_files": n_tb_files,
        "n_tiebreak_ok": n_tb_ok,
        "n_tiebreak_parsed": n_tb_parsed,
        "tiebreak_parse_rate": (n_tb_parsed / n_tb_ok) if n_tb_ok > 0 else None,
        "tiebreak_none_count": tb_none_count,
        "extra_calls_per_pool": (n_tb_expected / n_pools) if n_pools > 0 else None,
        "n_paired_m1": len(paired_by_arm["M1"]),
        "criterion_recovery_frac": criterion_recovery(sdt["M1"], sdt["PICK"], sdt["ISO"]),
        "ta_false_choice": ta_fc,
        "tp_hit_aligned": tp_hit,
        "sdt": sdt,
        "sdt_diffs": sdt_diffs,
    }


def _analyze_math_haiku_m3_foil(
    root: Path,
    v1_root: Path,
    rng: random.Random,
    n_boot: int,
) -> Dict[str, Any]:
    c7_dir = root / "exps" / "c7_mitigation"
    jobs = load_jsonl(c7_dir / "jobs_math_haiku_m3_foil.jsonl")
    m2_haiku_jobs = load_jsonl(c7_dir / "jobs_math_haiku_m2.jsonl")
    orig_pool_by_key = {(j["pid"], j["kind"]): j for j in m2_haiku_jobs}
    raw_dir = c7_dir / "raw_math_haiku_m3_foil"

    n_expected = len(jobs)
    n_files = 0
    n_ok = 0
    n_parsed = 0

    pids = sorted({j["pid"] for j in jobs})
    foil_ta: List[float] = []
    foil_tp: List[float] = []
    foil_all: List[float] = []
    real_wrong_ta: List[float] = []
    any_fc_ta: List[float] = []
    tp_hit_m3: List[float] = []

    ta_vals: Dict[str, Dict[str, Optional[float]]] = {p: {} for p in pids}
    tp_vals: Dict[str, Dict[str, Optional[float]]] = {p: {} for p in pids}

    for job in jobs:
        pid = job["pid"]
        pool_id = job["pool"]
        kind = job["kind"]
        n_cands = int(job["n_cands"])
        foil_pos = int(job["foil_pos"])
        rpos = job.get("right_pos_1idx")

        fp = raw_dir / f"{job['id']}.json"
        rec = read_v2_record(fp)
        if rec is not None:
            n_files += 1
        ch: Optional[int] = None
        if is_v2_ok(rec):
            n_ok += 1
            ch = parsers.choice(rec.get("text"), n_cands)
            if ch is not None:
                n_parsed += 1

        orig_job = orig_pool_by_key[(pid, kind)]
        orig_cids = list(orig_job["cids"])
        orig_rpos = orig_job.get("right_pos_1idx")
        b_pick = v1_haiku_pick_choice(v1_root, pool_id, kind, 3)
        b_iso = [v1_haiku_iso_verdict(v1_root, cid) for cid in orig_cids]

        if ch is not None:
            is_foil = 1.0 if ch == foil_pos else 0.0
            foil_all.append(is_foil)
            if kind == "TA":
                foil_ta.append(is_foil)
                rw = 1.0 if (ch > 0 and ch != foil_pos) else 0.0
                af = 1.0 if ch > 0 else 0.0
                real_wrong_ta.append(rw)
                any_fc_ta.append(af)
                ta_vals[pid]["M3_any_fa"] = af
                ta_vals[pid]["M3_real_wrong_fa"] = rw
            else:
                foil_tp.append(is_foil)
                hit = 1.0 if ch == rpos else 0.0
                tp_hit_m3.append(hit)
                tp_vals[pid]["M3_any_fa"] = hit
                tp_vals[pid]["M3_real_wrong_fa"] = hit
        else:
            if kind == "TA":
                ta_vals[pid]["M3_any_fa"] = None
                ta_vals[pid]["M3_real_wrong_fa"] = None
            else:
                tp_vals[pid]["M3_any_fa"] = None
                tp_vals[pid]["M3_real_wrong_fa"] = None

        if kind == "TA":
            ta_vals[pid]["PICK"] = (1.0 if b_pick > 0 else 0.0) if b_pick is not None else None
            ta_vals[pid]["ISO"] = aligned_from_verdicts(b_iso, None, is_tp=False)
        else:
            tp_vals[pid]["PICK"] = (1.0 if b_pick == orig_rpos else 0.0) if (b_pick is not None and orig_rpos is not None) else None
            tp_vals[pid]["ISO"] = aligned_from_verdicts(b_iso, orig_rpos, is_tp=True)

    arms = ("M3_any_fa", "M3_real_wrong_fa", "PICK", "ISO")
    ta_fc = {
        a: boot_rate_summary([float(ta_vals[p][a]) for p in pids if ta_vals[p].get(a) is not None], rng, n_boot)
        for a in arms
    }
    tp_hit = {
        a: boot_rate_summary([float(tp_vals[p][a]) for p in pids if tp_vals[p].get(a) is not None], rng, n_boot)
        for a in arms
    }
    paired_by_arm = {
        a: [p for p in pids if ta_vals[p].get(a) is not None and tp_vals[p].get(a) is not None]
        for a in arms
    }
    sdt = {
        a: boot_sdt_summary(
            [float(tp_vals[p][a]) for p in paired_by_arm[a]],
            [float(ta_vals[p][a]) for p in paired_by_arm[a]],
            rng,
            n_boot,
        )
        for a in arms
    }
    diff_specs = (
        ("M3_any_fa_minus_PICK", "M3_any_fa", "PICK"),
        ("M3_any_fa_minus_ISO", "M3_any_fa", "ISO"),
        ("M3_real_wrong_fa_minus_PICK", "M3_real_wrong_fa", "PICK"),
        ("M3_real_wrong_fa_minus_ISO", "M3_real_wrong_fa", "ISO"),
    )
    sdt_diffs: Dict[str, Any] = {}
    for dname, a, b in diff_specs:
        both = [
            p for p in pids
            if (
                ta_vals[p].get(a) is not None
                and tp_vals[p].get(a) is not None
                and ta_vals[p].get(b) is not None
                and tp_vals[p].get(b) is not None
            )
        ]
        sdt_diffs[dname] = boot_sdt_diff(
            [float(tp_vals[p][a]) for p in both],
            [float(ta_vals[p][a]) for p in both],
            [float(tp_vals[p][b]) for p in both],
            [float(ta_vals[p][b]) for p in both],
            rng,
            n_boot,
        )

    return {
        "status": arm_status_label(n_ok, n_expected),
        "n_expected_calls": n_expected,
        "n_files": n_files,
        "n_ok": n_ok,
        "n_parsed": n_parsed,
        "parse_rate": (n_parsed / n_ok) if n_ok > 0 else None,
        "n_paired_m3": len(paired_by_arm["M3_any_fa"]),
        "foil_pick_rate_ta": boot_rate_summary(foil_ta, rng, n_boot),
        "foil_pick_rate_tp": boot_rate_summary(foil_tp, rng, n_boot),
        "foil_pick_rate_all": boot_rate_summary(foil_all, rng, n_boot),
        "real_wrong_pick_rate_ta": boot_rate_summary(real_wrong_ta, rng, n_boot),
        "any_false_choice_rate_ta": boot_rate_summary(any_fc_ta, rng, n_boot),
        "tp_hit_rate": boot_rate_summary(tp_hit_m3, rng, n_boot),
        "ta_false_choice": ta_fc,
        "tp_hit_aligned": tp_hit,
        "sdt": sdt,
        "sdt_diffs": sdt_diffs,
    }


def analyze_c7_mitigation(
    root: Path,
    v1_root: Path,
    science_cache: Dict[str, Dict[str, Any]],
    math_cache: Dict[str, Dict[str, Any]],
    rng: random.Random,
    n_boot: int,
) -> Dict[str, Any]:
    c7_dir = root / "exps" / "c7_mitigation"
    sci_jobs = load_jsonl(c7_dir / "jobs_science_m2.jsonl")
    math_cross_jobs = load_jsonl(c7_dir / "jobs_math_cross_m2.jsonl")
    math_haiku_jobs = load_jsonl(c7_dir / "jobs_math_haiku_m2.jsonl")

    science_m2: Dict[str, Any] = {}
    for model in ("gptoss", "gemini", "gemini_low", "hydrogen", "haiku"):
        sc = science_cache[model]
        pick_map = sc["pick_map"]
        iso_map = sc["iso_map"]
        science_m2[model] = _analyze_m2_panel(
            jobs=sci_jobs,
            raw_dir=c7_dir / f"raw_science_{model}_m2",
            id_field="item",
            baseline_pick_fn=lambda j, pm=pick_map: pm.get(j["pool"]),
            baseline_iso_fn=lambda j, im=iso_map: [im.get(cid) for cid in j["cids"]],
            rng=rng,
            n_boot=n_boot,
        )

    math_m2: Dict[str, Any] = {}
    for model in ("gptoss", "gemini"):
        mc = math_cache[model]
        pick_map = mc["pick_map"]
        iso_map = mc["iso_map"]
        math_m2[model] = _analyze_m2_panel(
            jobs=math_cross_jobs,
            raw_dir=c7_dir / f"raw_math_{model}_m2",
            id_field="pid",
            baseline_pick_fn=lambda j, pm=pick_map: pm.get(j["pool"]),
            baseline_iso_fn=lambda j, im=iso_map: [im.get(cid) for cid in j["cids"]],
            rng=rng,
            n_boot=n_boot,
        )

    math_m2["haiku"] = _analyze_m2_panel(
        jobs=math_haiku_jobs,
        raw_dir=c7_dir / "raw_math_haiku_m2",
        id_field="pid",
        baseline_pick_fn=lambda j: v1_haiku_pick_choice(v1_root, j["pool"], j["kind"], 3),
        baseline_iso_fn=lambda j: [v1_haiku_iso_verdict(v1_root, cid) for cid in j["cids"]],
        rng=rng,
        n_boot=n_boot,
    )

    return {
        "science_m2": science_m2,
        "math_m2": math_m2,
        "math_haiku_m1": _analyze_math_haiku_m1(root, v1_root, rng, n_boot),
        "math_haiku_m3_foil": _analyze_math_haiku_m3_foil(root, v1_root, rng, n_boot),
    }


# ---------------------------------------------------------------------------
# Exact Binomial / McNemar / Science Boundary Sensitivity / Human Audit
# ---------------------------------------------------------------------------

def _clopper_pearson_ci95(k: int, n: int) -> List[float]:
    """Exact two-sided 95% Clopper-Pearson confidence interval for k/n."""
    if n <= 0:
        return [0.0, 1.0]
    if k <= 0:
        lo = 0.0
    else:
        a, b = 0.0, 1.0
        for _ in range(64):
            m = 0.5 * (a + b)
            tail = sum(math.comb(n, j) * (m ** j) * ((1.0 - m) ** (n - j)) for j in range(k, n + 1))
            if tail < 0.025:
                a = m
            else:
                b = m
        lo = 0.5 * (a + b)
    if k >= n:
        hi = 1.0
    else:
        a, b = 0.0, 1.0
        for _ in range(64):
            m = 0.5 * (a + b)
            tail = sum(math.comb(n, j) * (m ** j) * ((1.0 - m) ** (n - j)) for j in range(0, k + 1))
            if tail < 0.025:
                b = m
            else:
                a = m
        hi = 0.5 * (a + b)
    return [lo, hi]


def _exact_mcnemar_p(n10: int, n01: int) -> float:
    """Exact two-sided paired McNemar binomial p-value on discordant pairs."""
    m = n10 + n01
    if m <= 0:
        return 1.0
    k_min = min(n10, n01)
    tail = sum(math.comb(m, j) for j in range(k_min + 1)) / (2 ** m)
    return min(1.0, 2.0 * tail)


def _sdt_from_counts(tp_k: int, tp_n: int, ta_k: int, ta_n: int, mode: str) -> Dict[str, Any]:
    """Compute SDT d' and c from integer counts under raw or boundary-corrected rates."""
    if tp_n <= 0 or ta_n <= 0:
        return {"h": None, "f": None, "d_prime": None, "c": None}
    if mode == "raw":
        h = tp_k / tp_n
        f = ta_k / ta_n
        if h <= 0.0 or h >= 1.0 or f <= 0.0 or f >= 1.0:
            return {"h": h, "f": f, "d_prime": None, "c": None}
    elif mode == "hautus_05_n1":
        h = (tp_k + 0.5) / (tp_n + 1.0)
        f = (ta_k + 0.5) / (ta_n + 1.0)
    elif mode == "macmillan_05_n":
        h = (0.5 / tp_n) if tp_k == 0 else ((1.0 - 0.5 / tp_n) if tp_k == tp_n else (tp_k / tp_n))
        f = (0.5 / ta_n) if ta_k == 0 else ((1.0 - 0.5 / ta_n) if ta_k == ta_n else (ta_k / ta_n))
    elif mode == "quarter_025_n":
        h = (0.25 / tp_n) if tp_k == 0 else ((1.0 - 0.25 / tp_n) if tp_k == tp_n else (tp_k / tp_n))
        f = (0.25 / ta_n) if ta_k == 0 else ((1.0 - 0.25 / ta_n) if ta_k == ta_n else (ta_k / ta_n))
    else:
        raise ValueError(f"Unknown SDT correction mode: {mode}")
    zh = norm_ppf(h)
    zf = norm_ppf(f)
    return {"h": h, "f": f, "d_prime": zh - zf, "c": -0.5 * (zh + zf)}


def _science_raw_counts_and_exact_tests(
    items: Sequence[str],
    ta_map: Dict[str, Dict[str, Optional[float]]],
    tp_al_map: Dict[str, Dict[str, Optional[float]]],
    tp_st_map: Dict[str, Dict[str, Optional[float]]],
) -> Dict[str, Any]:
    """Compute raw integer counts, exact McNemar tests, and boundary SDT sensitivity for science."""
    arms_out: Dict[str, Any] = {}
    arm_counts: Dict[str, Dict[str, int]] = {}
    for arm in ("PICK", "ISO", "EACH"):
        ta_vals = [1 if ta_map[it][arm] > 0.0 else 0 for it in items if ta_map[it].get(arm) is not None]
        tp_al_vals = [1 if tp_al_map[it][arm] > 0.0 else 0 for it in items if tp_al_map[it].get(arm) is not None]
        tp_st_vals = [1 if tp_st_map[it][arm] > 0.0 else 0 for it in items if tp_st_map[it].get(arm) is not None]
        ta_k, ta_n = sum(ta_vals), len(ta_vals)
        tpa_k, tpa_n = sum(tp_al_vals), len(tp_al_vals)
        tps_k, tps_n = sum(tp_st_vals), len(tp_st_vals)
        arm_counts[arm] = {
            "ta_k": ta_k,
            "ta_n": ta_n,
            "tp_aligned_k": tpa_k,
            "tp_aligned_n": tpa_n,
            "tp_strict_k": tps_k,
            "tp_strict_n": tps_n,
        }
        boundary_al = (ta_n > 0 and ta_k in (0, ta_n)) or (tpa_n > 0 and tpa_k in (0, tpa_n))
        boundary_st = (ta_n > 0 and ta_k in (0, ta_n)) or (tps_n > 0 and tps_k in (0, tps_n))
        arms_out[arm] = {
            "ta_k": ta_k,
            "ta_n": ta_n,
            "ta_rate": (ta_k / ta_n) if ta_n else None,
            "ta_ci95_exact": _clopper_pearson_ci95(ta_k, ta_n) if ta_n else None,
            "tp_aligned_k": tpa_k,
            "tp_aligned_n": tpa_n,
            "tp_aligned_rate": (tpa_k / tpa_n) if tpa_n else None,
            "tp_strict_k": tps_k,
            "tp_strict_n": tps_n,
            "tp_strict_rate": (tps_k / tps_n) if tps_n else None,
            "boundary_hit_aligned": boundary_al,
            "boundary_hit_strict": boundary_st,
            "unsmoothed_sdt_aligned": _sdt_from_counts(tpa_k, tpa_n, ta_k, ta_n, "raw"),
            "unsmoothed_sdt_strict": _sdt_from_counts(tps_k, tps_n, ta_k, ta_n, "raw"),
        }

    def _paired_mcnemar(map_ref: Dict[str, Dict[str, Optional[float]]], arm1: str, arm2: str) -> Dict[str, Any]:
        n10 = 0
        n01 = 0
        n11 = 0
        n00 = 0
        for it in items:
            v1 = map_ref[it].get(arm1)
            v2 = map_ref[it].get(arm2)
            if v1 is None or v2 is None:
                continue
            b1 = 1 if v1 > 0.0 else 0
            b2 = 1 if v2 > 0.0 else 0
            if b1 == 1 and b2 == 0:
                n10 += 1
            elif b1 == 0 and b2 == 1:
                n01 += 1
            elif b1 == 1 and b2 == 1:
                n11 += 1
            else:
                n00 += 1
        return {
            "n_paired": n10 + n01 + n11 + n00,
            "n_10": n10,
            "n_01": n01,
            "n_11": n11,
            "n_00": n00,
            "exact_mcnemar_p": _exact_mcnemar_p(n10, n01),
        }

    mcnemar_out = {
        "TA_PICK_vs_ISO_any": _paired_mcnemar(ta_map, "PICK", "ISO"),
        "TA_PICK_vs_EACH_any": _paired_mcnemar(ta_map, "PICK", "EACH"),
        "TP_aligned_PICK_vs_ISO": _paired_mcnemar(tp_al_map, "PICK", "ISO"),
        "TP_strict_PICK_vs_ISO": _paired_mcnemar(tp_st_map, "PICK", "ISO"),
    }

    clip_sens: Dict[str, Any] = {}
    pc = arm_counts["PICK"]
    ic = arm_counts["ISO"]
    for mode in ("hautus_05_n1", "macmillan_05_n", "quarter_025_n"):
        p_al = _sdt_from_counts(pc["tp_aligned_k"], pc["tp_aligned_n"], pc["ta_k"], pc["ta_n"], mode)
        i_al = _sdt_from_counts(ic["tp_aligned_k"], ic["tp_aligned_n"], ic["ta_k"], ic["ta_n"], mode)
        i_st = _sdt_from_counts(ic["tp_strict_k"], ic["tp_strict_n"], ic["ta_k"], ic["ta_n"], mode)
        clip_sens[mode] = {
            "aligned_delta_d": (p_al["d_prime"] - i_al["d_prime"]) if (p_al["d_prime"] is not None and i_al["d_prime"] is not None) else None,
            "aligned_delta_c": (p_al["c"] - i_al["c"]) if (p_al["c"] is not None and i_al["c"] is not None) else None,
            "strict_delta_d": (p_al["d_prime"] - i_st["d_prime"]) if (p_al["d_prime"] is not None and i_st["d_prime"] is not None) else None,
            "strict_delta_c": (p_al["c"] - i_st["c"]) if (p_al["c"] is not None and i_st["c"] is not None) else None,
        }

    return {
        "arms": arms_out,
        "exact_mcnemar": mcnemar_out,
        "sdt_clipping_sensitivity_PICK_minus_ISO": clip_sens,
    }


def _c3_unsolved_sdt_snapshot(
    v1_root: Path,
    ta_pids: Sequence[str],
    tp_pids: Sequence[str],
    ta_map: Dict[str, Dict[str, Any]],
    tp_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute C3 Haiku UNSOLVED PICK vs ISO rates and Hautus SDT on specified TA and TP pid lists."""
    p_ta_vals: List[float] = []
    i_ta_vals: List[float] = []
    p_tp_vals: List[float] = []
    i_tp_al_vals: List[float] = []
    i_tp_st_vals: List[float] = []

    for pid in ta_pids:
        pool = ta_map[pid]
        pc = v1_haiku_pick_choice(v1_root, pool["pool"], "TA", 3)
        ivs = [v1_haiku_iso_verdict(v1_root, c["cid"]) for c in pool["cands"]]
        if pc is not None:
            p_ta_vals.append(1.0 if pc > 0 else 0.0)
        al = aligned_from_verdicts(ivs, None, is_tp=False)
        if al is not None:
            i_ta_vals.append(al)

    for pid in tp_pids:
        if pid not in tp_map:
            continue
        pool = tp_map[pid]
        rpos = right_pos_1idx(pool)
        pc = v1_haiku_pick_choice(v1_root, pool["pool"], "TP", 3)
        ivs = [v1_haiku_iso_verdict(v1_root, c["cid"]) for c in pool["cands"]]
        if pc is not None and rpos is not None:
            p_tp_vals.append(1.0 if pc == rpos else 0.0)
        al = aligned_from_verdicts(ivs, rpos, is_tp=True)
        st = strict_from_verdicts(ivs, rpos)
        if al is not None:
            i_tp_al_vals.append(al)
        if st is not None:
            i_tp_st_vals.append(st)

    p_sdt = hautus_sdt_point(p_tp_vals, p_ta_vals) if (p_tp_vals and p_ta_vals) else None
    ia_sdt = hautus_sdt_point(i_tp_al_vals, i_ta_vals) if (i_tp_al_vals and i_ta_vals) else None
    is_sdt = hautus_sdt_point(i_tp_st_vals, i_ta_vals) if (i_tp_st_vals and i_ta_vals) else None
    return {
        "n_ta": len(p_ta_vals),
        "n_tp": len(p_tp_vals),
        "pick_ta_fa": (sum(p_ta_vals) / len(p_ta_vals)) if p_ta_vals else None,
        "iso_ta_fa": (sum(i_ta_vals) / len(i_ta_vals)) if i_ta_vals else None,
        "pick_tp_hit": (sum(p_tp_vals) / len(p_tp_vals)) if p_tp_vals else None,
        "iso_tp_aligned_hit": (sum(i_tp_al_vals) / len(i_tp_al_vals)) if i_tp_al_vals else None,
        "iso_tp_strict_hit": (sum(i_tp_st_vals) / len(i_tp_st_vals)) if i_tp_st_vals else None,
        "pick_d_prime": p_sdt["d_prime"] if p_sdt else None,
        "pick_c": p_sdt["c"] if p_sdt else None,
        "iso_aligned_d_prime": ia_sdt["d_prime"] if ia_sdt else None,
        "iso_aligned_c": ia_sdt["c"] if ia_sdt else None,
        "iso_strict_d_prime": is_sdt["d_prime"] if is_sdt else None,
        "iso_strict_c": is_sdt["c"] if is_sdt else None,
        "delta_d_aligned": (p_sdt["d_prime"] - ia_sdt["d_prime"]) if (p_sdt and ia_sdt) else None,
        "delta_c_aligned": (p_sdt["c"] - ia_sdt["c"]) if (p_sdt and ia_sdt) else None,
        "delta_d_strict": (p_sdt["d_prime"] - is_sdt["d_prime"]) if (p_sdt and is_sdt) else None,
        "delta_c_strict": (p_sdt["c"] - is_sdt["c"]) if (p_sdt and is_sdt) else None,
    }


def analyze_human_audit(root: Path, v1_root: Path) -> Dict[str, Any]:
    """Ingest audit/human_audit_results.json if present; compute exact Clopper-Pearson CIs and sensitivity."""
    audit_path = root / "audit" / "human_audit_results.json"
    if not audit_path.is_file():
        return {
            "status": "pending_user",
            "file": "audit/human_audit_results.json",
            "sections": {},
            "sensitivity": None,
        }

    raw = load_json(audit_path)
    responses = raw.get("responses", {})

    # Reconstruct exact item_id -> pid mapping from C3 ground truth files
    c3_dir = v1_root / "exps" / "c3"
    hand_map = {
        r["id"]: r["decision"].strip().lower()
        for r in csv.DictReader((c3_dir / "hand_checks.csv").open(encoding="utf-8"))
    }
    audit_map = {
        r["pid"]: r["audited_stratum"].strip().upper()
        for r in csv.DictReader((c3_dir / "audit_unsolved.csv").open(encoding="utf-8"))
    }

    sec_a_counts: Counter = Counter()
    hidden_right_pids: List[str] = []
    broken_prompt_pids: List[str] = []
    sec_b_counts: Counter = Counter()
    sec_b_agree = 0
    sec_b_decided = 0
    sec_c_counts: Counter = Counter()
    sec_c_agree = 0
    sec_c_decided = 0

    for item_id, rec in sorted(responses.items()):
        sec = rec.get("section", "")
        verdict = (rec.get("verdict") or "").strip()
        if not verdict:
            continue
        if sec == "a":
            sec_a_counts[verdict] += 1
            pid = item_id.split("_", 2)[2]
            if verdict == "Hidden equivalent right answer":
                hidden_right_pids.append(pid)
            elif verdict == "Broken prompt":
                broken_prompt_pids.append(pid)
        elif sec == "b":
            sec_b_counts[verdict] += 1
            solve_id = item_id.split("_", 2)[2]
            if verdict in ("Correct", "Wrong"):
                sec_b_decided += 1
                ai_dec = hand_map.get(solve_id, "")
                if (verdict == "Correct" and ai_dec == "correct") or (verdict == "Wrong" and ai_dec == "wrong"):
                    sec_b_agree += 1
        elif sec == "c":
            sec_c_counts[verdict] += 1
            pid = item_id.split("_", 2)[2]
            if verdict != "Unsure":
                sec_c_decided += 1
                human_stratum = verdict.split(" ", 1)[0].strip().upper()
                if human_stratum == audit_map.get(pid, ""):
                    sec_c_agree += 1

    a_done = sum(sec_a_counts.values())
    a_decided = a_done - sec_a_counts.get("Unsure", 0)
    a_flagged = len(hidden_right_pids) + len(broken_prompt_pids)
    b_done = sum(sec_b_counts.values())
    c_done = sum(sec_c_counts.values())

    # Sensitivity recalculation on C3 corrected Haiku UNSOLVED
    c3_pools = load_json(v1_root / "banks" / "locked_c3" / "pools.json")
    ta_map = {p["pid"]: p for p in c3_pools if p["kind"] == "TA"}
    tp_map = {p["pid"]: p for p in c3_pools if p["kind"] == "TP"}
    c4_bank = load_json(root / "banks" / "locked_v2" / "c4_haiku_compute.json")
    corr_ta_pids = sorted({p["pid"] for p in c4_bank["pools"] if p["kind"] == "TA"})
    corr_tp_pids = sorted({p["pid"] for p in c4_bank["pools"] if p["kind"] == "TP"})

    hidden_set = set(hidden_right_pids)
    broken_set = set(broken_prompt_pids)
    flagged_set = hidden_set | broken_set

    c6_bank = load_json(root / "banks" / "locked_v2" / "c6_crossvendor_math.json")
    c6_pids = {p["pid"] for p in c6_bank["pools"]}

    sensitivity = {
        "flagged_in_c4_unsolved": sorted(flagged_set & set(corr_ta_pids)),
        "flagged_in_c6_crossvendor": sorted(flagged_set & c6_pids),
        "baseline_c3_unsolved": _c3_unsolved_sdt_snapshot(v1_root, corr_ta_pids, corr_tp_pids, ta_map, tp_map),
        "drop_flagged": _c3_unsolved_sdt_snapshot(
            v1_root,
            [p for p in corr_ta_pids if p not in flagged_set],
            [p for p in corr_tp_pids if p not in flagged_set],
            ta_map,
            tp_map,
        ),
        "relabel_hidden_right_drop_broken": _c3_unsolved_sdt_snapshot(
            v1_root,
            [p for p in corr_ta_pids if p not in flagged_set],
            [p for p in corr_tp_pids if p not in broken_set],
            ta_map,
            tp_map,
        ),
    }

    return {
        "status": "complete" if (a_done == 50 and b_done == 22 and c_done == 20) else "partial",
        "file": "audit/human_audit_results.json",
        "exported_at": raw.get("exported_at"),
        "sections": {
            "section_a": {
                "n_completed": a_done,
                "n_decided": a_decided,
                "counts": dict(sec_a_counts),
                "n_hidden_right": len(hidden_right_pids),
                "n_broken_prompt": len(broken_prompt_pids),
                "n_flagged": a_flagged,
                "error_rate_decided": (a_flagged / a_decided) if a_decided else None,
                "error_rate_decided_ci95_exact": _clopper_pearson_ci95(a_flagged, a_decided) if a_decided else None,
                "error_rate_all": (a_flagged / a_done) if a_done else None,
                "error_rate_all_ci95_exact": _clopper_pearson_ci95(a_flagged, a_done) if a_done else None,
                "hidden_right_pids": sorted(hidden_right_pids),
                "broken_prompt_pids": sorted(broken_prompt_pids),
            },
            "section_b": {
                "n_completed": b_done,
                "n_decided": sec_b_decided,
                "counts": dict(sec_b_counts),
                "n_agree_with_ai": sec_b_agree,
                "agreement_rate": (sec_b_agree / sec_b_decided) if sec_b_decided else None,
                "agreement_rate_ci95_exact": _clopper_pearson_ci95(sec_b_agree, sec_b_decided) if sec_b_decided else None,
            },
            "section_c": {
                "n_completed": c_done,
                "n_decided": sec_c_decided,
                "counts": dict(sec_c_counts),
                "n_agree_with_ai": sec_c_agree,
                "agreement_rate": (sec_c_agree / sec_c_decided) if sec_c_decided else None,
                "agreement_rate_ci95_exact": _clopper_pearson_ci95(sec_c_agree, sec_c_decided) if sec_c_decided else None,
            },
        },
        "sensitivity": sensitivity,
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Independent dual-script analysis (analysis_a.py) for Lineups Without a Culprit v2."
    )
    p.add_argument(
        "--root",
        default=str(DEFAULT_ROOT),
        help="Path to v2-upgrade study root directory.",
    )
    p.add_argument(
        "--v1-root",
        default=str(DEFAULT_V1_ROOT),
        help="Path to v1 C3 repository root directory.",
    )
    p.add_argument(
        "--out",
        default=str(DEFAULT_ROOT / "results" / "results_a.json"),
        help="Output JSON path (default: results/results_a.json).",
    )
    p.add_argument(
        "--boot",
        type=int,
        default=DEFAULT_BOOT_N,
        help="Number of bootstrap resamples (default: 5000).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for paired bootstrap (default: 20261120).",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    v1_root = Path(args.v1_root).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (root / out_path).resolve()

    rng = random.Random(args.seed)
    n_boot = int(args.boot)

    c5_own = analyze_c5_own_removal(root, v1_root, rng, n_boot)
    c5_wells = analyze_c5_wells_removal(root, v1_root, rng, n_boot)
    c4_comp = analyze_c4_compute(root, v1_root, rng, n_boot)
    c9_sci, sci_cache = analyze_c9_science(root, rng, n_boot)
    c6_mth, mth_cache = analyze_c6_math(root, rng, n_boot)
    c7_mit = analyze_c7_mitigation(root, v1_root, sci_cache, mth_cache, rng, n_boot)
    h_audit = analyze_human_audit(root, v1_root)

    payload = {
        "meta": {
            "verifier": "analysis_a",
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bootstrap_resamples": n_boot,
            "seed": int(args.seed),
            "strict_mode": True,
            "independent_parsers": False,
            "independent_math_grader": False,
        },
        "c5_own_removal": c5_own,
        "c5_wells_removal": c5_wells,
        "c4_compute": c4_comp,
        "c9_science": c9_sci,
        "c6_math": c6_mth,
        "c7_mitigation": c7_mit,
        "human_audit": h_audit,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
