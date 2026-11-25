#!/usr/bin/env python3
"""Build locked v2 banks and Round 1 job JSONLs under v2-upgrade/.

Pure Python 3.9 stdlib only (no third-party packages).
Produces:
  banks/locked_v2/c6_crossvendor_math.json
  banks/locked_v2/c6_claude_free_math.json
  banks/locked_v2/c4_haiku_compute.json
  banks/locked_v2/c5_haiku_removal.json
  banks/locked_v2/c9_science_pools.json
  banks/locked_v2/BANK_MANIFEST.md
  banks/locked_v2/LOCKED.sha256
  exps/c4_compute/jobs_haiku.jsonl
  exps/c5_removal/jobs_haiku_own_removal.jsonl
  exps/c5_removal/jobs_haiku_wells.jsonl
  exps/c6_crossvendor/jobs_math_solve.jsonl
  exps/c6_crossvendor/jobs_math_iso.jsonl
  exps/c6_crossvendor/jobs_math_pick.jsonl
  exps/c6_crossvendor/jobs_math_each.jsonl
  exps/c6_crossvendor/jobs_science_iso.jsonl
  exps/c6_crossvendor/jobs_science_pick.jsonl
  exps/c6_crossvendor/jobs_science_each.jsonl
"""
import csv
import glob
import hashlib
import json
import math
import os
import random
import re
import string
import sys
from collections import Counter

V1_DIR = "/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar"
V2_DIR = "/Users/chaitanya/research/mas-study/v2-upgrade"
X6_DIR = "/Users/chaitanya/research/mas-study/09-autoresearch/09-autoresearch/exp/x6-researchbench-lineup"
X1C_DIR = "/Users/chaitanya/research/mas-study/09-autoresearch/09-autoresearch/exp/x1c-confirmatory"

BANKS_OUT = os.path.join(V2_DIR, "banks", "locked_v2")
EXPS_OUT = os.path.join(V2_DIR, "exps")

sys.path.insert(0, os.path.join(V1_DIR, "harness"))
import lineup_prompts as LP  # noqa: E402
import parse  # noqa: E402

C6_SEED = 20261120
POOL_SOURCES = [
    ("locked_c3", os.path.join(V1_DIR, "banks", "locked_c3", "pools.json")),
    ("confirm", os.path.join(V1_DIR, "banks", "locked_ma", "confirm_pools.json")),
    ("replication", os.path.join(V1_DIR, "banks", "locked_ma", "replication_pools.json")),
    ("s1_lineup", os.path.join(V1_DIR, "exps", "screens", "s1_lineup", "pools.json")),
]

VENDORS = (
    "claude",
    "gemini",
    "gpt",
    "deepseek",
    "qwen",
    "glm",
    "grok",
    "kimi",
    "mistral",
    "other",
)


def classify_vendor(gen):
    """Map candidate generator string to canonical vendor family."""
    gl = gen.lower()
    if "claude" in gl:
        return "claude"
    if "gemini" in gl:
        return "gemini"
    if gl.startswith("gpt") or re.match(r"^o[134](-|\b)", gl):
        return "gpt"
    if "deepseek" in gl:
        return "deepseek"
    if "qwen" in gl:
        return "qwen"
    if gl.startswith("glm"):
        return "glm"
    if "grok" in gl:
        return "grok"
    if "kimi" in gl or gl.startswith("k2-think"):
        return "kimi"
    if "mistral" in gl:
        return "mistral"
    return "other"


def classify_source(comp):
    """Classify competition identifier into arxivmath vs contest."""
    return "arxivmath" if comp.startswith("arxivmath") else "contest"


def normalize_problem(text):
    """Normalize problem text by lowercasing and stripping whitespace and punctuation."""
    return re.sub(r"[\s" + re.escape(string.punctuation) + r"]+", "", text.lower())


def enrich_pool(pool, origin_file):
    """Return a copy of pool enriched with source and candidate vendor fields."""
    cands = []
    for c in pool["cands"]:
        c_new = dict(c)
        c_new["vendor"] = classify_vendor(c["gen"])
        cands.append(c_new)
    return {
        "pool": pool["pool"],
        "pid": pool["pid"],
        "comp": pool["comp"],
        "origin_file": origin_file,
        "source": classify_source(pool["comp"]),
        "kind": pool["kind"],
        "problem": pool["problem"],
        "gold": pool["gold"],
        "roles": [c["role"] for c in cands],
        "answers": [c["answer"] for c in cands],
        "gens": [c["gen"] for c in cands],
        "vendors": [c["vendor"] for c in cands],
        "cands": cands,
    }


def apply_latin_shift(cands, shift, is_tp):
    """Deterministically canonicalize and cyclically rotate 3 candidates by shift."""
    if is_tp:
        right = [c for c in cands if c["role"] == "right"]
        wrong = sorted([c for c in cands if c["role"] == "wrong"], key=lambda c: c["cid"])
        if len(right) != 1 or len(wrong) != 2:
            raise AssertionError(f"Expected 1 right + 2 wrong in TP, got {len(right)}+{len(wrong)}")
        base = right + wrong
    else:
        if len(cands) != 3 or any(c["role"] != "wrong" for c in cands):
            raise AssertionError(f"Expected 3 wrong in TA, got {[c['role'] for c in cands]}")
        base = sorted(cands, key=lambda c: c["cid"])
    return [dict(base[(pos - shift) % 3]) for pos in range(3)]


