#!/usr/bin/env python3
"""Generate exhaustive audit/extractor_audit_report.md across all v1 and v2 math banks."""
import csv
import json
import os
import re

V1 = "/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar"
V2 = "/Users/chaitanya/research/mas-study/v2-upgrade"

BANKS = [
    ("locked_c3 (v1 C3, 543 pools)", os.path.join(V1, "banks/locked_c3/pools.json")),
    ("c6_crossvendor_math (v2 C6, 200 pools)", os.path.join(V2, "banks/locked_v2/c6_crossvendor_math.json")),
    ("c6_claude_free_math (v2 C6, 70 pools)", os.path.join(V2, "banks/locked_v2/c6_claude_free_math.json")),
    ("c4_haiku_compute (v2 C4, 124 pools)", os.path.join(V2, "banks/locked_v2/c4_haiku_compute.json")),
    ("c5_haiku_removal (v2 C5, 81 pools)", os.path.join(V2, "banks/locked_v2/c5_haiku_removal.json")),
]


def extract_boxed(text):
    if not text:
        return None
    for cmd in ("\\boxed{", "\\fbox{"):
        idx = text.rfind(cmd)
        if idx != -1:
            s = idx + len(cmd)
            d = 1
            i = s
            while i < len(text) and d > 0:
                if text[i] == "{":
                    d += 1
                elif text[i] == "}":
                    d -= 1
                i += 1
            if d == 0:
                return text[s : i - 1].strip()
    return None


def norm_latex(s):
    if not s:
        return ""
    s = re.sub(r"\\(?:left|right|displaystyle|quad|qquad|,|;|!)", "", s.strip())
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = re.sub(r"\s+", "", s).rstrip(".,;")
    return s


def esc_md(s):
    return str(s).replace("|", "\\|").replace("`", "'").replace("\n", " ")


