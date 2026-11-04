"""Grade a subject's final answer against an official MathArena answer (supplementary to
MathArena's own grading, which is used for all candidate labels). Normalization then a
sympy equivalence check; returns True, False, or None when the reply has no answer."""
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../banks"))
from build_prm_bank import norm, sym_equal  # noqa: E402


def strip_boxed(a):
    m = re.search(r"\\boxed\{(.*)\}", a)
    return m.group(1) if m else a


def grade(ans, gold):
    if ans is None:
        return None
    a = strip_boxed(ans.strip())
    g = str(gold)
    if norm(a) == norm(g):
        return True
    try:
        if float(norm(a).replace(",", "")) == float(norm(g)):
            return True
    except ValueError:
        pass
    return sym_equal(a, g)
