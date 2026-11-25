#!/usr/bin/env python3
"""Automated zero-mistake gate checker for the Auto-Research Science Loop.

Supports --stage <bank|pilot|run|paper> using Python 3.9 stdlib only.
Exits non-zero on any failed gate and prints a clear pass/fail table.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import statistics
import sys
import tokenize
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import parsers  # noqa: E402


SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache"}
STAGES = ("bank", "pilot", "run", "paper")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_family(name: str) -> str:
    low = (name or "").strip().lower()
    if not low:
        return "unknown"
    if any(k in low for k in ("claude", "anthropic", "haiku", "sonnet", "opus", "fable")):
        return "anthropic"
    if any(k in low for k in ("gemini", "google", "gemma")):
        return "google"
    if "gpt-oss" in low or "gpt_oss" in low:
        return "gpt-oss"
    if any(k in low for k in ("gpt", "openai", "o1-", "o3-", "o4-")):
        return "openai"
    if "deepseek" in low:
        return "deepseek"
    if "qwen" in low:
        return "qwen"
    if "llama" in low or "meta" in low:
        return "meta"
    if "mistral" in low:
        return "mistral"
    base = re.split(r"[#/:\s]", low, maxsplit=1)[0]
    return base or "unknown"


def check_budget_env(root: Path) -> Tuple[str, str]:
    bpath = root / "budget.env"
    if not bpath.is_file():
        return "FAIL", f"missing {bpath}"
    cfg: Dict[str, str] = {}
    for raw in bpath.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip()
    required_num = ("OOP_MAX_USD", "API_SCAFFOLD_CAP_USD", "API_VENDOR4_CAP_USD")
    for k in required_num:
        if k not in cfg:
            return "FAIL", f"budget.env missing {k}"
        try:
            float(cfg[k])
        except ValueError:
            return "FAIL", f"budget.env invalid number for {k}: {cfg[k]!r}"
    mode = cfg.get("ROUTE_MODE", "")
    if not mode:
        return "FAIL", "budget.env missing ROUTE_MODE"
    return "PASS", f"ROUTE_MODE={mode}, OOP_MAX_USD={cfg['OOP_MAX_USD']}"


def check_locked_hashes(lockfile: Path) -> Tuple[str, str]:
    if not lockfile.is_file():
        return "FAIL", f"missing {lockfile.name}"
    base_dir = lockfile.resolve().parent
    lines = [ln.strip() for ln in lockfile.read_text(encoding="utf-8").splitlines() if ln.strip()]
    entries = [ln for ln in lines if not ln.startswith("#")]
    if not entries:
        return "FAIL", f"{lockfile.name} has 0 hash entries"
    mismatches: List[str] = []
    verified = 0
    for idx, line in enumerate(entries, 1):
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+)$", line)
        if not m:
            mismatches.append(f"line {idx}: malformed")
            continue
        exp_hex, rel = m.group(1).lower(), m.group(2).strip()
        target = Path(rel) if os.path.isabs(rel) else (base_dir / rel)
        if not target.is_file():
            mismatches.append(f"missing:{rel}")
            continue
        act_hex = sha256_file(target)
        if act_hex != exp_hex:
            mismatches.append(f"mismatch:{rel}")
            continue
        verified += 1
    if mismatches:
        sample = ", ".join(mismatches[:3])
        return "FAIL", f"{len(mismatches)} error(s): {sample}"
    return "PASS", f"{verified} locked file(s) verified"


def _strip_fenced_blocks(text: str, is_tex: bool = False) -> str:
    """Replace fenced code blocks and LaTeX display-math environments while preserving newlines."""
    out_lines: List[str] = []
    in_fence = False
    fence_char = ""
    in_tex_math = False
    tex_math_envs = ("equation", "equation*", "align", "align*", "gather", "gather*")
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if is_tex and not in_fence:
            if not in_tex_math and any(stripped.startswith(f"\\begin{{{e}}}") for e in tex_math_envs):
                in_tex_math = True
                out_lines.append("\n" if line.endswith("\n") else "")
                continue
            if in_tex_math:
                if any(f"\\end{{{e}}}" in stripped for e in tex_math_envs):
                    in_tex_math = False
                out_lines.append("\n" if line.endswith("\n") else "")
                continue
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_char = stripped[:3]
                out_lines.append("\n" if line.endswith("\n") else "")
                continue
            out_lines.append(line)
        else:
            if stripped.startswith(fence_char):
                in_fence = False
                fence_char = ""
            out_lines.append("\n" if line.endswith("\n") else "")
    return "".join(out_lines)


def _strip_inline_code_and_math(line: str, is_tex: bool) -> str:
    s = re.sub(r"`[^`]*`", " ", line)
    s = re.sub(r"\$\$[^$]*\$\$", " ", s)
    s = re.sub(r"\$[^$]*\$", " ", s)
    if is_tex:
        s = re.sub(r"\\\[.*?\\\]", " ", s)
        s = re.sub(r"\\\(.*?\\\)", " ", s)
    return s


def _scan_text_prose_dashes(rel_path: str, text: str, is_tex: bool) -> List[str]:
    violations: List[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if "\u2014" in line:
            violations.append(f"{rel_path}:{lineno}: em dash (U+2014)")
        if "\u2013" in line:
            violations.append(f"{rel_path}:{lineno}: en dash (U+2013)")

    body = _strip_fenced_blocks(text, is_tex=is_tex)
    for lineno, raw_line in enumerate(body.splitlines(), 1):
        if re.match(r"^\s*\|[-:\s|]+\|\s*$", raw_line):
            continue
        cleaned = _strip_inline_code_and_math(raw_line, is_tex=is_tex)
        # Allow standard markdown list bullets at start of line.
        cleaned = re.sub(r"^(\s*)[-*+](\s+)", r"\1 \2", cleaned)
        # Allow markdown blockquote bullet lines.
        cleaned = re.sub(r"^(\s*>\s*)[-*+](\s+)", r"\1 \2", cleaned)
        if re.search(r"[A-Za-z0-9,.)\]]\s-\s[A-Za-z0-9(\[]", cleaned) or re.search(r"(?:^|\s)-\s", cleaned.lstrip()):
            if re.search(r"\S\s-\s\S", cleaned):
                violations.append(f"{rel_path}:{lineno}: prose spaced hyphen")
    return violations


def _scan_py_comments(rel_path: str, text: str) -> List[str]:
    violations: List[str] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for tok_type, tok_str, start, _, _ in tokens:
            if tok_type == tokenize.COMMENT:
                lineno = start[0]
                if "\u2014" in tok_str:
                    violations.append(f"{rel_path}:{lineno}: em dash in comment")
                if "\u2013" in tok_str:
                    violations.append(f"{rel_path}:{lineno}: en dash in comment")
                comment_body = tok_str.lstrip("#").strip()
                comment_body = re.sub(r"`[^`]*`", " ", comment_body)
                if re.search(r"\S\s-\s\S", comment_body):
                    violations.append(f"{rel_path}:{lineno}: prose spaced hyphen in comment")
    except tokenize.TokenError as exc:
        violations.append(f"{rel_path}: tokenize error ({exc})")
    return violations


def check_dashes(root: Path) -> Tuple[str, str]:
    violations: List[str] = []
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            if not fn.endswith((".md", ".tex", ".py")):
                continue
            p = Path(dirpath) / fn
            rel = str(p.relative_to(root))
            text = p.read_text(encoding="utf-8")
            scanned += 1
            if fn.endswith(".py"):
                violations.extend(_scan_py_comments(rel, text))
            else:
                violations.extend(_scan_text_prose_dashes(rel, text, is_tex=fn.endswith(".tex")))
    if violations:
        sample = "; ".join(violations[:4])
        return "FAIL", f"{len(violations)} violation(s) across {scanned} file(s): {sample}"
    return "PASS", f"0 violations across {scanned} .md/.tex/.py file(s)"


def _discover_pool_files(root: Path, bank_arg: Optional[str]) -> Tuple[List[Path], Optional[str]]:
    if bank_arg:
        bp = Path(bank_arg)
        if not bp.exists():
            return [], f"specified --bank path not found: {bp}"
        if bp.is_file():
            return [bp], None
        files = sorted(list(bp.rglob("*.json")) + list(bp.rglob("*.jsonl")))
        if not files:
            return [], f"no JSON/JSONL files found under {bp}"
        return files, None
    banks_dir = root / "banks"
    if not banks_dir.is_dir():
        return [], None
    locked_v2 = banks_dir / "locked_v2"
    scan_root = locked_v2 if locked_v2.is_dir() else banks_dir
    files = sorted(list(scan_root.rglob("*.json")) + list(scan_root.rglob("*.jsonl")))
    return files, None


def _get_excluded_families(mapping: Dict[str, Any], fallback: Any = None) -> Any:
    for k in ("excluded_judge_vendors", "excluded_judge_family", "judge_family", "judge"):
        val = mapping.get(k)
        if val:
            return val
    return fallback


def _extract_pool_records(obj: Any, file_family: Any = None) -> List[Tuple[Any, Dict[str, Any]]]:
    records: List[Tuple[Any, Dict[str, Any]]] = []
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                fam = _get_excluded_families(item, file_family)
                records.append((fam, item))
        return records
    if isinstance(obj, dict):
        meta = obj.get("meta") if isinstance(obj.get("meta"), dict) else {}
        top_fam = _get_excluded_families(obj) or _get_excluded_families(meta) or file_family
        if "pools" in obj and isinstance(obj["pools"], list):
            return _extract_pool_records(obj["pools"], top_fam)
        if "pools_by_judge" in obj and isinstance(obj["pools_by_judge"], dict):
            for jkey, plist in obj["pools_by_judge"].items():
                records.extend(_extract_pool_records(plist, jkey))
            return records
        # Check multi-section bank dicts (e.g. researchbench_pools, own_answer_removal)
        section_lists = [
            (k, v)
            for k, v in obj.items()
            if k != "meta"
            and isinstance(v, list)
            and any(isinstance(x, dict) and ("cands" in x or "candidates" in x or "gens" in x) for x in v)
        ]
        if section_lists:
            for _, plist in section_lists:
                records.extend(_extract_pool_records(plist, top_fam))
            return records
        # Check dict keyed by judge/family name -> list of pools
        if obj and all(isinstance(v, list) for v in obj.values()):
            for jkey, plist in obj.items():
                records.extend(_extract_pool_records(plist, jkey))
            return records
        if "cands" in obj or "gens" in obj or "candidates" in obj:
            records.append((top_fam, obj))
    return records


def check_judge_family_exclusion(root: Path, bank_arg: Optional[str]) -> Tuple[str, str]:
    files, err = _discover_pool_files(root, bank_arg)
    if err:
        return "FAIL", err
    if not files:
        return "SKIP", "no pool bank JSON found under banks/"

    total_pools = 0
    checked_pools = 0
    violations: List[str] = []
    missing_family_meta = 0
    for pf in files:
        if pf.suffix == ".jsonl":
            raw_items = [json.loads(ln) for ln in pf.read_text(encoding="utf-8").splitlines() if ln.strip()]
            pool_recs = _extract_pool_records(raw_items)
        else:
            data = json.loads(pf.read_text(encoding="utf-8"))
            pool_recs = _extract_pool_records(data)

        for raw_fam, pool in pool_recs:
            total_pools += 1
            pid = pool.get("pool") or pool.get("pool_id") or pool.get("pid") or f"idx_{total_pools}"
            if not raw_fam:
                missing_family_meta += 1
                continue
            fam_list = raw_fam if isinstance(raw_fam, (list, tuple, set)) else [raw_fam]
            judge_fams = {infer_family(str(f)) for f in fam_list if str(f).strip()}
            judge_fams.discard("unknown")
            if not judge_fams:
                missing_family_meta += 1
                continue
            checked_pools += 1
            cands = pool.get("cands") or pool.get("candidates") or []
            gens = pool.get("gens") or []
            vendors = pool.get("vendors") or []
            cand_sources: List[str] = []
            for idx, c in enumerate(cands):
                if isinstance(c, dict):
                    if c.get("is_own_answer") is True:
                        violations.append(f"{pf.name}:{pid}:cand{idx+1}=own_answer")
                    src = c.get("family") or c.get("vendor") or c.get("model") or c.get("gen") or ""
                    if src:
                        cand_sources.append(str(src))
                elif isinstance(c, str):
                    cand_sources.append(c)
            for g in gens:
                cand_sources.append(str(g))
            for v in vendors:
                cand_sources.append(str(v))
            for idx, src in enumerate(cand_sources, 1):
                cfam = infer_family(src)
                if cfam in judge_fams:
                    violations.append(f"{pf.name}:{pid}:cand{idx}({src}) matches {cfam}")

    if total_pools == 0:
        return "FAIL", f"found {len(files)} pool file(s) but 0 pool records"
    if missing_family_meta == total_pools:
        return "FAIL", f"{total_pools} pool(s) checked, none record judge_family/excluded_judge_family"
    if violations:
        sample = "; ".join(violations[:3])
        return "FAIL", f"{len(violations)} exclusion violation(s) in {checked_pools} pool(s): {sample}"
    return "PASS", f"{checked_pools} excluded-family pool(s) clean across {len(files)} file(s) ({total_pools} total)"


def _discover_run_dirs(root: Path, stage: str, run_dir_args: Optional[List[str]]) -> Tuple[List[Path], Optional[str]]:
    if run_dir_args:
        dirs: List[Path] = []
        for raw in run_dir_args:
            p = Path(raw)
            if not p.is_dir():
                return [], f"specified --run-dir not found: {p}"
            dirs.append(p)
        return dirs, None
    exps = root / "exps"
    if stage == "pilot":
        p = exps / "pilot"
        return ([p] if p.is_dir() else []), None
    if not exps.is_dir():
        return [], None
    dirs = [d for d in sorted(exps.iterdir()) if d.is_dir() and any(d.rglob("*.json"))]
    return dirs, None


def _load_run_records(run_dirs: List[Path]) -> List[Tuple[Path, Dict[str, Any]]]:
    recs: List[Tuple[Path, Dict[str, Any]]] = []
    for rdir in run_dirs:
        for jp in sorted(rdir.rglob("*.json")):
            if jp.name.startswith("."):
                continue
            try:
                data = json.loads(jp.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, dict) and ("job_id" in data or "id" in data) and ("text" in data or "result" in data or "status" in data):
                recs.append((jp, data))
    return recs


def _infer_arm(rec: Dict[str, Any], path: Path) -> str:
    arm = str(rec.get("arm") or "").upper()
    if arm:
        if arm.startswith(("M1_PICK", "M2", "M3")):
            return "PICK"
        return arm
    jid = str(rec.get("job_id") or rec.get("id") or path.stem).upper()
    pdir = path.parent.name.upper()
    for tag in ("EACH", "FORCED", "PICK", "M2", "M3", "M1_TIEBREAK", "ISO", "SOLVE"):
        if tag in jid or tag in pdir:
            return "PICK" if tag in ("M2", "M3", "M1_TIEBREAK") else tag
    txt = rec.get("text") or rec.get("result") or ""
    if re.search(r"^\W*VERDICT\s*1\W*:", txt, re.M | re.I):
        return "EACH"
    if re.search(r"^\W*CHOICE\W*:", txt, re.M | re.I):
        return "PICK"
    if re.search(r"^\W*VERDICT\W*:", txt, re.M | re.I):
        return "ISO"
    if re.search(r"^\W*ANSWER\W*:", txt, re.M | re.I):
        return "SOLVE"
    return "UNKNOWN"


def _parse_record_value(rec: Dict[str, Any], arm: str, path: Optional[Path] = None) -> Any:
    if rec.get("status") not in (None, "ok"):
        return None
    if rec.get("rc") not in (None, 0):
        return None
    text = rec.get("text")
    if text is None:
        text = rec.get("result")
    if not isinstance(text, str) or not text.strip():
        return None
    default_k = 3
    if path is not None:
        pl = str(path).lower()
        if "science" in pl or "m3_foil" in pl:
            default_k = 4
        elif "c5_removal" in pl:
            default_k = 2
    n_cands = int(rec.get("n_cands") or default_k)
    if arm == "ISO":
        return parsers.verdict(text)
    if arm in ("PICK", "FORCED"):
        return parsers.choice(text, n_cands)
    if arm == "EACH":
        vals = parsers.each(text, n_cands)
        return vals if all(v is not None for v in vals) else None
    if arm == "SOLVE":
        return parsers.answer(text)
    # Fallback across standard tags
    v = parsers.verdict(text)
    if v is not None:
        return v
    c = parsers.choice(text, n_cands)
    if c is not None:
        return c
    return parsers.answer(text)


def check_parse_and_calibration(
    root: Path, stage: str, run_dir_args: Optional[List[str]]
) -> Tuple[Tuple[str, str], Tuple[str, str]]:
    run_dirs, err = _discover_run_dirs(root, stage, run_dir_args)
    if err:
        return ("FAIL", err), ("FAIL", err)
    if not run_dirs:
        return ("FAIL", f"no run directory found for stage={stage}"), ("FAIL", f"no run directory found for stage={stage}")

    records = _load_run_records(run_dirs)
    if not records:
        return ("FAIL", f"0 job JSON records in {len(run_dirs)} run dir(s)"), ("FAIL", "no ISO records to calibrate")

    total = len(records)
    parsed = 0
    iso_right: List[bool] = []
    iso_wrong: List[bool] = []

    for jp, rec in records:
        arm = _infer_arm(rec, jp)
        val = _parse_record_value(rec, arm, jp)
        if val is not None:
            parsed += 1
        if arm == "ISO" and isinstance(val, bool):
            role = rec.get("role")
            if role is None and "is_correct" in rec:
                role = "right" if rec["is_correct"] else "wrong"
            if isinstance(role, str):
                rlow = role.strip().lower()
                if rlow in ("right", "correct", "tp_right"):
                    iso_right.append(val)
                elif rlow in ("wrong", "incorrect", "ta_wrong", "foil"):
                    iso_wrong.append(val)

    parse_rate = parsed / total
    if parse_rate >= 0.90:
        parse_res = ("PASS", f"{parsed}/{total} ({parse_rate:.3f} >= 0.90)")
    else:
        parse_res = ("FAIL", f"{parsed}/{total} ({parse_rate:.3f} < 0.90)")

    if not iso_right or not iso_wrong:
        cal_res = (
            "SKIP",
            f"ISO right/wrong labels incomplete (right={len(iso_right)}, wrong={len(iso_wrong)})",
        )
    else:
        acc_r = sum(iso_right) / len(iso_right)
        acc_w = sum(iso_wrong) / len(iso_wrong)
        diff = acc_r - acc_w
        if diff >= 0.10:
            cal_res = ("PASS", f"ISO_right={acc_r:.3f} - ISO_wrong={acc_w:.3f} = {diff:+.3f} (>= 0.10)")
        else:
            cal_res = ("FAIL", f"ISO_right={acc_r:.3f} - ISO_wrong={acc_w:.3f} = {diff:+.3f} (< 0.10)")
    return parse_res, cal_res


def check_c4_token_ratio(root: Path, run_dir_args: Optional[List[str]]) -> Tuple[str, str]:
    c4_dirs: List[Path] = []
    if run_dir_args:
        for raw in run_dir_args:
            p = Path(raw)
            if p.is_dir() and "c4" in p.name.lower():
                c4_dirs.append(p)
    default_c4 = root / "exps" / "c4_compute"
    if default_c4.is_dir() and default_c4 not in c4_dirs:
        c4_dirs.append(default_c4)
    if not c4_dirs:
        return "SKIP", "no c4_compute run directory present"

    recs = _load_run_records(c4_dirs)
    if not recs:
        return "SKIP", "c4_compute has 0 JSON records"

    pick_by_pool: Dict[str, int] = {}
    iso_by_pool: Dict[str, int] = {}
    ref_iso_median: Optional[float] = None
    for cdir in c4_dirs:
        meta_p = cdir / "c4_meta.json"
        if meta_p.is_file():
            try:
                m = json.loads(meta_p.read_text(encoding="utf-8"))
                if isinstance(m.get("iso_median_tokens"), (int, float)):
                    ref_iso_median = float(m["iso_median_tokens"])
            except Exception:
                pass

    for jp, rec in recs:
        tok = rec.get("output_tokens")
        if not isinstance(tok, (int, float)):
            continue
        scaffold = rec.get("scaffold_tokens") or 0
        net_tok = max(0, int(tok) - int(scaffold))
        arm = _infer_arm(rec, jp)
        pool_id = str(
            rec.get("pool_id")
            or rec.get("pool")
            or re.sub(r"_(?:r|rep|call)?\d+$", "", str(rec.get("job_id") or jp.stem), flags=re.I)
        )
        if arm == "PICK":
            pick_by_pool[pool_id] = pick_by_pool.get(pool_id, 0) + net_tok
        elif arm == "ISO":
            iso_by_pool[pool_id] = iso_by_pool.get(pool_id, 0) + net_tok

    if not pick_by_pool:
        return "FAIL", "C4 directory has no PICK token records"
    pick_med = statistics.median(pick_by_pool.values())
    if iso_by_pool:
        iso_med = statistics.median(iso_by_pool.values())
    elif ref_iso_median is not None and ref_iso_median > 0:
        iso_med = ref_iso_median
    else:
        return "FAIL", "C4 missing ISO baseline tokens (no ISO records and no c4_meta.json iso_median_tokens)"

    if iso_med <= 0:
        return "FAIL", f"invalid ISO median tokens ({iso_med})"
    ratio = pick_med / iso_med
    if 0.90 <= ratio <= 1.10:
        return "PASS", f"median ratio={ratio:.3f} (PICK={pick_med:.1f}, ISO={iso_med:.1f})"
    return "FAIL", f"median ratio={ratio:.3f} outside [0.90, 1.10] (PICK={pick_med:.1f}, ISO={iso_med:.1f})"


def check_paper_artifacts(root: Path) -> Tuple[str, str]:
    paper_dir = root / "paper"
    if not paper_dir.is_dir():
        return "FAIL", f"missing directory: {paper_dir}"
    tex_files = sorted(paper_dir.glob("*.tex"))
    if not tex_files:
        return "FAIL", "no .tex files in paper/"
    txt_files = sorted(paper_dir.glob("*.txt"))
    for tf in txt_files:
        qq = tf.read_text(encoding="utf-8").count("??")
        if qq > 0:
            return "FAIL", f"{tf.name} contains {qq} unresolved '??' reference(s)"
    return "PASS", f"{len(tex_files)} .tex file(s) present"


def print_table(rows: List[Tuple[str, str, str]]) -> None:
    name_w = max(len("CHECK"), *(len(r[0]) for r in rows))
    stat_w = max(len("STATUS"), *(len(r[1]) for r in rows))
    print(f"{'CHECK':<{name_w}}  {'STATUS':<{stat_w}}  DETAIL")
    print(f"{'-' * name_w}  {'-' * stat_w}  {'-' * 40}")
    for name, status, detail in rows:
        print(f"{name:<{name_w}}  {status:<{stat_w}}  {detail}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    default_root = str(Path(__file__).resolve().parent.parent)
    p = argparse.ArgumentParser(description="Automated zero-mistake preflight gate checker.")
    p.add_argument("--stage", required=True, choices=STAGES, help="Pipeline stage to validate.")
    p.add_argument("--root", default=default_root, help="Workspace root directory (default: v2-upgrade).")
    p.add_argument("--lockfile", default=None, help="Path to LOCKED.sha256 (default: <root>/LOCKED.sha256).")
    p.add_argument("--bank", default=None, help="Optional pool bank JSON/JSONL file or directory.")
    p.add_argument("--run-dir", action="append", default=None, help="Optional run directory (repeatable).")
    return p.parse_args(argv)


def _resolve_lockfile(root: Path, lockfile_arg: Optional[str]) -> Path:
    if lockfile_arg:
        return Path(lockfile_arg).resolve()
    candidates = [
        root / "LOCKED.sha256",
        root / "banks" / "locked_v2" / "LOCKED.sha256",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    banks_dir = root / "banks"
    if banks_dir.is_dir():
        found = sorted(banks_dir.rglob("LOCKED.sha256"))
        if found:
            return found[0].resolve()
    return (root / "banks" / "locked_v2" / "LOCKED.sha256").resolve()


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    lockfile = _resolve_lockfile(root, args.lockfile)

    rows: List[Tuple[str, str, str]] = []
    rows.append(("budget_env", *check_budget_env(root)))
    rows.append(("locked_sha256", *check_locked_hashes(lockfile)))
    rows.append(("dash_scan", *check_dashes(root)))
    rows.append(("judge_family_exclusion", *check_judge_family_exclusion(root, args.bank)))

    if args.stage in ("pilot", "run", "paper"):
        parse_res, cal_res = check_parse_and_calibration(root, args.stage, args.run_dir)
        rows.append(("parse_rate_gate", *parse_res))
        rows.append(("calibration_gate", *cal_res))

    if args.stage in ("run", "paper"):
        rows.append(("c4_token_ratio", *check_c4_token_ratio(root, args.run_dir)))

    if args.stage == "paper":
        rows.append(("paper_artifacts", *check_paper_artifacts(root)))

    print_table(rows)
    failed = sum(1 for _, status, _ in rows if status == "FAIL")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
