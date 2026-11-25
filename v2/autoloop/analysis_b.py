#!/usr/bin/env python3
"""Independent Verifier B for Auto-Research Science Loop V2 (C4, C5, C6 Math, C7 Mitigation, C9 Science).

Pure Python 3.9 stdlib only (zero external packages, zero imports from autoloop/parsers.py
or C3 harness/parse.py). Implements independent inline regex parsers, pure-Python LaTeX/AST
math equivalence grading, Acklam Phi^-1, Hautus (1995) SDT, and 5,000-resample bootstraps.
"""
import argparse
import ast
import cmath
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import re
import statistics
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple


DEFAULT_ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")
DEFAULT_C3_ROOT = Path("/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar")
DEFAULT_BOOT = 5000
DEFAULT_SEED = 20261120


# ---------------------------------------------------------------------------
# 1. Independent Inline Regex Parsers (no import of autoloop/parsers.py)
# ---------------------------------------------------------------------------

def _strip_md_edge(s: str) -> str:
    prev = None
    cur = s.strip()
    while prev != cur:
        prev = cur
        cur = cur.strip("*_`\"' ").strip()
    return cur


def parse_verdict(text: Optional[str]) -> Optional[bool]:
    """Extract final VERDICT: ACCEPT or REJECT from reply text."""
    if not isinstance(text, str) or not text.strip():
        return None
    for raw_line in reversed(text.splitlines()):
        cleaned = _strip_md_edge(raw_line)
        if not cleaned:
            continue
        m = re.search(r"\bVERDICT\b[\s*`_:]*\b(ACCEPT|REJECT)\b", cleaned, re.IGNORECASE)
        if m:
            return m.group(1).upper() == "ACCEPT"
    for raw_line in reversed(text.splitlines()):
        cleaned = _strip_md_edge(raw_line)
        if not cleaned:
            continue
        m = re.fullmatch(r"(ACCEPT|REJECT)\.?", cleaned, re.IGNORECASE)
        if m:
            return m.group(1).upper() == "ACCEPT"
        break
    return None


def parse_choice(text: Optional[str], n_cands: int) -> Optional[int]:
    """Extract final CHOICE: NONE (0) or 1..n_cands from reply text."""
    if not isinstance(text, str) or not text.strip():
        return None
    for raw_line in reversed(text.splitlines()):
        cleaned = _strip_md_edge(raw_line)
        if not cleaned:
            continue
        m = re.search(
            r"\bCHOICE\b[\s*`_:]*\b(NONE(?:\s+OF\s+THEM)?|(?:SOLUTION|HYPOTHESIS|CANDIDATE)?\s*\d+)\b",
            cleaned,
            re.IGNORECASE,
        )
        if m:
            tok = m.group(1).strip().upper()
            if tok.startswith("NONE"):
                return 0
            dm = re.search(r"(\d+)$", tok)
            if dm:
                val = int(dm.group(1))
                return val if 1 <= val <= n_cands else None
    return None


def parse_each(text: Optional[str], n_cands: int) -> Optional[List[bool]]:
    """Extract VERDICT 1..n_cands: ACCEPT/REJECT list; returns None if any slot missing."""
    if not isinstance(text, str) or not text.strip():
        return None
    found: Dict[int, bool] = {}
    for raw_line in text.splitlines():
        cleaned = _strip_md_edge(raw_line)
        if not cleaned:
            continue
        m = re.search(
            r"\bVERDICT\s*#?\s*(\d+)\b[\s*`_:]*\b(ACCEPT|REJECT)\b",
            cleaned,
            re.IGNORECASE,
        )
        if m:
            idx = int(m.group(1))
            if 1 <= idx <= n_cands:
                found[idx] = m.group(2).upper() == "ACCEPT"
    if len(found) != n_cands:
        return None
    return [found[i] for i in range(1, n_cands + 1)]