def rebuild_pool_with_cands(pool, new_cands, extra=None):
    """Return pool dict with updated cands and synchronized metadata lists."""
    out = dict(pool)
    out["cands"] = new_cands
    out["roles"] = [c["role"] for c in new_cands]
    out["answers"] = [c["answer"] for c in new_cands]
    out["gens"] = [c["gen"] for c in new_cands]
    out["vendors"] = [c["vendor"] for c in new_cands]
    if extra:
        out.update(extra)
    return out


def chi2_uniform_df2(counts):
    """Compute Pearson chi-square statistic and exact p-value for 3 equiprobable bins."""
    total = sum(counts)
    if total == 0:
        return 0.0, 1.0
    exp = total / 3.0
    stat = sum((c - exp) ** 2 / exp for c in counts)
    pval = math.exp(-stat / 2.0)
    return stat, pval


def chi2_uniform_df3(counts):
    """Compute Pearson chi-square statistic and exact p-value for 4 equiprobable bins."""
    total = sum(counts)
    if total == 0:
        return 0.0, 1.0
    exp = total / 4.0
    stat = sum((c - exp) ** 2 / exp for c in counts)
    pval = math.erfc(math.sqrt(stat / 2.0)) + math.sqrt(2.0 * stat / math.pi) * math.exp(-stat / 2.0)
    return stat, min(1.0, pval)


def load_deduped_matharena():
    """Load all MathArena pools, exclude bad labels and duplicates, require paired TA+TP."""
    c3_dir = os.path.join(V1_DIR, "exps", "c3")
    bad_pids = {
        r["pid"] for r in csv.DictReader(open(os.path.join(c3_dir, "candidate_label_audit.csv")))
    }
    dups_raw = json.load(open(os.path.join(c3_dir, "duplicates_of_used.json")))
    dup_pids = set(dups_raw.keys() if isinstance(dups_raw, dict) else dups_raw)
    excluded_pids = bad_pids | dup_pids

    seen_norm = {}
    paired_items = []
    stats = {
        "raw_pool_rows": 0,
        "excluded_bad_or_dup_pid": 0,
        "dropped_unpaired": 0,
        "dropped_norm_duplicate": 0,
    }

    for origin_name, path in POOL_SOURCES:
        raw_pools = json.load(open(path))
        stats["raw_pool_rows"] += len(raw_pools)
        by_pid = {}
        for p in raw_pools:
            by_pid.setdefault(p["pid"], {})[p["kind"]] = p

        for pid in sorted(by_pid.keys()):
            if pid in excluded_pids:
                stats["excluded_bad_or_dup_pid"] += 1
                continue
            kinds = by_pid[pid]
            if "TA" not in kinds or "TP" not in kinds:
                stats["dropped_unpaired"] += 1
                continue
            ta = enrich_pool(kinds["TA"], origin_name)
            tp = enrich_pool(kinds["TP"], origin_name)
            if len(ta["cands"]) != 3 or any(r != "wrong" for r in ta["roles"]):
                raise AssertionError(f"Invalid TA pool structure for {pid}")
            if len(tp["cands"]) != 3 or tp["roles"].count("right") != 1 or tp["roles"].count("wrong") != 2:
                raise AssertionError(f"Invalid TP pool structure for {pid}")
            norm_key = normalize_problem(ta["problem"])
            if norm_key in seen_norm:
                stats["dropped_norm_duplicate"] += 1
                continue
            seen_norm[norm_key] = (origin_name, pid)
            paired_items.append({"pid": pid, "source": ta["source"], "ta": ta, "tp": tp})

    return paired_items, stats


