#!/usr/bin/env python3
"""Explanatory diagrams for the paper (plain SVG, Python stdlib only).

Writes four files to paper/figures/:
  figA_two_ways.svg   how PICK and ISO show the answers to the judge
  figB_bar_skill.svg  what "skill" and "bar" mean, and why a lower bar hurts more on hard problems
  figC_fixes.svg      the three fixes M1, M2, M3 and what each one did
  figD_glance.svg     wrong-pick rates under ISO and PICK for every test, in one picture

figA and the curves in figB are illustrations. Every number printed in figC and
figD is read from paper/results.tex, so the diagrams cannot drift from the paper.
"""
import math
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper" / "figures"

BLUE = "#0072B2"
RED = "#D55E00"
GREEN = "#009E73"
ORANGE = "#E69F00"
INK = "#111827"
MUTED = "#6B7280"
GRID = "#E5E7EB"
PANEL = "#F9FAFB"
FONT = "system-ui, -apple-system, Helvetica, Arial, sans-serif"


def load_macros():
    text = (ROOT / "paper" / "results.tex").read_text() + (ROOT / "paper" / "results_extra.tex").read_text()
    return dict(re.findall(r"res@([A-Za-z0-9_]+)\\endcsname\{(.*)\}", text))


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.el = w, h, []

    def add(self, s):
        self.el.append(s)

    def rect(self, x, y, w, h, fill="#FFFFFF", stroke="none", sw=1.0, rx=0.0, op=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" fill-opacity="{op:.2f}" stroke="{stroke}" stroke-width="{sw:.1f}"{d}/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.2, dash=None, arrow=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arr)"' if arrow else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw:.1f}"{d}{m}/>')

    def circle(self, cx, cy, r, fill=INK, stroke="#FFFFFF", sw=1.0):
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.1f}"/>')

    def path(self, pts, fill="none", stroke=INK, sw=1.5, op=1.0, close=False):
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + (" Z" if close else "")
        self.add(f'<path d="{d}" fill="{fill}" fill-opacity="{op:.2f}" stroke="{stroke}" stroke-width="{sw:.1f}" stroke-linejoin="round"/>')

    def text(self, x, y, s, size=11.0, weight="400", fill=INK, anchor="start"):
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size:.1f}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>')

    def render(self):
        head = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">\n'
            f"<style>text {{ font-family: {FONT}; }}</style>\n"
            '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{INK}"/></marker></defs>\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#FFFFFF"/>\n'
        )
        return head + "\n".join(self.el) + "\n</svg>\n"


def card(s, x, y, w, h, label):
    """An answer card marked as wrong."""
    s.rect(x, y, w, h, fill="#FFFFFF", stroke="#9CA3AF", sw=1.2, rx=5)
    s.text(x + 12, y + h / 2 + 4, label, size=11.5, weight="600")
    cx, cy = x + w - 16, y + h / 2
    s.circle(cx, cy, 8, fill=RED, stroke="#FFFFFF", sw=1.0)
    s.line(cx - 3.5, cy - 3.5, cx + 3.5, cy + 3.5, stroke="#FFFFFF", sw=1.8)
    s.line(cx - 3.5, cy + 3.5, cx + 3.5, cy - 3.5, stroke="#FFFFFF", sw=1.8)


def judge(s, x, y, w=64, h=40):
    s.rect(x, y, w, h, fill="#EEF2FF", stroke="#4B5563", sw=1.3, rx=8)
    s.text(x + w / 2, y + h / 2 + 4, "Judge", size=11.5, weight="700", anchor="middle")