def parse_confidence(text: Optional[str]) -> Optional[int]:
    """Extract final CONFIDENCE: 1..5 integer from reply text."""
    if not isinstance(text, str) or not text.strip():
        return None
    for raw_line in reversed(text.splitlines()):
        cleaned = _strip_md_edge(raw_line)
        if not cleaned:
            continue
        m = re.search(r"\bCONFIDENCE\b[\s*`_:]*([1-5])\b", cleaned, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def _match_brace(s: str, open_idx: int) -> int:
    depth = 0
    for j in range(open_idx, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j
    return -1


def _last_boxed(s: str) -> Optional[str]:
    res: Optional[str] = None
    for m in re.finditer(r"\\(?:boxed|fbox)\s*\{", s):
        i = m.end() - 1
        j = _match_brace(s, i)
        if j != -1:
            res = s[i + 1 : j]
    return res


def _clean_answer_tail(tail: str) -> str:
    t = tail.strip()
    for _ in range(3):
        t = t.strip().strip("*_`").strip()
        t = re.sub(r"^\\\(|\\\)$", "", t).strip()
        t = re.sub(r"^\\\[|\\\]$", "", t).strip()
        t = t.strip("$").strip()
        t = t.rstrip(".").strip()
    boxed = _last_boxed(t)
    if boxed is not None:
        return boxed.strip()
    return t.strip()


def parse_answer(text: Optional[str]) -> Optional[str]:
    """Extract final ANSWER: ... (or fallback \\boxed{...}) from SOLVE reply."""
    if not isinstance(text, str) or not text.strip():
        return None
    for raw_line in reversed(text.splitlines()):
        m = list(re.finditer(r"(?:^|\W)ANSWER\**\s*:\s*", raw_line, re.IGNORECASE))
        if m:
            tail = raw_line[m[-1].end() :]
            cleaned = _clean_answer_tail(tail)
            if cleaned:
                return cleaned
    boxed = _last_boxed(text)
    if boxed is not None and boxed.strip():
        return boxed.strip()
    return None


# ---------------------------------------------------------------------------
# 2. Pure Python 3.9 Stdlib Math Equivalence Grader (no sympy)
# ---------------------------------------------------------------------------

def _strip_tex_wrappers(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = re.sub(
            r"\\(?:text|textbf|textit|mathrm|mathbf|mbox|operatorname)\s*\{([^{}]*)\}",
            r"\1",
            s,
        )
    return s


def _norm_math(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\\\(|\\\)|\\\[|\\\]", "", s)
    s = s.replace("$", "")
    b = _last_boxed(s)
    if b is not None and s.strip().startswith("\\boxed"):
        s = b
    s = s.replace("\u2212", "-").replace("\u202f", " ").replace("\u00a0", " ")
    s = re.sub(r"\\(?:left|right|big|Big|bigg|Bigg|displaystyle|limits)(?![A-Za-z])", "", s)
    s = re.sub(r"\\[!,;:> ]|\\quad|\\qquad", "", s)
    s = _strip_tex_wrappers(s)
    s = re.sub(r"\\[dt]frac", r"\\frac", s)
    s = re.sub(r"\s+", "", s)
    s = s.rstrip(".")
    if re.fullmatch(r"[+-]?\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    s = s.replace("^{\\circ}", "").replace("^\\circ", "").replace("\u00b0", "")
    return s


def _replace_cmd(s: str, cmd: str, fmt: str, nargs: int) -> str:
    pat = "\\" + cmd
    while True:
        idx = s.find(pat)
        if idx == -1:
            return s
        after = idx + len(pat)
        if after < len(s) and s[after].isalpha():
            # Avoid matching prefix of another command like \fraction
            return s
        j = after
        args: List[str] = []
        ok = True
        for _ in range(nargs):
            while j < len(s) and s[j] == " ":
                j += 1
            if j < len(s) and s[j] == "{":
                k = _match_brace(s, j)
                if k == -1:
                    ok = False
                    break
                args.append(s[j + 1 : k])
                j = k + 1
            elif j < len(s) and (s[j].isalnum() or s[j] in "+-"):
                args.append(s[j])
                j += 1
            else:
                ok = False
                break
        if not ok:
            return s
        wrapped = ["(" + a + ")" for a in args]
        s = s[:idx] + fmt.format(*wrapped) + s[j:]


def _insert_implicit_mul(expr: str) -> str:
    # Insert '*' between:
    # 1) digit or ')' followed by '(', letter, or (for ')') digit
    # 2) letter (except known func before '(') followed by '('
    # 3) adjacent single-letter variables not part of known functions/constants
    funcs = ("sqrt", "sin", "cos", "tan", "log", "ln", "exp", "abs")
    known = set(funcs) | {"pi", "inf", "alpha", "beta", "gamma", "delta", "epsilon", "theta", "lambda", "mu", "nu", "rho", "sigma", "tau", "phi", "psi", "omega", "Omega"}
    tokens = re.findall(r"[A-Za-z]+|\d+(?:\.\d+)?|\*\*|[+\-*/(),]", expr)
    expanded: List[str] = []
    for tok in tokens:
        if tok.isalpha() and len(tok) > 1 and tok not in known:
            expanded.extend(list(tok))
        else:
            expanded.append(tok)
    out: List[str] = []
    for i, tok in enumerate(expanded):
        if i > 0:
            prev = expanded[i - 1]
            prev_is_val = (prev not in ("+", "-", "*", "/", "**", ",", "(")) and (prev not in funcs)
            cur_is_val = tok not in ("+", "-", "*", "/", "**", ",", ")")
            if prev_is_val and cur_is_val:
                out.append("*")
        out.append(tok)
    return "".join(out)


def _latex_to_py(s: str) -> str:
    s = _norm_math(s)
    m = re.fullmatch(r"[A-Za-z]=([^=<>]+)", s)
    if m:
        s = m.group(1)
    s = s.replace("\\cdot", "*").replace("\\times", "*").replace("\\div", "/")
    s = re.sub(r"\\sqrt\[([^\]]*)\]", r"\\rt[\1]", s)
    for _ in range(12):
        before = s
        s = _replace_cmd(s, "frac", "({0}/{1})", 2)
        m_rt = re.search(r"\\rt\[([^\]]*)\]\{", s)
        if m_rt:
            i = m_rt.end() - 1
            k = _match_brace(s, i)
            if k != -1:
                s = (
                    s[: m_rt.start()]
                    + "(("
                    + s[i + 1 : k]
                    + ")**(1/("
                    + m_rt.group(1)
                    + ")))"
                    + s[k + 1 :]
                )
        s = _replace_cmd(s, "sqrt", "sqrt({0})", 1)
        if s == before:
            break
    s = re.sub(r"\\(pi)(?![A-Za-z])", "pi", s)
    s = re.sub(r"\\(infty)(?![A-Za-z])", "inf", s)
    s = re.sub(r"\\(sin|cos|tan|log|ln|exp)(?![A-Za-z])", r"\1", s)
    s = re.sub(r"\|([^|]+)\|", r"abs(\1)", s)
    s = s.replace("{", "(").replace("}", ")").replace("\\", "")
    s = re.sub(r"(?<=\d)%", "/100", s)
    s = s.replace("^", "**")
    s = re.sub(r"\*\*(-?[A-Za-z0-9]+(?:\.\d+)?)", r"**(\1)", s)
    s = _insert_implicit_mul(s)
    return s


_ALLOWED_FUNCS: Dict[str, Callable[..., Any]] = {
    "sqrt": cmath.sqrt,
    "sin": cmath.sin,
    "cos": cmath.cos,
    "tan": cmath.tan,
    "log": cmath.log,
    "ln": cmath.log,
    "exp": cmath.exp,
    "abs": abs,
}


def _eval_ast_node(node: ast.AST, env: Dict[str, complex]) -> complex:
    if isinstance(node, ast.Expression):
        return _eval_ast_node(node.body, env)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return complex(node.value)
        raise ValueError("unsupported constant")
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise ValueError(f"unknown symbol: {node.id}")
    if isinstance(node, ast.UnaryOp):
        v = _eval_ast_node(node.operand, env)
        if isinstance(node.op, ast.UAdd):
            return +v
        if isinstance(node.op, ast.USub):
            return -v
        raise ValueError("unsupported unary op")
    if isinstance(node, ast.BinOp):
        lv = _eval_ast_node(node.left, env)
        rv = _eval_ast_node(node.right, env)
        if isinstance(node.op, ast.Add):
            return lv + rv
        if isinstance(node.op, ast.Sub):
            return lv - rv
        if isinstance(node.op, ast.Mult):
            return lv * rv
        if isinstance(node.op, ast.Div):
            return lv / rv
        if isinstance(node.op, ast.Pow):
            return lv ** rv
        raise ValueError("unsupported binary op")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
            raise ValueError("disallowed call")
        if node.keywords or len(node.args) != 1:
            raise ValueError("bad call args")
        arg_v = _eval_ast_node(node.args[0], env)
        return complex(_ALLOWED_FUNCS[node.func.id](arg_v))
    raise ValueError(f"disallowed AST node: {type(node).__name__}")


def _collect_free_names(node: ast.AST) -> Set[str]:
    names: Set[str] = set()
    known = {"pi", "e", "inf", "i"} | set(_ALLOWED_FUNCS.keys())
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id not in known:
            names.add(sub.id)
    return names


def _ast_expr_equal(a: str, b: str) -> bool:
    if "=" in a or "<" in a or ">" in a or "=" in b or "<" in b or ">" in b:
        pa_eq = re.fullmatch(r"[A-Za-z]=([^=<>]+)", _norm_math(a))
        pb_eq = re.fullmatch(r"[A-Za-z]=([^=<>]+)", _norm_math(b))
        if not (pa_eq or pb_eq):
            return False
    py_a = _latex_to_py(a)
    py_b = _latex_to_py(b)
    try:
        tree_a = ast.parse(py_a, mode="eval")
        tree_b = ast.parse(py_b, mode="eval")
    except SyntaxError:
        return False

    free_a = _collect_free_names(tree_a)
    free_b = _collect_free_names(tree_b)
    if free_a != free_b:
        return False

    base_env: Dict[str, complex] = {
        "pi": complex(math.pi),
        "e": complex(math.e),
        "inf": complex(float("inf")),
        "i": complex(0.0, 1.0),
    }

    if not free_a:
        try:
            va = _eval_ast_node(tree_a, base_env)
            vb = _eval_ast_node(tree_b, base_env)
        except Exception:
            return False
        if cmath.isinf(va) and cmath.isinf(vb):
            return va.real == vb.real
        if cmath.isnan(va) or cmath.isnan(vb) or cmath.isinf(va) or cmath.isinf(vb):
            return False
        tol = 1e-9 * max(1.0, abs(va), abs(vb))
        return abs(va - vb) <= tol

    # Randomized multi-point evaluation for symbolic expressions with free variables
    rng = random.Random(2026042)
    matched = 0
    for _ in range(16):
        env = dict(base_env)
        for name in sorted(free_a):
            env[name] = complex(rng.uniform(1.3, 4.7), 0.0)
        try:
            va = _eval_ast_node(tree_a, env)
            vb = _eval_ast_node(tree_b, env)
        except Exception:
            continue
        if cmath.isnan(va) or cmath.isnan(vb) or cmath.isinf(va) or cmath.isinf(vb):
            continue
        tol = 1e-7 * max(1.0, abs(va), abs(vb))
        if abs(va - vb) > tol:
            return False
        matched += 1
    return matched >= 4


def _split_top_level(s: str) -> List[str]:
    parts: List[str] = []
    depth = 0
    cur: List[str] = []
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _tuple_parts(s: str) -> Optional[Tuple[str, str, List[str]]]:
    s = s.replace("\\{", "{").replace("\\}", "}")
    if len(s) >= 2 and s[0] in "([{" and s[-1] in ")]}":
        depth = 0
        for idx, ch in enumerate(s):
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
                if depth == 0 and idx != len(s) - 1:
                    return None
        parts = _split_top_level(s[1:-1])
        if len(parts) > 1:
            return s[0], s[-1], parts
        return None
    parts = _split_top_level(s)
    if len(parts) > 1:
        return "", "", parts
    return None


def _paren_letter(s: str) -> Optional[str]:
    m = re.fullmatch(r"\(?([A-Za-z])\)?", s)
    return m.group(1) if m else None


def _math_equal(a: str, b: str) -> bool:
    na = _norm_math(a)
    nb = _norm_math(b)
    if na == nb:
        return True
    la, lb = _paren_letter(na), _paren_letter(nb)
    if la and lb and (na.isalpha() or nb.isalpha() or "(" in na + nb):
        return la == lb
    ta, tb = _tuple_parts(na), _tuple_parts(nb)
    if ta or tb:
        if not (ta and tb):
            return False
        if ta[0] != tb[0] or ta[1] != tb[1] or len(ta[2]) != len(tb[2]):
            return False
        return all(_math_equal(x, y) for x, y in zip(ta[2], tb[2]))
    return _ast_expr_equal(na, nb)


def grade_math_answer(reply_text: Optional[str], gold: Any) -> Optional[bool]:
    """Extract and grade a SOLVE reply against official gold answer in pure stdlib."""
    ans = parse_answer(reply_text)
    if ans is None or gold is None:
        return None
    try:
        return bool(_math_equal(ans, str(gold)))
    except Exception:
        return False


def run_self_tests() -> None:
    """Verify inline parsers, math grader, and Acklam Phi^-1."""
    assert parse_verdict("Reasoning...\nVERDICT: ACCEPT") is True
    assert parse_verdict("**VERDICT: REJECT**") is False
    assert parse_choice("Line\nCHOICE: 2", 3) == 2
    assert parse_choice("Line\nCHOICE: NONE", 3) == 0
    assert parse_choice("Line\nCHOICE: 4", 3) is None
    assert parse_each("VERDICT 1: ACCEPT\nVERDICT 2: REJECT\nVERDICT 3: ACCEPT", 3) == [True, False, True]
    assert parse_confidence("Reasoning\nCHOICE: NONE\nCONFIDENCE: 4") == 4
    assert parse_confidence("**CONFIDENCE: 5**") == 5
    assert parse_confidence("CONFIDENCE: 9") is None
    assert parse_answer("work\nANSWER: $\\sqrt{17}-1$") == "\\sqrt{17}-1"

    math_cases = [
        ("ANSWER: $\\sqrt{17}-1$", "\\sqrt{17}-1", True),
        ("work\n**ANSWER: 42**", "42", True),
        ("so \\boxed{\\frac{1}{2}}", "0.5", True),
        ("ANSWER: 1,000", "1000", True),
        ("ANSWER: (1, 2)", "(1,2)", True),
        ("ANSWER: 2\\sqrt{3}", "\\sqrt{12}", True),
        ("ANSWER: \\frac{\\pi}{6}", "\\pi/6", True),
        ("ANSWER: \\dfrac{3}{4}", "\\frac{3}{4}", True),
        ("ANSWER: \\( 28800 \\)", "28800", True),
        ("ANSWER: B", "\\text{B}", True),
        ("ANSWER: (B)", "\\text{B}", True),
        ("ANSWER: x^2+1", "x^2+1", True),
        ("ANSWER: 1+x^2", "x^2+1", True),
        ("ANSWER: 7.", "7", True),
        ("ANSWER: \\boxed{12}", "12", True),
        ("ANSWER: x=5", "5", True),
        ("ANSWER: \\left(1,\\ 2\\right)", "(1,2)", True),
        ("ANSWER: 0.3333", "\\frac13", False),
        ("ANSWER: 41", "42", False),
        ("ANSWER: (1,2)", "(2,1)", False),
        ("ANSWER: (1,2)", "[1,2]", False),
        ("ANSWER: 2\\sqrt{3}", "\\sqrt{13}", False),
        ("ANSWER: x^2+2", "x^2+1", False),
        ("I think it is 4", "4", None),
    ]
    for rep, g, exp in math_cases:
        got = grade_math_answer(rep, g)
        if got is not exp:
            raise AssertionError(f"Math grader self-test failed: {rep!r} vs {g!r}: expected {exp}, got {got}")

    for p, expected_z in [(0.5, 0.0), (0.8413447460685429, 1.0), (0.975, 1.959963984540054), (0.025, -1.959963984540054)]:
        z = norm_ppf(p)
        if abs(z - expected_z) > 1e-8:
            raise AssertionError(f"Acklam ppf failed at p={p}: {z} vs {expected_z}")
        if abs(norm_cdf(z) - p) > 1e-8:
            raise AssertionError(f"CDF roundtrip failed at p={p}")


# ---------------------------------------------------------------------------
# 3. Acklam Phi^-1, Normal CDF, Hautus SDT, and Problem Bootstrap
# ---------------------------------------------------------------------------

def norm_ppf(p: float) -> float:
    """Inverse standard normal CDF Phi^-1(p) via Acklam's rational approximation."""
    if not (0.0 < p < 1.0):
        raise ValueError(f"p must be strictly in (0, 1), got {p}")
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    plow = 0.02425
    phigh = 1.0 - plow
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        return num / den
    if p <= phigh:
        q = p - 0.5
        r = q * q
        num = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
        den = ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0
        return num / den
    q = math.sqrt(-2.0 * math.log(1.0 - p))
    num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
    den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
    return -num / den


def norm_cdf(z: float) -> float:
    """Standard normal CDF Phi(z)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def ci95_percentile(sorted_vals: Sequence[float]) -> Optional[List[float]]:
    n = len(sorted_vals)
    if n == 0:
        return None
    lo = sorted_vals[max(0, min(n - 1, int(0.025 * n)))]
    hi = sorted_vals[max(0, min(n - 1, int(0.975 * n) - 1))]
    return [lo, hi]


def hautus_sdt(hits: Sequence[float], fas: Sequence[float]) -> Optional[Dict[str, Any]]:
    """Compute Hautus (1995) log-linear adjusted H, F, d', and c for paired trials."""
    n = len(hits)
    if n == 0 or len(fas) != n:
        return None
    h_raw = sum(hits) / n
    f_raw = sum(fas) / n
    h_adj = (sum(hits) + 0.5) / (n + 1.0)
    f_adj = (sum(fas) + 0.5) / (n + 1.0)
    zh = norm_ppf(h_adj)
    zf = norm_ppf(f_adj)
    return {
        "n": n,
        "H_raw": h_raw,
        "F_raw": f_raw,
        "H_adj": h_adj,
        "F_adj": f_adj,
        "zH": zh,
        "zF": zf,
        "d_prime": zh - zf,
        "c": -0.5 * (zh + zf),
    }


def bootstrap_sdt(hits: Sequence[float], fas: Sequence[float], seed: int, n_boot: int = DEFAULT_BOOT) -> Optional[Dict[str, Any]]:
    n = len(hits)
    if n == 0:
        return None
    point = hautus_sdt(hits, fas)
    assert point is not None
    rng = random.Random(seed)
    dp_draws: List[float] = []
    c_draws: List[float] = []
    h_draws: List[float] = []
    f_draws: List[float] = []
    for _ in range(n_boot):
        idxs = [rng.randrange(n) for _ in range(n)]
        hs = sum(hits[i] for i in idxs)
        fs = sum(fas[i] for i in idxs)
        h_draws.append(hs / n)
        f_draws.append(fs / n)
        zh = norm_ppf((hs + 0.5) / (n + 1.0))
        zf = norm_ppf((fs + 0.5) / (n + 1.0))
        dp_draws.append(zh - zf)
        c_draws.append(-0.5 * (zh + zf))
    dp_draws.sort()
    c_draws.sort()
    h_draws.sort()
    f_draws.sort()
    point["d_prime_ci95"] = ci95_percentile(dp_draws)
    point["c_ci95"] = ci95_percentile(c_draws)
    point["H_raw_ci95"] = ci95_percentile(h_draws)
    point["F_raw_ci95"] = ci95_percentile(f_draws)
    return point


def bootstrap_sdt_diff(
    pairs_a: Sequence[Tuple[float, float]],
    pairs_b: Sequence[Tuple[float, float]],
    seed: int,
    n_boot: int = DEFAULT_BOOT,
) -> Optional[Dict[str, Any]]:
    n = len(pairs_a)
    if n == 0 or len(pairs_b) != n:
        return None
    ha = [x[0] for x in pairs_a]
    fa = [x[1] for x in pairs_a]
    hb = [x[0] for x in pairs_b]
    fb = [x[1] for x in pairs_b]
    sa = hautus_sdt(ha, fa)
    sb = hautus_sdt(hb, fb)
    assert sa is not None and sb is not None
    rng = random.Random(seed)
    ddp: List[float] = []
    dc: List[float] = []
    dh: List[float] = []
    df: List[float] = []
    for _ in range(n_boot):
        idxs = [rng.randrange(n) for _ in range(n)]
        has = sum(ha[i] for i in idxs)
        fas_s = sum(fa[i] for i in idxs)
        hbs = sum(hb[i] for i in idxs)
        fbs_s = sum(fb[i] for i in idxs)
        zha = norm_ppf((has + 0.5) / (n + 1.0))
        zfa = norm_ppf((fas_s + 0.5) / (n + 1.0))
        zhb = norm_ppf((hbs + 0.5) / (n + 1.0))
        zfb = norm_ppf((fbs_s + 0.5) / (n + 1.0))
        ddp.append((zha - zfa) - (zhb - zfb))
        dc.append((-0.5 * (zha + zfa)) - (-0.5 * (zhb + zfb)))
        dh.append((has - hbs) / n)
        df.append((fas_s - fbs_s) / n)
    ddp.sort()
    dc.sort()
    dh.sort()
    df.sort()
    return {
        "n": n,
        "d_prime_diff": sa["d_prime"] - sb["d_prime"],
        "d_prime_diff_ci95": ci95_percentile(ddp),
        "d_prime_diff_p_one_sided_lt0": sum(1 for x in ddp if x >= 0.0) / n_boot,
        "d_prime_diff_p_one_sided_gt0": sum(1 for x in ddp if x <= 0.0) / n_boot,
        "c_diff": sa["c"] - sb["c"],
        "c_diff_ci95": ci95_percentile(dc),
        "c_diff_p_one_sided_gt0": sum(1 for x in dc if x <= 0.0) / n_boot,
        "c_diff_p_one_sided_lt0": sum(1 for x in dc if x >= 0.0) / n_boot,
        "H_diff": sa["H_raw"] - sb["H_raw"],
        "H_diff_ci95": ci95_percentile(dh),
        "H_diff_p_one_sided_lt0": sum(1 for x in dh if x >= 0.0) / n_boot,
        "F_diff": sa["F_raw"] - sb["F_raw"],
        "F_diff_ci95": ci95_percentile(df),
        "F_diff_p_one_sided_lt0": sum(1 for x in df if x >= 0.0) / n_boot,
    }


def bootstrap_mean(xs: Sequence[float], seed: int, n_boot: int = DEFAULT_BOOT) -> Dict[str, Any]:
    n = len(xs)
    if n == 0:
        return {
            "n": 0,
            "mean": None,
            "ci95": None,
            "p_one_sided_gt0": None,
            "p_one_sided_lt0": None,
        }
    rng = random.Random(seed)
    draws = [sum(rng.choice(xs) for _ in range(n)) / n for _ in range(n_boot)]
    draws.sort()
    return {
        "n": n,
        "mean": sum(xs) / n,
        "ci95": ci95_percentile(draws),
        "p_one_sided_gt0": sum(1 for x in draws if x <= 0.0) / n_boot,
        "p_one_sided_lt0": sum(1 for x in draws if x >= 0.0) / n_boot,
    }


# ---------------------------------------------------------------------------
# 4. Data Loaders & Token Extraction
# ---------------------------------------------------------------------------

def load_v2_raw_dir(raw_dir: Path) -> Dict[str, Any]:
    if not raw_dir.is_dir():
        return {"exists": False, "n_files": 0, "n_ok": 0, "records": {}}
    records: Dict[str, Dict[str, Any]] = {}
    n_files = 0
    n_ok = 0
    for fp in sorted(raw_dir.glob("*.json")):
        if fp.name.startswith("."):
            continue
        n_files += 1
        try:
            rec = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        jid = str(rec.get("job_id") or rec.get("id") or fp.stem)
        if rec.get("status") == "ok" and isinstance(rec.get("text"), str):
            n_ok += 1
            records[jid] = rec
    return {"exists": True, "n_files": n_files, "n_ok": n_ok, "records": records}


def extract_v2_output_thinking_tokens(rec: Dict[str, Any]) -> Optional[int]:
    """Return total output+thinking tokens without double-counting nested thinking tokens."""
    out_tok = rec.get("output_tokens")
    think_tok = rec.get("thinking_tokens")
    in_tok = rec.get("input_tokens")
    if not isinstance(out_tok, (int, float)):
        return None
    out_i = int(out_tok)
    if not isinstance(think_tok, (int, float)) or int(think_tok) <= 0:
        return out_i
    think_i = int(think_tok)
    raw_meta = rec.get("raw_meta") if isinstance(rec.get("raw_meta"), dict) else {}
    usage = raw_meta.get("usage") if isinstance(raw_meta.get("usage"), dict) else {}
    # Anthropic claude_cli puts thinking_tokens inside output_tokens_details and includes it in output_tokens.
    if isinstance(usage.get("output_tokens_details"), dict) and "thinking_tokens" in usage["output_tokens_details"]:
        return out_i
    total_tok = usage.get("total_tokens")
    if isinstance(total_tok, (int, float)) and isinstance(in_tok, (int, float)):
        if int(total_tok) == int(in_tok) + out_i:
            return out_i
    if rec.get("route") == "claude_cli" or out_i >= think_i:
        return out_i
    return out_i + think_i


def load_c3_record(c3_root: Path, arm_id: str) -> Optional[Dict[str, Any]]:
    for sub in ("raw/arms", "raw/a4"):
        cand = c3_root / "exps" / "c3" / sub / f"{arm_id}.json"
        if cand.is_file():
            try:
                rec = json.loads(cand.read_text(encoding="utf-8"))
                if rec.get("rc") in (None, 0) and isinstance(rec.get("result"), str):
                    return rec
            except Exception:
                return None
    return None


def extract_c3_output_thinking_tokens(rec: Dict[str, Any]) -> Optional[int]:
    usage = rec.get("usage")
    if isinstance(usage, dict) and isinstance(usage.get("output_tokens"), (int, float)):
        return int(usage["output_tokens"])
    return None


def _arm_completeness(loaded: Dict[str, Any], expected_n: int) -> str:
    if not loaded["exists"]:
        return "missing"
    if loaded["n_ok"] == 0:
        return "empty_ok"
    if loaded["n_ok"] < expected_n:
        return "partial"
    return "complete"


# ---------------------------------------------------------------------------
# 5. Study Analyzers
# ---------------------------------------------------------------------------

def _has_claude_cand(pool: Dict[str, Any]) -> bool:
    for c in pool.get("cands", []):
        tag = f"{c.get('vendor', '')} {c.get('gen', '')}".lower()
        if "claude" in tag:
            return True
    return False


def _compute_c5_own_subset(
    sub_pools: Sequence[Dict[str, Any]],
    parsed_by_pool: Dict[str, int],
    c3_root: Path,
    n_boot: int,
    sb: int,
) -> Dict[str, Any]:
    fa_pick2_vals: List[float] = []
    fa_iso2_vals: List[float] = []
    d_c5_vals: List[float] = []
    fa_pick3_vals: List[float] = []
    fa_iso3_vals: List[float] = []
    d_c3_vals: List[float] = []
    red_vals: List[float] = []
    used_pids: List[str] = []

    for p in sub_pools:
        pname = p["pool"]
        if pname not in parsed_by_pool:
            continue
        iso_retained: List[bool] = []
        for cid in p["retained_cids"]:
            c3_iso = load_c3_record(c3_root, f"haiku__ISO__{cid}")
            v = parse_verdict(c3_iso["result"]) if c3_iso else None
            if v is None:
                iso_retained = []
                break
            iso_retained.append(v)
        if len(iso_retained) != 2:
            continue

        c3_rem = load_c3_record(c3_root, f"haiku__ISO__{p['removed_cid']}")
        v_rem = parse_verdict(c3_rem["result"]) if c3_rem else None
        c3_pick = load_c3_record(c3_root, f"haiku__PICK__{pname}")
        k_pick3 = parse_choice(c3_pick["result"], 3) if c3_pick else None
        if v_rem is None or k_pick3 is None:
            continue

        fa_p2 = 1.0 if parsed_by_pool[pname] > 0 else 0.0
        fa_i2 = 1.0 if any(iso_retained) else 0.0
        d5 = fa_p2 - fa_i2

        fa_p3 = 1.0 if k_pick3 > 0 else 0.0
        fa_i3 = 1.0 if (any(iso_retained) or v_rem) else 0.0
        d3 = fa_p3 - fa_i3

        fa_pick2_vals.append(fa_p2)
        fa_iso2_vals.append(fa_i2)
        d_c5_vals.append(d5)
        fa_pick3_vals.append(fa_p3)
        fa_iso3_vals.append(fa_i3)
        d_c3_vals.append(d3)
        red_vals.append(d3 - d5)
        used_pids.append(p["pid"])

    b_p2 = bootstrap_mean(fa_pick2_vals, sb + 1, n_boot)
    b_i2 = bootstrap_mean(fa_iso2_vals, sb + 2, n_boot)
    b_d5 = bootstrap_mean(d_c5_vals, sb + 3, n_boot)
    b_p3 = bootstrap_mean(fa_pick3_vals, sb + 4, n_boot)
    b_i3 = bootstrap_mean(fa_iso3_vals, sb + 5, n_boot)
    b_d3 = bootstrap_mean(d_c3_vals, sb + 6, n_boot)
    b_red = bootstrap_mean(red_vals, sb + 7, n_boot)

    kill_sole = False
    if b_d5["p_one_sided_gt0"] is not None and b_d5["ci95"] is not None:
        kill_sole = (b_d5["p_one_sided_gt0"] >= 0.05) and (b_d5["ci95"][1] < 0.10)

    return {
        "n_bank": len(sub_pools),
        "n_analyzed": len(used_pids),
        "pids": used_pids,
        "fa_pick2": b_p2["mean"],
        "fa_pick2_ci95": b_p2["ci95"],
        "fa_iso2": b_i2["mean"],
        "fa_iso2_ci95": b_i2["ci95"],
        "d_c5": b_d5["mean"],
        "d_c5_ci95": b_d5["ci95"],
        "d_c5_p_one_sided": b_d5["p_one_sided_gt0"],
        "fa_pick3_c3": b_p3["mean"],
        "fa_iso3_c3": b_i3["mean"],
        "d_c3": b_d3["mean"],
        "d_c3_ci95": b_d3["ci95"],
        "effect_reduction_d_c3_minus_d_c5": b_red["mean"],
        "effect_reduction_ci95": b_red["ci95"],
        "kill_own_sole_driver": kill_sole,
    }


def analyze_c5_own_removal(
    root: Path,
    c3_root: Path,
    n_boot: int,
    base_seed: int,
) -> Dict[str, Any]:
    bank = json.loads((root / "banks/locked_v2/c5_haiku_removal.json").read_text(encoding="utf-8"))
    pools = bank["own_answer_removal"]
    raw_dir = root / "exps/c5_removal/raw_own"
    loaded = load_v2_raw_dir(raw_dir)
    status = _arm_completeness(loaded, len(pools))

    parsed_by_pool: Dict[str, int] = {}
    for p in pools:
        jid = f"haiku__PICK2_OWN__{p['pool']}"
        rec = loaded["records"].get(jid)
        if rec is None:
            continue
        ch = parse_choice(rec["text"], 2)
        if ch is not None:
            parsed_by_pool[p["pool"]] = ch

    subsets_out: Dict[str, Any] = {}
    for s_idx, (sub_name, sub_pools) in enumerate(
        [
            ("all_38", pools),
            ("corrected_33", [p for p in pools if p.get("is_corrected_unsolved")]),
        ]
    ):
        sb = base_seed + 1000 + s_idx * 50
        res = _compute_c5_own_subset(sub_pools, parsed_by_pool, c3_root, n_boot, sb)
        zero_cl = [p for p in sub_pools if not _has_claude_cand(p)]
        ge1_cl = [p for p in sub_pools if _has_claude_cand(p)]
        res["claude_candidate_subgroups"] = {
            "zero_claude": _compute_c5_own_subset(zero_cl, parsed_by_pool, c3_root, n_boot, sb + 15),
            "ge1_claude": _compute_c5_own_subset(ge1_cl, parsed_by_pool, c3_root, n_boot, sb + 30),
        }
        subsets_out[sub_name] = res

    return {
        "status": status,
        "n_expected": len(pools),
        "n_files": loaded["n_files"],
        "n_ok": loaded["n_ok"],
        "n_parsed": len(parsed_by_pool),
        "parse_rate": (len(parsed_by_pool) / loaded["n_ok"]) if loaded["n_ok"] else None,
        "subsets": subsets_out,
    }


def analyze_c5_wells_removal(
    root: Path,
    c3_root: Path,
    n_boot: int,
    base_seed: int,
) -> Dict[str, Any]:
    bank = json.loads((root / "banks/locked_v2/c5_haiku_removal.json").read_text(encoding="utf-8"))
    pools = bank["wells_removal"]
    raw_dir = root / "exps/c5_removal/raw_wells"
    loaded = load_v2_raw_dir(raw_dir)
    status = _arm_completeness(loaded, len(pools))

    parsed_by_pool: Dict[str, int] = {}
    for p in pools:
        jid = f"haiku__PICK2_WELLS__{p['pool']}"
        rec = loaded["records"].get(jid)
        if rec is None:
            continue
        ch = parse_choice(rec["text"], 2)
        if ch is not None:
            parsed_by_pool[p["pool"]] = ch

    pick2_vals: List[float] = []
    iso2_vals: List[float] = []
    iso_rem_vals: List[float] = []
    iso3_vals: List[float] = []
    diff_iso2_vals: List[float] = []
    used_pids: List[str] = []

    for p in pools:
        pname = p["pool"]
        if pname not in parsed_by_pool:
            continue
        iso_ret: List[bool] = []
        for cid in p["retained_cids"]:
            c3_iso = load_c3_record(c3_root, f"haiku__ISO__{cid}")
            v = parse_verdict(c3_iso["result"]) if c3_iso else None
            if v is None:
                iso_ret = []
                break
            iso_ret.append(v)
        if len(iso_ret) != 2:
            continue
        c3_rem = load_c3_record(c3_root, f"haiku__ISO__{p['removed_cid']}")
        v_rem = parse_verdict(c3_rem["result"]) if c3_rem else None
        if v_rem is None:
            continue

        p2 = 1.0 if parsed_by_pool[pname] > 0 else 0.0
        i2 = 1.0 if any(iso_ret) else 0.0
        pick2_vals.append(p2)
        iso2_vals.append(i2)
        iso_rem_vals.append(1.0 if v_rem else 0.0)
        iso3_vals.append(1.0 if (any(iso_ret) or v_rem) else 0.0)
        diff_iso2_vals.append(p2 - i2)
        used_pids.append(p["pid"])

    sb = base_seed + 2000
    b_p2 = bootstrap_mean(pick2_vals, sb + 1, n_boot)
    b_i2 = bootstrap_mean(iso2_vals, sb + 2, n_boot)
    b_diff = bootstrap_mean(diff_iso2_vals, sb + 3, n_boot)

    n_src = bank["meta"].get("n_wells_source_pools", 68)
    c3_pick3_rate_all = len(pools) / n_src if n_src else None
    prop_2_of_3 = ((2.0 / 3.0) * c3_pick3_rate_all) if c3_pick3_rate_all is not None else None
    indep_2_of_3 = (1.0 - (1.0 - c3_pick3_rate_all) ** (2.0 / 3.0)) if c3_pick3_rate_all is not None else None

    diff_vs_prop = (
        (b_p2["mean"] - prop_2_of_3)
        if (b_p2["mean"] is not None and prop_2_of_3 is not None)
        else None
    )

    return {
        "status": status,
        "n_expected": len(pools),
        "n_files": loaded["n_files"],
        "n_ok": loaded["n_ok"],
        "n_parsed": len(parsed_by_pool),
        "parse_rate": (len(parsed_by_pool) / loaded["n_ok"]) if loaded["n_ok"] else None,
        "n_analyzed": len(used_pids),
        "choosing_rate_pick2": b_p2["mean"],
        "choosing_rate_pick2_ci95": b_p2["ci95"],
        "abstain_rate_pick2": (1.0 - b_p2["mean"]) if b_p2["mean"] is not None else None,
        "fa_iso2_c3": b_i2["mean"],
        "fa_iso2_c3_ci95": b_i2["ci95"],
        "diff_pick2_minus_iso2": b_diff["mean"],
        "diff_pick2_minus_iso2_ci95": b_diff["ci95"],
        "diff_pick2_minus_iso2_p_one_sided": b_diff["p_one_sided_gt0"],
        "c3_pick3_rate_all_source": c3_pick3_rate_all,
        "proportional_2_of_3_baseline": prop_2_of_3,
        "indep_2_of_3_baseline": indep_2_of_3,
        "diff_vs_proportional_2_of_3": diff_vs_prop,
        "c3_iso_removed_accept_rate": (sum(iso_rem_vals) / len(iso_rem_vals)) if iso_rem_vals else None,
        "c3_iso3_accept_rate_on_analyzed": (sum(iso3_vals) / len(iso3_vals)) if iso3_vals else None,
    }


def analyze_c4_compute(
    root: Path,
    c3_root: Path,
    n_boot: int,
    base_seed: int,
) -> Dict[str, Any]:
    bank = json.loads((root / "banks/locked_v2/c4_haiku_compute.json").read_text(encoding="utf-8"))
    pools = bank["pools"]
    n_expected_calls = len(pools) * 3
    raw_dir = root / "exps/c4_compute/raw_haiku"
    loaded = load_v2_raw_dir(raw_dir)
    status = _arm_completeness(loaded, n_expected_calls)

    parsed_calls = 0
    pool_reps: Dict[str, List[Optional[int]]] = {}
    pool_tokens: Dict[str, Optional[int]] = {}

    for p in pools:
        pname = p["pool"]
        reps: List[Optional[int]] = []
        tok_sum = 0
        tok_complete = True
        for rep in range(3):
            jid = f"haiku__PICK__{pname}__rep{rep}"
            rec = loaded["records"].get(jid)
            if rec is None:
                reps.append(None)
                tok_complete = False
                continue
            ch = parse_choice(rec["text"], 3)
            if ch is not None:
                parsed_calls += 1
            reps.append(ch)
            tk = extract_v2_output_thinking_tokens(rec)
            if tk is None:
                tok_complete = False
            else:
                tok_sum += tk
        pool_reps[pname] = reps
        pool_tokens[pname] = tok_sum if tok_complete else None

    ta_pools = [p for p in pools if p["kind"] == "TA"]
    tp_pools = {p["pid"]: p for p in pools if p["kind"] == "TP"}

    def _agg_c4_pool(p: Dict[str, Any], ks: List[int]) -> Dict[str, float]:
        # Primary MAJ3: consensus >= 2, else 0
        counts: Dict[int, int] = {}
        for k in ks:
            counts[k] = counts.get(k, 0) + 1
        maj = 0
        for m_val, cnt in counts.items():
            if cnt >= 2:
                maj = m_val
                break
        is_tp = p["kind"] == "TP"
        right_idx = next((i + 1 for i, c in enumerate(p["cands"]) if c["role"] == "right"), -1) if is_tp else -1

        if is_tp:
            maj_score = 1.0 if (maj > 0 and maj == right_idx) else 0.0
            if maj > 0 or any(cnt >= 2 for cnt in counts.values()):
                maj_unif = maj_score
            else:
                maj_unif = sum(1.0 for k in ks if k == right_idx) / 3.0
            uniq = {k for k in ks if k > 0}
            any3_aligned = (1.0 / len(uniq)) if (uniq and right_idx in uniq) else 0.0
            any3_strict = 1.0 if (uniq == {right_idx}) else 0.0
        else:
            maj_score = 1.0 if maj > 0 else 0.0
            if maj > 0 or any(cnt >= 2 for cnt in counts.values()):
                maj_unif = maj_score
            else:
                maj_unif = sum(1.0 for k in ks if k > 0) / 3.0
            any3_aligned = 1.0 if any(k > 0 for k in ks) else 0.0
            any3_strict = any3_aligned
        return {
            "maj3": maj_score,
            "maj3_tieunif": maj_unif,
            "any3": any3_aligned,
            "any3_strict": any3_strict,
        }

    def _c3_baselines(p: Dict[str, Any]) -> Optional[Dict[str, float]]:
        verdicts: List[bool] = []
        iso_tok = 0
        iso_tok_ok = True
        for c in p["cands"]:
            rec = load_c3_record(c3_root, f"haiku__ISO__{c['cid']}")
            v = parse_verdict(rec["result"]) if rec else None
            if v is None:
                return None
            verdicts.append(v)
            tk = extract_c3_output_thinking_tokens(rec) if rec else None
            if tk is None:
                iso_tok_ok = False
            else:
                iso_tok += tk
        rec_p = load_c3_record(c3_root, f"haiku__PICK__{p['pool']}")
        k_p1 = parse_choice(rec_p["result"], 3) if rec_p else None
        if k_p1 is None:
            return None

        is_tp = p["kind"] == "TP"
        if is_tp:
            right_i = next(i for i, c in enumerate(p["cands"]) if c["role"] == "right")
            a = sum(1 for v in verdicts if v)
            iso_aligned = (1.0 / a) if (a > 0 and verdicts[right_i]) else 0.0
            iso_strict = 1.0 if all(v == (i == right_i) for i, v in enumerate(verdicts)) else 0.0
            pick1_score = 1.0 if k_p1 == right_i + 1 else 0.0
        else:
            iso_aligned = 1.0 if any(verdicts) else 0.0
            iso_strict = iso_aligned
            pick1_score = 1.0 if k_p1 > 0 else 0.0

        return {
            "iso_aligned": iso_aligned,
            "iso_strict": iso_strict,
            "pick1": pick1_score,
            "iso_tokens": float(iso_tok) if iso_tok_ok else -1.0,
        }

    # TA analysis (N=68)
    ta_arms: Dict[str, List[float]] = {
        k: [] for k in ("PICK_MAJ3", "PICK_MAJ3_TIEUNIF", "PICK_ANY3", "ISO_any", "PICK_1X")
    }
    ta_pids: List[str] = []
    for p in ta_pools:
        ks = pool_reps[p["pool"]]
        if any(x is None for x in ks):
            continue
        c3_b = _c3_baselines(p)
        if c3_b is None:
            continue
        agg = _agg_c4_pool(p, [int(x) for x in ks if x is not None])
        ta_arms["PICK_MAJ3"].append(agg["maj3"])
        ta_arms["PICK_MAJ3_TIEUNIF"].append(agg["maj3_tieunif"])
        ta_arms["PICK_ANY3"].append(agg["any3"])
        ta_arms["ISO_any"].append(c3_b["iso_aligned"])
        ta_arms["PICK_1X"].append(c3_b["pick1"])
        ta_pids.append(p["pid"])

    sb = base_seed + 3000
    ta_summary = {
        arm: bootstrap_mean(vals, sb + idx, n_boot)
        for idx, (arm, vals) in enumerate(ta_arms.items())
    }
    ta_contrasts = {}
    for idx, (a_name, b_name) in enumerate(
        [
            ("PICK_MAJ3", "ISO_any"),
            ("PICK_ANY3", "ISO_any"),
            ("PICK_MAJ3_TIEUNIF", "ISO_any"),
            ("PICK_MAJ3", "PICK_1X"),
        ]
    ):
        diffs = [x - y for x, y in zip(ta_arms[a_name], ta_arms[b_name])]
        ta_contrasts[f"{a_name}_minus_{b_name}"] = bootstrap_mean(diffs, sb + 50 + idx, n_boot)

    # Paired TA+TP SDT analysis (N=56)
    sdt_pairs: Dict[str, List[Tuple[float, float]]] = {
        k: [] for k in ("PICK_MAJ3", "PICK_MAJ3_TIEUNIF", "PICK_ANY3", "ISO", "PICK_1X")
    }
    strict_tp_hits: Dict[str, List[float]] = {
        k: [] for k in ("PICK_MAJ3", "PICK_ANY3", "ISO", "PICK_1X")
    }
    tp_pids: List[str] = []
    for p_ta in ta_pools:
        pid = p_ta["pid"]
        if pid not in tp_pools:
            continue
        p_tp = tp_pools[pid]
        ks_ta = pool_reps[p_ta["pool"]]
        ks_tp = pool_reps[p_tp["pool"]]
        if any(x is None for x in ks_ta) or any(x is None for x in ks_tp):
            continue
        c3_ta = _c3_baselines(p_ta)
        c3_tp = _c3_baselines(p_tp)
        if c3_ta is None or c3_tp is None:
            continue
        agg_ta = _agg_c4_pool(p_ta, [int(x) for x in ks_ta if x is not None])
        agg_tp = _agg_c4_pool(p_tp, [int(x) for x in ks_tp if x is not None])

        sdt_pairs["PICK_MAJ3"].append((agg_tp["maj3"], agg_ta["maj3"]))
        sdt_pairs["PICK_MAJ3_TIEUNIF"].append((agg_tp["maj3_tieunif"], agg_ta["maj3_tieunif"]))
        sdt_pairs["PICK_ANY3"].append((agg_tp["any3"], agg_ta["any3"]))
        sdt_pairs["ISO"].append((c3_tp["iso_aligned"], c3_ta["iso_aligned"]))
        sdt_pairs["PICK_1X"].append((c3_tp["pick1"], c3_ta["pick1"]))

        strict_tp_hits["PICK_MAJ3"].append(agg_tp["maj3"])
        strict_tp_hits["PICK_ANY3"].append(agg_tp["any3_strict"])
        strict_tp_hits["ISO"].append(c3_tp["iso_strict"])
        strict_tp_hits["PICK_1X"].append(c3_tp["pick1"])
        tp_pids.append(pid)

    sdt_out = {}
    for idx, (arm, pairs) in enumerate(sdt_pairs.items()):
        hits = [x[0] for x in pairs]
        fas = [x[1] for x in pairs]
        sdt_out[arm] = bootstrap_sdt(hits, fas, sb + 100 + idx, n_boot)
    sdt_diffs = {}
    for idx, (a_name, b_name) in enumerate(
        [
            ("PICK_MAJ3", "ISO"),
            ("PICK_ANY3", "ISO"),
            ("PICK_MAJ3_TIEUNIF", "ISO"),
            ("PICK_MAJ3", "PICK_1X"),
        ]
    ):
        sdt_diffs[f"{a_name}_minus_{b_name}"] = bootstrap_sdt_diff(
            sdt_pairs[a_name], sdt_pairs[b_name], sb + 150 + idx, n_boot
        )
    strict_hits_out = {
        arm: bootstrap_mean(vals, sb + 200 + idx, n_boot)
        for idx, (arm, vals) in enumerate(strict_tp_hits.items())
    }

    # Exact median output+thinking token ratio (PICK_3x / ISO_3x)
    tok_sections: Dict[str, Any] = {}
    for sec_name, sec_pools in [
        ("ta", ta_pools),
        ("tp", list(tp_pools.values())),
        ("all", pools),
    ]:
        p3_list: List[int] = []
        i3_list: List[int] = []
        ratios_per_pool: List[float] = []
        for p in sec_pools:
            pt = pool_tokens.get(p["pool"])
            c3_b = _c3_baselines(p)
            if pt is None or c3_b is None or c3_b["iso_tokens"] <= 0:
                continue
            it = int(c3_b["iso_tokens"])
            p3_list.append(pt)
            i3_list.append(it)
            ratios_per_pool.append(pt / it)
        if p3_list and i3_list:
            p_med = float(statistics.median(p3_list))
            i_med = float(statistics.median(i3_list))
            ratio = p_med / i_med if i_med > 0 else None
            tok_sections[sec_name] = {
                "n_pools": len(p3_list),
                "pick_3x_median_tokens": p_med,
                "iso_3x_median_tokens": i_med,
                "median_ratio": ratio,
                "per_pool_ratio_median": float(statistics.median(ratios_per_pool)),
                "gate_090_to_110": (0.90 <= ratio <= 1.10) if ratio is not None else False,
            }
        else:
            tok_sections[sec_name] = {
                "n_pools": 0,
                "pick_3x_median_tokens": None,
                "iso_3x_median_tokens": None,
                "median_ratio": None,
                "per_pool_ratio_median": None,
                "gate_090_to_110": False,
            }

    return {
        "status": status,
        "n_expected_calls": n_expected_calls,
        "n_files": loaded["n_files"],
        "n_ok": loaded["n_ok"],
        "n_parsed_calls": parsed_calls,
        "parse_rate_calls": (parsed_calls / loaded["n_ok"]) if loaded["n_ok"] else None,
        "n_ta_analyzed": len(ta_pids),
        "n_tp_paired_analyzed": len(tp_pids),
        "ta_rates": ta_summary,
        "ta_contrasts": ta_contrasts,
        "sdt_aligned": sdt_out,
        "sdt_diffs": sdt_diffs,
        "strict_tp_hits": strict_hits_out,
        "token_ratio": tok_sections,
    }


def _evaluate_pool_arms(
    items: Sequence[Dict[str, Any]],
    pick_recs: Dict[str, Any],
    each_recs: Dict[str, Any],
    iso_recs: Dict[str, Any],
    n_cands: int,
    n_boot: int,
    seed: int,
    include_m1: bool = False,
) -> Dict[str, Any]:
    """Compute TA FA, TP aligned H, Right|pick, SDT d'/c, paired diffs, and optional M1."""
    arms = ["PICK", "EACH", "ISO"]
    if include_m1:
        arms.extend(["M1_unif", "M1_pick_tiebreak", "M1_pick_or_abstain"])

    arm_ta: Dict[str, List[float]] = {a: [] for a in arms}
    arm_tp_aligned: Dict[str, List[float]] = {a: [] for a in arms}
    arm_tp_strict: Dict[str, List[float]] = {a: [] for a in arms}
    arm_pairs: Dict[str, Dict[str, Tuple[float, float]]] = {a: {} for a in arms}

    right_given_pick_vals: List[float] = []
    right_given_each_vals: List[float] = []
    right_given_iso_vals: List[float] = []

    for it in items:
        pid = it["pid"]
        ta_pool = it["ta"]
        tp_pool = it["tp"]

        # PICK
        pr_ta = pick_recs.get(f"PICK__{ta_pool['pool']}")
        pr_tp = pick_recs.get(f"PICK__{tp_pool['pool']}")
        k_ta = parse_choice(pr_ta["text"], n_cands) if pr_ta else None
        k_tp = parse_choice(pr_tp["text"], n_cands) if pr_tp else None
        right_tp_1idx = next(i + 1 for i, c in enumerate(tp_pool["cands"]) if c["role"] == "right")

        if k_ta is not None:
            arm_ta["PICK"].append(1.0 if k_ta > 0 else 0.0)
        if k_tp is not None:
            h_p = 1.0 if k_tp == right_tp_1idx else 0.0
            arm_tp_aligned["PICK"].append(h_p)
            arm_tp_strict["PICK"].append(h_p)
            if k_tp > 0:
                right_given_pick_vals.append(h_p)
        if k_ta is not None and k_tp is not None:
            arm_pairs["PICK"][pid] = (1.0 if k_tp == right_tp_1idx else 0.0, 1.0 if k_ta > 0 else 0.0)

        # EACH
        er_ta = each_recs.get(f"EACH__{ta_pool['pool']}")
        er_tp = each_recs.get(f"EACH__{tp_pool['pool']}")
        ev_ta = parse_each(er_ta["text"], n_cands) if er_ta else None
        ev_tp = parse_each(er_tp["text"], n_cands) if er_tp else None
        if ev_ta is not None:
            arm_ta["EACH"].append(1.0 if any(ev_ta) else 0.0)
        if ev_tp is not None:
            a_e = sum(1 for v in ev_tp if v)
            h_ea = (1.0 / a_e) if (a_e > 0 and ev_tp[right_tp_1idx - 1]) else 0.0
            h_es = 1.0 if all(v == (i == right_tp_1idx - 1) for i, v in enumerate(ev_tp)) else 0.0
            arm_tp_aligned["EACH"].append(h_ea)
            arm_tp_strict["EACH"].append(h_es)
            if a_e > 0:
                right_given_each_vals.append(h_ea)
        if ev_ta is not None and ev_tp is not None:
            a_e = sum(1 for v in ev_tp if v)
            h_ea = (1.0 / a_e) if (a_e > 0 and ev_tp[right_tp_1idx - 1]) else 0.0
            arm_pairs["EACH"][pid] = (h_ea, 1.0 if any(ev_ta) else 0.0)

        # ISO
        iv_ta: List[bool] = []
        for c in ta_pool["cands"]:
            ir = iso_recs.get(f"ISO__{c['cid']}")
            v = parse_verdict(ir["text"]) if ir else None
            if v is None:
                iv_ta = []
                break
            iv_ta.append(v)
        iv_tp: List[bool] = []
        for c in tp_pool["cands"]:
            ir = iso_recs.get(f"ISO__{c['cid']}")
            v = parse_verdict(ir["text"]) if ir else None
            if v is None:
                iv_tp = []
                break
            iv_tp.append(v)

        if iv_ta:
            arm_ta["ISO"].append(1.0 if any(iv_ta) else 0.0)
        if iv_tp:
            a_i = sum(1 for v in iv_tp if v)
            h_ia = (1.0 / a_i) if (a_i > 0 and iv_tp[right_tp_1idx - 1]) else 0.0
            h_is = 1.0 if all(v == (i == right_tp_1idx - 1) for i, v in enumerate(iv_tp)) else 0.0
            arm_tp_aligned["ISO"].append(h_ia)
            arm_tp_strict["ISO"].append(h_is)
            if a_i > 0:
                right_given_iso_vals.append(h_ia)
        if iv_ta and iv_tp:
            a_i = sum(1 for v in iv_tp if v)
            h_ia = (1.0 / a_i) if (a_i > 0 and iv_tp[right_tp_1idx - 1]) else 0.0
            arm_pairs["ISO"][pid] = (h_ia, 1.0 if any(iv_ta) else 0.0)

        # Optional Two-Stage M1 exact offline simulation
        if include_m1 and iv_ta and iv_tp:
            s_ta = [i for i, v in enumerate(iv_ta) if v]
            s_tp = [i for i, v in enumerate(iv_tp) if v]
            # M1_unif == aligned ISO
            fa_u = 1.0 if s_ta else 0.0
            h_u = (1.0 / len(s_tp)) if (s_tp and (right_tp_1idx - 1) in s_tp) else 0.0
            arm_ta["M1_unif"].append(fa_u)
            arm_tp_aligned["M1_unif"].append(h_u)
            arm_tp_strict["M1_unif"].append(h_u)
            arm_pairs["M1_unif"][pid] = (h_u, fa_u)

            if k_ta is not None and k_tp is not None:
                # M1_pick_tiebreak: if |S|>=2 and PICK choice in S, take PICK choice; else uniform over S
                if len(s_ta) == 0:
                    fa_m1, fa_m1a = 0.0, 0.0
                elif len(s_ta) == 1:
                    fa_m1, fa_m1a = 1.0, 1.0
                else:
                    fa_m1 = 1.0
                    fa_m1a = 0.0 if k_ta == 0 else 1.0

                if len(s_tp) == 0:
                    h_m1, h_m1a = 0.0, 0.0
                elif len(s_tp) == 1:
                    hit_single = 1.0 if s_tp[0] == (right_tp_1idx - 1) else 0.0
                    h_m1, h_m1a = hit_single, hit_single
                else:
                    if k_tp > 0 and (k_tp - 1) in s_tp:
                        hit_pick = 1.0 if (k_tp - 1) == (right_tp_1idx - 1) else 0.0
                        h_m1, h_m1a = hit_pick, hit_pick
                    elif k_tp == 0:
                        h_m1 = (1.0 / len(s_tp)) if (right_tp_1idx - 1) in s_tp else 0.0
                        h_m1a = 0.0
                    else:
                        h_m1 = (1.0 / len(s_tp)) if (right_tp_1idx - 1) in s_tp else 0.0
                        h_m1a = h_m1

                arm_ta["M1_pick_tiebreak"].append(fa_m1)
                arm_tp_aligned["M1_pick_tiebreak"].append(h_m1)
                arm_tp_strict["M1_pick_tiebreak"].append(h_m1)
                arm_pairs["M1_pick_tiebreak"][pid] = (h_m1, fa_m1)

                arm_ta["M1_pick_or_abstain"].append(fa_m1a)
                arm_tp_aligned["M1_pick_or_abstain"].append(h_m1a)
                arm_tp_strict["M1_pick_or_abstain"].append(h_m1a)
                arm_pairs["M1_pick_or_abstain"][pid] = (h_m1a, fa_m1a)

    ta_out = {
        a: bootstrap_mean(arm_ta[a], seed + 10 + i, n_boot)
        for i, a in enumerate(arms)
    }
    tp_out = {
        a: bootstrap_mean(arm_tp_aligned[a], seed + 30 + i, n_boot)
        for i, a in enumerate(arms)
    }
    tp_strict_out = {
        a: bootstrap_mean(arm_tp_strict[a], seed + 50 + i, n_boot)
        for i, a in enumerate(arms)
    }

    ordered_pids = [it["pid"] for it in items]
    sdt_out = {}
    for i, a in enumerate(arms):
        pids_a = [pid for pid in ordered_pids if pid in arm_pairs[a]]
        hits_a = [arm_pairs[a][pid][0] for pid in pids_a]
        fas_a = [arm_pairs[a][pid][1] for pid in pids_a]
        sdt_out[a] = bootstrap_sdt(hits_a, fas_a, seed + 70 + i, n_boot)

    contrast_pairs = [("PICK", "ISO"), ("EACH", "ISO"), ("PICK", "EACH")]
    if include_m1:
        contrast_pairs.extend(
            [("M1_pick_tiebreak", "PICK"), ("M1_pick_or_abstain", "PICK"), ("M1_unif", "PICK")]
        )
    diffs_out = {}
    for i, (a_arm, b_arm) in enumerate(contrast_pairs):
        shared = [pid for pid in ordered_pids if pid in arm_pairs[a_arm] and pid in arm_pairs[b_arm]]
        pa = [arm_pairs[a_arm][pid] for pid in shared]
        pb = [arm_pairs[b_arm][pid] for pid in shared]
        diffs_out[f"{a_arm}_minus_{b_arm}"] = bootstrap_sdt_diff(pa, pb, seed + 90 + i, n_boot)

    return {
        "n_items": len(items),
        "ta_false_choice": ta_out,
        "tp_hit_aligned": tp_out,
        "tp_hit_strict": tp_strict_out,
        "right_given_pick": bootstrap_mean(right_given_pick_vals, seed + 110, n_boot),
        "right_given_each": bootstrap_mean(right_given_each_vals, seed + 111, n_boot),
        "right_given_iso": bootstrap_mean(right_given_iso_vals, seed + 112, n_boot),
        "sdt": sdt_out,
        "sdt_diffs": diffs_out,
    }


def analyze_c9_science(
    root: Path,
    n_boot: int,
    base_seed: int,
) -> Dict[str, Any]:
    bank = json.loads((root / "banks/locked_v2/c9_science_pools.json").read_text(encoding="utf-8"))
    rb_pools = bank["researchbench_pools"]
    by_item: Dict[str, Dict[str, Any]] = {}
    unique_cands: Dict[str, str] = {}
    for p in rb_pools:
        iid = p["item"]
        by_item.setdefault(iid, {"pid": iid})[p["kind"].lower()] = p
        for c in p["cands"]:
            unique_cands[c["cid"]] = c["role"]
    items = [by_item[iid] for iid in sorted(by_item.keys())]

    models_out: Dict[str, Any] = {}
    for m_idx, model in enumerate(("gptoss", "gemini", "gemini_low", "hydrogen", "haiku")):
        arm_dirs = {
            "pick": (root / f"exps/c6_crossvendor/raw_science_{model}_pick", 60),
            "iso": (root / f"exps/c6_crossvendor/raw_science_{model}_iso", 130),
            "each": (root / f"exps/c6_crossvendor/raw_science_{model}_each", 60),
        }
        loaded = {arm: load_v2_raw_dir(d) for arm, (d, _) in arm_dirs.items()}
        statuses = {arm: _arm_completeness(loaded[arm], exp_n) for arm, (_, exp_n) in arm_dirs.items()}

        parsed_counts = {}
        ok_counts = {}
        # Parse rates
        p_ok = loaded["pick"]["n_ok"]
        p_par = sum(
            1
            for r in loaded["pick"]["records"].values()
            if parse_choice(r["text"], 4) is not None
        )
        i_ok = loaded["iso"]["n_ok"]
        i_par = sum(
            1
            for r in loaded["iso"]["records"].values()
            if parse_verdict(r["text"]) is not None
        )
        e_ok = loaded["each"]["n_ok"]
        e_par = sum(
            1
            for r in loaded["each"]["records"].values()
            if parse_each(r["text"], 4) is not None
        )
        ok_counts = {"pick": p_ok, "iso": i_ok, "each": e_ok, "total": p_ok + i_ok + e_ok}
        parsed_counts = {"pick": p_par, "iso": i_par, "each": e_par, "total": p_par + i_par + e_par}
        parse_rates = {
            k: (parsed_counts[k] / ok_counts[k]) if ok_counts[k] else None
            for k in ("pick", "iso", "each", "total")
        }

        # Calibration gate on unique 130 cids (30 right vs 100 wrong) + TA slot check
        iso_right_vals: List[float] = []
        iso_wrong_vals: List[float] = []
        for cid, role in sorted(unique_cands.items()):
            ir = loaded["iso"]["records"].get(f"ISO__{cid}")
            v = parse_verdict(ir["text"]) if ir else None
            if v is None:
                continue
            if role == "right":
                iso_right_vals.append(1.0 if v else 0.0)
            else:
                iso_wrong_vals.append(1.0 if v else 0.0)

        iso_r_rate = (sum(iso_right_vals) / len(iso_right_vals)) if iso_right_vals else None
        iso_w_rate = (sum(iso_wrong_vals) / len(iso_wrong_vals)) if iso_wrong_vals else None
        cal_diff = (iso_r_rate - iso_w_rate) if (iso_r_rate is not None and iso_w_rate is not None) else None
        cal_pass = bool(
            (parse_rates["iso"] is not None and parse_rates["iso"] >= 0.90)
            and (cal_diff is not None and cal_diff >= 0.10)
            and (iso_w_rate is not None and iso_w_rate > 0.0)
        )

        ev = _evaluate_pool_arms(
            items,
            loaded["pick"]["records"],
            loaded["each"]["records"],
            loaded["iso"]["records"],
            n_cands=4,
            n_boot=n_boot,
            seed=base_seed + 4000 + m_idx * 300,
            include_m1=True,
        )
        raw_exact = _science_raw_counts_and_exact_b(
            items,
            loaded["pick"]["records"],
            loaded["each"]["records"],
            loaded["iso"]["records"],
        )

        models_out[model] = {
            "arm_statuses": statuses,
            "n_ok": ok_counts,
            "n_parsed": parsed_counts,
            "parse_rates": parse_rates,
            "calibration": {
                "n_iso_right": len(iso_right_vals),
                "n_iso_wrong": len(iso_wrong_vals),
                "iso_right": iso_r_rate,
                "iso_wrong": iso_w_rate,
                "iso_right_minus_wrong": cal_diff,
                "gate_pass": cal_pass,
            },
            "metrics": ev,
            "raw_counts_and_exact_tests": raw_exact,
        }

    return {
        "n_items": len(items),
        "n_unique_cands": len(unique_cands),
        "models": models_out,
    }


def analyze_c6_math(
    root: Path,
    n_boot: int,
    base_seed: int,
) -> Dict[str, Any]:
    bank = json.loads((root / "banks/locked_v2/c6_crossvendor_math.json").read_text(encoding="utf-8"))
    pools = bank["pools"]
    by_pid: Dict[str, Dict[str, Any]] = {}
    unique_cands: Dict[str, str] = {}
    for p in pools:
        pid = p["pid"]
        entry = by_pid.setdefault(pid, {"pid": pid, "source": p["source"], "gold": p["gold"]})
        entry[p["kind"].lower()] = p
        for c in p["cands"]:
            unique_cands[c["cid"]] = c["role"]
    all_items = [by_pid[pid] for pid in sorted(by_pid.keys())]

    models_out: Dict[str, Any] = {}
    for m_idx, model in enumerate(("gptoss", "gemini")):
        arm_dirs = {
            "solve": (root / f"exps/c6_crossvendor/raw_math_{model}_solve", 200),
            "pick": (root / f"exps/c6_crossvendor/raw_math_{model}_pick", 200),
            "iso": (root / f"exps/c6_crossvendor/raw_math_{model}_iso", 400),
            "each": (root / f"exps/c6_crossvendor/raw_math_{model}_each", 200),
        }
        loaded = {arm: load_v2_raw_dir(d) for arm, (d, _) in arm_dirs.items()}
        statuses = {arm: _arm_completeness(loaded[arm], exp_n) for arm, (_, exp_n) in arm_dirs.items()}

        # Parse rates
        s_ok = loaded["solve"]["n_ok"]
        s_par = sum(
            1
            for r in loaded["solve"]["records"].values()
            if parse_answer(r["text"]) is not None
        )
        p_ok = loaded["pick"]["n_ok"]
        p_par = sum(
            1
            for r in loaded["pick"]["records"].values()
            if parse_choice(r["text"], 3) is not None
        )
        i_ok = loaded["iso"]["n_ok"]
        i_par = sum(
            1
            for r in loaded["iso"]["records"].values()
            if parse_verdict(r["text"]) is not None
        )
        e_ok = loaded["each"]["n_ok"]
        e_par = sum(
            1
            for r in loaded["each"]["records"].values()
            if parse_each(r["text"], 3) is not None
        )
        ok_counts = {"solve": s_ok, "pick": p_ok, "iso": i_ok, "each": e_ok, "total": s_ok + p_ok + i_ok + e_ok}
        parsed_counts = {"solve": s_par, "pick": p_par, "iso": i_par, "each": e_par, "total": s_par + p_par + i_par + e_par}
        parse_rates = {
            k: (parsed_counts[k] / ok_counts[k]) if ok_counts[k] else None
            for k in ("solve", "pick", "iso", "each", "total")
        }

        # Grade 2 SOLVE attempts against gold to stratify into SOLVED_M, UNSOLVED_M, MIXED_M
        strata_by_pid: Dict[str, str] = {}
        solve_details: Dict[str, Any] = {}
        n_unparsed_solve = 0
        for it in all_items:
            pid = it["pid"]
            gold = it["gold"]
            r0 = loaded["solve"]["records"].get(f"SOLVE__{pid}__0")
            r1 = loaded["solve"]["records"].get(f"SOLVE__{pid}__1")
            if r0 is None or r1 is None:
                continue
            g0 = grade_math_answer(r0["text"], gold)
            g1 = grade_math_answer(r1["text"], gold)
            if g0 is None:
                n_unparsed_solve += 1
            if g1 is None:
                n_unparsed_solve += 1
            score = int(bool(g0)) + int(bool(g1))
            if score == 2:
                st = "SOLVED_M"
            elif score == 1:
                st = "MIXED_M"
            else:
                st = "UNSOLVED_M"
            strata_by_pid[pid] = st
            solve_details[pid] = {"g0": g0, "g1": g1, "stratum": st, "source": it["source"]}

        stratum_counts: Dict[str, Dict[str, int]] = {}
        for st in ("ALL", "SOLVED_M", "UNSOLVED_M", "MIXED_M"):
            st_pids = [
                pid for pid, s in strata_by_pid.items() if st == "ALL" or s == st
            ] if st != "ALL" else [it["pid"] for it in all_items]
            stratum_counts[st] = {
                "all": len(st_pids),
                "contest": sum(1 for pid in st_pids if by_pid[pid]["source"] == "contest"),
                "arxivmath": sum(1 for pid in st_pids if by_pid[pid]["source"] == "arxivmath"),
            }

        # Calibration gate on unique 400 cids
        iso_right_vals: List[float] = []
        iso_wrong_vals: List[float] = []
        for cid, role in sorted(unique_cands.items()):
            ir = loaded["iso"]["records"].get(f"ISO__{cid}")
            v = parse_verdict(ir["text"]) if ir else None
            if v is None:
                continue
            if role == "right":
                iso_right_vals.append(1.0 if v else 0.0)
            else:
                iso_wrong_vals.append(1.0 if v else 0.0)
        iso_r_rate = (sum(iso_right_vals) / len(iso_right_vals)) if iso_right_vals else None
        iso_w_rate = (sum(iso_wrong_vals) / len(iso_wrong_vals)) if iso_wrong_vals else None
        cal_diff = (iso_r_rate - iso_w_rate) if (iso_r_rate is not None and iso_w_rate is not None) else None
        cal_pass = bool(
            (parse_rates["iso"] is not None and parse_rates["iso"] >= 0.90)
            and (cal_diff is not None and cal_diff >= 0.10)
            and (iso_w_rate is not None and iso_w_rate > 0.0)
            and stratum_counts["SOLVED_M"]["all"] >= 25
            and stratum_counts["UNSOLVED_M"]["all"] >= 25
        )

        # Evaluate per stratum and per source (all, contest, arxivmath)
        strata_metrics: Dict[str, Dict[str, Any]] = {}
        for st_idx, st in enumerate(("ALL", "SOLVED_M", "UNSOLVED_M", "MIXED_M")):
            strata_metrics[st] = {}
            for src_idx, src in enumerate(("all", "contest", "arxivmath")):
                sub_items = [
                    it
                    for it in all_items
                    if (st == "ALL" or strata_by_pid.get(it["pid"]) == st)
                    and (src == "all" or it["source"] == src)
                ]
                if not sub_items:
                    strata_metrics[st][src] = {"n_items": 0}
                    continue
                strata_metrics[st][src] = _evaluate_pool_arms(
                    sub_items,
                    loaded["pick"]["records"],
                    loaded["each"]["records"],
                    loaded["iso"]["records"],
                    n_cands=3,
                    n_boot=n_boot,
                    seed=base_seed + 5000 + m_idx * 1000 + st_idx * 200 + src_idx * 50,
                    include_m1=False,
                )

        # H3 Out-of-Sample SDT Prediction:
        # Fit delta_c on SOLVED_M ONLY, predict UNSOLVED_M PICK FA via:
        # `F_pred = 1 - Phi(d'_ISO_unsolved / 2 + c_ISO_unsolved + delta_c_solved)`
        solved_all = strata_metrics.get("SOLVED_M", {}).get("all", {})
        unsolved_all = strata_metrics.get("UNSOLVED_M", {}).get("all", {})
        h3_out: Dict[str, Any] = {"status": "insufficient_data"}
        if (
            solved_all.get("n_items", 0) > 0
            and unsolved_all.get("n_items", 0) > 0
            and solved_all.get("sdt_diffs", {}).get("PICK_minus_ISO")
            and unsolved_all.get("sdt", {}).get("ISO")
            and unsolved_all.get("sdt", {}).get("PICK")
            and unsolved_all.get("ta_false_choice", {}).get("PICK")
        ):
            delta_c_solved = solved_all["sdt_diffs"]["PICK_minus_ISO"]["c_diff"]
            iso_uns = unsolved_all["sdt"]["ISO"]
            pick_uns_sdt = unsolved_all["sdt"]["PICK"]
            pick_uns_ta = unsolved_all["ta_false_choice"]["PICK"]
            dp_iso_uns = iso_uns["d_prime"]
            c_iso_uns = iso_uns["c"]
            z_arg = 0.5 * dp_iso_uns + c_iso_uns + delta_c_solved
            f_pred = 1.0 - norm_cdf(z_arg)

            obs_mean = pick_uns_ta["mean"]
            obs_ci95 = pick_uns_ta["ci95"]
            obs_adj_ci95 = pick_uns_sdt.get("F_raw_ci95")
            in_ci = (obs_ci95[0] <= f_pred <= obs_ci95[1]) if obs_ci95 else None
            in_adj_ci = (obs_adj_ci95[0] <= f_pred <= obs_adj_ci95[1]) if obs_adj_ci95 else None

            h3_out = {
                "status": "ok",
                "n_solved": solved_all["sdt_diffs"]["PICK_minus_ISO"]["n"],
                "n_unsolved": pick_uns_ta["n"],
                "delta_c_solved": delta_c_solved,
                "d_prime_iso_unsolved": dp_iso_uns,
                "c_iso_unsolved": c_iso_uns,
                "c_pred_unsolved": c_iso_uns + delta_c_solved,
                "F_pred": f_pred,
                "F_obs_unsolved_pick": obs_mean,
                "F_obs_unsolved_pick_ci95": obs_ci95,
                "F_obs_hautus": pick_uns_sdt["F_adj"],
                "in_ci95": in_ci,
                "in_paired_ci95": in_adj_ci,
                "abs_err": abs(f_pred - obs_mean) if obs_mean is not None else None,
            }

        models_out[model] = {
            "arm_statuses": statuses,
            "n_ok": ok_counts,
            "n_parsed": parsed_counts,
            "parse_rates": parse_rates,
            "n_unparsed_solve_attempts": n_unparsed_solve,
            "stratum_counts": stratum_counts,
            "calibration": {
                "n_iso_right": len(iso_right_vals),
                "n_iso_wrong": len(iso_wrong_vals),
                "iso_right": iso_r_rate,
                "iso_wrong": iso_w_rate,
                "iso_right_minus_wrong": cal_diff,
                "gate_pass": cal_pass,
            },
            "strata": strata_metrics,
            "h3_out_of_sample_prediction": h3_out,
        }

    return {
        "n_problems": len(all_items),
        "n_unique_cands": len(unique_cands),
        "models": models_out,
    }


def _load_c3_pick_iso_recs(
    c3_root: Path,
    pools: Sequence[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load C3 Haiku PICK and ISO records into v2-compatible dicts keyed by PICK__/ISO__."""
    pick_recs: Dict[str, Any] = {}
    iso_recs: Dict[str, Any] = {}
    for p in pools:
        pname = p["pool"]
        rec_p = load_c3_record(c3_root, f"haiku__PICK__{pname}")
        if rec_p is not None:
            pick_recs[f"PICK__{pname}"] = {"text": rec_p["result"]}
        for c in p["cands"]:
            cid = c["cid"]
            key = f"ISO__{cid}"
            if key not in iso_recs:
                rec_i = load_c3_record(c3_root, f"haiku__ISO__{cid}")
                if rec_i is not None:
                    iso_recs[key] = {"text": rec_i["result"]}
    return pick_recs, iso_recs


def _summarize_paired_arms(
    ordered_pids: Sequence[str],
    arm_pairs: Dict[str, Dict[str, Tuple[float, float]]],
    contrast_pairs: Sequence[Tuple[str, str]],
    n_boot: int,
    seed: int,
) -> Dict[str, Any]:
    """Summarize TA FA, TP hit, Hautus SDT, and paired SDT diffs over arm_pairs."""
    arms = list(arm_pairs.keys())
    ta_out: Dict[str, Any] = {}
    tp_out: Dict[str, Any] = {}
    sdt_out: Dict[str, Any] = {}
    for i, a in enumerate(arms):
        pids_a = [pid for pid in ordered_pids if pid in arm_pairs[a]]
        hits_a = [arm_pairs[a][pid][0] for pid in pids_a]
        fas_a = [arm_pairs[a][pid][1] for pid in pids_a]
        ta_out[a] = bootstrap_mean(fas_a, seed + 10 + i, n_boot)
        tp_out[a] = bootstrap_mean(hits_a, seed + 30 + i, n_boot)
        sdt_out[a] = bootstrap_sdt(hits_a, fas_a, seed + 50 + i, n_boot)

    diffs_out: Dict[str, Any] = {}
    for i, (a_arm, b_arm) in enumerate(contrast_pairs):
        shared = [pid for pid in ordered_pids if pid in arm_pairs[a_arm] and pid in arm_pairs[b_arm]]
        pa = [arm_pairs[a_arm][pid] for pid in shared]
        pb = [arm_pairs[b_arm][pid] for pid in shared]
        diffs_out[f"{a_arm}_minus_{b_arm}"] = bootstrap_sdt_diff(pa, pb, seed + 90 + i, n_boot)

    return {
        "ta_false_choice": ta_out,
        "tp_hit_aligned": tp_out,
        "sdt": sdt_out,
        "sdt_diffs": diffs_out,
    }


def _evaluate_c7_m2(
    items: Sequence[Dict[str, Any]],
    m2_loaded: Dict[str, Any],
    pick_recs: Dict[str, Any],
    iso_recs: Dict[str, Any],
    n_cands: int,
    conf_threshold: int,
    n_boot: int,
    seed: int,
) -> Dict[str, Any]:
    """Evaluate C7 Arm M2 (raw choice and confidence>=tau gate) vs matched PICK and ISO."""
    n_expected = len(items) * 2
    status = _arm_completeness(m2_loaded, n_expected)

    n_parsed_choice = 0
    n_parsed_conf = 0
    n_parsed_both = 0
    conf_hist_ta: Dict[str, int] = {str(k): 0 for k in range(1, 6)}
    conf_hist_tp: Dict[str, int] = {str(k): 0 for k in range(1, 6)}

    for it in items:
        for kind_key in ("ta", "tp"):
            pool_obj = it[kind_key]
            rec = m2_loaded["records"].get(f"M2__{pool_obj['pool']}")
            if rec is None:
                continue
            ch = parse_choice(rec["text"], n_cands)
            cf = parse_confidence(rec["text"])
            if ch is not None:
                n_parsed_choice += 1
            if cf is not None:
                n_parsed_conf += 1
                hist = conf_hist_ta if kind_key == "ta" else conf_hist_tp
                hist[str(cf)] += 1
            if ch is not None and cf is not None:
                n_parsed_both += 1

    arm_pairs: Dict[str, Dict[str, Tuple[float, float]]] = {
        "M2_raw": {},
        "M2_gate4": {},
        "PICK": {},
        "ISO": {},
    }

    for it in items:
        pid = it["pid"]
        ta_pool = it["ta"]
        tp_pool = it["tp"]
        right_tp_1idx = next(i + 1 for i, c in enumerate(tp_pool["cands"]) if c["role"] == "right")

        r_ta = m2_loaded["records"].get(f"M2__{ta_pool['pool']}")
        r_tp = m2_loaded["records"].get(f"M2__{tp_pool['pool']}")
        ch_ta = parse_choice(r_ta["text"], n_cands) if r_ta else None
        ch_tp = parse_choice(r_tp["text"], n_cands) if r_tp else None
        cf_ta = parse_confidence(r_ta["text"]) if r_ta else None
        cf_tp = parse_confidence(r_tp["text"]) if r_tp else None

        if ch_ta is not None and ch_tp is not None:
            arm_pairs["M2_raw"][pid] = (
                1.0 if ch_tp == right_tp_1idx else 0.0,
                1.0 if ch_ta > 0 else 0.0,
            )
            if cf_ta is not None and cf_tp is not None:
                g_ta = ch_ta if cf_ta >= conf_threshold else 0
                g_tp = ch_tp if cf_tp >= conf_threshold else 0
                arm_pairs["M2_gate4"][pid] = (
                    1.0 if g_tp == right_tp_1idx else 0.0,
                    1.0 if g_ta > 0 else 0.0,
                )

        # Baselines restricted to items where M2_raw is parsed, when available
        if pid in arm_pairs["M2_raw"]:
            pr_ta = pick_recs.get(f"PICK__{ta_pool['pool']}")
            pr_tp = pick_recs.get(f"PICK__{tp_pool['pool']}")
            kp_ta = parse_choice(pr_ta["text"], n_cands) if pr_ta else None
            kp_tp = parse_choice(pr_tp["text"], n_cands) if pr_tp else None
            if kp_ta is not None and kp_tp is not None:
                arm_pairs["PICK"][pid] = (
                    1.0 if kp_tp == right_tp_1idx else 0.0,
                    1.0 if kp_ta > 0 else 0.0,
                )

            iv_ta: List[bool] = []
            for c in ta_pool["cands"]:
                ir = iso_recs.get(f"ISO__{c['cid']}")
                v = parse_verdict(ir["text"]) if ir else None
                if v is None:
                    iv_ta = []
                    break
                iv_ta.append(v)
            iv_tp: List[bool] = []
            for c in tp_pool["cands"]:
                ir = iso_recs.get(f"ISO__{c['cid']}")
                v = parse_verdict(ir["text"]) if ir else None
                if v is None:
                    iv_tp = []
                    break
                iv_tp.append(v)
            if iv_ta and iv_tp:
                a_i = sum(1 for v in iv_tp if v)
                h_ia = (1.0 / a_i) if (a_i > 0 and iv_tp[right_tp_1idx - 1]) else 0.0
                arm_pairs["ISO"][pid] = (h_ia, 1.0 if any(iv_ta) else 0.0)

    ordered_pids = [it["pid"] for it in items]
    summary = _summarize_paired_arms(
        ordered_pids,
        arm_pairs,
        [
            ("M2_raw", "PICK"),
            ("M2_raw", "ISO"),
            ("M2_gate4", "PICK"),
            ("M2_gate4", "ISO"),
            ("M2_gate4", "M2_raw"),
            ("PICK", "ISO"),
        ],
        n_boot=n_boot,
        seed=seed,
    )

    # Criterion recovery fraction toward ISO: `(c(M2) - c(PICK)) / (c(ISO) - c(PICK))`
    recovery: Dict[str, Optional[float]] = {"M2_raw": None, "M2_gate4": None}
    sdt_pick = summary["sdt"].get("PICK")
    sdt_iso = summary["sdt"].get("ISO")
    if sdt_pick and sdt_iso and sdt_pick["n"] == sdt_iso["n"] and sdt_pick["n"] > 0:
        denom = sdt_iso["c"] - sdt_pick["c"]
        if abs(denom) > 1e-12:
            for mkey in ("M2_raw", "M2_gate4"):
                sdt_m = summary["sdt"].get(mkey)
                if sdt_m and sdt_m["n"] == sdt_pick["n"]:
                    recovery[mkey] = (sdt_m["c"] - sdt_pick["c"]) / denom

    n_ok = m2_loaded["n_ok"]
    return {
        "status": status,
        "n_expected_calls": n_expected,
        "n_files": m2_loaded["n_files"],
        "n_ok": n_ok,
        "n_parsed_choice": n_parsed_choice,
        "n_parsed_conf": n_parsed_conf,
        "n_parsed_both": n_parsed_both,
        "parse_rate_choice": (n_parsed_choice / n_ok) if n_ok else None,
        "parse_rate_conf": (n_parsed_conf / n_ok) if n_ok else None,
        "n_paired_m2_raw": len(arm_pairs["M2_raw"]),
        "n_paired_m2_gate4": len(arm_pairs["M2_gate4"]),
        "n_matched_pick": len(arm_pairs["PICK"]),
        "n_matched_iso": len(arm_pairs["ISO"]),
        "confidence_hist": {"ta": conf_hist_ta, "tp": conf_hist_tp},
        "criterion_recovery_frac": recovery,
        **summary,
    }


def _analyze_c7_math_haiku_m1(
    root: Path,
    c3_root: Path,
    c4_items_by_pid: Dict[str, Dict[str, Any]],
    haiku_pids: Sequence[str],
    pick_recs: Dict[str, Any],
    iso_recs: Dict[str, Any],
    n_boot: int,
    seed: int,
) -> Dict[str, Any]:
    """Analyze actual Two-Stage M1 (ISO -> PICK tiebreak) on Haiku C3 UNSOLVED N=40."""
    plan_path = root / "exps/c7_mitigation/m1_stage1_math_haiku_c3.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    tb_loaded = load_v2_raw_dir(root / "exps/c7_mitigation/raw_math_haiku_m1_tiebreak")
    n_tb_expected = int(plan.get("tiebreak_jobs", 0))
    status = _arm_completeness(tb_loaded, n_tb_expected) if n_tb_expected > 0 else "complete"

    plan_by_pool = {rec["pool"]: rec for rec in plan["pools"]}
    n_tb_parsed = 0
    tb_none_count = 0
    for rec in plan["pools"]:
        if rec["status"] != "needs_tiebreak":
            continue
        tb_raw = tb_loaded["records"].get(rec["tiebreak_job_id"])
        if tb_raw is None:
            continue
        ch = parse_choice(tb_raw["text"], int(rec["n_accepted"]))
        if ch is not None:
            n_tb_parsed += 1
            if ch == 0:
                tb_none_count += 1

    def _resolve_m1_choice(pool_name: str) -> Optional[int]:
        prec = plan_by_pool.get(pool_name)
        if prec is None:
            return None
        if prec["status"] == "resolved_deterministic":
            return int(prec["deterministic_choice_1idx"])
        if prec["status"] == "needs_tiebreak":
            tb_raw = tb_loaded["records"].get(prec["tiebreak_job_id"])
            if tb_raw is None:
                return None
            ch = parse_choice(tb_raw["text"], int(prec["n_accepted"]))
            if ch is None:
                return None
            if ch == 0:
                return 0
            return int(prec["accepted_orig_positions_1idx"][ch - 1])
        return None

    arm_pairs: Dict[str, Dict[str, Tuple[float, float]]] = {
        "M1": {},
        "PICK": {},
        "ISO": {},
    }
    for pid in haiku_pids:
        it = c4_items_by_pid[pid]
        ta_pool = it["ta"]
        tp_pool = it["tp"]
        right_tp_1idx = next(i + 1 for i, c in enumerate(tp_pool["cands"]) if c["role"] == "right")

        m1_ta = _resolve_m1_choice(ta_pool["pool"])
        m1_tp = _resolve_m1_choice(tp_pool["pool"])
        if m1_ta is not None and m1_tp is not None:
            arm_pairs["M1"][pid] = (
                1.0 if m1_tp == right_tp_1idx else 0.0,
                1.0 if m1_ta > 0 else 0.0,
            )

        pr_ta = pick_recs.get(f"PICK__{ta_pool['pool']}")
        pr_tp = pick_recs.get(f"PICK__{tp_pool['pool']}")
        kp_ta = parse_choice(pr_ta["text"], 3) if pr_ta else None
        kp_tp = parse_choice(pr_tp["text"], 3) if pr_tp else None
        if kp_ta is not None and kp_tp is not None:
            arm_pairs["PICK"][pid] = (
                1.0 if kp_tp == right_tp_1idx else 0.0,
                1.0 if kp_ta > 0 else 0.0,
            )

        iv_ta: List[bool] = []
        for c in ta_pool["cands"]:
            ir = iso_recs.get(f"ISO__{c['cid']}")
            v = parse_verdict(ir["text"]) if ir else None
            if v is None:
                iv_ta = []
                break
            iv_ta.append(v)
        iv_tp: List[bool] = []
        for c in tp_pool["cands"]:
            ir = iso_recs.get(f"ISO__{c['cid']}")
            v = parse_verdict(ir["text"]) if ir else None
            if v is None:
                iv_tp = []
                break
            iv_tp.append(v)
        if iv_ta and iv_tp:
            a_i = sum(1 for v in iv_tp if v)
            h_ia = (1.0 / a_i) if (a_i > 0 and iv_tp[right_tp_1idx - 1]) else 0.0
            arm_pairs["ISO"][pid] = (h_ia, 1.0 if any(iv_ta) else 0.0)

    summary = _summarize_paired_arms(
        haiku_pids,
        arm_pairs,
        [("M1", "PICK"), ("M1", "ISO"), ("PICK", "ISO")],
        n_boot=n_boot,
        seed=seed,
    )
    recovery: Optional[float] = None
    sdt_m1 = summary["sdt"].get("M1")
    sdt_p = summary["sdt"].get("PICK")
    sdt_i = summary["sdt"].get("ISO")
    if sdt_m1 and sdt_p and sdt_i and sdt_m1["n"] == sdt_p["n"] == sdt_i["n"] and sdt_p["n"] > 0:
        denom = sdt_i["c"] - sdt_p["c"]
        if abs(denom) > 1e-12:
            recovery = (sdt_m1["c"] - sdt_p["c"]) / denom

    return {
        "status": status,
        "n_problems": len(haiku_pids),
        "stage1_counts": plan.get("counts", {}),
        "n_tiebreak_expected": n_tb_expected,
        "n_tiebreak_files": tb_loaded["n_files"],
        "n_tiebreak_ok": tb_loaded["n_ok"],
        "n_tiebreak_parsed": n_tb_parsed,
        "tiebreak_parse_rate": (n_tb_parsed / tb_loaded["n_ok"]) if tb_loaded["n_ok"] else None,
        "tiebreak_none_count": tb_none_count,
        "extra_calls_per_pool": n_tb_expected / len(plan["pools"]) if plan.get("pools") else None,
        "n_paired_m1": len(arm_pairs["M1"]),
        "criterion_recovery_frac": recovery,
        **summary,
    }


def _analyze_c7_math_haiku_m3_foil(
    root: Path,
    c4_items_by_pid: Dict[str, Dict[str, Any]],
    pick_recs: Dict[str, Any],
    iso_recs: Dict[str, Any],
    n_boot: int,
    seed: int,
) -> Dict[str, Any]:
    """Analyze M3 Known-Foil 4-candidate lineup on Haiku C3 UNSOLVED N=40."""
    jobs_path = root / "exps/c7_mitigation/jobs_math_haiku_m3_foil.jsonl"
    jobs = [json.loads(ln) for ln in jobs_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    loaded = load_v2_raw_dir(root / "exps/c7_mitigation/raw_math_haiku_m3_foil")
    status = _arm_completeness(loaded, len(jobs))

    by_pid: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for j in jobs:
        by_pid.setdefault(j["pid"], {})[j["kind"].lower()] = j
    ordered_pids = sorted(by_pid.keys())

    n_parsed = 0
    foil_ta_vals: List[float] = []
    foil_tp_vals: List[float] = []
    foil_all_vals: List[float] = []
    real_wrong_ta_vals: List[float] = []
    any_false_ta_vals: List[float] = []
    hit_tp_vals: List[float] = []

    arm_pairs: Dict[str, Dict[str, Tuple[float, float]]] = {
        "M3_any_fa": {},
        "M3_real_wrong_fa": {},
        "PICK": {},
        "ISO": {},
    }

    for pid in ordered_pids:
        j_ta = by_pid[pid]["ta"]
        j_tp = by_pid[pid]["tp"]
        r_ta = loaded["records"].get(j_ta["id"])
        r_tp = loaded["records"].get(j_tp["id"])
        ch_ta = parse_choice(r_ta["text"], 4) if r_ta else None
        ch_tp = parse_choice(r_tp["text"], 4) if r_tp else None
        if ch_ta is not None:
            n_parsed += 1
            f_ta = 1.0 if ch_ta == int(j_ta["foil_pos"]) else 0.0
            rw_ta = 1.0 if (ch_ta > 0 and ch_ta != int(j_ta["foil_pos"])) else 0.0
            any_ta = 1.0 if ch_ta > 0 else 0.0
            foil_ta_vals.append(f_ta)
            foil_all_vals.append(f_ta)
            real_wrong_ta_vals.append(rw_ta)
            any_false_ta_vals.append(any_ta)
        if ch_tp is not None:
            n_parsed += 1
            f_tp = 1.0 if ch_tp == int(j_tp["foil_pos"]) else 0.0
            h_tp = 1.0 if ch_tp == int(j_tp["right_pos_1idx"]) else 0.0
            foil_tp_vals.append(f_tp)
            foil_all_vals.append(f_tp)
            hit_tp_vals.append(h_tp)

        if ch_ta is not None and ch_tp is not None:
            h_tp = 1.0 if ch_tp == int(j_tp["right_pos_1idx"]) else 0.0
            rw_ta = 1.0 if (ch_ta > 0 and ch_ta != int(j_ta["foil_pos"])) else 0.0
            any_ta = 1.0 if ch_ta > 0 else 0.0
            arm_pairs["M3_any_fa"][pid] = (h_tp, any_ta)
            arm_pairs["M3_real_wrong_fa"][pid] = (h_tp, rw_ta)

            it = c4_items_by_pid[pid]
            ta_pool = it["ta"]
            tp_pool = it["tp"]
            right_c3 = next(i + 1 for i, c in enumerate(tp_pool["cands"]) if c["role"] == "right")

            pr_ta = pick_recs.get(f"PICK__{ta_pool['pool']}")
            pr_tp = pick_recs.get(f"PICK__{tp_pool['pool']}")
            kp_ta = parse_choice(pr_ta["text"], 3) if pr_ta else None
            kp_tp = parse_choice(pr_tp["text"], 3) if pr_tp else None
            if kp_ta is not None and kp_tp is not None:
                arm_pairs["PICK"][pid] = (
                    1.0 if kp_tp == right_c3 else 0.0,
                    1.0 if kp_ta > 0 else 0.0,
                )

            iv_ta: List[bool] = []
            for c in ta_pool["cands"]:
                ir = iso_recs.get(f"ISO__{c['cid']}")
                v = parse_verdict(ir["text"]) if ir else None
                if v is None:
                    iv_ta = []
                    break
                iv_ta.append(v)
            iv_tp: List[bool] = []
            for c in tp_pool["cands"]:
                ir = iso_recs.get(f"ISO__{c['cid']}")
                v = parse_verdict(ir["text"]) if ir else None
                if v is None:
                    iv_tp = []
                    break
                iv_tp.append(v)
            if iv_ta and iv_tp:
                a_i = sum(1 for v in iv_tp if v)
                h_ia = (1.0 / a_i) if (a_i > 0 and iv_tp[right_c3 - 1]) else 0.0
                arm_pairs["ISO"][pid] = (h_ia, 1.0 if any(iv_ta) else 0.0)

    summary = _summarize_paired_arms(
        ordered_pids,
        arm_pairs,
        [
            ("M3_any_fa", "PICK"),
            ("M3_any_fa", "ISO"),
            ("M3_real_wrong_fa", "PICK"),
            ("M3_real_wrong_fa", "ISO"),
        ],
        n_boot=n_boot,
        seed=seed + 50,
    )

    return {
        "status": status,
        "n_expected_calls": len(jobs),
        "n_files": loaded["n_files"],
        "n_ok": loaded["n_ok"],
        "n_parsed": n_parsed,
        "parse_rate": (n_parsed / loaded["n_ok"]) if loaded["n_ok"] else None,
        "n_paired_m3": len(arm_pairs["M3_any_fa"]),
        "foil_pick_rate_ta": bootstrap_mean(foil_ta_vals, seed + 1, n_boot),
        "foil_pick_rate_tp": bootstrap_mean(foil_tp_vals, seed + 2, n_boot),
        "foil_pick_rate_all": bootstrap_mean(foil_all_vals, seed + 3, n_boot),
        "real_wrong_pick_rate_ta": bootstrap_mean(real_wrong_ta_vals, seed + 4, n_boot),
        "any_false_choice_rate_ta": bootstrap_mean(any_false_ta_vals, seed + 5, n_boot),
        "tp_hit_rate": bootstrap_mean(hit_tp_vals, seed + 6, n_boot),
        **summary,
    }


def analyze_c7_mitigation(
    root: Path,
    c3_root: Path,
    n_boot: int,
    base_seed: int,
) -> Dict[str, Any]:
    """Analyze Round 2 C7 Mitigation Matrix (Science M2, Math M2, Haiku M1 & M3)."""
    c7_dir = root / "exps/c7_mitigation"

    # 1. Science M2 (all 5 judge configs on ResearchBench N=30 paired items)
    sci_bank = json.loads((root / "banks/locked_v2/c9_science_pools.json").read_text(encoding="utf-8"))
    sci_by_item: Dict[str, Dict[str, Any]] = {}
    for p in sci_bank["researchbench_pools"]:
        iid = p["item"]
        sci_by_item.setdefault(iid, {"pid": iid})[p["kind"].lower()] = p
    sci_items = [sci_by_item[iid] for iid in sorted(sci_by_item.keys())]

    science_m2: Dict[str, Any] = {}
    for m_idx, model in enumerate(("gptoss", "gemini", "gemini_low", "hydrogen", "haiku")):
        m2_loaded = load_v2_raw_dir(c7_dir / f"raw_science_{model}_m2")
        pick_loaded = load_v2_raw_dir(root / f"exps/c6_crossvendor/raw_science_{model}_pick")
        iso_loaded = load_v2_raw_dir(root / f"exps/c6_crossvendor/raw_science_{model}_iso")
        science_m2[model] = _evaluate_c7_m2(
            sci_items,
            m2_loaded,
            pick_loaded["records"],
            iso_loaded["records"],
            n_cands=4,
            conf_threshold=4,
            n_boot=n_boot,
            seed=base_seed + 9000 + m_idx * 200,
        )

    # 2. Math M2: cross-vendor (gptoss, gemini) and Haiku C3 UNSOLVED N=40
    c6_bank = json.loads((root / "banks/locked_v2/c6_crossvendor_math.json").read_text(encoding="utf-8"))
    c6_by_pid: Dict[str, Dict[str, Any]] = {}
    for p in c6_bank["pools"]:
        c6_by_pid.setdefault(p["pid"], {"pid": p["pid"]})[p["kind"].lower()] = p
    cross_jobs = [
        json.loads(ln)
        for ln in (c7_dir / "jobs_math_cross_m2.jsonl").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    cross_pids = sorted({j["pid"] for j in cross_jobs})
    cross_items = [c6_by_pid[pid] for pid in cross_pids]

    math_m2: Dict[str, Any] = {}
    for m_idx, model in enumerate(("gptoss", "gemini")):
        m2_loaded = load_v2_raw_dir(c7_dir / f"raw_math_{model}_m2")
        pick_loaded = load_v2_raw_dir(root / f"exps/c6_crossvendor/raw_math_{model}_pick")
        iso_loaded = load_v2_raw_dir(root / f"exps/c6_crossvendor/raw_math_{model}_iso")
        math_m2[model] = _evaluate_c7_m2(
            cross_items,
            m2_loaded,
            pick_loaded["records"],
            iso_loaded["records"],
            n_cands=3,
            conf_threshold=4,
            n_boot=n_boot,
            seed=base_seed + 10000 + m_idx * 200,
        )

    c4_bank = json.loads((root / "banks/locked_v2/c4_haiku_compute.json").read_text(encoding="utf-8"))
    c4_by_pid: Dict[str, Dict[str, Any]] = {}
    for p in c4_bank["pools"]:
        c4_by_pid.setdefault(p["pid"], {"pid": p["pid"]})[p["kind"].lower()] = p
    haiku_jobs = [
        json.loads(ln)
        for ln in (c7_dir / "jobs_math_haiku_m2.jsonl").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    haiku_pids = sorted({j["pid"] for j in haiku_jobs})
    haiku_items = [c4_by_pid[pid] for pid in haiku_pids]
    haiku_pools = [p for it in haiku_items for p in (it["ta"], it["tp"])]
    c3_pick_recs, c3_iso_recs = _load_c3_pick_iso_recs(c3_root, haiku_pools)

    math_m2["haiku"] = _evaluate_c7_m2(
        haiku_items,
        load_v2_raw_dir(c7_dir / "raw_math_haiku_m2"),
        c3_pick_recs,
        c3_iso_recs,
        n_cands=3,
        conf_threshold=4,
        n_boot=n_boot,
        seed=base_seed + 10400,
    )

    # 3. Haiku Math M1 (actual Two-Stage ISO -> PICK) and M3 (Known-Foil 4-candidate)
    math_haiku_m1 = _analyze_c7_math_haiku_m1(
        root,
        c3_root,
        c4_by_pid,
        haiku_pids,
        c3_pick_recs,
        c3_iso_recs,
        n_boot=n_boot,
        seed=base_seed + 11000,
    )
    math_haiku_m3_foil = _analyze_c7_math_haiku_m3_foil(
        root,
        c4_by_pid,
        c3_pick_recs,
        c3_iso_recs,
        n_boot=n_boot,
        seed=base_seed + 11500,
    )

    return {
        "science_m2": science_m2,
        "math_m2": math_m2,
        "math_haiku_m1": math_haiku_m1,
        "math_haiku_m3_foil": math_haiku_m3_foil,
    }


def _clopper_pearson_ci95_b(k: int, n: int) -> List[float]:
    if n <= 0:
        return [0.0, 1.0]
    lo = 0.0
    if k > 0:
        l_lo, l_hi = 0.0, 1.0
        for _ in range(64):
            mid = 0.5 * (l_lo + l_hi)
            prob = sum(math.comb(n, j) * (mid ** j) * ((1.0 - mid) ** (n - j)) for j in range(k, n + 1))
            if prob < 0.025:
                l_lo = mid
            else:
                l_hi = mid
        lo = 0.5 * (l_lo + l_hi)
    hi = 1.0
    if k < n:
        u_lo, u_hi = 0.0, 1.0
        for _ in range(64):
            mid = 0.5 * (u_lo + u_hi)
            prob = sum(math.comb(n, j) * (mid ** j) * ((1.0 - mid) ** (n - j)) for j in range(0, k + 1))
            if prob < 0.025:
                u_hi = mid
            else:
                u_lo = mid
        hi = 0.5 * (u_lo + u_hi)
    return [lo, hi]


def _exact_mcnemar_b(n10: int, n01: int) -> float:
    m = n10 + n01
    if m <= 0:
        return 1.0
    k = min(n10, n01)
    return min(1.0, 2.0 * sum(math.comb(m, j) for j in range(k + 1)) / (2 ** m))


def _sdt_counts_b(tp_k: int, tp_n: int, ta_k: int, ta_n: int, mode: str) -> Dict[str, Any]:
    if tp_n <= 0 or ta_n <= 0:
        return {"h": None, "f": None, "d_prime": None, "c": None}
    if mode == "raw":
        h, f = tp_k / tp_n, ta_k / ta_n
        if h <= 0.0 or h >= 1.0 or f <= 0.0 or f >= 1.0:
            return {"h": h, "f": f, "d_prime": None, "c": None}
    elif mode == "hautus_05_n1":
        h, f = (tp_k + 0.5) / (tp_n + 1.0), (ta_k + 0.5) / (ta_n + 1.0)
    elif mode == "macmillan_05_n":
        h = (0.5 / tp_n) if tp_k == 0 else ((1.0 - 0.5 / tp_n) if tp_k == tp_n else tp_k / tp_n)
        f = (0.5 / ta_n) if ta_k == 0 else ((1.0 - 0.5 / ta_n) if ta_k == ta_n else ta_k / ta_n)
    elif mode == "quarter_025_n":
        h = (0.25 / tp_n) if tp_k == 0 else ((1.0 - 0.25 / tp_n) if tp_k == tp_n else tp_k / tp_n)
        f = (0.25 / ta_n) if ta_k == 0 else ((1.0 - 0.25 / ta_n) if ta_k == ta_n else ta_k / ta_n)
    else:
        raise ValueError(mode)
    zh, zf = norm_ppf(h), norm_ppf(f)
    return {"h": h, "f": f, "d_prime": zh - zf, "c": -0.5 * (zh + zf)}


def _science_raw_counts_and_exact_b(
    items: Sequence[Dict[str, Any]],
    pick_recs: Dict[str, Dict[str, Any]],
    each_recs: Dict[str, Dict[str, Any]],
    iso_recs: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    ta_bins: Dict[str, Dict[str, Optional[int]]] = {"PICK": {}, "ISO": {}, "EACH": {}}
    tpa_bins: Dict[str, Dict[str, Optional[int]]] = {"PICK": {}, "ISO": {}, "EACH": {}}
    tps_bins: Dict[str, Dict[str, Optional[int]]] = {"PICK": {}, "ISO": {}, "EACH": {}}

    for it in items:
        pid = it["pid"]
        p_ta, p_tp = it["ta"], it["tp"]
        rpos = next((i + 1 for i, c in enumerate(p_tp["cands"]) if c["role"] == "right"), None)

        pr_ta = pick_recs.get(f"PICK__{p_ta['pool']}")
        pr_tp = pick_recs.get(f"PICK__{p_tp['pool']}")
        pc_ta = parse_choice(pr_ta["text"], 4) if pr_ta else None
        pc_tp = parse_choice(pr_tp["text"], 4) if pr_tp else None
        ta_bins["PICK"][pid] = (1 if pc_ta > 0 else 0) if pc_ta is not None else None
        tpa_bins["PICK"][pid] = (1 if pc_tp == rpos else 0) if (pc_tp is not None and rpos is not None) else None
        tps_bins["PICK"][pid] = tpa_bins["PICK"][pid]

        er_ta = each_recs.get(f"EACH__{p_ta['pool']}")
        er_tp = each_recs.get(f"EACH__{p_tp['pool']}")
        ev_ta = parse_each(er_ta["text"], 4) if er_ta else None
        ev_tp = parse_each(er_tp["text"], 4) if er_tp else None
        ta_bins["EACH"][pid] = (1 if any(ev_ta) else 0) if ev_ta is not None else None
        tpa_bins["EACH"][pid] = (1 if ev_tp[rpos - 1] else 0) if (ev_tp is not None and rpos is not None) else None
        tps_bins["EACH"][pid] = (
            (1 if (ev_tp[rpos - 1] and sum(1 for x in ev_tp if x) == 1) else 0)
            if (ev_tp is not None and rpos is not None)
            else None
        )

        iv_ta = [
            parse_verdict(iso_recs[f"ISO__{c['cid']}"]["text"])
            if f"ISO__{c['cid']}" in iso_recs
            else None
            for c in p_ta["cands"]
        ]
        iv_tp = [
            parse_verdict(iso_recs[f"ISO__{c['cid']}"]["text"])
            if f"ISO__{c['cid']}" in iso_recs
            else None
            for c in p_tp["cands"]
        ]
        ta_bins["ISO"][pid] = (1 if any(iv_ta) else 0) if all(v is not None for v in iv_ta) else None
        tpa_bins["ISO"][pid] = (
            (1 if iv_tp[rpos - 1] else 0)
            if (all(v is not None for v in iv_tp) and rpos is not None)
            else None
        )
        tps_bins["ISO"][pid] = (
            (1 if (iv_tp[rpos - 1] and sum(1 for x in iv_tp if x) == 1) else 0)
            if (all(v is not None for v in iv_tp) and rpos is not None)
            else None
        )

    arms_out: Dict[str, Any] = {}
    cnts: Dict[str, Dict[str, int]] = {}
    for arm in ("PICK", "ISO", "EACH"):
        tv = [v for v in ta_bins[arm].values() if v is not None]
        av = [v for v in tpa_bins[arm].values() if v is not None]
        sv = [v for v in tps_bins[arm].values() if v is not None]
        ta_k, ta_n = sum(tv), len(tv)
        tpa_k, tpa_n = sum(av), len(av)
        tps_k, tps_n = sum(sv), len(sv)
        cnts[arm] = {
            "ta_k": ta_k, "ta_n": ta_n,
            "tp_aligned_k": tpa_k, "tp_aligned_n": tpa_n,
            "tp_strict_k": tps_k, "tp_strict_n": tps_n,
        }
        arms_out[arm] = {
            "ta_k": ta_k,
            "ta_n": ta_n,
            "ta_rate": (ta_k / ta_n) if ta_n else None,
            "ta_ci95_exact": _clopper_pearson_ci95_b(ta_k, ta_n) if ta_n else None,
            "tp_aligned_k": tpa_k,
            "tp_aligned_n": tpa_n,
            "tp_aligned_rate": (tpa_k / tpa_n) if tpa_n else None,
            "tp_strict_k": tps_k,
            "tp_strict_n": tps_n,
            "tp_strict_rate": (tps_k / tps_n) if tps_n else None,
            "boundary_hit_aligned": (ta_n > 0 and ta_k in (0, ta_n)) or (tpa_n > 0 and tpa_k in (0, tpa_n)),
            "boundary_hit_strict": (ta_n > 0 and ta_k in (0, ta_n)) or (tps_n > 0 and tps_k in (0, tps_n)),
            "unsmoothed_sdt_aligned": _sdt_counts_b(tpa_k, tpa_n, ta_k, ta_n, "raw"),
            "unsmoothed_sdt_strict": _sdt_counts_b(tps_k, tps_n, ta_k, ta_n, "raw"),
        }

    def _pair_mc(d: Dict[str, Dict[str, Optional[int]]], a1: str, a2: str) -> Dict[str, Any]:
        n10 = n01 = n11 = n00 = 0
        for it in items:
            pid = it["pid"]
            v1, v2 = d[a1].get(pid), d[a2].get(pid)
            if v1 is None or v2 is None:
                continue
            if v1 == 1 and v2 == 0:
                n10 += 1
            elif v1 == 0 and v2 == 1:
                n01 += 1
            elif v1 == 1 and v2 == 1:
                n11 += 1
            else:
                n00 += 1
        return {
            "n_paired": n10 + n01 + n11 + n00,
            "n_10": n10,
            "n_01": n01,
            "n_11": n11,
            "n_00": n00,
            "exact_mcnemar_p": _exact_mcnemar_b(n10, n01),
        }

    clip_sens: Dict[str, Any] = {}
    pc, ic = cnts["PICK"], cnts["ISO"]
    for mode in ("hautus_05_n1", "macmillan_05_n", "quarter_025_n"):
        p_al = _sdt_counts_b(pc["tp_aligned_k"], pc["tp_aligned_n"], pc["ta_k"], pc["ta_n"], mode)
        i_al = _sdt_counts_b(ic["tp_aligned_k"], ic["tp_aligned_n"], ic["ta_k"], ic["ta_n"], mode)
        i_st = _sdt_counts_b(ic["tp_strict_k"], ic["tp_strict_n"], ic["ta_k"], ic["ta_n"], mode)
        clip_sens[mode] = {
            "aligned_delta_d": (p_al["d_prime"] - i_al["d_prime"]) if (p_al["d_prime"] is not None and i_al["d_prime"] is not None) else None,
            "aligned_delta_c": (p_al["c"] - i_al["c"]) if (p_al["c"] is not None and i_al["c"] is not None) else None,
            "strict_delta_d": (p_al["d_prime"] - i_st["d_prime"]) if (p_al["d_prime"] is not None and i_st["d_prime"] is not None) else None,
            "strict_delta_c": (p_al["c"] - i_st["c"]) if (p_al["c"] is not None and i_st["c"] is not None) else None,
        }

    return {
        "arms": arms_out,
        "exact_mcnemar": {
            "TA_PICK_vs_ISO_any": _pair_mc(ta_bins, "PICK", "ISO"),
            "TA_PICK_vs_EACH_any": _pair_mc(ta_bins, "PICK", "EACH"),
            "TP_aligned_PICK_vs_ISO": _pair_mc(tpa_bins, "PICK", "ISO"),
            "TP_strict_PICK_vs_ISO": _pair_mc(tps_bins, "PICK", "ISO"),
        },
        "sdt_clipping_sensitivity_PICK_minus_ISO": clip_sens,
    }


def _c3_unsolved_snapshot_b(
    c3_root: Path,
    ta_pids: Sequence[str],
    tp_pids: Sequence[str],
    ta_map: Dict[str, Dict[str, Any]],
    tp_map: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    p_ta: List[float] = []
    i_ta: List[float] = []
    p_tp: List[float] = []
    i_tpa: List[float] = []
    i_tps: List[float] = []

    for pid in ta_pids:
        pool = ta_map[pid]
        pr = load_c3_record(c3_root, f"haiku__PICK__{pool['pool']}")
        pc = parse_choice(pr["text"], 3) if pr else None
        if pc is not None:
            p_ta.append(1.0 if pc > 0 else 0.0)
        ivs = []
        for c in pool["cands"]:
            ir = load_c3_record(c3_root, f"haiku__ISO__{c['cid']}")
            ivs.append(parse_verdict(ir["text"]) if ir else None)
        if all(v is not None for v in ivs):
            i_ta.append(1.0 if any(ivs) else 0.0)

    for pid in tp_pids:
        if pid not in tp_map:
            continue
        pool = tp_map[pid]
        rpos = next((i + 1 for i, c in enumerate(pool["cands"]) if c["role"] == "right"), None)
        pr = load_c3_record(c3_root, f"haiku__PICK__{pool['pool']}")
        pc = parse_choice(pr["text"], 3) if pr else None
        if pc is not None and rpos is not None:
            p_tp.append(1.0 if pc == rpos else 0.0)
        ivs = []
        for c in pool["cands"]:
            ir = load_c3_record(c3_root, f"haiku__ISO__{c['cid']}")
            ivs.append(parse_verdict(ir["text"]) if ir else None)
        if all(v is not None for v in ivs) and rpos is not None:
            i_tpa.append(1.0 if ivs[rpos - 1] else 0.0)
            i_tps.append(1.0 if (ivs[rpos - 1] and sum(1 for x in ivs if x) == 1) else 0.0)

    p_sdt = hautus_sdt(p_tp, p_ta) if (p_tp and p_ta) else None
    ia_sdt = hautus_sdt(i_tpa, i_ta) if (i_tpa and i_ta) else None
    is_sdt = hautus_sdt(i_tps, i_ta) if (i_tps and i_ta) else None
    return {
        "n_ta": len(p_ta),
        "n_tp": len(p_tp),
        "pick_ta_fa": (sum(p_ta) / len(p_ta)) if p_ta else None,
        "iso_ta_fa": (sum(i_ta) / len(i_ta)) if i_ta else None,
        "pick_tp_hit": (sum(p_tp) / len(p_tp)) if p_tp else None,
        "iso_tp_aligned_hit": (sum(i_tpa) / len(i_tpa)) if i_tpa else None,
        "iso_tp_strict_hit": (sum(i_tps) / len(i_tps)) if i_tps else None,
        "pick_d_prime": p_sdt["d_prime"] if p_sdt else None,
        "pick_c": p_sdt["c"] if p_sdt else None,
        "iso_aligned_d_prime": ia_sdt["d_prime"] if ia_sdt else None,
        "iso_aligned_c": ia_sdt["c"] if ia_sdt else None,
        "iso_strict_d_prime": is_sdt["d_prime"] if is_sdt else None,
        "iso_strict_c": is_sdt["c"] if is_sdt else None,
        "delta_d_aligned": (p_sdt["d_prime"] - ia_sdt["d_prime"]) if (p_sdt and ia_sdt) else None,
        "delta_c_aligned": (p_sdt["c"] - ia_sdt["c"]) if (p_sdt and ia_sdt) else None,
        "delta_d_strict": (p_sdt["d_prime"] - is_sdt["d_prime"]) if (p_sdt and is_sdt) else None,
        "delta_c_strict": (p_sdt["c"] - is_sdt["c"]) if (p_sdt and is_sdt) else None,
    }


def analyze_human_audit_b(root: Path, c3_root: Path) -> Dict[str, Any]:
    audit_path = root / "audit" / "human_audit_results.json"
    if not audit_path.is_file():
        return {
            "status": "pending_user",
            "file": "audit/human_audit_results.json",
            "sections": {},
            "sensitivity": None,
        }
    raw = json.loads(audit_path.read_text(encoding="utf-8"))
    responses = raw.get("responses", {})
    c3_dir = c3_root / "exps" / "c3"
    hand_map = {
        r["id"]: r["decision"].strip().lower()
        for r in csv.DictReader((c3_dir / "hand_checks.csv").open(encoding="utf-8"))
    }
    audit_map = {
        r["pid"]: r["audited_stratum"].strip().upper()
        for r in csv.DictReader((c3_dir / "audit_unsolved.csv").open(encoding="utf-8"))
    }

    a_cnt: Counter = Counter()
    b_cnt: Counter = Counter()
    c_cnt: Counter = Counter()
    hidden_pids: List[str] = []
    broken_pids: List[str] = []
    b_agree = b_dec = c_agree = c_dec = 0

    for item_id, rec in sorted(responses.items()):
        sec = rec.get("section", "")
        v = (rec.get("verdict") or "").strip()
        if not v:
            continue
        if sec == "a":
            a_cnt[v] += 1
            pid = item_id.split("_", 2)[2]
            if v == "Hidden equivalent right answer":
                hidden_pids.append(pid)
            elif v == "Broken prompt":
                broken_pids.append(pid)
        elif sec == "b":
            b_cnt[v] += 1
            sid = item_id.split("_", 2)[2]
            if v in ("Correct", "Wrong"):
                b_dec += 1
                if (v == "Correct" and hand_map.get(sid) == "correct") or (v == "Wrong" and hand_map.get(sid) == "wrong"):
                    b_agree += 1
        elif sec == "c":
            c_cnt[v] += 1
            pid = item_id.split("_", 2)[2]
            if v != "Unsure":
                c_dec += 1
                if v.split(" ", 1)[0].strip().upper() == audit_map.get(pid, ""):
                    c_agree += 1

    a_done = sum(a_cnt.values())
    a_dec = a_done - a_cnt.get("Unsure", 0)
    a_flag = len(hidden_pids) + len(broken_pids)
    b_done = sum(b_cnt.values())
    c_done = sum(c_cnt.values())

    c3_pools = json.loads((c3_root / "banks/locked_c3/pools.json").read_text(encoding="utf-8"))
    ta_map = {p["pid"]: p for p in c3_pools if p["kind"] == "TA"}
    tp_map = {p["pid"]: p for p in c3_pools if p["kind"] == "TP"}
    c4_bank = json.loads((root / "banks/locked_v2/c4_haiku_compute.json").read_text(encoding="utf-8"))
    corr_ta = sorted({p["pid"] for p in c4_bank["pools"] if p["kind"] == "TA"})
    corr_tp = sorted({p["pid"] for p in c4_bank["pools"] if p["kind"] == "TP"})
    c6_bank = json.loads((root / "banks/locked_v2/c6_crossvendor_math.json").read_text(encoding="utf-8"))
    c6_pids = {p["pid"] for p in c6_bank["pools"]}

    hidden_s, broken_s = set(hidden_pids), set(broken_pids)
    flag_s = hidden_s | broken_s

    return {
        "status": "complete" if (a_done == 50 and b_done == 22 and c_done == 20) else "partial",
        "file": "audit/human_audit_results.json",
        "exported_at": raw.get("exported_at"),
        "sections": {
            "section_a": {
                "n_completed": a_done,
                "n_decided": a_dec,
                "counts": dict(a_cnt),
                "n_hidden_right": len(hidden_pids),
                "n_broken_prompt": len(broken_pids),
                "n_flagged": a_flag,
                "error_rate_decided": (a_flag / a_dec) if a_dec else None,
                "error_rate_decided_ci95_exact": _clopper_pearson_ci95_b(a_flag, a_dec) if a_dec else None,
                "error_rate_all": (a_flag / a_done) if a_done else None,
                "error_rate_all_ci95_exact": _clopper_pearson_ci95_b(a_flag, a_done) if a_done else None,
                "hidden_right_pids": sorted(hidden_pids),
                "broken_prompt_pids": sorted(broken_pids),
            },
            "section_b": {
                "n_completed": b_done,
                "n_decided": b_dec,
                "counts": dict(b_cnt),
                "n_agree_with_ai": b_agree,
                "agreement_rate": (b_agree / b_dec) if b_dec else None,
                "agreement_rate_ci95_exact": _clopper_pearson_ci95_b(b_agree, b_dec) if b_dec else None,
            },
            "section_c": {
                "n_completed": c_done,
                "n_decided": c_dec,
                "counts": dict(c_cnt),
                "n_agree_with_ai": c_agree,
                "agreement_rate": (c_agree / c_dec) if c_dec else None,
                "agreement_rate_ci95_exact": _clopper_pearson_ci95_b(c_agree, c_dec) if c_dec else None,
            },
        },
        "sensitivity": {
            "flagged_in_c4_unsolved": sorted(flag_s & set(corr_ta)),
            "flagged_in_c6_crossvendor": sorted(flag_s & c6_pids),
            "baseline_c3_unsolved": _c3_unsolved_snapshot_b(c3_root, corr_ta, corr_tp, ta_map, tp_map),
            "drop_flagged": _c3_unsolved_snapshot_b(
                c3_root,
                [p for p in corr_ta if p not in flag_s],
                [p for p in corr_tp if p not in flag_s],
                ta_map,
                tp_map,
            ),
            "relabel_hidden_right_drop_broken": _c3_unsolved_snapshot_b(
                c3_root,
                [p for p in corr_ta if p not in flag_s],
                [p for p in corr_tp if p not in broken_s],
                ta_map,
                tp_map,
            ),
        },
    }


def _collect_strict_failures(results: Dict[str, Any]) -> List[str]:
    failures: List[str] = []
    if results["c5_own_removal"]["status"] != "complete":
        failures.append(f"c5_own_removal={results['c5_own_removal']['status']}")
    if results["c5_wells_removal"]["status"] != "complete":
        failures.append(f"c5_wells_removal={results['c5_wells_removal']['status']}")
    if results["c4_compute"]["status"] != "complete":
        failures.append(f"c4_compute={results['c4_compute']['status']}")
    for m, mdata in results["c9_science"]["models"].items():
        for arm, st in mdata["arm_statuses"].items():
            if st != "complete":
                failures.append(f"c9_science.{m}.{arm}={st}")
    for m, mdata in results["c6_math"]["models"].items():
        for arm, st in mdata["arm_statuses"].items():
            if st != "complete":
                failures.append(f"c6_math.{m}.{arm}={st}")
    c7 = results.get("c7_mitigation", {})
    for m, mdata in c7.get("science_m2", {}).items():
        if mdata.get("status") != "complete":
            failures.append(f"c7.science_m2.{m}={mdata.get('status')}")
    for m, mdata in c7.get("math_m2", {}).items():
        if mdata.get("status") != "complete":
            failures.append(f"c7.math_m2.{m}={mdata.get('status')}")
    if c7.get("math_haiku_m1", {}).get("status") != "complete":
        failures.append(f"c7.math_haiku_m1={c7.get('math_haiku_m1', {}).get('status')}")
    if c7.get("math_haiku_m3_foil", {}).get("status") != "complete":
        failures.append(f"c7.math_haiku_m3_foil={c7.get('math_haiku_m3_foil', {}).get('status')}")
    return failures


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Independent verifier analysis_b.py (pure stdlib).")
    p.add_argument("--root", default=str(DEFAULT_ROOT), help="Path to v2-upgrade root.")
    p.add_argument("--c3-root", default=str(DEFAULT_C3_ROOT), help="Path to C3 repo root.")
    p.add_argument("--out", default=None, help="Output JSON path (default: <root>/results/results_b.json).")
    p.add_argument("--boot", type=int, default=DEFAULT_BOOT, help="Bootstrap resamples (default: 5000).")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Base RNG seed.")
    p.add_argument("--strict", action="store_true", help="Require all arms to be complete; exit 1 otherwise.")
    p.add_argument("--self-test", action="store_true", help="Run inline parser/grader/Acklam self-tests only.")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    run_self_tests()
    if args.self_test:
        print("SELF-TEST PASS")
        return 0

    root = Path(args.root).resolve()
    c3_root = Path(args.c3_root).resolve()
    out_path = Path(args.out).resolve() if args.out else (root / "results" / "results_b.json")

    payload: Dict[str, Any] = {
        "meta": {
            "verifier": "analysis_b.py",
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bootstrap_resamples": args.boot,
            "seed": args.seed,
            "strict_mode": bool(args.strict),
            "independent_parsers": True,
            "independent_math_grader": True,
        },
        "c5_own_removal": analyze_c5_own_removal(root, c3_root, args.boot, args.seed),
        "c5_wells_removal": analyze_c5_wells_removal(root, c3_root, args.boot, args.seed),
        "c4_compute": analyze_c4_compute(root, c3_root, args.boot, args.seed),
        "c9_science": analyze_c9_science(root, args.boot, args.seed),
        "c6_math": analyze_c6_math(root, args.boot, args.seed),
        "c7_mitigation": analyze_c7_mitigation(root, c3_root, args.boot, args.seed),
        "human_audit": analyze_human_audit_b(root, c3_root),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    strict_failures = _collect_strict_failures(payload)
    print(f"Wrote {out_path}")
    print(
        f"Arm status summary: incomplete={len(strict_failures)} "
        f"({', '.join(strict_failures[:6]) if strict_failures else 'all complete'})"
    )
    if args.strict and strict_failures:
        print(f"ERROR (--strict): incomplete arms: {', '.join(strict_failures)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
