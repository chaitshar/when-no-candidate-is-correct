#!/usr/bin/env python3
"""Build the PRM800K candidate bank (deterministic, no model calls).

Source: openai/prm800k, phase 2 test labels (GPT-4 step-by-step solutions to MATH test
problems, each solution rated step by step by human labelers) joined with the MATH test
split for level and subject. Files fetched from media.githubusercontent.com into
DATA_DIR on 2026-11-03.

A candidate counts as WRONG only if all three hold:
  1. the human label run ended with finish_reason == "found_error" (a labeler marked an
     erroneous step),
  2. its final answer differs from the MATH ground truth after normalization,
  3. a symbolic check (sympy) cannot show the two answers are equal.
A candidate counts as RIGHT only if finish_reason == "solution" (labelers rated every
step acceptable) and its final answer string equals the ground truth.
Wrong candidates are deduplicated by normalized final answer (one solution per distinct
answer, the first in file order), so a pool never shows the same answer twice.

usage: build_prm_bank.py DATA_DIR OUT.jsonl
"""
import hashlib
import json
import re
import sys
from collections import OrderedDict

try:
    from sympy import simplify
    from sympy.parsing.latex import parse_latex
    parse_latex("1/2")  # raises if antlr4-python3-runtime 4.11 is missing
except Exception as _e:  # changed 2026-11-04: fail loudly; a silent fallback mis-grades LaTeX answers
    raise RuntimeError("sympy LaTeX parsing unavailable (need sympy and antlr4-python3-runtime==4.11.1); "
                       "grading would silently mark LaTeX answers wrong") from _e


def norm(a):
    a = a.strip().strip("$").replace(" ", "").replace("\\!", "").replace("\\left", "").replace("\\right", "")
    a = re.sub(r"\\text\{([^}]*)\}", r"\1", a)
    a = re.sub(r"\\(d|t)frac", r"\\frac", a)
    a = a.replace("^\\circ", "").replace("^{\\circ}", "").replace("\\%", "").rstrip(".")
    if re.fullmatch(r"-?\d+\.0+", a):
        a = a.split(".")[0]
    return a


def _alarm(signum, frame):
    raise TimeoutError


def sym_equal(a, b):
    """Symbolic equality; gives up (False) after 5 s (added 2026-11-04: some LaTeX hangs sympy)."""
    import signal
    if parse_latex is None:
        return False
    old = signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(5)
    try:
        return _sym_equal(a, b)
    except Exception:
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def _sym_equal(a, b):
    try:
        x, y = parse_latex(norm(a)), parse_latex(norm(b))
        return bool(simplify(x - y) == 0)
    except Exception:
        return False


def text_of(steps):
    body = [s for s in steps if not s.strip().startswith("# Answer")]
    return "\n".join(body)


def main():
    data, out = sys.argv[1], sys.argv[2]
    ms = {}
    for l in open(f"{data}/math_splits_test.jsonl"):
        d = json.loads(l)
        ms[d["problem"]] = d
    probs = OrderedDict()
    for l in open(f"{data}/data_phase2_test.jsonl"):
        r = json.loads(l)
        q = r["question"]
        a, g = q.get("pre_generated_answer"), q["ground_truth_answer"]
        fr = r["label"].get("finish_reason")
        if a is None or q["problem"] not in ms:
            continue
        p = probs.setdefault(q["problem"], {"wrong": OrderedDict(), "right": [], "gold": g})
        cand = {"answer": a, "text": text_of(q["pre_generated_steps"]), "finish_reason": fr,
                "labeler": r["labeler"], "timestamp": r["timestamp"]}
        if fr == "found_error" and norm(a) != norm(g) and not sym_equal(a, g):
            if norm(a) not in p["wrong"]:
                p["wrong"][norm(a)] = cand
        elif fr == "solution" and a == g:
            p["right"].append(cand)
    n = 0
    with open(out, "w") as f:
        for prob, p in probs.items():
            m = ms[prob]
            wrong = list(p["wrong"].values())
            # drop wrong answers that are symbolically equal to an earlier kept wrong answer
            kept = []
            for c in wrong:
                if not any(sym_equal(c["answer"], k["answer"]) for k in kept):
                    kept.append(c)
            pid = "prm_" + hashlib.sha256(prob.encode()).hexdigest()[:10]
            rec = {"pid": pid, "problem": prob, "gold": p["gold"], "level": m["level"],
                   "subject": m["subject"], "math_id": m["unique_id"],
                   "wrong": kept, "right": p["right"][:3]}
            f.write(json.dumps(rec) + "\n")
            n += 1
    print("problems", n)


if __name__ == "__main__":
    main()
