#!/usr/bin/env python3
"""Seeded generator of counting tasks written for this study (2026-11-03).

A task asks how many integers n with LO <= n <= HI satisfy a conjunction of randomly
drawn arithmetic conditions (digit sums, residues, binary popcount, digit membership,
digit order). Ground truth is brute-force enumeration in Python, so no model or human
grading is involved. Instances are created from seeds after this file is frozen.
Program tracing (gen/progtrace*.py) was at ceiling for current models (S0); counting
under several interacting conditions requires either enumeration, which a model cannot
do in its head at these sizes, or a correct combinatorial decomposition, which is error
prone. Difficulty knobs: HI (range size) and k (number of conditions).

The per-condition counts and the count after each successive condition are stored, so
intermediate claims ("exactly X numbers satisfy the first two conditions") are
machine-checkable for critique and attribution experiments.
"""
import json
import random
import sys


def _conditions(rng):
    m = rng.choice([3, 4, 5, 6, 7, 9, 11, 13])
    r = rng.randrange(m)
    m2 = rng.choice([3, 4, 5, 7, 8])
    r2 = rng.randrange(m2)
    d = rng.randint(0, 9)
    b = rng.choice([2, 3, 4, 5])
    pool = [
        (f"the sum of its decimal digits leaves remainder {r2} when divided by {m2}",
         lambda n, m2=m2, r2=r2: sum(map(int, str(n))) % m2 == r2),
        (f"n leaves remainder {r} when divided by {m}", lambda n, m=m, r=r: n % m == r),
        (f"its binary representation contains exactly {b} ones", lambda n, b=b: bin(n).count("1") == b),
        (f"its binary representation contains an even number of ones", lambda n: bin(n).count("1") % 2 == 0),
        (f"its decimal representation contains the digit {d}", lambda n, d=d: str(d) in str(n)),
        (f"its decimal representation does not contain the digit {d}", lambda n, d=d: str(d) not in str(n)),
        ("its decimal digits are in non-decreasing order from left to right",
         lambda n: list(str(n)) == sorted(str(n))),
        ("its first and last decimal digits are different", lambda n: str(n)[0] != str(n)[-1]),
    ]
    return pool


def make_task(seed, hi, k):
    rng = random.Random(f"countgen-{seed}-{hi}-{k}")
    lo = rng.randint(1, max(1, hi // 10))
    for _ in range(100):
        conds = rng.sample(_conditions(rng), k)
        texts = [c[0] for c in conds]
        if len(set(t.split(" ")[1] for t in texts)) < 1:
            continue
        cum, ok = [], list(range(lo, hi + 1))
        for _, fn in conds:
            ok = [n for n in ok if fn(n)]
            cum.append(len(ok))
        if cum[-1] >= 3:  # avoid trivial zero answers
            break
    q = (f"How many integers n with {lo} <= n <= {hi} satisfy ALL of the following conditions?\n"
         + "\n".join(f"{i + 1}. {t}" for i, t in enumerate(texts)))
    return {"tid": f"cg_{seed}_{hi}_{k}", "seed": seed, "hi": hi, "lo": lo, "k": k,
            "question": q, "answer": cum[-1], "cumulative": cum, "conditions": texts}


def question(task):
    return task["question"]


if __name__ == "__main__":
    s, hi, k = map(int, sys.argv[1:4])
    print(json.dumps(make_task(s, hi, k), indent=1))
