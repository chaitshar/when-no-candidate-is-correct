#!/usr/bin/env python3
"""Build Round 2 (Experiment C7) Mitigation Matrix job JSONLs and preregistration.

Pure Python 3.9 stdlib only. Zero em dashes, en dashes, or prose spaced hyphens.

Supports:
  --mode generate_m2_m3 (default):
    Writes under exps/c7_mitigation/:
      jobs_science_m2.jsonl
      jobs_math_haiku_m2.jsonl
      jobs_math_cross_m2.jsonl
      jobs_math_haiku_m3_foil.jsonl
      PREREG_C7.md
      C7_LOCKED.sha256

  --mode generate_m1:
    Scans completed ISO raw folders (Haiku C3 Math, Haiku Science, GPT-OSS
    Science/Math, Gemini Science/Math, or a custom --iso-dir) and generates:
      m1_stage1_<tag>.json
      jobs_<tag>_m1_tiebreak.jsonl  (only pools where Stage 1 ISO accepted k >= 2)
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import parsers  # noqa: E402

BANKS_DIR = ROOT_DIR / "banks" / "locked_v2"
C7_DIR = ROOT_DIR / "exps" / "c7_mitigation"
C6_EXPS_DIR = ROOT_DIR / "exps" / "c6_crossvendor"
V1_C3_RAW_ARMS = Path(
    "/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar/exps/c3/raw/arms"
)

SEED_C6_CONTEST = 20261121
SEED_C6_ARXIV = 20261122
SEED_C4_HAIKU = 20261123
CALIBRATION_CONF_TAU = 4
DEFAULT_TIMEOUT_S = 900


def sha256_file(path: Path) -> str:
    """Compute lowercase hex SHA-256 digest for a file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_v2_bank_lock() -> None:
    """Verify banks/locked_v2/LOCKED.sha256 before building Round 2 artifacts."""
    lockfile = BANKS_DIR / "LOCKED.sha256"
    if not lockfile.is_file():
        raise FileNotFoundError(f"Missing bank lockfile: {lockfile}")
    for lineno, raw in enumerate(lockfile.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+)$", line)
        if not m:
            raise ValueError(f"{lockfile}:{lineno}: malformed SHA-256 line")
        exp_hex, rel = m.group(1).lower(), m.group(2).strip()
        target = BANKS_DIR / rel
        if not target.is_file():
            raise FileNotFoundError(f"Locked bank file missing: {target}")
        act_hex = sha256_file(target)
        if act_hex != exp_hex:
            raise ValueError(f"Checksum mismatch for {target}: expected {exp_hex} got {act_hex}")