def fig_two_ways():
    s = Svg(900, 372)
    s.text(24, 26, "Two ways to ask the judge", size=14.5, weight="700")
    s.text(24, 44, "Example pool: three answers to one problem, and all three are wrong (red cross). The best reply is NONE.", size=10.5, fill=MUTED)

    # PICK panel
    px, py, pw, ph = 24, 58, 414, 290
    s.rect(px, py, pw, ph, fill=PANEL, stroke=GRID, sw=1.0, rx=6)
    s.text(px + 16, py + 24, "PICK", size=13, weight="700", fill=RED)
    s.text(px + 62, py + 24, "all answers together, one call", size=11.5)
    s.rect(px + 18, py + 44, 150, 186, fill="#FFFFFF", stroke="#9CA3AF", sw=1.0, rx=6, dash="4,3")
    for i, lab in enumerate(("Answer A", "Answer B", "Answer C")):
        card(s, px + 30, py + 56 + i * 58, 126, 44, lab)
    s.line(px + 172, py + 137, px + 206, py + 137, arrow=True)
    judge(s, px + 210, py + 117)
    s.line(px + 278, py + 137, px + 304, py + 137, arrow=True)
    s.rect(px + 308, py + 113, 92, 48, fill="#FFF1E8", stroke=RED, sw=1.4, rx=6)
    s.text(px + 354, py + 133, '"I pick B"', size=11.5, weight="700", anchor="middle")
    s.text(px + 354, py + 150, "or NONE", size=9.5, fill=MUTED, anchor="middle")
    s.text(px + 16, py + 256, "If the judge picks A, B or C here, that is a", size=11)
    s.text(px + 16, py + 273, "wrong pick.", size=11.5, weight="700", fill=RED)
    s.text(px + 92, py + 273, "Only NONE is correct.", size=11)

    # ISO panel
    qx = 462
    s.rect(qx, py, pw, ph, fill=PANEL, stroke=GRID, sw=1.0, rx=6)
    s.text(qx + 16, py + 24, "ISO", size=13, weight="700", fill=BLUE)
    s.text(qx + 50, py + 24, "each answer alone, three separate calls", size=11.5)
    for i, lab in enumerate(("Answer A", "Answer B", "Answer C")):
        y = py + 56 + i * 58
        card(s, qx + 24, y, 126, 44, lab)
        s.line(qx + 154, y + 22, qx + 186, y + 22, arrow=True)
        judge(s, qx + 190, y + 2)
        s.line(qx + 258, y + 22, qx + 290, y + 22, arrow=True)
        s.rect(qx + 294, y + 2, 104, 40, fill="#E8F3FA", stroke=BLUE, sw=1.4, rx=6)
        s.text(qx + 346, y + 20, '"not correct"', size=10.5, weight="700", anchor="middle")
        s.text(qx + 346, y + 34, "or correct", size=9, fill=MUTED, anchor="middle")
    s.text(qx + 16, py + 256, "If the judge accepts no answer, the result is NONE.", size=11)
    s.text(qx + 16, py + 273, "If it accepts any answer here, that is a", size=11)
    s.text(qx + 222, py + 273, "wrong pick.", size=11.5, weight="700", fill=RED)

    s.text(24, 364, "This is one example. The paper counts how often each method ends in a wrong pick, over many pools.", size=10, fill=MUTED)
    return s


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def pdf(x, mu):
    return math.exp(-0.5 * (x - mu) ** 2) / math.sqrt(2.0 * math.pi)


