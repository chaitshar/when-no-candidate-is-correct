#!/usr/bin/env python3
"""Recursive numeric leaf comparator for dual-script verification (results_a vs results_b).

Pure Python 3.9 stdlib only. Classifies shared numeric leaves into:
  - count_or_rate: exact integer counts and deterministic raw rates (tol_count = 1e-9)
  - stat: deterministic SDT d'/c and analytical predictions (tol_stat = 1e-5)
  - ci: Monte Carlo bootstrap CIs and p-values (tol_ci = 0.02)
Exits 0 only on full agreement across all shared numeric leaves.
"""
import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")


def _is_num(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def classify_leaf(
    path: str,
    val_a: float,
    val_b: float,
    tol_count: float,
    tol_stat: float,
    tol_ci: float,
) -> Tuple[str, float]:
    """Classify a numeric leaf path into (tier_name, tolerance)."""
    low = path.lower()
    # Strip trailing list index like [0] to inspect the owning field name
    base = re.sub(r"\[\d+\]$", "", low)
    leaf = base.rsplit(".", 1)[-1]

    # 1. Monte Carlo bootstrap intervals and p-values
    ci_markers = ("ci95", "_ci", "ci_", "boot", "p_one_sided", "p_two_sided", "pval", "p_value")
    if any(m in leaf for m in ci_markers) or ".ci" in low:
        return "ci", tol_ci

    # 2. Deterministic SDT statistics, diffs, and analytical predictions
    stat_exact = {"c", "zh", "zf", "h_adj", "f_adj", "d_prime", "f_pred", "c_pred", "abs_err"}
    stat_markers = (
        "d_prime",
        "delta_d",
        "delta_c",
        "d_prime_diff",
        "c_diff",
        "c_crit",
        "c_iso",
        "c_pick",
        "c_each",
        "f_pred",
        "c_pred",
        "slope",
        "ols",
        "t_stat",
        "chi2",
        "se_",
    )
    if leaf in stat_exact or any(m in leaf for m in stat_markers):
        return "stat", tol_stat

    # 3. Exact integer counts and deterministic raw rates / medians / ratios
    if isinstance(val_a, int) and isinstance(val_b, int):
        return "count_or_rate", tol_count

    count_markers = (
        "h_raw",
        "f_raw",
        "h_diff",
        "f_diff",
        "f_obs",
        "fa_",
        "hit_",
        "parse_rate",
        "parsed",
        "mean",
        "median",
        "ratio",
        "tokens",
        "d_c3",
        "d_c5",
        "effect_reduction",
        "choosing_rate",
        "abstain_rate",
        "right_given",
        "iso_right",
        "iso_wrong",
        "baseline",
        "diff_",
    )
    count_exact = {"n", "fa", "hit", "pick", "iso", "iso_any", "each", "rate", "diff"}
    if leaf in count_exact or leaf.startswith("n_") or any(m in leaf for m in count_markers):
        return "count_or_rate", tol_count

    # Fallback for any other float leaf
    return "stat", tol_stat


def compare_trees(
    a: Any,
    b: Any,
    path: str,
    tol_count: float,
    tol_stat: float,
    tol_ci: float,
    checked: List[Dict[str, Any]],
    mismatches: List[Dict[str, Any]],
    skipped_top_only: List[str],
) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        keys_a = set(a.keys())
        keys_b = set(b.keys())
        if not path:
            for k in sorted((keys_a ^ keys_b) - {"meta"}):
                side = "A_only" if k in keys_a else "B_only"
                skipped_top_only.append(f"{k}({side})")
        for k in sorted(keys_a & keys_b):
            if not path and k == "meta":
                continue
            sub_path = f"{path}.{k}" if path else k
            compare_trees(
                a[k],
                b[k],
                sub_path,
                tol_count,
                tol_stat,
                tol_ci,
                checked,
                mismatches,
                skipped_top_only,
            )
        return

    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            if all(_is_num(x) for x in a) and all(_is_num(y) for y in b):
                mismatches.append(
                    {
                        "path": path,
                        "tier": "count_or_rate",
                        "tol": tol_count,
                        "a": f"len={len(a)}",
                        "b": f"len={len(b)}",
                        "diff": None,
                        "reason": "list length mismatch",
                    }
                )
            return
        for idx, (va, vb) in enumerate(zip(a, b)):
            compare_trees(
                va,
                vb,
                f"{path}[{idx}]",
                tol_count,
                tol_stat,
                tol_ci,
                checked,
                mismatches,
                skipped_top_only,
            )
        return

    if _is_num(a) and _is_num(b):
        fa = float(a)
        fb = float(b)
        tier, tol = classify_leaf(path, a, b, tol_count, tol_stat, tol_ci)
        if math.isnan(fa) or math.isnan(fb) or math.isinf(fa) or math.isinf(fb):
            mismatches.append(
                {
                    "path": path,
                    "tier": tier,
                    "tol": tol,
                    "a": a,
                    "b": b,
                    "diff": None,
                    "reason": "non-finite float",
                }
            )
            return
        diff = abs(fa - fb)
        rec = {
            "path": path,
            "tier": tier,
            "tol": tol,
            "a": a,
            "b": b,
            "diff": diff,
        }
        checked.append(rec)
        if diff > tol:
            rec["reason"] = f"diff {diff:.6g} > tol {tol:.6g}"
            mismatches.append(rec)
        return

    if type(a) is bool and type(b) is bool and a != b:
        mismatches.append(
            {
                "path": path,
                "tier": "count_or_rate",
                "tol": 0.0,
                "a": a,
                "b": b,
                "diff": None,
                "reason": "boolean mismatch",
            }
        )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare results_a.json and results_b.json on shared numeric leaves.")
    p.add_argument("--a", default=str(DEFAULT_ROOT / "results" / "results_a.json"), help="Path to results_a.json.")
    p.add_argument("--b", default=str(DEFAULT_ROOT / "results" / "results_b.json"), help="Path to results_b.json.")
    p.add_argument("--tol-count", type=float, default=1e-9, help="Tolerance for exact counts/raw rates.")
    p.add_argument("--tol-stat", type=float, default=1e-5, help="Tolerance for deterministic SDT d'/c.")
    p.add_argument("--tol-ci", type=float, default=0.02, help="Tolerance for Monte Carlo bootstrap CIs.")
    p.add_argument("--allow-empty", action="store_true", help="Do not fail if 0 shared numeric leaves exist.")
    p.add_argument("--json-out", default=None, help="Optional path to write structured diff report JSON.")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    path_a = Path(args.a).resolve()
    path_b = Path(args.b).resolve()

    if not path_a.is_file():
        print(f"ERROR: missing {path_a}", file=sys.stderr)
        return 2
    if not path_b.is_file():
        print(f"ERROR: missing {path_b}", file=sys.stderr)
        return 2

    data_a = json.loads(path_a.read_text(encoding="utf-8"))
    data_b = json.loads(path_b.read_text(encoding="utf-8"))

    checked: List[Dict[str, Any]] = []
    mismatches: List[Dict[str, Any]] = []
    skipped_top: List[str] = []

    compare_trees(
        data_a,
        data_b,
        "",
        args.tol_count,
        args.tol_stat,
        args.tol_ci,
        checked,
        mismatches,
        skipped_top,
    )

    tiers = ("count_or_rate", "stat", "ci")
    tier_summary: Dict[str, Dict[str, Any]] = {}
    for t in tiers:
        t_rows = [r for r in checked if r["tier"] == t]
        t_bad = [r for r in mismatches if r["tier"] == t]
        max_d = max((r["diff"] for r in t_rows), default=0.0)
        tier_summary[t] = {
            "checked": len(t_rows),
            "mismatches": len(t_bad),
            "max_abs_diff": max_d,
        }

    print(f"Compared: A={path_a.name} vs B={path_b.name}")
    print(f"Shared numeric leaves checked: {len(checked)} | Mismatches: {len(mismatches)}")
    if skipped_top:
        print(f"Unshared top-level keys: {', '.join(skipped_top)}")
    for t in tiers:
        s = tier_summary[t]
        print(f"  {t:<14}: checked={s['checked']:<5} mismatches={s['mismatches']:<4} max_abs_diff={s['max_abs_diff']:.6g}")

    if mismatches:
        print("\nMISMATCHES:")
        for m in mismatches[:30]:
            print(
                f"  * {m['path']} [{m['tier']}]: A={m['a']} B={m['b']} "
                f"({m.get('reason', 'mismatch')})"
            )
        if len(mismatches) > 30:
            print(f"  ... and {len(mismatches) - 30} more")

    report = {
        "a": str(path_a),
        "b": str(path_b),
        "checked_count": len(checked),
        "mismatch_count": len(mismatches),
        "unshared_top_keys": skipped_top,
        "tiers": tier_summary,
        "mismatches": mismatches,
    }
    if args.json_out:
        out_p = Path(args.json_out).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if len(checked) == 0 and not args.allow_empty:
        print("ERROR: 0 shared numeric leaves found.", file=sys.stderr)
        return 1
    return 0 if len(mismatches) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