def check_no_dashes_text(text: str, label: str) -> None:
    """Assert zero em dashes, en dashes, or prose spaced hyphens in text."""
    if "\u2014" in text or "\u2013" in text:
        raise ValueError(f"Em/en dash detected in {label}")
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if re.match(r"^\|[-:\s|]+\|$", stripped):
            continue
        cleaned = re.sub(r"`[^`]*`", " ", line)
        cleaned = re.sub(r"^(\s*)[-*+](\s+)", r"\1 \2", cleaned)
        cleaned = re.sub(r"^(\s*>\s*)[-*+](\s+)", r"\1 \2", cleaned)
        if re.search(r"\S\s-\s\S", cleaned):
            raise ValueError(f"Prose spaced hyphen in {label}:{lineno}: {line}")


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> int:
    """Write a list of dicts as UTF-8 JSON Lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def get_right_pos_1idx(pool: Dict[str, Any]) -> Optional[int]:
    """Return 1-indexed position of the right candidate if present, else None."""
    if pool.get("kind") != "TP":
        return None
    for idx, cand in enumerate(pool["cands"], 1):
        if cand.get("role") == "right":
            return idx
    return None


def select_stratified_pids(
    items_by_pid: Dict[str, Dict[str, Any]],
    n_target: int,
    seed: int,
) -> List[str]:
    """Deterministically select n_target paired pids balanced across TP right_pos_1idx."""
    if len(items_by_pid) < n_target:
        raise ValueError(f"Requested {n_target} items, only {len(items_by_pid)} available")
    rng = random.Random(seed)
    by_pos: Dict[int, List[str]] = {1: [], 2: [], 3: []}
    for pid in sorted(items_by_pid.keys()):
        tp_pool = items_by_pid[pid]["TP"]
        rpos = tp_pool.get("right_pos_1idx") or get_right_pos_1idx(tp_pool)
        if rpos not in by_pos:
            raise ValueError(f"Unexpected TP right_pos_1idx={rpos} for {pid}")
        by_pos[rpos].append(pid)
    for pos in (1, 2, 3):
        rng.shuffle(by_pos[pos])

    pos_order = [1, 2, 3]
    rng.shuffle(pos_order)
    chosen: List[str] = []
    step = 0
    while len(chosen) < n_target:
        pos = pos_order[step % 3]
        if by_pos[pos]:
            chosen.append(by_pos[pos].pop())
        step += 1
        if step > 10000:
            raise RuntimeError("Stratified selection stalled")
    chosen.sort()
    return chosen


def format_math_cand_block(idx: int, cand: Dict[str, Any]) -> str:
    """Format one math candidate block matching Round 1 lineup_prompts style."""
    return f"Solution {idx}:\n{cand['text'].strip()}\nFinal answer: {cand['answer']}"


def format_math_pool_head(problem: str, cands: List[Dict[str, Any]]) -> Tuple[int, str]:
    """Format math problem and numbered proposed solutions."""
    n = len(cands)
    body = "\n\n".join(format_math_cand_block(i + 1, c) for i, c in enumerate(cands))
    head = f"Here is a math problem and {n} proposed solutions.\n\nProblem:\n{problem}\n\n{body}\n\n"
    return n, head


def format_science_pool_head(q: str, a: str, cands: List[Dict[str, Any]]) -> Tuple[int, str]:
    """Format ResearchBench question, abstract evidence, and numbered hypotheses."""
    n = len(cands)
    body = "\n\n".join(f"Hypothesis {i + 1}:\n{c['text'].strip()}" for i, c in enumerate(cands))
    head = (
        "You are verifying scientific hypotheses against a published study.\n\n"
        f"Research question:\n{q}\n\n"
        f"Evidence (the study's abstract):\n{a}\n\n"
        f"Candidate hypotheses:\n{body}\n\n"
    )
    return n, head


def math_pick_prompt(problem: str, cands: List[Dict[str, Any]]) -> str:
    """Standard PICK prompt for Stage 2 M1 tie-breaker over k >= 2 math candidates."""
    n, head = format_math_pool_head(problem, cands)
    return (
        head
        + "Which solution has the correct final answer, if any? It is possible that none "
        "of them is correct. Check the work as carefully as you need to. End your reply "
        f"with exactly one line: CHOICE: <solution number from 1 to {n}> or CHOICE: NONE "
        "(if no solution has the correct final answer)."
    )


def science_pick_prompt(q: str, a: str, cands: List[Dict[str, Any]]) -> str:
    """Standard PICK prompt for Stage 2 M1 tie-breaker over k >= 2 science hypotheses."""
    n, head = format_science_pool_head(q, a, cands)
    return (
        head
        + "Which hypothesis is the main hypothesis that this study's evidence supports, if any? "
        "It is possible that none of them is correct. Check the evidence as carefully as you need to. "
        f"End your reply with exactly one line: CHOICE: <hypothesis number from 1 to {n}> "
        "or CHOICE: NONE (if no hypothesis is supported)."
    )


def math_m2_prompt(problem: str, cands: List[Dict[str, Any]]) -> str:
    """Arm M2 Falsification-First Criterion Recalibration Gate prompt for math."""
    n, head = format_math_pool_head(problem, cands)
    return (
        head
        + "Follow this two-step verification protocol strictly before making any selection:\n"
        f"Step 1 (Independent Falsification): For each of the {n} solutions independently, "
        "actively try to falsify it by checking every derivation step, edge case, and arithmetic "
        "calculation to find any concrete error, logical gap, or unsupported leap. Do NOT compare "
        "solutions against one another during Step 1.\n"
        "Step 2 (Calibrated Selection Gate): Only after trying to falsify every solution, "
        "consider whether any solution completely survived falsification. Select a solution ONLY "
        "if its final answer is verified with high certainty (confidence 4 or 5 on a 1 to 5 scale, "
        "where 1 is a guess, 3 is moderate/uncertain, and 5 is completely verified). "
        "If no solution survives falsification with confidence at least 4, you MUST output CHOICE: NONE.\n\n"
        f"Write the line: CHOICE: <solution number from 1 to {n}> or CHOICE: NONE\n"
        "Then end your reply with exactly one final line: CONFIDENCE: <1 to 5 integer>"
    )


def science_m2_prompt(q: str, a: str, cands: List[Dict[str, Any]]) -> str:
    """Arm M2 Falsification-First Criterion Recalibration Gate prompt for science."""
    n, head = format_science_pool_head(q, a, cands)
    return (
        head
        + "Follow this two-step verification protocol strictly before making any selection:\n"
        f"Step 1 (Independent Falsification): For each of the {n} hypotheses independently, "
        "actively try to falsify it against the study's abstract by identifying any concrete "
        "contradiction, unsupported causal leap, or mismatch with the reported evidence. Do NOT "
        "compare hypotheses against one another during Step 1.\n"
        "Step 2 (Calibrated Selection Gate): Only after trying to falsify every hypothesis, "
        "consider whether any hypothesis completely survived falsification as the main hypothesis "
        "supported by this study's evidence. Select a hypothesis ONLY if you are highly certain "
        "(confidence 4 or 5 on a 1 to 5 scale, where 1 is a guess, 3 is moderate/uncertain, and 5 "
        "is completely verified). If no hypothesis survives falsification with confidence at least 4, "
        "you MUST output CHOICE: NONE.\n\n"
        f"Write the line: CHOICE: <hypothesis number from 1 to {n}> or CHOICE: NONE\n"
        "Then end your reply with exactly one final line: CONFIDENCE: <1 to 5 integer>"
    )


def math_m3_foil_prompt(problem: str, cands: List[Dict[str, Any]]) -> str:
    """Arm M3 Mock-Witness / Known-Foil Calibrated Lineup prompt for math (4 candidates)."""
    n, head = format_math_pool_head(problem, cands)
    return (
        head
        + "Follow this calibrated screening procedure carefully:\n"
        f"First, inspect all {n} solutions one by one and explicitly identify and reject any "
        "solution that is clearly wrong, off-target, or contains a mathematical error "
        "(there may be one or more known wrong decoy foils in the set, and all solutions may be wrong).\n"
        "Only after explicitly rejecting the flawed solutions, decide whether any remaining "
        "solution has the strictly correct final answer. Do not pick the best of a bad set.\n\n"
        f"End your reply with exactly one line: CHOICE: <solution number from 1 to {n}> "
        "or CHOICE: NONE (if no solution has the correct final answer)."
    )


def load_c9_researchbench_pools() -> List[Dict[str, Any]]:
    """Load all 60 ResearchBench pools (30 TA + 30 TP) from c9_science_pools.json."""
    data = json.loads((BANKS_DIR / "c9_science_pools.json").read_text(encoding="utf-8"))
    pools = data["researchbench_pools"]
    if len(pools) != 60:
        raise AssertionError(f"Expected 60 ResearchBench pools, got {len(pools)}")
    return pools


def load_c6_crossvendor_subset() -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Any]]:
    """Load balanced 40-problem (20 contest + 20 arxivmath, TA+TP = 80 pools) c6 subset."""
    data = json.loads((BANKS_DIR / "c6_crossvendor_math.json").read_text(encoding="utf-8"))
    by_src: Dict[str, Dict[str, Dict[str, Any]]] = {"contest": {}, "arxivmath": {}}
    for p in data["pools"]:
        src = p["source"]
        if src not in by_src:
            raise ValueError(f"Unexpected source {src!r} in c6_crossvendor_math")
        by_src[src].setdefault(p["pid"], {})[p["kind"]] = p

    sel_con = select_stratified_pids(by_src["contest"], 20, SEED_C6_CONTEST)
    sel_arx = select_stratified_pids(by_src["arxivmath"], 20, SEED_C6_ARXIV)
    selected_pids = sel_con + sel_arx

    pools_out: List[Dict[str, Any]] = []
    for pid in sel_con:
        pools_out.append(by_src["contest"][pid]["TA"])
        pools_out.append(by_src["contest"][pid]["TP"])
    for pid in sel_arx:
        pools_out.append(by_src["arxivmath"][pid]["TA"])
        pools_out.append(by_src["arxivmath"][pid]["TP"])

    tp_pos_counts = Counter(
        p["right_pos_1idx"] for p in pools_out if p["kind"] == "TP"
    )
    stats = {
        "n_problems": len(selected_pids),
        "n_contest": len(sel_con),
        "n_arxivmath": len(sel_arx),
        "n_pools": len(pools_out),
        "tp_right_pos_counts": dict(sorted(tp_pos_counts.items())),
        "excluded_judge_vendors": data["meta"]["excluded_judge_vendors"],
    }
    return pools_out, selected_pids, stats


def load_c4_haiku_subset() -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]], Dict[str, Any]]:
    """Load 40 paired corrected Haiku UNSOLVED C3 problems (80 pools) from c4_haiku_compute.json."""
    data = json.loads((BANKS_DIR / "c4_haiku_compute.json").read_text(encoding="utf-8"))
    by_pid: Dict[str, Dict[str, Any]] = {}
    for p in data["pools"]:
        by_pid.setdefault(p["pid"], {})[p["kind"]] = p
    paired = {pid: d for pid, d in by_pid.items() if "TA" in d and "TP" in d}

    sel_pids = select_stratified_pids(paired, 40, SEED_C4_HAIKU)
    pools_out: List[Dict[str, Any]] = []
    for pid in sel_pids:
        pools_out.append(paired[pid]["TA"])
        pools_out.append(paired[pid]["TP"])

    tp_pos_counts = Counter(
        get_right_pos_1idx(p) for p in pools_out if p["kind"] == "TP"
    )
    src_counts = Counter(paired[pid]["TA"]["source"] for pid in sel_pids)
    stats = {
        "n_problems": len(sel_pids),
        "n_pools": len(pools_out),
        "sources": dict(sorted(src_counts.items())),
        "tp_right_pos_counts": dict(sorted(tp_pos_counts.items())),
    }
    return pools_out, sel_pids, data["pools"], stats


def assign_deterministic_donor_foils(
    sel_pids: List[str],
    all_c4_pools: List[Dict[str, Any]],
) -> Dict[str, Tuple[str, Dict[str, Any]]]:
    """Select one deterministic wrong candidate from another pid as a known foil per pid."""
    pools_by_pid: Dict[str, List[Dict[str, Any]]] = {}
    wrong_catalog: List[Tuple[str, Dict[str, Any]]] = []
    seen_cids = set()
    for p in all_c4_pools:
        pools_by_pid.setdefault(p["pid"], []).append(p)
        for c in p["cands"]:
            if c["role"] == "wrong" and c["cid"] not in seen_cids:
                seen_cids.add(c["cid"])
                wrong_catalog.append((p["pid"], c))
    wrong_catalog.sort(key=lambda item: (item[0], item[1]["cid"]))

    assigned: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    n_cat = len(wrong_catalog)
    for idx, pid in enumerate(sel_pids):
        target_pools = pools_by_pid[pid]
        forbidden = [target_pools[0]["gold"]]
        for tp in target_pools:
            forbidden.extend(c["answer"] for c in tp["cands"])
        chosen: Optional[Tuple[str, Dict[str, Any]]] = None
        for offset in range(n_cat):
            donor_pid, donor_cand = wrong_catalog[(idx * 17 + offset) % n_cat]
            if donor_pid == pid:
                continue
            d_ans = donor_cand["answer"]
            if any(parsers.math_equal(d_ans, f_ans) for f_ans in forbidden):
                continue
            chosen = (donor_pid, donor_cand)
            break
        if chosen is None:
            raise RuntimeError(f"Could not find distinct wrong donor foil for {pid}")
        assigned[pid] = chosen
    return assigned


def build_m2_and_m3_jobs() -> Dict[str, Any]:
    """Build M2 and M3 job JSONLs, PREREG_C7.md, and C7_LOCKED.sha256."""
    C7_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Science M2 (all 60 ResearchBench pools)
    sci_pools = load_c9_researchbench_pools()
    sci_m2_jobs: List[Dict[str, Any]] = []
    for p in sci_pools:
        cands = p["cands"]
        rpos = get_right_pos_1idx(p)
        sci_m2_jobs.append(
            {
                "id": f"M2__{p['pool']}",
                "item": p["item"],
                "row": p["row"],
                "doi": p["doi"],
                "discipline": p["discipline"],
                "pool": p["pool"],
                "kind": p["kind"],
                "arm": "M2_FALSIFY",
                "n_cands": len(cands),
                "right_pos_1idx": rpos,
                "roles": [c["role"] for c in cands],
                "cids": [c["cid"] for c in cands],
                "conf_threshold": CALIBRATION_CONF_TAU,
                "timeout": DEFAULT_TIMEOUT_S,
                "prompt": science_m2_prompt(p["research_question"], p["abstract"], cands),
            }
        )

    # 2. Cross-vendor Math M2 (80 pools: 20 contest + 20 arxivmath, TA+TP)
    c6_pools, c6_pids, c6_stats = load_c6_crossvendor_subset()
    math_cross_m2_jobs: List[Dict[str, Any]] = []
    for p in c6_pools:
        cands = p["cands"]
        rpos = get_right_pos_1idx(p)
        math_cross_m2_jobs.append(
            {
                "id": f"M2__{p['pool']}",
                "pid": p["pid"],
                "pool": p["pool"],
                "kind": p["kind"],
                "source": p["source"],
                "comp": p["comp"],
                "arm": "M2_FALSIFY",
                "n_cands": len(cands),
                "right_pos_1idx": rpos,
                "roles": [c["role"] for c in cands],
                "cids": [c["cid"] for c in cands],
                "vendors": list(p["vendors"]),
                "conf_threshold": CALIBRATION_CONF_TAU,
                "timeout": DEFAULT_TIMEOUT_S,
                "prompt": math_m2_prompt(p["problem"], cands),
            }
        )

    # 3. Haiku Math M2 and M3 Foil (40 paired corrected Haiku UNSOLVED C3 problems = 80 pools)
    c4_pools, c4_pids, all_c4_pools, c4_stats = load_c4_haiku_subset()
    donor_foils = assign_deterministic_donor_foils(c4_pids, all_c4_pools)

    math_haiku_m2_jobs: List[Dict[str, Any]] = []
    math_haiku_m3_jobs: List[Dict[str, Any]] = []
    pid_to_idx = {pid: idx for idx, pid in enumerate(c4_pids)}
    m3_foil_pos_counts = Counter()
    m3_tp_right_pos_counts = Counter()

    for p in c4_pools:
        cands = p["cands"]
        rpos = get_right_pos_1idx(p)
        math_haiku_m2_jobs.append(
            {
                "id": f"M2__{p['pool']}",
                "pid": p["pid"],
                "pool": p["pool"],
                "kind": p["kind"],
                "source": p["source"],
                "comp": p["comp"],
                "arm": "M2_FALSIFY",
                "model": "haiku",
                "n_cands": len(cands),
                "right_pos_1idx": rpos,
                "roles": [c["role"] for c in cands],
                "cids": [c["cid"] for c in cands],
                "vendors": list(p["vendors"]),
                "conf_threshold": CALIBRATION_CONF_TAU,
                "timeout": DEFAULT_TIMEOUT_S,
                "prompt": math_m2_prompt(p["problem"], cands),
            }
        )

        prob_idx = pid_to_idx[p["pid"]]
        kind_offset = 0 if p["kind"] == "TA" else 2
        foil_pos_1idx = ((prob_idx + kind_offset) % 4) + 1
        donor_pid, donor_cand = donor_foils[p["pid"]]
        foil_cand = {
            "cid": f"{donor_cand['cid']}__FOIL",
            "text": donor_cand["text"],
            "answer": donor_cand["answer"],
            "role": "foil",
            "gen": donor_cand["gen"],
            "vendor": donor_cand["vendor"],
        }
        aug_cands = [dict(c) for c in cands]
        aug_cands.insert(foil_pos_1idx - 1, foil_cand)
        new_rpos = get_right_pos_1idx({"kind": p["kind"], "cands": aug_cands})
        m3_foil_pos_counts[foil_pos_1idx] += 1
        if new_rpos is not None:
            m3_tp_right_pos_counts[new_rpos] += 1

        math_haiku_m3_jobs.append(
            {
                "id": f"M3_FOIL__{p['pool']}",
                "pid": p["pid"],
                "pool": p["pool"],
                "kind": p["kind"],
                "source": p["source"],
                "comp": p["comp"],
                "arm": "M3_FOIL",
                "model": "haiku",
                "n_cands": len(aug_cands),
                "foil_pos": foil_pos_1idx,
                "foil_cid": foil_cand["cid"],
                "foil_donor_pid": donor_pid,
                "foil_donor_cid": donor_cand["cid"],
                "foil_answer": foil_cand["answer"],
                "right_pos_1idx": new_rpos,
                "orig_right_pos_1idx": rpos,
                "roles": [c["role"] for c in aug_cands],
                "cids": [c["cid"] for c in aug_cands],
                "vendors": [c["vendor"] for c in aug_cands],
                "timeout": DEFAULT_TIMEOUT_S,
                "prompt": math_m3_foil_prompt(p["problem"], aug_cands),
            }
        )

    files_written: Dict[str, int] = {}
    files_written["jobs_science_m2.jsonl"] = write_jsonl(
        C7_DIR / "jobs_science_m2.jsonl", sci_m2_jobs
    )
    files_written["jobs_math_haiku_m2.jsonl"] = write_jsonl(
        C7_DIR / "jobs_math_haiku_m2.jsonl", math_haiku_m2_jobs
    )
    files_written["jobs_math_cross_m2.jsonl"] = write_jsonl(
        C7_DIR / "jobs_math_cross_m2.jsonl", math_cross_m2_jobs
    )
    files_written["jobs_math_haiku_m3_foil.jsonl"] = write_jsonl(
        C7_DIR / "jobs_math_haiku_m3_foil.jsonl", math_haiku_m3_jobs
    )

    m3_stats = {
        "foil_pos_counts": dict(sorted(m3_foil_pos_counts.items())),
        "tp_right_pos_counts": dict(sorted(m3_tp_right_pos_counts.items())),
    }

    prereg_text = build_prereg_c7_md(
        files_written=files_written,
        c6_stats=c6_stats,
        c4_stats=c4_stats,
        m3_stats=m3_stats,
        c6_pids=c6_pids,
        c4_pids=c4_pids,
    )
    check_no_dashes_text(prereg_text, "PREREG_C7.md")
    prereg_path = C7_DIR / "PREREG_C7.md"
    prereg_path.write_text(prereg_text, encoding="utf-8")

    lock_targets = sorted(list(files_written.keys()) + ["PREREG_C7.md"])
    lock_lines = [f"{sha256_file(C7_DIR / fn)}  {fn}" for fn in lock_targets]
    lock_path = C7_DIR / "C7_LOCKED.sha256"
    lock_path.write_text("\n".join(lock_lines) + "\n", encoding="utf-8")

    return {
        "files": files_written,
        "c6_stats": c6_stats,
        "c4_stats": c4_stats,
        "m3_stats": m3_stats,
        "lockfile": str(lock_path),
    }


def build_prereg_c7_md(
    files_written: Dict[str, int],
    c6_stats: Dict[str, Any],
    c4_stats: Dict[str, Any],
    m3_stats: Dict[str, Any],
    c6_pids: List[str],
    c4_pids: List[str],
) -> str:
    """Build deterministic PREREG_C7.md locking hypotheses, banks, and SHA-256 hashes."""
    sci_sha = sha256_file(C7_DIR / "jobs_science_m2.jsonl")
    haiku_m2_sha = sha256_file(C7_DIR / "jobs_math_haiku_m2.jsonl")
    cross_m2_sha = sha256_file(C7_DIR / "jobs_math_cross_m2.jsonl")
    haiku_m3_sha = sha256_file(C7_DIR / "jobs_math_haiku_m3_foil.jsonl")

    lines = [
        "# Preregistration C7: Compute-Matched Eyewitness-Lineup Mitigation Matrix (Round 2)",
        "",
        "Generated deterministically by `autoloop/build_round2_mitigation.py` using Python 3.9 stdlib.",
        "Locked before any Round 2 (C7) M2 or M3 subject calls are executed.",
        "",
        "## 1. Motivation and Theoretical Anchor",
        "",
        "Round 1 and C3 established the SDT Criterion-Shift Law: pooling candidates in `PICK` lowers "
        "the judge acceptance criterion relative to independent `ISO` verification (`delta c ~ -0.45` "
        "to `-0.53` on Haiku UNSOLVED), inflating target-absent (TA) false alarms without improving "
        "target-present (TP) discrimination. Experiment C7 evaluates three compute-matched mitigation "
        "arms against `PICK` (M0) and `ISO` baselines across scientific hypotheses and competition math.",
        "",
        "## 2. Locked Banks and Deterministic Subsets",
        "",
        f"* **Leg 1 (Science, ResearchBench):** All 30 items (`30 TA + 30 TP = 60` pools, `4` candidates per pool) from `banks/locked_v2/c9_science_pools.json` (`researchbench_pools`).",
        f"* **Leg 2a (Judge-Family-Free Cross-Vendor Math):** Deterministic stratified subset of `{c6_stats['n_problems']}` problems (`{c6_stats['n_contest']}` contest + `{c6_stats['n_arxivmath']}` arxivmath, both TA and TP = `{c6_stats['n_pools']}` pools, `3` candidates per pool) from `banks/locked_v2/c6_crossvendor_math.json` (seeds `{SEED_C6_CONTEST}` and `{SEED_C6_ARXIV}`; TP right-position counts: `{c6_stats['tp_right_pos_counts']}`; zero Gemini and zero GPT candidates).",
        f"* **Leg 2b (Haiku UNSOLVED C3 Math):** Deterministic stratified subset of `{c4_stats['n_problems']}` paired corrected Haiku UNSOLVED C3 problems (both TA and TP = `{c4_stats['n_pools']}` pools, `3` candidates per pool in M2; sources: `{c4_stats['sources']}`; TP right-position counts: `{c4_stats['tp_right_pos_counts']}`) from `banks/locked_v2/c4_haiku_compute.json` (seed `{SEED_C4_HAIKU}`).",
        "",
        "## 3. Mitigation Arms",
        "",
        "* **M0 (Baseline Pooled `PICK`):** Single-call Round 1 `PICK` baseline on the exact matched pools.",
        "* **M1 (Two-Stage `ISO -> PICK` Tie-Breaker):** Stage 1 reads completed `ISO` verdicts per candidate. Pools with `0` accepted candidates resolve deterministically to `NONE` (`0` extra calls). Pools with `1` accepted candidate resolve deterministically to that candidate (`0` extra calls). Pools with `k >= 2` accepted candidates invoke a single Stage 2 `PICK-k` tie-breaker restricted to the accepted subset (`jobs_*_m1_tiebreak.jsonl` generated via `--mode generate_m1`).",
        f"* **M2 (Falsification-First Criterion Recalibration Gate):** Single-call pooled prompt requiring independent per-candidate falsification (identifying concrete errors or unsupported leaps) before comparing candidates, coupled with a locked certainty threshold `tau = {CALIBRATION_CONF_TAU}` (`CONFIDENCE >= 4` on the 1 to 5 scale; otherwise `CHOICE: NONE`). Both raw `CHOICE` and threshold-enforced `CHOICE_GATE4` (`NONE` if `CONFIDENCE < 4`) are logged.",
        f"* **M3 (Mock-Witness / Known-Foil Calibrated Lineup, Wells C-D3):** Inserts `1` deterministic known-wrong donor foil from another problem in `c4_haiku_compute.json` (verified `math_equal` false against gold and all 3 real candidate answers) into each Haiku C3 pool (`4` candidates total; Latin-balanced `foil_pos` counts `{m3_stats['foil_pos_counts']}`; TP right-position counts `{m3_stats['tp_right_pos_counts']}`). Instructs the judge to first inspect and reject flawed/decoy candidates before selecting among survivors.",
        "",
        "## 4. Preregistered Confirmatory Hypotheses (Holm-Corrected at alpha = 0.05, 5,000 Problem Bootstraps)",
        "",
        "* **H_C7a (TA False-Alarm Reduction vs PICK):** Paired `FA(M_arm) minus FA(PICK) < 0` on TA pools (one-sided bootstrap) for M1, M2, and M3 across Haiku C3 Math, Cross-Vendor Math, and ResearchBench Science.",
        "* **H_C7b (Criterion Restoration Toward ISO):** Paired `c(M_arm) minus c(PICK) > 0` (shifting `c` back toward `c(ISO)`), quantifying how much of `delta c(PICK minus ISO)` is recovered by M1, M2, and M3.",
        "* **H_C7c (TP Hit Retention vs ISO and PICK):** Non-inferiority of aligned TP hit rate `H_aligned(M_arm) minus H_aligned(ISO) >= -0.05` and net Hautus sensitivity gain `d'(M_arm) minus d'(PICK) > 0`.",
        "* **H_C7d (M3 Foil Rejection Audit):** In M3, the judge selects `foil_pos` at rate `< 0.05` on both TA and TP pools; any foil selection is flagged as an attention/calibration failure.",
        "",
        "## 5. Gate and Kill Rules",
        "",
        "* **Parse Gate:** Parsed `CHOICE` rate `>= 0.90` (and parsed `CONFIDENCE` rate `>= 0.90` for M2) per model and bank.",
        "* **Calibration / Failure Kill:** An intervention arm is flagged as ineffective if on UNSOLVED math or science it fails to reduce TA false alarms by at least `0.10` relative to `PICK` (`FA(M_arm) minus FA(PICK) > -0.10`), OR if it reduces `FA` only by collapsing `TP` hits (`H_aligned(M_arm) minus H_aligned(ISO) < -0.05` with 95% CI upper bound `< 0`), yielding no net improvement in `d'`.",
        "* **Budget Guard:** Subscription CLI routes only (`claude_cli` and `agy`, `OOP_MAX_USD=0`).",
        "",
        "## 6. Locked Job Files and SHA-256 Digests (`C7_LOCKED.sha256`)",
        "",
        "| File | Jobs | SHA-256 |",
        "|---|---:|---|",
        f"| `jobs_science_m2.jsonl` | {files_written['jobs_science_m2.jsonl']} | `{sci_sha}` |",
        f"| `jobs_math_haiku_m2.jsonl` | {files_written['jobs_math_haiku_m2.jsonl']} | `{haiku_m2_sha}` |",
        f"| `jobs_math_cross_m2.jsonl` | {files_written['jobs_math_cross_m2.jsonl']} | `{cross_m2_sha}` |",
        f"| `jobs_math_haiku_m3_foil.jsonl` | {files_written['jobs_math_haiku_m3_foil.jsonl']} | `{haiku_m3_sha}` |",
        "",
        "### Selected Problem IDs",
        "",
        f"* `c6_crossvendor_math` (40 problems): `{', '.join(c6_pids)}`",
        f"* `c4_haiku_compute` (40 problems): `{', '.join(c4_pids)}`",
        "",
    ]
    return "\n".join(lines)


def _read_iso_verdict_from_dir(iso_dir: Path, cid: str, judge_prefix: Optional[str]) -> Optional[bool]:
    """Read and parse an ISO verdict for candidate cid from v1 or v2 raw JSON."""
    candidates: List[Path] = []
    if judge_prefix:
        candidates.append(iso_dir / f"{judge_prefix}__ISO__{cid}.json")
    candidates.append(iso_dir / f"ISO__{cid}.json")
    candidates.append(iso_dir / f"haiku__ISO__{cid}.json")
    for path in candidates:
        if not path.is_file():
            continue
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if "status" in rec:
            if rec.get("status") != "ok":
                return None
            txt = rec.get("text")
        else:
            if rec.get("rc") not in (None, 0):
                return None
            txt = rec.get("result")
        return parsers.verdict(txt)
    return None


def generate_m1_for_source(
    tag: str,
    domain: str,
    pools: List[Dict[str, Any]],
    iso_dir: Path,
    judge_prefix: Optional[str] = None,
    model_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Build Stage 1 M1 resolution manifest and PICK-k tie-breaker JSONL for k >= 2 pools."""
    if not iso_dir.is_dir():
        return {"tag": tag, "status": "skipped_missing_dir", "iso_dir": str(iso_dir)}

    tiebreak_jobs: List[Dict[str, Any]] = []
    pool_records: List[Dict[str, Any]] = []
    counts = Counter()
    incomplete = 0

    for p in pools:
        verdicts: List[Optional[bool]] = [
            _read_iso_verdict_from_dir(iso_dir, c["cid"], judge_prefix) for c in p["cands"]
        ]
        if any(v is None for v in verdicts):
            incomplete += 1
            counts["incomplete"] += 1
            pool_records.append(
                {
                    "pool": p["pool"],
                    "kind": p["kind"],
                    "status": "incomplete",
                    "verdicts": verdicts,
                }
            )
            continue

        accepted_indices_1idx = [idx + 1 for idx, v in enumerate(verdicts) if v is True]
        accepted_cands = [p["cands"][idx - 1] for idx in accepted_indices_1idx]
        k = len(accepted_cands)
        counts[f"k_{k}"] += 1

        if k == 0:
            pool_records.append(
                {
                    "pool": p["pool"],
                    "kind": p["kind"],
                    "status": "resolved_deterministic",
                    "n_accepted": 0,
                    "accepted_orig_positions_1idx": [],
                    "deterministic_choice_1idx": 0,
                }
            )
        elif k == 1:
            pool_records.append(
                {
                    "pool": p["pool"],
                    "kind": p["kind"],
                    "status": "resolved_deterministic",
                    "n_accepted": 1,
                    "accepted_orig_positions_1idx": accepted_indices_1idx,
                    "accepted_cids": [accepted_cands[0]["cid"]],
                    "deterministic_choice_1idx": accepted_indices_1idx[0],
                }
            )
        else:
            job_id = f"M1_TIEBREAK__{tag}__{p['pool']}"
            if domain == "science":
                prompt = science_pick_prompt(
                    p["research_question"], p["abstract"], accepted_cands
                )
            else:
                prompt = math_pick_prompt(p["problem"], accepted_cands)

            rpos_orig = get_right_pos_1idx(p)
            rpos_sub: Optional[int] = None
            if rpos_orig is not None and rpos_orig in accepted_indices_1idx:
                rpos_sub = accepted_indices_1idx.index(rpos_orig) + 1

            job: Dict[str, Any] = {
                "id": job_id,
                "pool": p["pool"],
                "kind": p["kind"],
                "arm": f"M1_PICK{k}",
                "domain": domain,
                "n_cands": k,
                "orig_n_cands": len(p["cands"]),
                "accepted_orig_positions_1idx": accepted_indices_1idx,
                "accepted_cids": [c["cid"] for c in accepted_cands],
                "right_pos_1idx": rpos_sub,
                "orig_right_pos_1idx": rpos_orig,
                "timeout": DEFAULT_TIMEOUT_S,
                "prompt": prompt,
            }
            if "pid" in p:
                job["pid"] = p["pid"]
            if "source" in p:
                job["source"] = p["source"]
            if "comp" in p:
                job["comp"] = p["comp"]
            if "item" in p:
                job["item"] = p["item"]
            if "doi" in p:
                job["doi"] = p["doi"]
            if model_hint:
                job["model"] = model_hint
            tiebreak_jobs.append(job)

            pool_records.append(
                {
                    "pool": p["pool"],
                    "kind": p["kind"],
                    "status": "needs_tiebreak",
                    "n_accepted": k,
                    "accepted_orig_positions_1idx": accepted_indices_1idx,
                    "accepted_cids": [c["cid"] for c in accepted_cands],
                    "tiebreak_job_id": job_id,
                }
            )

    resolved_total = len(pools) - incomplete
    if resolved_total == 0:
        return {
            "tag": tag,
            "status": "skipped_no_complete_pools",
            "iso_dir": str(iso_dir),
            "incomplete": incomplete,
        }

    plan_path = C7_DIR / f"m1_stage1_{tag}.json"
    jobs_path = C7_DIR / f"jobs_{tag}_m1_tiebreak.jsonl"
    write_jsonl(jobs_path, tiebreak_jobs)
    summary = {
        "tag": tag,
        "domain": domain,
        "iso_dir": str(iso_dir),
        "total_pools": len(pools),
        "resolved_pools": resolved_total,
        "incomplete_pools": incomplete,
        "counts": dict(sorted(counts.items())),
        "tiebreak_jobs": len(tiebreak_jobs),
        "jobs_file": str(jobs_path),
        "pools": pool_records,
    }
    plan_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {
        "tag": tag,
        "status": "ok",
        "resolved_pools": resolved_total,
        "incomplete_pools": incomplete,
        "tiebreak_jobs": len(tiebreak_jobs),
        "counts": dict(sorted(counts.items())),
        "plan_file": str(plan_path),
        "jobs_file": str(jobs_path),
    }