def fig_bar_skill():
    s = Svg(900, 440)
    s.text(24, 26, "Skill and bar: why the same lower bar hurts more on hard problems", size=14.5, weight="700")
    s.text(24, 44, "A drawing of the idea, not measured data. Each curve shows how correct a group of answers looks to the judge.", size=10.5, fill=MUTED)

    c_iso, c_pick = 0.075, -0.410  # first-study averages, as in the curve figure
    panels = [
        (24, "Easy problems: high skill", "Right and wrong answers look very different.", 3.0),
        (462, "Hard problems: low skill", "Right and wrong answers look almost the same.", 0.2),
    ]
    for px, title, sub, dp in panels:
        pw, ph, py = 414, 368, 58
        s.rect(px, py, pw, ph, fill=PANEL, stroke=GRID, sw=1.0, rx=6)
        s.text(px + 16, py + 24, title, size=12.5, weight="700")
        s.text(px + 16, py + 41, sub, size=10.5, fill=MUTED)
        x0, x1, base, top = px + 24, px + pw - 24, py + 262, py + 104
        lo, hi = -4.2, 4.2

        def X(v):
            return x0 + (v - lo) / (hi - lo) * (x1 - x0)

        def Y(p):
            return base - p / 0.40 * (base - top)

        grid = [lo + (hi - lo) * i / 240 for i in range(241)]
        mw, mr = -dp / 2.0, dp / 2.0
        # wrong picks with the ISO bar, and the extra wrong picks with the lower PICK bar
        a_iso = [(X(v), Y(pdf(v, mw))) for v in grid if v >= c_iso]
        s.path([(X(c_iso), base)] + a_iso + [(X(hi), base)], fill=BLUE, stroke="none", sw=0, op=0.30, close=True)
        a_extra = [(X(v), Y(pdf(v, mw))) for v in grid if c_pick <= v <= c_iso]
        s.path([(X(c_pick), base)] + a_extra + [(X(c_iso), base)], fill=RED, stroke="none", sw=0, op=0.45, close=True)
        s.path([(X(v), Y(pdf(v, mw))) for v in grid], stroke="#4B5563", sw=2.0)
        s.path([(X(v), Y(pdf(v, mr))) for v in grid], stroke=GREEN, sw=2.0)
        s.line(x0, base, x1, base, stroke="#374151", sw=1.2)
        # bars
        s.line(X(c_iso), top - 30, X(c_iso), base, stroke=BLUE, sw=2.2)
        s.line(X(c_pick), top - 30, X(c_pick), base, stroke=RED, sw=2.2, dash="5,3")
        s.text(X(c_iso) + 5, top - 22, "ISO bar", size=10, weight="700", fill=BLUE)
        s.text(X(c_pick) - 5, top - 22, "lower PICK bar", size=10, weight="700", fill=RED, anchor="end")
        # curve labels
        if dp > 1:
            s.text(X(mw), Y(0.40) - 6, "wrong answers", size=10.5, weight="600", fill="#4B5563", anchor="middle")
            s.text(X(mr), Y(0.40) - 6, "right answers", size=10.5, weight="600", fill=GREEN, anchor="middle")
        else:
            s.text(X(mw) - 96, Y(0.30), "wrong answers", size=10.5, weight="600", fill="#4B5563", anchor="middle")
            s.text(X(mr) + 96, Y(0.30), "right answers", size=10.5, weight="600", fill=GREEN, anchor="middle")
        s.text(x0, base + 16, "looks wrong", size=9.5, fill=MUTED)
        s.text(x1, base + 16, "looks right", size=9.5, fill=MUTED, anchor="end")
        s.text((x0 + x1) / 2, base + 16, "the judge chooses answers to the right of its bar", size=9.5, fill=MUTED, anchor="middle")
        f_iso = 1.0 - phi(c_iso + dp / 2.0)
        f_pick = 1.0 - phi(c_pick + dp / 2.0)
        ly = base + 42
        s.rect(px + 16, ly - 10, 12, 12, fill=BLUE, op=0.30)
        s.text(px + 34, ly, f"Wrong picks with the ISO bar: about {round(f_iso * 100)} in 100", size=11)
        s.rect(px + 16, ly + 10, 12, 12, fill=RED, op=0.45)
        s.text(px + 34, ly + 20, f"Extra wrong picks with the lower bar: about {round((f_pick - f_iso) * 100)} in 100", size=11, weight="700", fill=RED)
        s.text(px + 16, ly + 44, "The bar moves by the same amount in both drawings.", size=10, fill=MUTED)
    return s


def wrap_lines(s, x, y, lines, size=10.5, fill=INK, weight="400", lh=14.5, anchor="start"):
    for i, ln in enumerate(lines):
        s.text(x, y + i * lh, ln, size=size, fill=fill, weight=weight, anchor=anchor)


