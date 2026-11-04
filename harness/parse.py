"""Parsers for subject replies. Each returns None when the reply is unparseable;
unparseable replies are counted and reported, never dropped silently.
The LAST matching line wins (subjects sometimes restate the format earlier)."""
import re


def _last(pattern, text):
    m = re.findall(pattern, text or "", re.I | re.M)
    return m[-1] if m else None


def verdict(text):
    v = _last(r"^\W*VERDICT\W*:?\W*(ACCEPT|REJECT)\b", text)
    return None if v is None else v.upper() == "ACCEPT"


def choice(text, n):
    v = _last(r"^\W*CHOICE\W*:?\W*(NONE|\d+)\b", text)
    if v is None:
        return None
    if v.upper() == "NONE":
        return 0
    k = int(v)
    return k if 1 <= k <= n else None


def each(text, n):
    out = []
    for i in range(1, n + 1):
        v = _last(rf"^\W*VERDICT\s*{i}\W*:?\W*(ACCEPT|REJECT)\b", text)
        out.append(None if v is None else v.upper() == "ACCEPT")
    return out


def answer(text):
    # fixed 2026-11-04 after round-3 review: the earlier pattern r"^\W*ANSWER\W*:?\s*(.+?)\s*$"
    # let \W* swallow a leading "$\" of LaTeX answers (e.g. "$\sqrt{17}$" -> "sqrt{17}").
    v = _last(r"^\W*ANSWER\s*:\s*(.+?)\s*$", text)
    return v.strip().strip("*`$ ").strip() if v else None


def winner(text):
    v = _last(r"^\W*WINNER\W*:?\W*([AB])\b", text)
    return v.upper() if v else None


def confidence(text):
    v = _last(r"^\W*CONFIDENCE\W*:?\W*([1-5])\b", text)
    return int(v) if v else None
