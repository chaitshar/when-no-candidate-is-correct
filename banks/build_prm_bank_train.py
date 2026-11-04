#!/usr/bin/env python3
"""Replication bank variant of build_prm_bank.py on PRM800K phase 2 TRAIN labels.

Same WRONG / RIGHT definitions as build_prm_bank.py (norm, sym_equal and text_of are
imported unchanged). Source: data_phase2_train.jsonl joined to math_splits_train.jsonl
by problem text. phase2_train can hold several label runs of the same solution; the
per-distinct-normalized-answer dedup (first in file order) handles repeats exactly as
in the test builder. sym_equal results are memoized (pure function, no semantic change).
The imported sym_equal runs in a child process capped at 2 GB address space with a 30 s
timeout: a first unguarded run was OOM-killed (11 GB) by sympy on a pathological answer.
A capped or timed-out call returns False, the same outcome sym_equal gives on exceptions.

Selection: keep problems with >= 3 distinct wrong answers (after the symbolic dedup).
If more than N_MAX qualify, shuffle the qualifying list (file order) with
random.Random(SEED).shuffle and keep the first N_MAX, in shuffled order.
Problems whose text equals any MATH test problem text (math_splits_test.jsonl) or any
phase2 test problem are dropped before selection.

usage: build_prm_bank_train.py DATA_DIR OUT.jsonl
"""
import hashlib
import json
import os
import random
import sys
from collections import OrderedDict
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_prm_bank import norm, sym_equal as _sym_equal, text_of  # noqa: E402

MIN_WRONG = 3
N_MAX = 400
SEED = 7


SYM_MEM_BYTES = 2 * 1024 ** 3
SYM_TIMEOUT_S = 30


def _worker(conn):
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (SYM_MEM_BYTES, SYM_MEM_BYTES))
    while True:
        a, b = conn.recv()
        try:
            conn.send(_sym_equal(a, b))
        except BaseException:  # e.g. MemoryError: treated like any sympy failure
            conn.send(False)


class _Sym:
    """Runs the unchanged sym_equal in a memory-capped child process. A pathological
    expression that exhausts memory or exceeds the timeout returns False, the same
    outcome sym_equal already gives on any exception."""

    def __init__(self):
        self.p = None
        self.n_fail = 0

    def _start(self):
        import multiprocessing as mp
        self.conn, child = mp.Pipe()
        self.p = mp.Process(target=_worker, args=(child,), daemon=True)
        self.p.start()

    def __call__(self, a, b):
        if self.p is None or not self.p.is_alive():
            self._start()
        try:
            self.conn.send((a, b))
            if self.conn.poll(SYM_TIMEOUT_S):
                return self.conn.recv()
        except (EOFError, OSError):
            pass
        self.n_fail += 1
        self.p.kill()
        self.p.join()
        self.p = None
        return False


_SYM = _Sym()


@lru_cache(maxsize=None)
def sym_equal(a, b):
    return _SYM(a, b)


def main():
    data, out = sys.argv[1], sys.argv[2]
    ms = {}
    for l in open(f"{data}/math_splits_train.jsonl"):
        d = json.loads(l)
        ms[d["problem"]] = d
    test_texts = set()
    for l in open(f"{data}/math_splits_test.jsonl"):
        test_texts.add(json.loads(l)["problem"])
    for l in open(f"{data}/data_phase2_test.jsonl"):
        test_texts.add(json.loads(l)["question"]["problem"])
    probs = OrderedDict()
    for l in open(f"{data}/data_phase2_train.jsonl"):
        r = json.loads(l)
        q = r["question"]
        a, g = q.get("pre_generated_answer"), q["ground_truth_answer"]
        fr = r["label"].get("finish_reason")
        if a is None or q["problem"] not in ms:
            continue
        p = probs.setdefault(q["problem"], {"wrong": OrderedDict(), "right": [], "gold": g})
        if fr == "found_error" and norm(a) != norm(g) and not sym_equal(a, g):
            if norm(a) not in p["wrong"]:
                p["wrong"][norm(a)] = {"answer": a, "text": text_of(q["pre_generated_steps"]),
                                       "finish_reason": fr, "labeler": r["labeler"],
                                       "timestamp": r["timestamp"]}
        elif fr == "solution" and a == g:
            if len(p["right"]) < 3:
                p["right"].append({"answer": a, "text": text_of(q["pre_generated_steps"]),
                                   "finish_reason": fr, "labeler": r["labeler"],
                                   "timestamp": r["timestamp"]})
    recs = []
    n_overlap = 0
    for prob, p in probs.items():
        m = ms[prob]
        kept = []
        for c in p["wrong"].values():
            if not any(sym_equal(c["answer"], k["answer"]) for k in kept):
                kept.append(c)
        if len(kept) < MIN_WRONG:
            continue
        if prob in test_texts:
            n_overlap += 1
            continue
        pid = "prm_" + hashlib.sha256(prob.encode()).hexdigest()[:10]
        recs.append({"pid": pid, "problem": prob, "gold": p["gold"], "level": m["level"],
                     "subject": m["subject"], "math_id": m["unique_id"],
                     "wrong": kept, "right": p["right"][:3]})
    n_qual = len(recs)
    if n_qual > N_MAX:
        random.Random(SEED).shuffle(recs)
        recs = recs[:N_MAX]
    with open(out, "w") as f:
        for rec in recs:
            f.write(json.dumps(rec) + "\n")
    print("problems_joined", len(probs), "qualifying", n_qual,
          "dropped_test_overlap", n_overlap, "written", len(recs),
          "sym_timeouts_or_crashes", _SYM.n_fail)


if __name__ == "__main__":
    main()
