#!/usr/bin/env python3
"""Self-check: a clean fixture passes every gate, and each planted defect fails its gate."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GOOD_TEX = r"""\documentclass{article}\begin{document}
Rate \res{a} over \res{ledger_total} tests \cite{k1}.
\begin{figure}\includegraphics{figures/f}\end{figure}
\end{document}"""
GOOD_BIB = "@article{k1,\n  title = {A Real Paper},\n  year = {2026}\n}\n"
MAKE = """import json
json.dump({'a': {'value': 0.5, 'source': 'exps/e1/raw/r.json'},
           'ledger_total': {'value': 3, 'source': 'results/hypothesis_ledger.csv'}},
          open('results/claims.json', 'w'), sort_keys=True)
"""


def sh(*a, cwd):
    subprocess.run(a, cwd=cwd, check=True, capture_output=True)


def w(root, path, text):
    p = os.path.join(root, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def commit(root, msg, t):
    sh("git", "add", "-A", cwd=root)
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{t} +0000", GIT_COMMITTER_DATE=f"{t} +0000")
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", msg],
                   cwd=root, check=True, env=env)


def build(root, prereg_first=True):
    sh("git", "init", "-q", cwd=root)
    w(root, "exps/e1/raw/r.json" if not prereg_first else "exps/e1/PREREGISTRATION.md", "x")
    commit(root, "first", 1700000000)
    w(root, "exps/e1/PREREGISTRATION.md" if not prereg_first else "exps/e1/raw/r.json", "x")
    commit(root, "second", 1700000100)
    w(root, "analysis/make_claims.py", MAKE)
    w(root, "analysis/make_figures.py", "")
    w(root, "results/hypothesis_ledger.csv", "id,status\nh1,killed\n")
    w(root, "paper/refs.bib", GOOD_BIB)
    w(root, "paper/figures/f.pdf", "x")
    w(root, "paper/main.tex", GOOD_TEX)
    w(root, "evidence/citations/k1.json", json.dumps({"url": "u", "fetched_title": "A real paper"}))
    for i in range(3):
        w(root, f"reviews/FINAL/r{i}.json", json.dumps({"verdict": "minor", "blockers": []}))
    for f in ("FINAL_REPORT.md", "PROVENANCE.md", "DEFENSE.md", "loop/EVOLUTION.md"):
        w(root, f, "x")
    subprocess.run([sys.executable, "analysis/make_claims.py"], cwd=root, check=True)
    w(root, "paper/main.pdf", "x")


def run(root):
    p = subprocess.run([sys.executable, os.path.join(HERE, "gates.py")], cwd=root,
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def expect_fail(name, gate, mutate=None, prereg_first=True):
    with tempfile.TemporaryDirectory() as d:
        build(d, prereg_first)
        if mutate:
            mutate(d)
            os.utime(os.path.join(d, "paper/main.pdf"))
        rc, out = run(d)
        assert rc == 1 and f"FAIL {gate}" in out, (name, out)
    print("caught", name)


with tempfile.TemporaryDirectory() as d:
    build(d)
    rc, out = run(d)
    assert rc == 0, out
print("clean fixture passes")

tex = lambda d, s: w(d, "paper/main.tex", GOOD_TEX.replace("Rate", s))
expect_fail("bare number", "grounding", lambda d: tex(d, "Rate 0.87 and"))
expect_fail("percent", "grounding", lambda d: tex(d, r"Rate 42\% and"))
expect_fail("em dash", "text", lambda d: tex(d, "Rate—and"))
expect_fail("latex dash", "text", lambda d: tex(d, "Rate --- and"))
expect_fail("chatbot text", "text", lambda d: tex(d, "As an AI model,"))
expect_fail("tampered claim", "claims_reproduce",
            lambda d: w(d, "results/claims.json", json.dumps(
                {"a": {"value": 0.9, "source": "exps/e1/raw/r.json"},
                 "ledger_total": {"value": 3, "source": "results/hypothesis_ledger.csv"}})))
expect_fail("fake citation", "citations",
            lambda d: w(d, "evidence/citations/k1.json",
                        json.dumps({"url": "u", "fetched_title": "A different paper"})))
expect_fail("uncited evidence", "citations", lambda d: os.remove(f"{d}/evidence/citations/k1.json"))
expect_fail("raw before prereg", "prereg", prereg_first=False)
expect_fail("reviewer blocker", "review",
            lambda d: w(d, "reviews/FINAL/r0.json",
                        json.dumps({"verdict": "minor", "blockers": ["x"]})))
expect_fail("rejecting reviewer", "review",
            lambda d: w(d, "reviews/FINAL/r0.json",
                        json.dumps({"verdict": "major", "blockers": []})))
print("all gate checks pass")