def build_c6_banks(paired_items):
    """Build c6_crossvendor_math.json and c6_claude_free_math.json."""
    # 1. Cross-vendor math: zero Gemini AND zero GPT/o1/o3/o4 in both TA and TP
    eligible_cv = []
    for item in paired_items:
        all_v = set(item["ta"]["vendors"]) | set(item["tp"]["vendors"])
        if "gemini" not in all_v and "gpt" not in all_v:
            eligible_cv.append(item)

    rng = random.Random(C6_SEED)
    by_src = {
        "contest": sorted([x for x in eligible_cv if x["source"] == "contest"], key=lambda x: x["pid"]),
        "arxivmath": sorted([x for x in eligible_cv if x["source"] == "arxivmath"], key=lambda x: x["pid"]),
    }
    rng.shuffle(by_src["contest"])
    rng.shuffle(by_src["arxivmath"])
    sel_contest = sorted(by_src["contest"][:50], key=lambda x: x["pid"])
    sel_arxiv = sorted(by_src["arxivmath"][:50], key=lambda x: x["pid"])

    cv_pools = []
    cv_selected_items = []
    for src_name, items in (("contest", sel_contest), ("arxivmath", sel_arxiv)):
        src_offset = 0 if src_name == "contest" else 1
        for idx, item in enumerate(items):
            shift = (idx + src_offset) % 3
            ta_rot = apply_latin_shift(item["ta"]["cands"], shift, is_tp=False)
            tp_rot = apply_latin_shift(item["tp"]["cands"], shift, is_tp=True)
            right_pos = next(i + 1 for i, c in enumerate(tp_rot) if c["role"] == "right")
            ta_out = rebuild_pool_with_cands(item["ta"], ta_rot, {"latin_shift": shift})
            tp_out = rebuild_pool_with_cands(
                item["tp"], tp_rot, {"latin_shift": shift, "right_pos_1idx": right_pos}
            )
            cv_pools.extend([ta_out, tp_out])
            cv_selected_items.append({"pid": item["pid"], "source": src_name, "ta": ta_out, "tp": tp_out})

    # Assert zero Gemini / zero GPT
    for p in cv_pools:
        if any(v in ("gemini", "gpt") for v in p["vendors"]):
            raise AssertionError(f"Vendor leak in c6_crossvendor_math: {p['pool']} {p['vendors']}")

    c6_cv_bank = {
        "meta": {
            "bank_name": "c6_crossvendor_math",
            "seed": C6_SEED,
            "excluded_judge_vendors": ["gemini", "gpt"],
            "n_problems": len(cv_selected_items),
            "n_contest": len(sel_contest),
            "n_arxivmath": len(sel_arxiv),
            "n_pools": len(cv_pools),
            "eligible_pool_universe": {
                "total": len(eligible_cv),
                "contest": len(by_src["contest"]),
                "arxivmath": len(by_src["arxivmath"]),
            },
            "rotation": "deterministic 3x3 Latin square across sorted pids per source",
        },
        "pools": cv_pools,
    }

    # 2. Claude-free math: ALL deduplicated paired items with zero Claude in TA and TP
    claude_free = []
    for item in paired_items:
        all_v = set(item["ta"]["vendors"]) | set(item["tp"]["vendors"])
        if "claude" not in all_v:
            claude_free.append(item)
    claude_free.sort(key=lambda x: (x["source"], x["pid"]))

    cf_pools = []
    for idx, item in enumerate(claude_free):
        shift = idx % 3
        ta_rot = apply_latin_shift(item["ta"]["cands"], shift, is_tp=False)
        tp_rot = apply_latin_shift(item["tp"]["cands"], shift, is_tp=True)
        right_pos = next(i + 1 for i, c in enumerate(tp_rot) if c["role"] == "right")
        cf_pools.append(rebuild_pool_with_cands(item["ta"], ta_rot, {"latin_shift": shift}))
        cf_pools.append(
            rebuild_pool_with_cands(item["tp"], tp_rot, {"latin_shift": shift, "right_pos_1idx": right_pos})
        )

    for p in cf_pools:
        if "claude" in p["vendors"]:
            raise AssertionError(f"Claude leak in c6_claude_free_math: {p['pool']}")

    cf_counts = Counter(item["source"] for item in claude_free)
    c6_cf_bank = {
        "meta": {
            "bank_name": "c6_claude_free_math",
            "excluded_judge_vendors": ["claude"],
            "n_problems": len(claude_free),
            "n_contest": cf_counts["contest"],
            "n_arxivmath": cf_counts["arxivmath"],
            "n_pools": len(cf_pools),
            "rotation": "deterministic 3x3 Latin square across sorted items",
        },
        "pools": cf_pools,
    }

    return c6_cv_bank, c6_cf_bank, cv_selected_items


def build_c4_and_c5_banks():
    """Build c4_haiku_compute.json and c5_haiku_removal.json from C3 data."""
    c3_dir = os.path.join(V1_DIR, "exps", "c3")
    c3_pools = json.load(open(os.path.join(V1_DIR, "banks", "locked_c3", "pools.json")))
    ta_map = {p["pid"]: enrich_pool(p, "locked_c3") for p in c3_pools if p["kind"] == "TA"}
    tp_map = {p["pid"]: enrich_pool(p, "locked_c3") for p in c3_pools if p["kind"] == "TP"}

    strata = json.load(open(os.path.join(c3_dir, "strata.json")))
    audit = {
        r["pid"]: r["audited_stratum"]
        for r in csv.DictReader(open(os.path.join(c3_dir, "audit_unsolved.csv")))
    }
    bad_pids = {
        r["pid"] for r in csv.DictReader(open(os.path.join(c3_dir, "candidate_label_audit.csv")))
    }
    dups_raw = json.load(open(os.path.join(c3_dir, "duplicates_of_used.json")))
    dup_pids = set(dups_raw.keys() if isinstance(dups_raw, dict) else dups_raw)

    prereg_uns = sorted(pid for pid in strata["selected"] if strata["stratum"][pid] == "UNSOLVED")
    corr_uns = sorted(
        pid
        for pid in strata["selected"]
        if pid not in bad_pids
        and pid not in dup_pids
        and audit.get(pid, strata["stratum"][pid]) == "UNSOLVED"
    )
    if len(corr_uns) != 68:
        raise AssertionError(f"Expected 68 corrected UNSOLVED problems, got {len(corr_uns)}")

    # C4 bank: 68 TA + 56 TP = 124 pools
    c4_pools = []
    n_tp = 0
    for pid in corr_uns:
        c4_pools.append(ta_map[pid])
        if pid in tp_map:
            c4_pools.append(tp_map[pid])
            n_tp += 1
    if n_tp != 56:
        raise AssertionError(f"Expected 56 paired TP in C4, got {n_tp}")

    c4_bank = {
        "meta": {
            "bank_name": "c4_haiku_compute",
            "stratum": "corrected_haiku_UNSOLVED",
            "n_problems": len(corr_uns),
            "n_ta": len(corr_uns),
            "n_tp": n_tp,
            "n_ta_only": len(corr_uns) - n_tp,
            "n_pools": len(c4_pools),
            "repeats_per_pool": 3,
        },
        "pools": c4_pools,
    }

    # C5 part (a): 38 clean 1-own-answer UNSOLVED TA pools with own candidate removed
    own_rows = {}
    for r in csv.DictReader(open(os.path.join(c3_dir, "own_answer_checks.csv"))):
        pos = [int(x) for x in r["own_answer_candidate_positions"].split(";") if x.strip()]
        own_rows[r["pid"]] = pos

    corr_set = set(corr_uns)
    own_removal_pools = []
    for pid in prereg_uns:
        positions = own_rows.get(pid, [])
        if len(positions) != 1:
            continue
        rem_pos = positions[0]
        orig = ta_map[pid]
        rem_cand = orig["cands"][rem_pos - 1]
        kept = [dict(c) for idx, c in enumerate(orig["cands"]) if idx != rem_pos - 1]
        own_removal_pools.append(
            rebuild_pool_with_cands(
                orig,
                kept,
                {
                    "removal_type": "own_answer",
                    "removed_pos_1idx": rem_pos,
                    "removed_cid": rem_cand["cid"],
                    "retained_cids": [c["cid"] for c in kept],
                    "is_corrected_unsolved": pid in corr_set,
                },
            )
        )
    if len(own_removal_pools) != 38:
        raise AssertionError(f"Expected 38 1-own-answer pools, got {len(own_removal_pools)}")

    # C5 part (b): Wells removal on corrected UNSOLVED TA pools where Haiku PICK chose k in {1, 2, 3}
    raw_arms = {}
    for f in glob.glob(os.path.join(c3_dir, "raw", "arms", "*.json")):
        rec = json.load(open(f))
        raw_arms[rec["id"]] = rec

    wells_pools = []
    wells_none_count = 0
    for pid in corr_uns:
        orig = ta_map[pid]
        rec = raw_arms.get(f"haiku__PICK__{orig['pool']}")
        if rec is None:
            raise AssertionError(f"Missing C3 Haiku PICK record for {orig['pool']}")
        choice_k = parse.choice(rec["result"], 3)
        if choice_k is None:
            raise AssertionError(f"Unparseable C3 Haiku PICK for {orig['pool']}")
        if choice_k == 0:
            wells_none_count += 1
            continue
        rem_cand = orig["cands"][choice_k - 1]
        kept = [dict(c) for idx, c in enumerate(orig["cands"]) if idx != choice_k - 1]
        wells_pools.append(
            rebuild_pool_with_cands(
                orig,
                kept,
                {
                    "removal_type": "wells_pick",
                    "c3_pick_choice_1idx": choice_k,
                    "removed_cid": rem_cand["cid"],
                    "retained_cids": [c["cid"] for c in kept],
                },
            )
        )

    c5_bank = {
        "meta": {
            "bank_name": "c5_haiku_removal",
            "n_own_answer_removal": len(own_removal_pools),
            "n_own_answer_removal_corrected_unsolved": sum(
                1 for p in own_removal_pools if p["is_corrected_unsolved"]
            ),
            "n_wells_source_pools": len(corr_uns),
            "n_wells_none_in_c3": wells_none_count,
            "n_wells_removal": len(wells_pools),
        },
        "own_answer_removal": own_removal_pools,
        "wells_removal": wells_pools,
    }

    return c4_bank, c5_bank


