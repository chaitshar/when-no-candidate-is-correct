"""Independent answer grader (B). grade_b(reply, gold) -> True/False/None."""
import re
import signal
import contextlib

import sympy
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application,
                                        convert_xor)

_TRANSF = standard_transformations + (implicit_multiplication_application, convert_xor)
_LOCALS = {n: sympy.Symbol(n) for n in "NSEIOQ"}
_LOCALS["pi"] = sympy.pi


class _TO(Exception):
    pass


@contextlib.contextmanager
def _timeout(sec=5):
    def h(sig, frm):
        raise _TO()
    try:
        old = signal.signal(signal.SIGALRM, h)
    except ValueError:  # not main thread
        yield
        return
    signal.alarm(sec)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------- extraction ----------------
def _match_brace(s, i):
    """s[i]=='{' ; return index of matching '}' or -1."""
    d = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            d += 1
        elif s[j] == '}':
            d -= 1
            if d == 0:
                return j
    return -1


def _last_boxed(s):
    res = None
    for m in re.finditer(r'\\(?:boxed|fbox)\s*\{', s):
        i = m.end() - 1
        j = _match_brace(s, i)
        if j != -1:
            res = s[i + 1:j]
    return res


def _clean_extracted(t):
    t = t.strip()
    for _ in range(3):
        t = t.strip().strip('*_`').strip()
        t = re.sub(r'^\\\(|\\\)$', '', t).strip()
        t = re.sub(r'^\\\[|\\\]$', '', t).strip()
        t = t.strip('$').strip()
        t = t.rstrip('.').strip() if not re.search(r'\d\.$', t) or True else t
    b = _last_boxed(t)
    if b is not None:
        return b.strip()
    return t.strip()


def extract_answer(reply):
    if not isinstance(reply, str):
        return None
    lines = reply.splitlines()
    for ln in reversed(lines):
        idx = ln.lower().rfind('answer:')
        if idx == -1:
            # markdown like **ANSWER**: 7
            m = list(re.finditer(r'answer\**\s*:', ln, re.I))
            if not m:
                continue
            tail = ln[m[-1].end():]
        else:
            tail = ln[idx + len('answer:'):]
        tail = _clean_extracted(tail)
        if tail:
            return tail
    return _last_boxed(reply)


# ---------------- normalization ----------------
def _strip_text(s):
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'\\(?:text|textbf|textit|mathrm|mathbf|mbox|operatorname)\s*\{([^{}]*)\}', r'\1', s)
    return s


def _norm(s):
    s = s.strip()
    s = re.sub(r'\\\(|\\\)|\\\[|\\\]', '', s)
    s = s.replace('$', '')
    b = _last_boxed(s)
    if b is not None and s.strip().startswith('\\boxed'):
        s = b
    s = re.sub(r'\\(?:left|right|big|Big|bigg|Bigg)(?![a-zA-Z])', '', s)
    s = re.sub(r'\\[!,;:> ]|\\quad|\\qquad', '', s)
    s = _strip_text(s)
    s = re.sub(r'\\[dt]frac', r'\\frac', s)
    s = re.sub(r'\s+', '', s)
    s = s.rstrip('.')
    if re.fullmatch(r'[+-]?\d{1,3}(,\d{3})+(\.\d+)?', s):
        s = s.replace(',', '')
    s = s.replace('^{\\circ}', '').replace('^\\circ', '').replace('°', '')
    return s


def _paren_letter(s):
    m = re.fullmatch(r'\(?([A-Za-z])\)?', s)
    return m.group(1) if m else None


# ---------------- latex -> sympy ----------------
def _repl_cmd(s, cmd, fmt, nargs):
    """Replace \\cmd{a}{b}.. via brace matching using fmt with {0},{1}."""
    pat = '\\' + cmd
    while True:
        i = s.find(pat)
        if i == -1:
            return s
        j = i + len(pat)
        args = []
        ok = True
        for _ in range(nargs):
            while j < len(s) and s[j] == ' ':
                j += 1
            if j < len(s) and s[j] == '{':
                k = _match_brace(s, j)
                if k == -1:
                    ok = False
                    break
                args.append(s[j + 1:k])
                j = k + 1
            elif j < len(s) and (s[j].isalnum()):
                args.append(s[j])
                j += 1
            else:
                ok = False
                break
        if not ok:
            return s.replace(pat, ' ?? ')
        s = s[:i] + fmt.format(*['(' + a + ')' for a in args]) + s[j:]


def _latex_to_py(s):
    s = _norm(s)
    s = s.replace('\\cdot', '*').replace('\\times', '*').replace('\\div', '/')
    s = re.sub(r'\\sqrt\[([^\]]*)\]', r'\\rt[\1]', s)
    for _ in range(10):
        before = s
        s = _repl_cmd(s, 'frac', '({0}/{1})', 2)
        # \rt[n]{x}
        m = re.search(r'\\rt\[([^\]]*)\]\{', s)
        if m:
            i = m.end() - 1
            k = _match_brace(s, i)
            if k != -1:
                s = s[:m.start()] + '((%s)**(1/(%s)))' % (s[i + 1:k], m.group(1)) + s[k + 1:]
        s = _repl_cmd(s, 'sqrt', 'sqrt({0})', 1)
        if s == before:
            break
    s = re.sub(r'\\(pi|infty)(?![a-zA-Z])', lambda m: {'pi': 'pi', 'infty': 'oo'}[m.group(1)], s)
    s = re.sub(r'\\(sin|cos|tan|log|ln|exp)(?![a-zA-Z])', r'\1', s)
    s = s.replace('{', '(').replace('}', ')').replace('\\', '')
    s = re.sub(r'(?<=\d)%', '/100', s)
    s = s.replace('^', '**')
    s = re.sub(r'\*\*(-?\w+(?:\.\d+)?)', lambda m: '**(' + m.group(1) + ')', s)
    return s