def fig_fixes(m):
    s = Svg(900, 420)
    s.text(24, 26, "The three fixes we tried", size=14.5, weight="700")
    s.text(24, 44, f"Numbers: claude-haiku-5-5 on 40 hard math problems. Plain PICK gives {m['c7_m1_pick_f']} wrong picks and {m['c7_m1_pick_h']} right picks; ISO gives {m['c7_m1_iso_f']} and {m['c7_m1_iso_h']}.", size=10.5, fill=MUTED)
    cols = [
        ("M1", "Check alone, then pick", GREEN,
         [["Check each answer alone", "(this is ISO, three calls)."],
          ["None accepted: say NONE.", "One accepted: take it."],
          ["Two or more accepted: one", "extra PICK among them."]],
         m["c7_m1_m1_f"], m["c7_m1_m1_h"], ["Works. Same wrong picks as ISO,", "at about 3 times the calls."], "#E7F6F1"),
        ("M2", "Error hunt", ORANGE,
         [["Show all answers together."],
          ["The judge must first look for", "a concrete error in each one."],
          ["It gives a confidence from 1 to 5.", "Keep its pick only at 4 or 5."]],
         m["c7_m2h_g4_f"], m["c7_m2h_g4_h"], ["Too strict. Almost no wrong picks,", "but most right picks are lost."], "#FDF3DC"),
        ("M3", "Known decoy", MUTED,
         [["Add one clearly wrong answer", "from a different problem."],
          ["Show all answers together", "and ask the judge to pick."],
          ["Hope: rejecting the decoy makes", "the judge more careful."]],
         m["c7_m3_f"], m["c7_m3_h"], ["No real help. The judge never picks", "the decoy, but still picks others."], "#F3F4F6"),
    ]
    cw, gap, x0, y0 = 272, 18, 24, 60
    for i, (code, name, col, steps, f, h, verdict, tint) in enumerate(cols):
        x = x0 + i * (cw + gap)
        s.rect(x, y0, cw, 344, fill=PANEL, stroke=GRID, sw=1.0, rx=6)
        s.rect(x, y0, cw, 34, fill=col, rx=6)
        s.text(x + 14, y0 + 22, f"{code}: {name}", size=12.5, weight="700", fill="#FFFFFF")
        y = y0 + 48
        for k, lines in enumerate(steps):
            bh = 46
            s.rect(x + 14, y, cw - 28, bh, fill="#FFFFFF", stroke="#9CA3AF", sw=1.0, rx=5)
            s.circle(x + 30, y + bh / 2, 9, fill=col, stroke="#FFFFFF")
            s.text(x + 30, y + bh / 2 + 4, str(k + 1), size=10.5, weight="700", fill="#FFFFFF", anchor="middle")
            ty = y + (bh / 2 + 4 if len(lines) == 1 else bh / 2 - 3)
            wrap_lines(s, x + 46, ty, lines, size=10.3)
            if k < len(steps) - 1:
                s.line(x + cw / 2, y + bh + 2, x + cw / 2, y + bh + 14, arrow=True)
            y += bh + 16
        ry = y0 + 240
        s.rect(x + 14, ry, cw - 28, 90, fill=tint, stroke=col, sw=1.4, rx=5)
        s.text(x + 26, ry + 20, f"Wrong picks: {f}", size=11, weight="700")
        s.text(x + cw - 26, ry + 20, f"Right picks: {h}", size=11, weight="700", anchor="end")
        s.line(x + 26, ry + 30, x + cw - 26, ry + 30, stroke="#D1D5DB", sw=1.0)
        wrap_lines(s, x + 26, ry + 50, verdict, size=10.8, weight="600")
    s.text(24, 414, "Lower is better for wrong picks (all-wrong pools). Higher is better for right picks (one-right pools).", size=10, fill=MUTED)
    return s