def build_c9_science_bank():
    """Build c9_science_pools.json from x6 ResearchBench and x1c synthetic companion."""
    rb_rows = [json.loads(l) for l in open(os.path.join(X6_DIR, "data", "tiny_ranking.jsonl"))]
    rb_papers = [json.loads(l) for l in open(os.path.join(X6_DIR, "data", "tiny_papers.jsonl"))]
    design = json.load(open(os.path.join(X6_DIR, "design.json")))

    # Index row -> research question, abstract, and candidate texts
    row_info = {}
    cand_texts = {}
    for ri, (r_row, p_row) in enumerate(zip(rb_rows, rb_papers)):
        if r_row["doi"] != p_row["doi"]:
            continue
        row_info[ri] = {
            "doi": r_row["doi"],
            "discipline": r_row["discipline"],
            "title": p_row["title"],
            "research_question": r_row["research_question"],
            "abstract": p_row["abstract"],
        }
        cand_texts[f"r{ri}_gold"] = {"text": r_row["gold_hypothesis"], "kind": "gold", "role": "right"}
        negs = [("fake", h) for h in r_row["fake_negative_hypotheses"]] + [
            ("model", h) for h in r_row["model_negative_hypotheses"]
        ]
        rng = random.Random(ri)
        rng.shuffle(negs)
        for s in range(3):
            cset = negs[4 * s : 4 * s + 4]
            for k, (kind, hyp) in enumerate(cset):
                cid = f"r{ri}s{s}_n{k}"
                cand_texts[cid] = {"text": hyp, "kind": kind, "role": "wrong"}

    if len(cand_texts) != 130:
        raise AssertionError(f"Expected 130 x6 candidates, got {len(cand_texts)}")

    rb_pools = []
    for item in design["items"]:
        iid = item["item"]
        ri = item["row"]
        info = row_info[ri]
        if info["doi"] != item["doi"]:
            raise AssertionError(f"DOI mismatch for {iid}")

        for kind, order_key in (("TA", "pool0_order"), ("TP", "pool1_order")):
            cands = []
            for cid in item[order_key]:
                c_meta = cand_texts[cid]
                cands.append(
                    {
                        "cid": cid,
                        "text": c_meta["text"],
                        "role": c_meta["role"],
                        "neg_source": c_meta["kind"],
                    }
                )
            pool_entry = {
                "pool": f"{iid}_{kind}",
                "item": iid,
                "row": ri,
                "doi": info["doi"],
                "discipline": info["discipline"],
                "title": info["title"],
                "kind": kind,
                "research_question": info["research_question"],
                "abstract": info["abstract"],
                "roles": [c["role"] for c in cands],
                "cands": cands,
            }
            if kind == "TP":
                pool_entry["right_pos_1idx"] = next(
                    i + 1 for i, c in enumerate(cands) if c["role"] == "right"
                )
            rb_pools.append(pool_entry)

    # Synthetic companion bank from x1c-confirmatory
    x1c_probs = json.load(open(os.path.join(X1C_DIR, "problems.json")))
    x1c_meta = json.load(open(os.path.join(X1C_DIR, "meta.json")))
    x1c_pools = []
    for idx, prob in enumerate(x1c_probs):
        pid = prob["pid"]
        cal48 = idx < 48  # First 12 rounds x 4 families = 48 balanced calibration problems
        for kind, meta_prefix in (("TA", "POOL0R1"), ("TP", "POOL1")):
            m = x1c_meta[f"{meta_prefix}__{pid}"]
            cands = []
            for c_id_local, text in m["members"]:
                role = "right" if c_id_local == "c0" else "wrong"
                cands.append({"cid": f"{pid}_{c_id_local}", "text": text, "role": role})
            entry = {
                "pool": f"{pid}_{kind}",
                "pid": pid,
                "family": prob["family"],
                "law": prob["law"],
                "kind": kind,
                "context": prob["context"],
                "calibration_48_subset": cal48,
                "roles": [c["role"] for c in cands],
                "cands": cands,
            }
            if kind == "TP":
                entry["right_pos_1idx"] = next(
                    i + 1 for i, c in enumerate(cands) if c["role"] == "right"
                )
            x1c_pools.append(entry)

    return {
        "meta": {
            "bank_name": "c9_science_pools",
            "n_researchbench_items": len(design["items"]),
            "n_researchbench_papers": len(row_info),
            "n_researchbench_pools": len(rb_pools),
            "n_researchbench_unique_cands": len(cand_texts),
            "n_synthetic_x1c_problems": len(x1c_probs),
            "n_synthetic_x1c_pools": len(x1c_pools),
            "n_synthetic_x1c_calibration_48_problems": sum(1 for i in range(len(x1c_probs)) if i < 48),
            "note_x1c": "x1c-confirmatory has 72 total problems (18 per family); first 48 (12 per family) flagged calibration_48_subset=True.",
        },
        "researchbench_pools": rb_pools,
        "synthetic_x1c_pools": x1c_pools,
    }