def _to_expr(s):
    s = _norm(s)
    m = re.fullmatch(r'[A-Za-z]=([^=<>]+)', s)
    if m:
        s = m.group(1)
    if '=' in s or '<' in s or '>' in s or '\\le' in s or '\\ge' in s:
        return None
    py = _latex_to_py(s)
    try:
        with _timeout():
            return parse_expr(py, local_dict=dict(_LOCALS), transformations=_TRANSF, evaluate=True)
    except BaseException:
        pass
    try:
        with _timeout():
            from sympy.parsing.latex import parse_latex
            return parse_latex(s)
    except BaseException:
        return None


def _expr_equal(a, b):
    ea, eb = _to_expr(a), _to_expr(b)
    if ea is None or eb is None:
        return False
    try:
        with _timeout():
            if not ea.free_symbols and not eb.free_symbols:
                va, vb = complex(sympy.N(ea, 30)), complex(sympy.N(eb, 30))
                return abs(va - vb) <= 1e-9 * max(1.0, abs(va), abs(vb))
    except BaseException:
        pass
    try:
        with _timeout():
            return sympy.simplify(ea - eb) == 0
    except BaseException:
        return False


def _split_top(s):
    parts, d, cur = [], 0, ''
    for ch in s:
        if ch in '([{':
            d += 1
        elif ch in ')]}':
            d -= 1
        if ch == ',' and d == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    return parts


def _tuple_parts(s):
    """Return (open, close, [elems]) or None."""
    s = s.replace('\\{', '{').replace('\\}', '}')
    if len(s) >= 2 and s[0] in '([{' and s[-1] in ')]}':
        # ensure outer brackets match each other
        d = 0
        for i, ch in enumerate(s):
            if ch in '([{':
                d += 1
            elif ch in ')]}':
                d -= 1
                if d == 0 and i != len(s) - 1:
                    return None
        parts = _split_top(s[1:-1])
        if len(parts) > 1:
            return s[0], s[-1], parts
        return None
    parts = _split_top(s)
    if len(parts) > 1:
        return '', '', parts
    return None


def _equal(a, b):
    na, nb = _norm(a), _norm(b)
    if na == nb:
        return True
    la, lb = _paren_letter(na), _paren_letter(nb)
    if la and lb and (na.isalpha() or nb.isalpha() or '(' in na + nb):
        return la == lb
    ta, tb = _tuple_parts(na), _tuple_parts(nb)
    if ta or tb:
        if not (ta and tb):
            return False
        if ta[0] != tb[0] or ta[1] != tb[1] or len(ta[2]) != len(tb[2]):
            return False
        return all(_equal(x, y) for x, y in zip(ta[2], tb[2]))
    return _expr_equal(na, nb)


def grade_b(reply, gold):
    ans = extract_answer(reply)
    if ans is None or gold is None:
        return None
    try:
        return bool(_equal(ans, str(gold)))
    except BaseException:
        return False


if __name__ == '__main__':
    T = [
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
        ("ANSWER: 3 apples\nthen ANSWER: 5", "5", True),
        ("no answer line but \\boxed{a_{1}} and \\boxed{\\frac{1}{\\sqrt{2}}}", "\\frac{\\sqrt{2}}{2}", True),
        ("ANSWER: \\boxed{12}", "12", True),
        ("ANSWER: x=5", "5", True),
        ("ANSWER: \\left(1,\\ 2\\right)", "(1,2)", True),
        ("ANSWER: 0.3333", "\\frac13", False),
        ("ANSWER: 41", "42", False),
        ("ANSWER: \\sqrt{17}", "\\sqrt{17}-1", False),
        ("ANSWER: (1,2)", "(2,1)", False),
        ("ANSWER: (1,2)", "[1,2]", False),
        ("ANSWER: 2\\sqrt{3}", "\\sqrt{13}", False),
        ("ANSWER: \\frac{\\pi}{6}", "\\frac{\\pi}{3}", False),
        ("ANSWER: x^2+2", "x^2+1", False),
        ("ANSWER: 1000", "100", False),
        ("ANSWER: A", "\\text{B}", False),
        ("ANSWER: 0.5001", "\\frac12", False),
        ("ANSWER: (1,2,3)", "(1,2)", False),
        ("I think it is 4", "4", None),
    ]
    bad = 0
    for r, g, exp in T:
        got = grade_b(r, g)
        ok = got is exp
        bad += not ok
        print(("ok  " if ok else "FAIL"), repr(r)[:50], repr(g), exp, got)
    print("failures:", bad)
    raise SystemExit(1 if bad else 0)
