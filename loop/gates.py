#!/usr/bin/env python3
"""Mechanical release gates. Locked: the loop may not edit this file or loop/RUBRIC.md.

Exit 0 only if every gate passes. Prints one line per gate.
Conventions the paper must follow:
- Every measured number in paper/main.tex comes from a \\res{id} macro, generated
  into paper/results.tex from results/claims.json by analysis/make_claims.py.
- Every bib key has evidence/citations/<key>.json with the fetched record.
- Every exps/<id>/raw/ was preceded in git history by exps/<id>/PREREGISTRATION.md.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata

ROOT = os.getcwd()
MIN_REVIEWERS = 3
BANNED = ["as an ai", "certainly!", "i hope this", "regenerate response", "todo", "xxx",
          "lipsum", "placeholder", "tbd"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT).stdout


def norm(s):
    s = unicodedata.normalize("NFKD", re.sub(r"[{}\\$]", "", s)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def body(tex):
    """Paper body with comments, the preamble and non-prose environments removed."""
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    tex = tex.split(r"\begin{document}", 1)[-1]
    return re.sub(r"\\begin\{(figure\*?|equation\*?|align\*?|thebibliography)\}.*?\\end\{\1\}",
                  " ", tex, flags=re.S)


def g_grounding():
    tex = body(read("paper/main.tex"))
    claims = json.load(open("results/claims.json"))
    used = set(re.findall(r"\\res\{([^}]+)\}", tex))
    missing = sorted(used - set(claims))
    if missing:
        return f"unknown claim ids: {missing[:10]}"
    if not used:
        return "no \\res{} macros used"
    for cid in used:
        src = claims[cid].get("source", "")
        if not (src and os.path.exists(src)):
            return f"claim {cid} has no existing source file: {src!r}"
    bare = re.findall(r"(?<![\w.{\\-])(?:\d+\.\d+|\d+(?:\.\d+)?\\?%)(?![\w}])",
                      re.sub(r"\\(res|cite\w*|ref|label|url|href|includegraphics(\[[^\]]*\])?)\{[^}]*\}",
                             " ", tex))
    if bare:
        return f"bare measured numbers, use \\res{{}}: {bare[:10]}"
    return None


def g_claims_reproduce():
    before = hashlib.sha256(open("results/claims.json", "rb").read()).hexdigest()
    p = subprocess.run([sys.executable, "analysis/make_claims.py"], capture_output=True,
                       text=True, cwd=ROOT, timeout=600)
    if p.returncode:
        return "make_claims failed: " + p.stderr[-300:]
    after = hashlib.sha256(open("results/claims.json", "rb").read()).hexdigest()
    return None if before == after else "claims.json changed when regenerated from raw"


def g_citations():
    keys = re.findall(r"@\w+\{\s*([^,\s]+)\s*,", read("paper/refs.bib"))
    bib = {}
    for m in re.finditer(r"@\w+\{\s*([^,\s]+)\s*,(.*?)(?=\n@|\Z)", read("paper/refs.bib"), re.S):
        t = re.search(r"title\s*=\s*[{\"](.+?)[}\"]\s*,?\s*\n", m.group(2), re.S)
        bib[m.group(1)] = t.group(1) if t else ""
    if not keys:
        return "empty refs.bib"
    cited = set()
    for c in re.findall(r"\\cite\w*(?:\[[^\]]*\])*\{([^}]+)\}", read("paper/main.tex")):
        cited |= {k.strip() for k in c.split(",")}
    if cited - set(keys):
        return f"cited but not in bib: {sorted(cited - set(keys))[:10]}"
    for k in keys:
        p = f"evidence/citations/{k}.json"
        if not os.path.exists(p):
            return f"no citation evidence for {k}"
        rec = json.load(open(p))
        if not (rec.get("url") and rec.get("fetched_title")):
            return f"evidence for {k} lacks url or fetched_title"
        if norm(rec["fetched_title"]) != norm(bib.get(k, "")):
            return f"bib title differs from fetched title for {k}"
    return None


def g_prereg():
    exps = [d for d in glob.glob("exps/*") if os.path.isdir(f"{d}/raw") and os.listdir(f"{d}/raw")]
    if not exps:
        return "no experiments with raw data"
    for d in exps:
        pre = git("log", "--format=%ct", "--reverse", "--", f"{d}/PREREGISTRATION.md").split()
        raw = git("log", "--format=%ct", "--reverse", "--", f"{d}/raw").split()
        if not pre or not raw:
            return f"{d}: prereg or raw not committed"
        if int(pre[0]) > int(raw[0]):
            return f"{d}: raw committed before prereg"
        if len(pre) > 1 and int(pre[-1]) > int(raw[0]):
            return f"{d}: prereg edited after data, use AMENDMENTS.md"
    return None


def g_ledger():
    rows = [l for l in read("results/hypothesis_ledger.csv").splitlines()[1:] if l.strip()]
    if not rows:
        return "empty hypothesis ledger"
    return None if re.search(r"\\res\{ledger", read("paper/main.tex")) else \
        "paper must report the ledger total via \\res{ledger...}"


def g_text():
    tex = read("paper/main.tex")
    if "\u2014" in tex or "\u2013" in tex or re.search(r"(?<!\d)--+(?!\d)", body(tex)):
        return "em or en dash in paper"
    low = body(tex).lower()
    hits = [b for b in BANNED if re.search(r"\b" + re.escape(b), low)]
    return f"leftover text: {hits}" if hits else None


def g_figures():
    figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", read("paper/main.tex"))
    if not figs:
        return "no figures"
    for f in figs:
        path = os.path.join("paper", f)
        if not any(os.path.exists(path + e) for e in ("", ".pdf", ".png")):
            return f"missing figure {f}"
    return None if os.path.exists("analysis/make_figures.py") else "no figure generator"


def g_pdf():
    if not os.path.exists("paper/main.pdf"):
        return "no paper/main.pdf"
    return None if os.path.getmtime("paper/main.pdf") >= os.path.getmtime("paper/main.tex") \
        else "main.pdf older than main.tex"


def g_review():
    files = glob.glob("reviews/FINAL/*.json")
    if len(files) < MIN_REVIEWERS:
        return f"need {MIN_REVIEWERS} final reviews, have {len(files)}"
    for f in files:
        r = json.load(open(f))
        if r.get("blockers"):
            return f"{f} has open blockers"
        if r.get("verdict") not in ("accept", "minor"):
            return f"{f} verdict is {r.get('verdict')}"
    return None


def g_files():
    for f in ("FINAL_REPORT.md", "PROVENANCE.md", "DEFENSE.md", "loop/EVOLUTION.md"):
        if not os.path.exists(f):
            return f"missing {f}"
    return None


GATES = [g_grounding, g_claims_reproduce, g_citations, g_prereg, g_ledger, g_text,
         g_figures, g_pdf, g_review, g_files]


def main():
    bad = 0
    for g in GATES:
        try:
            err = g()
        except Exception as e:  # a missing file is a failed gate, not a crash
            err = f"{type(e).__name__}: {e}"
        print(("PASS " if not err else "FAIL ") + g.__name__[2:] + ("" if not err else ": " + err))
        bad += bool(err)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