def science_iso_prompt(q, a, hyp_text):
    """ResearchBench ISO prompt preserving x6 evidence format and lineup_prompts VERDICT ending."""
    return (
        "You are verifying scientific hypotheses against a published study.\n\n"
        f"Research question:\n{q}\n\n"
        f"Evidence (the study's abstract):\n{a}\n\n"
        f"Candidate hypothesis:\n{hyp_text.strip()}\n\n"
        "Is this candidate the main hypothesis that this study's evidence supports? "
        "ACCEPT only if the evidence supports it as the study's hypothesis; otherwise REJECT. "
        "Check the evidence as carefully as you need to. "
        "End your reply with exactly one line: VERDICT: ACCEPT or VERDICT: REJECT"
    )


def science_pool_head(q, a, cands):
    """ResearchBench pool header preserving x6 evidence format and 4 numbered hypotheses."""
    n = len(cands)
    body = "\n\n".join(f"Hypothesis {i + 1}:\n{c['text'].strip()}" for i, c in enumerate(cands))
    return n, (
        "You are verifying scientific hypotheses against a published study.\n\n"
        f"Research question:\n{q}\n\n"
        f"Evidence (the study's abstract):\n{a}\n\n"
        f"Candidate hypotheses:\n{body}\n\n"
    )


def science_pick_prompt(q, a, cands):
    """ResearchBench PICK prompt matching lineup_prompts CHOICE ending."""
    n, head = science_pool_head(q, a, cands)
    return (
        head
        + "Which hypothesis is the main hypothesis that this study's evidence supports, if any? "
        "It is possible that none of them is correct. Check the evidence as carefully as you need to. "
        f"End your reply with exactly one line: CHOICE: <hypothesis number from 1 to {n}> "
        "or CHOICE: NONE (if no hypothesis is supported)."
    )


def science_each_prompt(q, a, cands):
    """ResearchBench EACH prompt matching lineup_prompts VERDICT i ending."""
    n, head = science_pool_head(q, a, cands)
    lines = "\n".join(f"VERDICT {i + 1}: ACCEPT or REJECT" for i in range(n))
    return (
        head
        + "For each hypothesis, decide whether it is the main hypothesis that this study's evidence supports. "
        "It is possible that none of them is correct. Check the evidence as carefully as you need to. "
        f"End your reply with exactly {n} lines, one per hypothesis, in this form:\n{lines}"
    )