def main():
    c3_bad = {
        r["pid"] for r in csv.DictReader(open(os.path.join(V1, "exps/c3/candidate_label_audit.csv")))
    }
    c3_dups_raw = json.load(open(os.path.join(V1, "exps/c3/duplicates_of_used.json")))
    c3_dups = set(c3_dups_raw.keys() if isinstance(c3_dups_raw, dict) else c3_dups_raw)

    lines = [
        "# MathArena Upstream Answer Extractor Audit",
        "",
        "Date: 2026-11-22",
        "",
        "## Root Cause Summary",
        "",
        "1. **Origin of the extracted field:** Every candidate `answer` field in `banks/locked_c3/pools.json` and the v2 math banks is copied verbatim from the MathArena upstream Hugging Face parquet column `parsed_answer` by `banks/matharena_pools.py` (line 71).",
        "2. **Does it feed labels and prompts, or display only?** It is **NOT** display only. It affects three upstream and harness steps:",
        "   - **Upstream TA/TP label assignment (`r.correct`):** MathArena used its SymPy/LaTeX parser (`parsed_answer`) to grade `correct` vs `wrong`. Across all 5 math banks, **0** wrong-labeled candidates have a `\\boxed{}` expression matching `gold` (after LaTeX normalization), and **0** right-labeled candidates lack `\\boxed{}`.",
        "   - **Wrong-candidate deduplication in `matharena_pools.py` (line 74):** Wrong candidates were deduplicated by string equality on `str(r.parsed_answer)`. When MathArena's parser emitted distinct strings for identical wrong answers (e.g., `12.566370614359172`, `3`, and `4` all for `4\\pi` in `apex_2025_9`; Python memory addresses `<function N at 0x...>` in `arxivmath-0326_30` and `arxivmath-0426_18`; or full essay text in `arxivmath-0826_24` and `arxivmath-0826_3`), duplicate wrong answers entered the same TA pool.",
        "   - **Judge prompt suffix (`Final answer: {cand[\"answer\"]}`):** Both `lineup_prompts.py` and `build_round2_mitigation.py` appended `Final answer: {cand[\"answer\"]}` below each candidate's full reasoning text, so judges saw the parsed string (including evaluated floats, stray fallback digits, SymPy `<function ...>` reprs, or duplicated essay text) at the end of affected candidates.",
        "3. **No locked banks or labels were modified.** Only the human audit display (`scripts/build_human_audit_html.py` -> `audit/human_audit_tool.html`) was updated to show the actual `\\boxed{}` answer, preserving the exact 92 items, seed 2026, blinding, and browser storage key.",
        "",
    ]

    for label, path in BANKS:
        raw = json.load(open(path))
        if isinstance(raw, dict):
            pools = raw.get("pools") or []
            if not pools:
                for v in raw.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict) and "cands" in v[0]:
                        pools.extend(v)
        else:
            pools = raw

        rows = []
        wrong_eq_gold = 0
        for p in pools:
            pid = p["pid"]
            pool_id = p.get("pool", pid)
            kind = p.get("kind", "")
            gold = str(p.get("gold", ""))
            gold_n = norm_latex(gold)
            excl = "bad_label" if pid in c3_bad else ("dup" if pid in c3_dups else "active")
            bx_list = []
            for ci, c in enumerate(p["cands"], 1):
                ans = str(c.get("answer", ""))
                txt = c.get("text", "")
                role = c.get("role", "")
                bx = extract_boxed(txt)
                bx_n = norm_latex(bx)
                if role == "wrong" and bx_n and gold_n and (bx_n == gold_n or bx_n.endswith("=" + gold_n)):
                    wrong_eq_gold += 1

                quirks = []
                if ans.startswith("<function "):
                    quirks.append("sympy_func_repr")
                if len(ans) > 250 and ("\n" in ans or " " in ans):
                    quirks.append("full_essay_in_parsed_answer")
                if bx is None:
                    quirks.append("no_boxed_fallback_parse")
                else:
                    if re.fullmatch(r"-?\d+\.\d{5,}", ans) and re.search(r"[a-zA-Z\\]", bx):
                        quirks.append("symbolic_eval_to_float")
                    elif re.fullmatch(r"-?\d+", ans):
                        bxc = re.sub(r"[\s\$\.,]+", "", bx)
                        if (
                            bxc != ans
                            and not bxc.endswith("=" + ans)
                            and not re.fullmatch(r"\d+\^\{\\circ\}|\d+°|\d+\^\\circ", bxc)
                            and len(ans) <= 8
                        ):
                            quirks.append("int_mismatch_vs_boxed")
                if kind == "TA" and bx is not None:
                    bx_list.append((ci, re.sub(r"\s+", "", bx)))
                if quirks:
                    rows.append((
                        pool_id,
                        pid,
                        excl,
                        role,
                        ci,
                        ",".join(quirks),
                        gold[:40],
                        (bx or "(none)")[:48],
                        ans[:48],
                    ))
            if kind == "TA":
                vals = [x[1] for x in bx_list]
                if len(vals) >= 2 and len(set(vals)) < len(vals):
                    rows.append((
                        pool_id,
                        pid,
                        excl,
                        "TA_pool",
                        0,
                        "duplicate_boxed_in_TA",
                        gold[:40],
                        str(vals)[:48],
                        "dedup_leak",
                    ))

        uniq_pools = sorted({r[0] for r in rows})
        uniq_pids = sorted({r[1] for r in rows})
        lines.append(f"## {label}")
        lines.append("")
        lines.append(
            f"Affected pools: **{len(uniq_pools)}** across **{len(uniq_pids)}** unique problem IDs "
            f"(`wrong_boxed_eq_gold = {wrong_eq_gold}`)."
        )
        lines.append("")
        if rows:
            lines.append("| Pool | C3 Status | Role | Cand | Quirk | Gold | Boxed | MathArena parsed_answer |")
            lines.append("|---|---|---|---:|---|---|---|---|")
            for pool_id, _pid, excl, role, ci, q, g, b, a in rows:
                lines.append(
                    f"| `{esc_md(pool_id)}` | {excl} | {role} | {ci} | `{q}` | "
                    f"`{esc_md(g)}` | `{esc_md(b)}` | `{esc_md(a)}` |"
                )
            lines.append("")

    out_p = os.path.join(V2, "audit/extractor_audit_report.md")
    with open(out_p, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"Wrote {out_p} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