def run_generate_m1(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Run M1 Stage 2 tie-breaker generation for custom or standard completed ISO folders."""
    C7_DIR.mkdir(parents=True, exist_ok=True)
    sci_pools = load_c9_researchbench_pools()
    c6_pools, _, _ = load_c6_crossvendor_subset()
    c4_pools, _, _, _ = load_c4_haiku_subset()

    if args.iso_dir:
        iso_path = Path(args.iso_dir)
        bank_map = {
            "science": ("science", sci_pools),
            "math_cross": ("math", c6_pools),
            "math_haiku": ("math", c4_pools),
        }
        domain, pools = bank_map[args.bank]
        tag = args.tag or f"{args.bank}_custom"
        return [
            generate_m1_for_source(
                tag=tag,
                domain=domain,
                pools=pools,
                iso_dir=iso_path,
                judge_prefix=args.judge_prefix,
                model_hint=args.model,
            )
        ]

    specs = [
        ("math_haiku_c3", "math", c4_pools, V1_C3_RAW_ARMS, "haiku", "haiku"),
        ("science_haiku", "science", sci_pools, C6_EXPS_DIR / "raw_science_haiku_iso", None, "haiku"),
        ("science_gptoss", "science", sci_pools, C6_EXPS_DIR / "raw_science_gptoss_iso", None, "gpt-oss-120b-medium"),
        ("science_gemini", "science", sci_pools, C6_EXPS_DIR / "raw_science_gemini_iso", None, "gemini-3.8-flash-medium"),
        ("math_gptoss", "math", c6_pools, C6_EXPS_DIR / "raw_math_gptoss_iso", None, "gpt-oss-120b-medium"),
        ("math_gemini", "math", c6_pools, C6_EXPS_DIR / "raw_math_gemini_iso", None, "gemini-3.8-flash-medium"),
    ]
    results = []
    for tag, domain, pools, iso_dir, jprefix, mhint in specs:
        results.append(
            generate_m1_for_source(
                tag=tag,
                domain=domain,
                pools=pools,
                iso_dir=iso_dir,
                judge_prefix=jprefix,
                model_hint=mhint,
            )
        )
    return results


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build Round 2 (C7) mitigation job JSONLs, preregistration, and M1 tie-breakers."
    )
    p.add_argument(
        "--mode",
        choices=["generate_m2_m3", "generate_m1", "all"],
        default="generate_m2_m3",
        help="Which mitigation artifacts to generate (default: generate_m2_m3).",
    )
    p.add_argument("--iso-dir", default=None, help="Optional single ISO raw folder for --mode generate_m1.")
    p.add_argument(
        "--bank",
        choices=["science", "math_cross", "math_haiku"],
        default="math_haiku",
        help="Target pool bank when --iso-dir is specified.",
    )
    p.add_argument("--tag", default=None, help="Output tag when --iso-dir is specified.")
    p.add_argument("--judge-prefix", default=None, help="Optional filename prefix such as 'haiku'.")
    p.add_argument("--model", default=None, help="Optional model field hint for M1 tie-breaker jobs.")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    verify_v2_bank_lock()

    out: Dict[str, Any] = {"mode": args.mode}
    if args.mode in ("generate_m2_m3", "all"):
        out["m2_m3"] = build_m2_and_m3_jobs()
    if args.mode in ("generate_m1", "all"):
        out["m1"] = run_generate_m1(args)

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