def write_jsonl(path, rows):
    """Write rows as JSON Lines."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return len(rows)


def write_all_jobs(c4_bank, c5_bank, cv_items, c9_bank):
    """Generate all Round 1 job JSONLs under exps/ and return counts and hashes."""
    job_counts = {}

    # C4: 3 independent repeats of PICK on TA and TP
    c4_jobs = []
    for p in c4_bank["pools"]:
        prompt = LP.pick(p["problem"], p["cands"])
        for rep in range(3):
            c4_jobs.append(
                {
                    "id": f"haiku__PICK__{p['pool']}__rep{rep}",
                    "pid": p["pid"],
                    "pool": p["pool"],
                    "kind": p["kind"],
                    "rep": rep,
                    "arm": "PICK",
                    "model": "haiku",
                    "timeout": 900,
                    "prompt": prompt,
                }
            )
    job_counts["c4_compute/jobs_haiku.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c4_compute", "jobs_haiku.jsonl"), c4_jobs
    )

    # C5a: PICK-2 on 38 own-answer-removed pools
    c5_own_jobs = []
    for p in c5_bank["own_answer_removal"]:
        c5_own_jobs.append(
            {
                "id": f"haiku__PICK2_OWN__{p['pool']}",
                "pid": p["pid"],
                "pool": p["pool"],
                "kind": "TA_2",
                "arm": "PICK2",
                "removed_cid": p["removed_cid"],
                "is_corrected_unsolved": p["is_corrected_unsolved"],
                "model": "haiku",
                "timeout": 900,
                "prompt": LP.pick(p["problem"], p["cands"]),
            }
        )
    job_counts["c5_removal/jobs_haiku_own_removal.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c5_removal", "jobs_haiku_own_removal.jsonl"), c5_own_jobs
    )

    # C5b: PICK-2 on Wells-removed pools
    c5_wells_jobs = []
    for p in c5_bank["wells_removal"]:
        c5_wells_jobs.append(
            {
                "id": f"haiku__PICK2_WELLS__{p['pool']}",
                "pid": p["pid"],
                "pool": p["pool"],
                "kind": "TA_2",
                "arm": "PICK2_WELLS",
                "c3_pick_choice_1idx": p["c3_pick_choice_1idx"],
                "removed_cid": p["removed_cid"],
                "model": "haiku",
                "timeout": 900,
                "prompt": LP.pick(p["problem"], p["cands"]),
            }
        )
    job_counts["c5_removal/jobs_haiku_wells.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c5_removal", "jobs_haiku_wells.jsonl"), c5_wells_jobs
    )

    # C6 Math: solve, iso, pick, each
    math_solve, math_iso, math_pick, math_each = [], [], [], []
    seen_cids = set()
    for item in cv_items:
        pid = item["pid"]
        src = item["source"]
        ta, tp = item["ta"], item["tp"]
        for k in (0, 1):
            math_solve.append(
                {
                    "id": f"SOLVE__{pid}__{k}",
                    "pid": pid,
                    "source": src,
                    "comp": ta["comp"],
                    "arm": "SOLVE",
                    "attempt": k,
                    "timeout": 900,
                    "prompt": LP.solve(ta["problem"]),
                }
            )
        for pool in (ta, tp):
            for c in pool["cands"]:
                if c["cid"] in seen_cids:
                    continue
                seen_cids.add(c["cid"])
                math_iso.append(
                    {
                        "id": f"ISO__{c['cid']}",
                        "pid": pid,
                        "cid": c["cid"],
                        "role": c["role"],
                        "vendor": c["vendor"],
                        "source": src,
                        "comp": pool["comp"],
                        "arm": "ISO",
                        "timeout": 900,
                        "prompt": LP.iso(pool["problem"], c),
                    }
                )
            math_pick.append(
                {
                    "id": f"PICK__{pool['pool']}",
                    "pid": pid,
                    "pool": pool["pool"],
                    "kind": pool["kind"],
                    "source": src,
                    "comp": pool["comp"],
                    "arm": "PICK",
                    "timeout": 900,
                    "prompt": LP.pick(pool["problem"], pool["cands"]),
                }
            )
            math_each.append(
                {
                    "id": f"EACH__{pool['pool']}",
                    "pid": pid,
                    "pool": pool["pool"],
                    "kind": pool["kind"],
                    "source": src,
                    "comp": pool["comp"],
                    "arm": "EACH",
                    "timeout": 900,
                    "prompt": LP.each(pool["problem"], pool["cands"]),
                }
            )

    job_counts["c6_crossvendor/jobs_math_solve.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c6_crossvendor", "jobs_math_solve.jsonl"), math_solve
    )
    job_counts["c6_crossvendor/jobs_math_iso.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c6_crossvendor", "jobs_math_iso.jsonl"), math_iso
    )
    job_counts["c6_crossvendor/jobs_math_pick.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c6_crossvendor", "jobs_math_pick.jsonl"), math_pick
    )
    job_counts["c6_crossvendor/jobs_math_each.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c6_crossvendor", "jobs_math_each.jsonl"), math_each
    )

    # C6 Science (ResearchBench 30 TA + 30 TP)
    sci_iso, sci_pick, sci_each = [], [], []
    seen_sci_cids = set()
    for pool in c9_bank["researchbench_pools"]:
        q = pool["research_question"]
        a = pool["abstract"]
        for c in pool["cands"]:
            if c["cid"] in seen_sci_cids:
                continue
            seen_sci_cids.add(c["cid"])
            sci_iso.append(
                {
                    "id": f"ISO__{c['cid']}",
                    "item": pool["item"],
                    "row": pool["row"],
                    "doi": pool["doi"],
                    "discipline": pool["discipline"],
                    "cid": c["cid"],
                    "role": c["role"],
                    "neg_source": c["neg_source"],
                    "arm": "ISO",
                    "timeout": 900,
                    "prompt": science_iso_prompt(q, a, c["text"]),
                }
            )
        sci_pick.append(
            {
                "id": f"PICK__{pool['pool']}",
                "item": pool["item"],
                "row": pool["row"],
                "doi": pool["doi"],
                "discipline": pool["discipline"],
                "pool": pool["pool"],
                "kind": pool["kind"],
                "arm": "PICK",
                "timeout": 900,
                "prompt": science_pick_prompt(q, a, pool["cands"]),
            }
        )
        sci_each.append(
            {
                "id": f"EACH__{pool['pool']}",
                "item": pool["item"],
                "row": pool["row"],
                "doi": pool["doi"],
                "discipline": pool["discipline"],
                "pool": pool["pool"],
                "kind": pool["kind"],
                "arm": "EACH",
                "timeout": 900,
                "prompt": science_each_prompt(q, a, pool["cands"]),
            }
        )

    job_counts["c6_crossvendor/jobs_science_iso.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c6_crossvendor", "jobs_science_iso.jsonl"), sci_iso
    )
    job_counts["c6_crossvendor/jobs_science_pick.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c6_crossvendor", "jobs_science_pick.jsonl"), sci_pick
    )
    job_counts["c6_crossvendor/jobs_science_each.jsonl"] = write_jsonl(
        os.path.join(EXPS_OUT, "c6_crossvendor", "jobs_science_each.jsonl"), sci_each
    )

    return job_counts


def vendor_table_md(pools, title):
    """Format markdown vendor breakdown table by kind and source."""
    counts = Counter()
    totals = Counter()
    for p in pools:
        src = p.get("source", "all")
        for v in p["vendors"]:
            counts[(v, p["kind"], src)] += 1
            counts[(v, "ALL", "ALL")] += 1
            totals[(p["kind"], src)] += 1
            totals[("ALL", "ALL")] += 1
    lines = [
        f"### {title}",
        "",
        "| Vendor | TA contest | TA arxivmath | TP contest | TP arxivmath | Total | Share |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    grand = totals[("ALL", "ALL")] or 1
    for v in VENDORS:
        tc = counts[(v, "TA", "contest")]
        ta = counts[(v, "TA", "arxivmath")]
        pc = counts[(v, "TP", "contest")]
        pa = counts[(v, "TP", "arxivmath")]
        tot = counts[(v, "ALL", "ALL")]
        if tot == 0:
            continue
        lines.append(f"| {v} | {tc} | {ta} | {pc} | {pa} | {tot} | {tot / grand:.3f} |")
    lines.append(
        f"| Total | {totals[('TA', 'contest')]} | {totals[('TA', 'arxivmath')]} | "
        f"{totals[('TP', 'contest')]} | {totals[('TP', 'arxivmath')]} | {totals[('ALL', 'ALL')]} | 1.000 |"
    )
    lines.append("")
    return lines


def pos_balance_line(label, tp_pools, n_bins):
    """Return formatted position balance summary string."""
    counts = [0] * n_bins
    for p in tp_pools:
        counts[p["right_pos_1idx"] - 1] += 1
    if n_bins == 3:
        stat, pval = chi2_uniform_df2(counts)
    else:
        stat, pval = chi2_uniform_df3(counts)
    return f"| {label} | {sum(counts)} | {counts} | {stat:.3f} | {pval:.4f} |"


def sha256_file(path):
    """Return hex SHA-256 digest of file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def check_no_dash_violations(text, label):
    """Assert zero em dashes, en dashes, or prose spaced hyphens."""
    if "\u2014" in text or "\u2013" in text:
        raise AssertionError(f"Em/en dash violation in {label}")
    for i, line in enumerate(text.splitlines(), 1):
        if " - " in line and not line.lstrip().startswith("|"):
            raise AssertionError(f"Spaced hyphen violation in {label} line {i}: {line}")