def fig_glance(m):
    groups = [
        ("Claude Haiku on hard math: three checks", [
            ("C4: both methods get three calls", "c4_ta_iso", "c4_ta_maj3"),
            ("C5: judge's own answer removed", "c5o_all_iso2", "c5o_all_pick2"),
            ("C5: judge's first pick removed", "c5w_iso2", "c5w_pick2"),
        ]),
        ("Judges from other companies on hard math (C6)", [
            ("gpt-oss-120b-medium", "c6_gptoss_u_ta_iso", "c6_gptoss_u_ta_pick"),
            ("gemini-3.8-flash-medium", "c6_gemini_u_ta_iso", "c6_gemini_u_ta_pick"),
        ]),
        ("Science ideas (C9, C8)", [
            ("claude-haiku-5-5", "c9_haiku_ta_iso", "c9_haiku_ta_pick"),
            ("gpt-oss-120b-medium", "c9_gptoss_ta_iso", "c9_gptoss_ta_pick"),
            ("gemini-3.8-flash-medium", "c9_gemini_ta_iso", "c9_gemini_ta_pick"),
            ("gemini-3.8-flash-low", "c9_gemlow_ta_iso", "c9_gemlow_ta_pick"),
            ("gemini-4-hydrogen-medium", "c9_hydro_ta_iso", "c9_hydro_ta_pick"),
        ]),
    ]
    row_h, head_h = 27, 30
    n_rows = sum(len(g[1]) for g in groups)
    top = 92
    height = top + n_rows * row_h + len(groups) * head_h + 62
    s = Svg(900, height)
    s.text(24, 26, "The results in one picture: wrong picks on all-wrong pools", size=14.5, weight="700")
    s.text(24, 44, "Each row is one test. Blue dot: ISO (each answer alone). Orange dot: PICK (all answers together). Further right means more wrong picks.", size=10.5, fill=MUTED)
    lx, x0, x1 = 24, 270, 620

    def X(v):
        return x0 + v * (x1 - x0)

    plot_bottom = top + n_rows * row_h + len(groups) * head_h
    for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        s.line(X(t), top - 6, X(t), plot_bottom, stroke=GRID, sw=1.0)
        s.text(X(t), plot_bottom + 16, f"{t:.1f}", size=10, fill="#374151", anchor="middle")
    s.text((x0 + x1) / 2, plot_bottom + 34, "Wrong-pick rate (0 = never, 1 = always)", size=11, weight="600", anchor="middle")
    # legend
    s.circle(x0 + 6, top - 22, 5.5, fill=BLUE)
    s.text(x0 + 16, top - 18, "ISO", size=10.5, weight="700", fill=BLUE)
    s.circle(x0 + 60, top - 22, 5.5, fill=RED)
    s.text(x0 + 70, top - 18, "PICK", size=10.5, weight="700", fill=RED)
    s.text(x1 + 30, top - 18, "ISO", size=10.5, weight="700", fill=BLUE)
    s.text(x1 + 78, top - 18, "PICK", size=10.5, weight="700", fill=RED)
    s.text(x1 + 128, top - 18, "Under PICK", size=10.5, weight="700", fill=INK)

    y = top
    for title, rows in groups:
        s.rect(lx, y, 852, head_h - 8, fill="#F3F4F6", rx=3)
        s.text(lx + 8, y + 15, title, size=11, weight="700")
        y += head_h
        for label, k_iso, k_pick in rows:
            f_iso, f_pick = float(m[k_iso]), float(m[k_pick])
            cy = y + row_h / 2 - 4
            s.text(lx + 8, cy + 4, label, size=10.8)
            worse = f_pick > f_iso + 1e-9
            s.line(X(f_iso), cy, X(f_pick), cy, stroke=RED if worse else "#9CA3AF", sw=3.0)
            s.circle(X(f_iso), cy, 6, fill=BLUE)
            s.circle(X(f_pick), cy, 6, fill=RED)
            s.text(x1 + 30, cy + 4, m[k_iso], size=10.5, fill=BLUE)
            s.text(x1 + 78, cy + 4, m[k_pick], size=10.5, fill=RED)
            diff = f_pick - f_iso
            if abs(diff) < 0.0005:
                note, col = "the same", MUTED
            elif diff > 0:
                note, col = "more wrong picks", RED
            else:
                note, col = "not more", MUTED
            s.text(x1 + 128, cy + 4, note, size=10.5, weight="600", fill=col)
            y += row_h
    s.text(24, height - 8, "Rates only. The text gives the ranges and says which differences could be luck. C6 and the Gemini science rows are the mixed results.", size=10, fill=MUTED)
    return s


def main():
    m = load_macros()
    OUT.mkdir(parents=True, exist_ok=True)
    figs = {
        "figA_two_ways.svg": fig_two_ways(),
        "figB_bar_skill.svg": fig_bar_skill(),
        "figC_fixes.svg": fig_fixes(m),
        "figD_glance.svg": fig_glance(m),
    }
    for name, svg in figs.items():
        (OUT / name).write_text(svg.render(), encoding="utf-8")
        print(f"wrote {name} ({svg.w}x{svg.h})")


if __name__ == "__main__":
    main()