def build_manifest(dedup_stats, paired_items, c6_cv, c6_cf, c4_bank, c5_bank, c9_bank, job_counts):
    """Generate BANK_MANIFEST.md and assert dash cleanliness."""
    lines = [
        "# Locked V2 Banks and Round 1 Job Manifest",
        "",
        "Generated deterministically by `scripts/build_v2_banks.py` using Python 3.9 stdlib.",
        "",
        "## 1. Deduplicated MathArena Universe",
        "",
        f"* Raw pool rows scanned across 4 sources: {dedup_stats['raw_pool_rows']}",
        f"* Excluded pid records (7 label audit + 5 duplicates of used): {dedup_stats['excluded_bad_or_dup_pid']}",
        f"* Dropped unpaired pid records (missing TA or TP): {dedup_stats['dropped_unpaired']}",
        f"* Dropped normalized text duplicates: {dedup_stats['dropped_norm_duplicate']}",
        f"* Surviving unique paired TA+TP problems: {len(paired_items)} "
        f"(contest: {sum(1 for x in paired_items if x['source'] == 'contest')}, "
        f"arxivmath: {sum(1 for x in paired_items if x['source'] == 'arxivmath')})",
        "",
        "## 2. Locked Banks Summary",
        "",
        "| Bank file | Description | Problems | TA pools | TP pools | Total pools |",
        "|---|---|---:|---:|---:|---:|",
        f"| `c6_crossvendor_math.json` | Balanced Gemini-free and GPT-free math (seed {C6_SEED}) | {c6_cv['meta']['n_problems']} | {c6_cv['meta']['n_problems']} | {c6_cv['meta']['n_problems']} | {c6_cv['meta']['n_pools']} |",
        f"| `c6_claude_free_math.json` | All Claude-free paired math ({c6_cf['meta']['n_contest']} contest, {c6_cf['meta']['n_arxivmath']} arxivmath) | {c6_cf['meta']['n_problems']} | {c6_cf['meta']['n_problems']} | {c6_cf['meta']['n_problems']} | {c6_cf['meta']['n_pools']} |",
        f"| `c4_haiku_compute.json` | Corrected Haiku UNSOLVED (56 paired + 12 TA only) | {c4_bank['meta']['n_problems']} | {c4_bank['meta']['n_ta']} | {c4_bank['meta']['n_tp']} | {c4_bank['meta']['n_pools']} |",
        f"| `c5_haiku_removal.json` | Own-answer removal (38) + Wells PICK removal (43) | 38 + 43 | 38 + 43 | 0 | 81 |",
        f"| `c9_science_pools.json` (ResearchBench) | Real published abstracts (10 papers x 3 slices) | {c9_bank['meta']['n_researchbench_items']} | {c9_bank['meta']['n_researchbench_items']} | {c9_bank['meta']['n_researchbench_items']} | {c9_bank['meta']['n_researchbench_pools']} |",
        f"| `c9_science_pools.json` (x1c synthetic) | Synthetic calibration companion (48 subset flagged inside 72) | {c9_bank['meta']['n_synthetic_x1c_problems']} | {c9_bank['meta']['n_synthetic_x1c_problems']} | {c9_bank['meta']['n_synthetic_x1c_problems']} | {c9_bank['meta']['n_synthetic_x1c_pools']} |",
        "",
        "## 3. Vendor Breakdown Tables",
        "",
    ]
    lines.extend(vendor_table_md(c6_cv["pools"], "3.1 c6_crossvendor_math.json (zero gemini, zero gpt)"))
    lines.extend(vendor_table_md(c6_cf["pools"], "3.2 c6_claude_free_math.json (zero claude)"))
    lines.extend(vendor_table_md(c4_bank["pools"], "3.3 c4_haiku_compute.json"))

    lines.extend(
        [
            "## 4. Target-Present Right-Answer Position Balance",
            "",
            "| Bank / Subset | TP N | Counts [Pos 1..k] | Chi2 | p-value |",
            "|---|---:|---|---:|---:|",
            pos_balance_line(
                "c6_crossvendor_math (all)",
                [p for p in c6_cv["pools"] if p["kind"] == "TP"],
                3,
            ),
            pos_balance_line(
                "c6_crossvendor_math (contest)",
                [p for p in c6_cv["pools"] if p["kind"] == "TP" and p["source"] == "contest"],
                3,
            ),
            pos_balance_line(
                "c6_crossvendor_math (arxivmath)",
                [p for p in c6_cv["pools"] if p["kind"] == "TP" and p["source"] == "arxivmath"],
                3,
            ),
            pos_balance_line(
                "c6_claude_free_math (all)",
                [p for p in c6_cf["pools"] if p["kind"] == "TP"],
                3,
            ),
            pos_balance_line(
                "c9_science ResearchBench (k=4)",
                [p for p in c9_bank["researchbench_pools"] if p["kind"] == "TP"],
                4,
            ),
            pos_balance_line(
                "c9_science x1c synthetic (all 72, k=4)",
                [p for p in c9_bank["synthetic_x1c_pools"] if p["kind"] == "TP"],
                4,
            ),
            pos_balance_line(
                "c9_science x1c synthetic (48 subset, k=4)",
                [
                    p
                    for p in c9_bank["synthetic_x1c_pools"]
                    if p["kind"] == "TP" and p["calibration_48_subset"]
                ],
                4,
            ),
            "",
            "## 5. Round 1 Job JSONLs",
            "",
            "| Job file (under `exps/`) | Job count | SHA-256 (first 16 hex) |",
            "|---|---:|---|",
        ]
    )
    for rel_path, count in job_counts.items():
        digest = sha256_file(os.path.join(EXPS_OUT, rel_path))[:16]
        lines.append(f"| `{rel_path}` | {count} | `{digest}` |")
    lines.append("")

    md_text = "\n".join(lines)
    check_no_dash_violations(md_text, "BANK_MANIFEST.md")
    return md_text


def main():
    os.makedirs(BANKS_OUT, exist_ok=True)
    paired_items, dedup_stats = load_deduped_matharena()
    c6_cv, c6_cf, cv_items = build_c6_banks(paired_items)
    c4_bank, c5_bank = build_c4_and_c5_banks()
    c9_bank = build_c9_science_bank()

    bank_files = {
        "c6_crossvendor_math.json": c6_cv,
        "c6_claude_free_math.json": c6_cf,
        "c4_haiku_compute.json": c4_bank,
        "c5_haiku_removal.json": c5_bank,
        "c9_science_pools.json": c9_bank,
    }
    for fname, obj in bank_files.items():
        with open(os.path.join(BANKS_OUT, fname), "w") as fh:
            json.dump(obj, fh, indent=2)

    job_counts = write_all_jobs(c4_bank, c5_bank, cv_items, c9_bank)
    manifest_text = build_manifest(
        dedup_stats, paired_items, c6_cv, c6_cf, c4_bank, c5_bank, c9_bank, job_counts
    )
    manifest_path = os.path.join(BANKS_OUT, "BANK_MANIFEST.md")
    with open(manifest_path, "w") as fh:
        fh.write(manifest_text)

    lock_files = sorted(list(bank_files.keys()) + ["BANK_MANIFEST.md"])
    lock_lines = [f"{sha256_file(os.path.join(BANKS_OUT, fn))}  {fn}" for fn in lock_files]
    with open(os.path.join(BANKS_OUT, "LOCKED.sha256"), "w") as fh:
        fh.write("\n".join(lock_lines) + "\n")

    print("Locked banks written to:", BANKS_OUT)
    print("Paired MathArena universe:", len(paired_items))
    print("c6_crossvendor_math:", c6_cv["meta"]["n_problems"], "problems,", c6_cv["meta"]["n_pools"], "pools")
    print("c6_claude_free_math:", c6_cf["meta"]["n_problems"], "problems,", c6_cf["meta"]["n_pools"], "pools")
    print("c4_haiku_compute:", c4_bank["meta"]["n_problems"], "problems,", c4_bank["meta"]["n_pools"], "pools")
    print(
        "c5_haiku_removal: own=",
        c5_bank["meta"]["n_own_answer_removal"],
        "wells=",
        c5_bank["meta"]["n_wells_removal"],
    )
    print(
        "c9_science_pools: rb_pools=",
        c9_bank["meta"]["n_researchbench_pools"],
        "x1c_pools=",
        c9_bank["meta"]["n_synthetic_x1c_pools"],
    )
    print("Job counts:", json.dumps(job_counts, indent=2))


if __name__ == "__main__":
    main()
