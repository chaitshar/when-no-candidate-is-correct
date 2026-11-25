#!/usr/bin/env python3
"""Publication-grade pure Python 3.9 stdlib SVG figure generator.

Reads a unified results JSON (supporting both existing
results/sdt_and_subgroups.json and future v2 combined results JSONs)
and generates vector SVG figures into paper/figures/:
  1. fig1_criterion_shift.svg
  2. fig2_sdt_law_curve.svg
  3. fig3_crossvendor_domains.svg
  4. fig4_mitigation_frontier.svg
"""

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

# Okabe-Ito colorblind-safe palette
OKABE_ITO = {
    "blue": "#0072B2",
    "vermilion": "#D55E00",
    "green": "#009E73",
    "purple": "#CC79A7",
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "yellow": "#F0E442",
    "black": "#1F2937",
}

PALETTE_CYCLE = [
    OKABE_ITO["blue"],
    OKABE_ITO["vermilion"],
    OKABE_ITO["green"],
    OKABE_ITO["purple"],
    OKABE_ITO["orange"],
    OKABE_ITO["sky"],
]

FONT_FAMILY = "system-ui, -apple-system, Helvetica, Arial, sans-serif"

INK = "#111827"
AXIS_COLOR = "#374151"
MUTED = "#6B7280"
GRID_COLOR = "#E5E7EB"
BAND_BG = "#F3F4F6"


def norm_cdf(x: float) -> float:
    """Standard normal CDF Phi(x) using math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def sdt_false_alarm(d_prime: float, c: float) -> float:
    """Equal-variance Gaussian SDT false-alarm rate F = 1 - Phi(d'/2 + c)."""
    return 0.5 * math.erfc((0.5 * d_prime + c) / math.sqrt(2.0))


def sanitize_text(text: str) -> str:
    """Ensure zero em/en dashes and safe XML text."""
    cleaned = text.replace("\u2014", " ").replace("\u2013", " to ")
    return escape(cleaned)


class SvgCanvas:
    """Minimal pure-stdlib SVG document builder."""

    def __init__(self, width: float, height: float, status: str = "live") -> None:
        self.width = width
        self.height = height
        self.status = status
        self.elements: List[str] = []
        self.defs: List[str] = []

    def add_def(self, raw_xml: str) -> None:
        self.defs.append(raw_xml)

    def add(self, raw_xml: str) -> None:
        self.elements.append(raw_xml)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "none",
        stroke: str = "none",
        stroke_width: float = 1.0,
        fill_opacity: Optional[float] = None,
        stroke_dasharray: Optional[str] = None,
        rx: float = 0.0,
    ) -> None:
        attrs = [
            f'x="{x:.2f}"',
            f'y="{y:.2f}"',
            f'width="{w:.2f}"',
            f'height="{h:.2f}"',
            f'fill="{fill}"',
        ]
        if fill_opacity is not None:
            attrs.append(f'fill-opacity="{fill_opacity:.3f}"')
        if stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{stroke_width:.2f}"')
        if stroke_dasharray:
            attrs.append(f'stroke-dasharray="{stroke_dasharray}"')
        if rx > 0:
            attrs.append(f'rx="{rx:.2f}"')
        self.add(f"<rect {' '.join(attrs)}/>")

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str = AXIS_COLOR,
        stroke_width: float = 1.0,
        stroke_dasharray: Optional[str] = None,
        stroke_opacity: Optional[float] = None,
        marker_end: Optional[str] = None,
    ) -> None:
        attrs = [
            f'x1="{x1:.2f}"',
            f'y1="{y1:.2f}"',
            f'x2="{x2:.2f}"',
            f'y2="{y2:.2f}"',
            f'stroke="{stroke}"',
            f'stroke-width="{stroke_width:.2f}"',
        ]
        if stroke_dasharray:
            attrs.append(f'stroke-dasharray="{stroke_dasharray}"')
        if stroke_opacity is not None:
            attrs.append(f'stroke-opacity="{stroke_opacity:.3f}"')
        if marker_end:
            attrs.append(f'marker-end="{marker_end}"')
        self.add(f"<line {' '.join(attrs)}/>")

    def polyline(
        self,
        points: Sequence[Tuple[float, float]],
        stroke: str,
        stroke_width: float = 2.0,
        fill: str = "none",
        stroke_dasharray: Optional[str] = None,
        stroke_opacity: Optional[float] = None,
    ) -> None:
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        attrs = [
            f'points="{pts}"',
            f'fill="{fill}"',
            f'stroke="{stroke}"',
            f'stroke-width="{stroke_width:.2f}"',
            'stroke-linecap="round"',
            'stroke-linejoin="round"',
        ]
        if stroke_dasharray:
            attrs.append(f'stroke-dasharray="{stroke_dasharray}"')
        if stroke_opacity is not None:
            attrs.append(f'stroke-opacity="{stroke_opacity:.3f}"')
        self.add(f"<polyline {' '.join(attrs)}/>")

    def polygon(
        self,
        points: Sequence[Tuple[float, float]],
        fill: str,
        fill_opacity: float = 1.0,
        stroke: str = "none",
        stroke_width: float = 1.0,
    ) -> None:
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        attrs = [
            f'points="{pts}"',
            f'fill="{fill}"',
            f'fill-opacity="{fill_opacity:.3f}"',
        ]
        if stroke != "none":
            attrs.append(f'stroke="{stroke}"')
            attrs.append(f'stroke-width="{stroke_width:.2f}"')
        self.add(f"<polygon {' '.join(attrs)}/>")

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: str = OKABE_ITO["blue"],
        stroke: str = "#FFFFFF",
        stroke_width: float = 1.2,
        fill_opacity: float = 1.0,
    ) -> None:
        attrs = [
            f'cx="{cx:.2f}"',
            f'cy="{cy:.2f}"',
            f'r="{r:.2f}"',
            f'fill="{fill}"',
            f'fill-opacity="{fill_opacity:.3f}"',
            f'stroke="{stroke}"',
            f'stroke-width="{stroke_width:.2f}"',
        ]
        self.add(f"<circle {' '.join(attrs)}/>")

    def marker(
        self,
        shape: str,
        cx: float,
        cy: float,
        size: float,
        fill: str,
        stroke: str = "#FFFFFF",
        stroke_width: float = 1.3,
    ) -> None:
        if shape == "circle":
            self.circle(cx, cy, size, fill=fill, stroke=stroke, stroke_width=stroke_width)
        elif shape == "square":
            s = size * 1.65
            self.rect(cx - s / 2, cy - s / 2, s, s, fill=fill, stroke=stroke, stroke_width=stroke_width, rx=1.0)
        elif shape == "diamond":
            r = size * 1.22
            self.polygon(
                [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)],
                fill=fill,
                stroke=stroke,
                stroke_width=stroke_width,
            )
        elif shape == "triangle":
            r = size * 1.25
            self.polygon(
                [(cx, cy - r), (cx + r * 0.92, cy + r * 0.78), (cx - r * 0.92, cy + r * 0.78)],
                fill=fill,
                stroke=stroke,
                stroke_width=stroke_width,
            )
        elif shape == "inv_triangle":
            r = size * 1.25
            self.polygon(
                [(cx, cy + r), (cx + r * 0.92, cy - r * 0.78), (cx - r * 0.92, cy - r * 0.78)],
                fill=fill,
                stroke=stroke,
                stroke_width=stroke_width,
            )
        elif shape == "hexagon":
            r = size * 1.18
            pts = [(cx + r * math.cos(math.radians(60 * k)), cy + r * math.sin(math.radians(60 * k))) for k in range(6)]
            self.polygon(pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        elif shape == "plus":
            r = size * 1.3
            w = size * 0.45
            pts = [
                (cx - w, cy - r), (cx + w, cy - r), (cx + w, cy - w), (cx + r, cy - w),
                (cx + r, cy + w), (cx + w, cy + w), (cx + w, cy + r), (cx - w, cy + r),
                (cx - w, cy + w), (cx - r, cy + w), (cx - r, cy - w), (cx - w, cy - w),
            ]
            self.polygon(pts, fill=fill, stroke=stroke, stroke_width=stroke_width)
        else:
            self.circle(cx, cy, size, fill=fill, stroke=stroke, stroke_width=stroke_width)

    def text(
        self,
        x: float,
        y: float,
        content: str,
        size: float = 11.0,
        weight: str = "400",
        fill: str = INK,
        anchor: str = "start",
        baseline: str = "alphabetic",
        transform: Optional[str] = None,
        style_extra: Optional[str] = None,
    ) -> None:
        attrs = [
            f'x="{x:.2f}"',
            f'y="{y:.2f}"',
            f'font-size="{size:.1f}"',
            f'font-weight="{weight}"',
            f'fill="{fill}"',
            f'text-anchor="{anchor}"',
            f'dominant-baseline="{baseline}"',
        ]
        if transform:
            attrs.append(f'transform="{transform}"')
        if style_extra:
            attrs.append(f'style="{style_extra}"')
        self.add(f"<text {' '.join(attrs)}>{sanitize_text(content)}</text>")

    def render(self) -> str:
        defs_block = ""
        if self.defs:
            defs_block = "<defs>\n  " + "\n  ".join(self.defs) + "\n</defs>\n"
        style_block = (
            "<style>\n"
            f"  text {{ font-family: {FONT_FAMILY}; }}\n"
            "  .num { font-variant-numeric: tabular-nums; }\n"
            "</style>\n"
        )
        header = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width:.0f}" height="{self.height:.0f}" '
            f'viewBox="0 0 {self.width:.0f} {self.height:.0f}" '
            f'data-status="{escape(self.status)}">\n'
        )
        bg = f'<rect x="0" y="0" width="{self.width:.0f}" height="{self.height:.0f}" fill="#FFFFFF"/>\n'
        body = "\n".join(self.elements)
        return header + style_block + defs_block + bg + body + "\n</svg>\n"


def format_judge_label(key: str) -> Tuple[str, str, str]:
    """Return (display_label, family_key, cohort_tag) for a judge key."""
    low = key.lower().strip()
    cohort = ""
    if low.endswith("_prereg"):
        cohort = "Prereg"
        base = key[:-7]
    elif low.endswith("_corrected"):
        cohort = "Corrected"
        base = key[:-10]
    else:
        base = key

    b_low = base.lower()
    if "haiku" in b_low:
        fam = "anthropic_haiku"
        name = "Claude Haiku"
    elif "sonnet" in b_low:
        fam = "anthropic_sonnet"
        name = "Claude Sonnet"
    elif "opus" in b_low:
        fam = "anthropic_opus"
        name = "Claude Opus"
    elif "hydrogen" in b_low:
        fam = "google_hydrogen"
        name = "gemini-4-hydrogen"
    elif "gemini_low" in b_low or "gemini-low" in b_low or "3.8-flash-low" in b_low:
        fam = "google_flash_low"
        name = "gemini-3.8-flash (low)"
    elif "gemini-3.8" in b_low or "gemini_3.8" in b_low or "flash" in b_low or b_low == "gemini":
        fam = "google_flash"
        name = "gemini-3.8-flash"
    elif "gemini" in b_low:
        fam = "google_gemini"
        name = base.replace("_", " ")
    elif "gpt-oss" in b_low or "gpt_oss" in b_low or b_low == "gptoss":
        fam = "gpt_oss"
        name = "gpt-oss-120b"
    elif "gpt" in b_low:
        fam = "openai"
        name = base.replace("_", " ")
    else:
        fam = b_low
        name = base.replace("_", " ")

    display = f"{name} ({cohort})" if cohort else name
    return display, fam, cohort


def linear_scale(val: float, d0: float, d1: float, r0: float, r1: float) -> float:
    if d1 == d0:
        return 0.5 * (r0 + r1)
    return r0 + (val - d0) / (d1 - d0) * (r1 - r0)


def nice_ticks(vmin: float, vmax: float, step: float) -> List[float]:
    ticks: List[float] = []
    start = math.ceil(vmin / step - 1e-9) * step
    cur = start
    while cur <= vmax + 1e-9:
        ticks.append(round(cur, 6))
        cur += step
    return ticks


def _extract_sdt_blocks(data: Dict[str, Any]) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Collect (domain, judge_key, stratum_dict) from v1 or v2 JSON structures."""
    blocks: List[Tuple[str, str, Dict[str, Any]]] = []

    sdt_root = data.get("sdt_aligned") or data.get("sdt") or {}
    if isinstance(sdt_root, dict):
        for jkey, jval in sdt_root.items():
            if not isinstance(jval, dict):
                continue
            # Case A: jval directly holds UNSOLVED / SOLVED
            if "UNSOLVED" in jval or "SOLVED" in jval:
                blocks.append(("Math", jkey, jval))
            else:
                # Case B: jval holds domain subdicts (e.g. Math, ResearchBench)
                for dkey, dval in jval.items():
                    if isinstance(dval, dict) and ("UNSOLVED" in dval or "SOLVED" in dval):
                        dom = "ResearchBench" if "research" in dkey.lower() or "science" in dkey.lower() else dkey.title()
                        blocks.append((dom, jkey, dval))

    # Optional separate domain SDT sections in future v2 combined JSONs
    for alt_key, dom_label in (
        ("sdt_researchbench", "ResearchBench"),
        ("researchbench_sdt", "ResearchBench"),
        ("sdt_math", "Math"),
    ):
        alt = data.get(alt_key)
        if isinstance(alt, dict):
            for jkey, jval in alt.items():
                if isinstance(jval, dict) and ("UNSOLVED" in jval or "SOLVED" in jval):
                    blocks.append((dom_label, jkey, jval))

    return blocks


# ---------------------------------------------------------------------------
# Figure 1: Forest Plot of Paired delta c (PICK minus ISO)
# ---------------------------------------------------------------------------


def build_fig1_criterion_shift(data: Dict[str, Any]) -> Tuple[SvgCanvas, str]:
    blocks = _extract_sdt_blocks(data)
    rows: List[Dict[str, Any]] = []

    for domain, jkey, strata_map in blocks:
        display_judge, fam, cohort = format_judge_label(jkey)
        for stratum in ("UNSOLVED", "SOLVED"):
            sdata = strata_map.get(stratum)
            if not isinstance(sdata, dict):
                continue
            diffs = sdata.get("diffs", {})
            pm = diffs.get("PICK_minus_ISO")
            if not isinstance(pm, dict):
                continue
            c_diff = pm.get("c_diff")
            ci = pm.get("c_diff_ci95")
            n = pm.get("n")
            if c_diff is None or not (isinstance(ci, list) and len(ci) == 2):
                continue
            rows.append(
                {
                    "domain": domain,
                    "judge_key": jkey,
                    "judge_label": display_judge,
                    "family": fam,
                    "cohort": cohort,
                    "stratum": stratum,
                    "n": n,
                    "c_diff": float(c_diff),
                    "ci_lo": float(ci[0]),
                    "ci_hi": float(ci[1]),
                }
            )

    if not rows:
        canvas = render_placeholder(
            title="Figure 1: Criterion Shift (PICK minus ISO)",
            subtitle="No paired delta c entries found in input JSON.",
            note="Expected sdt_aligned.<judge>.<UNSOLVED|SOLVED>.diffs.PICK_minus_ISO",
        )
        return canvas, "placeholder (no SDT diff rows)"

    has_multiple_domains = len({r["domain"] for r in rows}) > 1

    # Layout dimensions
    width = 860.0
    margin_top = 82.0
    margin_bottom = 66.0
    left_label_w = 248.0
    right_num_w = 178.0
    plot_x0 = left_label_w
    plot_x1 = width - right_num_w
    plot_w = plot_x1 - plot_x0

    row_h = 30.0
    group_gap = 10.0

    # Group rows by (domain, judge_key) so UNSOLVED & SOLVED stay paired
    grouped: List[List[Dict[str, Any]]] = []
    cur_group: List[Dict[str, Any]] = []
    last_key: Optional[Tuple[str, str]] = None
    for r in rows:
        gk = (r["domain"], r["judge_key"])
        if last_key is not None and gk != last_key:
            grouped.append(cur_group)
            cur_group = []
        cur_group.append(r)
        last_key = gk
    if cur_group:
        grouped.append(cur_group)

    total_rows = sum(len(g) for g in grouped)
    total_gaps = max(0, len(grouped) - 1) * group_gap
    plot_h = total_rows * row_h + total_gaps + 14.0
    height = margin_top + plot_h + margin_bottom

    # X-axis range
    min_ci = min(r["ci_lo"] for r in rows)
    max_ci = max(r["ci_hi"] for r in rows)
    xmin = min(-1.10, math.floor(min_ci * 10.0) / 10.0 - 0.05)
    xmax = max(0.15, math.ceil(max_ci * 10.0) / 10.0 + 0.05)

    def x_px(val: float) -> float:
        return linear_scale(val, xmin, xmax, plot_x0, plot_x1)

    canvas = SvgCanvas(width, height, status="live")

    # Title and subtitle
    canvas.text(24.0, 28.0, "How Much the Judge Lowers Its Bar Under PICK: Change in the Bar, delta c (PICK minus ISO)", size=14.5, weight="700", fill=INK)
    canvas.text(
        24.0,
        46.0,
        "Below zero means the judge chooses more easily under PICK; lines show 95% ranges",
        size=10.5,
        fill=MUTED,
    )

    # Legend at top right of plot header
    leg_y = 66.0
    lx = plot_x0
    canvas.circle(lx + 6, leg_y - 3, 4.5, fill=OKABE_ITO["vermilion"], stroke="#FFFFFF", stroke_width=1.0)
    canvas.text(lx + 15, leg_y, "HARD", size=10.5, weight="600", fill=INK)
    canvas.marker("square", lx + 66, leg_y - 3, 4.4, fill=OKABE_ITO["blue"], stroke="#FFFFFF", stroke_width=1.0)
    canvas.text(lx + 75, leg_y, "EASY", size=10.5, weight="600", fill=INK)
    canvas.rect(lx + 128, leg_y - 9, 14, 11, fill=OKABE_ITO["sky"], fill_opacity=0.22, stroke=OKABE_ITO["sky"], stroke_width=0.7)
    v1_dcs = [r["c_diff"] for r in rows if r["cohort"]] or [r["c_diff"] for r in rows]
    band_lo, band_hi = min(v1_dcs), max(v1_dcs)
    canvas.text(lx + 147, leg_y, f"Range of the first-study values [{band_lo:.2f}, {band_hi:.2f}]", size=10.5, fill=INK)

    # Column headers
    hdr_y = margin_top - 6.0
    canvas.text(24.0, hdr_y, "Judge / Problems", size=10.0, weight="700", fill=AXIS_COLOR)
    canvas.text(width - 20.0, hdr_y, "delta c [95% CI]", size=10.0, weight="700", fill=AXIS_COLOR, anchor="end")

    plot_y0 = margin_top
    plot_y1 = margin_top + plot_h

    # Plot frame background and the range of the v1 point estimates
    canvas.rect(plot_x0, plot_y0, plot_w, plot_h, fill="#FFFFFF", stroke=GRID_COLOR, stroke_width=1.0)
    bx0 = x_px(band_lo)
    bx1 = x_px(band_hi)
    canvas.rect(bx0, plot_y0, bx1 - bx0, plot_h, fill=OKABE_ITO["sky"], fill_opacity=0.14)
    canvas.line(bx0, plot_y0, bx0, plot_y1, stroke=OKABE_ITO["sky"], stroke_width=0.9, stroke_dasharray="2,3")
    canvas.line(bx1, plot_y0, bx1, plot_y1, stroke=OKABE_ITO["sky"], stroke_width=0.9, stroke_dasharray="2,3")

    # Gridlines and x-axis ticks
    ticks = nice_ticks(xmin, xmax, 0.2)
    for t in ticks:
        tx = x_px(t)
        if abs(t) < 1e-9:
            continue
        canvas.line(tx, plot_y0, tx, plot_y1, stroke=GRID_COLOR, stroke_width=0.8)
        canvas.line(tx, plot_y1, tx, plot_y1 + 4.5, stroke=AXIS_COLOR, stroke_width=1.0)
        canvas.text(tx, plot_y1 + 17.0, f"{t:+.1f}" if t != 0 else "0", size=10.0, fill=AXIS_COLOR, anchor="middle", style_extra="font-variant-numeric: tabular-nums;")

    # Reference line at delta c = 0
    x_zero = x_px(0.0)
    canvas.line(x_zero, plot_y0, x_zero, plot_y1, stroke=AXIS_COLOR, stroke_width=1.3, stroke_dasharray="4,3")
    canvas.line(x_zero, plot_y1, x_zero, plot_y1 + 4.5, stroke=AXIS_COLOR, stroke_width=1.2)
    canvas.text(x_zero, plot_y1 + 17.0, "0.0", size=10.0, weight="700", fill=INK, anchor="middle")

    # Bottom axis line & title
    canvas.line(plot_x0, plot_y1, plot_x1, plot_y1, stroke=AXIS_COLOR, stroke_width=1.2)
    canvas.text(0.5 * (plot_x0 + plot_x1), plot_y1 + 38.0, "Change in the bar, delta c (PICK minus ISO)", size=11.5, weight="600", fill=INK, anchor="middle")

    # Draw rows
    cur_y = plot_y0 + 7.0 + row_h * 0.5
    for g_idx, grp in enumerate(grouped):
        if g_idx > 0:
            sep_y = cur_y - row_h * 0.5 - group_gap * 0.5
            canvas.line(24.0, sep_y, width - 20.0, sep_y, stroke="#E5E7EB", stroke_width=0.9)

        for r_idx, r in enumerate(grp):
            # Subtle alternating row band
            if (g_idx + r_idx) % 2 == 1:
                canvas.rect(plot_x0 + 0.5, cur_y - row_h * 0.48, plot_w - 1.0, row_h * 0.96, fill=BAND_BG, fill_opacity=0.55)

            is_unsolved = r["stratum"] == "UNSOLVED"
            color = OKABE_ITO["vermilion"] if is_unsolved else OKABE_ITO["blue"]
            shape = "circle" if is_unsolved else "square"
            if has_multiple_domains and "research" in r["domain"].lower():
                shape = "diamond" if is_unsolved else "triangle"

            # Left label
            n_str = f"n={r['n']}" if r["n"] is not None else ""
            # ResearchBench pools are not stratified by solvability
            strat_lbl = "ALL POOLS" if "research" in r["domain"].lower() else {"UNSOLVED": "HARD", "SOLVED": "EASY"}.get(r["stratum"], r["stratum"])
            dom_prefix = f"{r['domain'].replace('ResearchBench', 'Science')} | " if has_multiple_domains else ""
            if r_idx == 0:
                canvas.text(24.0, cur_y - 3.5, f"{dom_prefix}{r['judge_label']}", size=10.5, weight="600", fill=INK, baseline="middle")
                canvas.text(24.0, cur_y + 9.0, f"  {strat_lbl} ({n_str})" if n_str else f"  {strat_lbl}", size=9.5, fill=color, weight="600", baseline="middle")
            else:
                canvas.text(24.0, cur_y, f"  {strat_lbl} ({n_str})" if n_str else f"  {strat_lbl}", size=9.5, fill=color, weight="600", baseline="middle")

            # CI bar and caps
            x_lo = x_px(r["ci_lo"])
            x_hi = x_px(r["ci_hi"])
            x_pt = x_px(r["c_diff"])
            canvas.line(x_lo, cur_y, x_hi, cur_y, stroke=color, stroke_width=2.1)
            canvas.line(x_lo, cur_y - 4.5, x_lo, cur_y + 4.5, stroke=color, stroke_width=1.6)
            canvas.line(x_hi, cur_y - 4.5, x_hi, cur_y + 4.5, stroke=color, stroke_width=1.6)

            # Central marker
            canvas.marker(shape, x_pt, cur_y, 4.6, fill=color, stroke="#FFFFFF", stroke_width=1.2)

            # Right numeric readout
            num_txt = f"{r['c_diff']:+.3f} [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]"
            canvas.text(width - 20.0, cur_y, num_txt, size=10.0, weight="500", fill=INK, anchor="end", baseline="middle", style_extra="font-variant-numeric: tabular-nums;")

            cur_y += row_h
        cur_y += group_gap

    return canvas, f"live ({len(rows)} judge x stratum cells)"


# ---------------------------------------------------------------------------
# Figure 2: SDT Criterion-Shift Law Curve
# ---------------------------------------------------------------------------


def _place_labels_greedy(
    anchors: List[Dict[str, Any]],
    bounds: Tuple[float, float, float, float],
    char_w: float = 5.4,
    box_h: float = 13.0,
) -> List[Tuple[float, float, str]]:
    """Choose non-overlapping (lx, ly, text_anchor) for point labels."""
    bx0, by0, bx1, by1 = bounds
    placed: List[Tuple[float, float, float, float]] = []

    # Reserve anchor circles as small occupied boxes so labels don't cover dots
    for a in anchors:
        px, py = a["px"], a["py"]
        placed.append((px - 5.0, py - 5.0, px + 5.0, py + 5.0))

    candidate_offsets = [
        (9.0, -7.0, "start"),
        (9.0, 11.0, "start"),
        (-9.0, -7.0, "end"),
        (-9.0, 11.0, "end"),
        (0.0, -13.0, "middle"),
        (0.0, 16.0, "middle"),
        (16.0, -14.0, "start"),
        (-16.0, -14.0, "end"),
        (16.0, 18.0, "start"),
        (-16.0, 18.0, "end"),
        (24.0, 2.0, "start"),
        (-24.0, 2.0, "end"),
        (0.0, -24.0, "middle"),
        (0.0, 26.0, "middle"),
    ]

    results: List[Tuple[float, float, str]] = []
    for a in anchors:
        px, py = a["px"], a["py"]
        txt = a["label"]
        tw = max(24.0, len(txt) * char_w)
        best_pos: Optional[Tuple[float, float, str]] = None
        best_overlap = 1e18

        for dx, dy, t_anchor in candidate_offsets:
            lx = px + dx
            ly = py + dy
            if t_anchor == "start":
                x0, x1 = lx, lx + tw
            elif t_anchor == "end":
                x0, x1 = lx - tw, lx
            else:
                x0, x1 = lx - 0.5 * tw, lx + 0.5 * tw
            y0, y1 = ly - box_h * 0.78, ly + box_h * 0.28

            # Compute penalty for out-of-bounds and overlaps
            pen = 0.0
            if x0 < bx0 + 2:
                pen += (bx0 + 2 - x0) * 40.0
            if x1 > bx1 - 2:
                pen += (x1 - (bx1 - 2)) * 40.0
            if y0 < by0 + 2:
                pen += (by0 + 2 - y0) * 40.0
            if y1 > by1 - 2:
                pen += (y1 - (by1 - 2)) * 40.0

            for ox0, oy0, ox1, oy1 in placed:
                ix = max(0.0, min(x1, ox1) - max(x0, ox0))
                iy = max(0.0, min(y1, oy1) - max(y0, oy0))
                if ix > 0 and iy > 0:
                    pen += ix * iy + 120.0

            if pen < best_overlap:
                best_overlap = pen
                best_pos = (lx, ly, t_anchor)
                best_box = (x0, y0, x1, y1)
                if pen == 0.0:
                    break

        assert best_pos is not None
        placed.append(best_box)
        results.append(best_pos)

    return results


def build_fig2_sdt_law_curve(data: Dict[str, Any]) -> Tuple[SvgCanvas, str]:
    blocks = _extract_sdt_blocks(data)
    points: List[Dict[str, Any]] = []
    delta_cs: List[float] = []
    iso_cs: List[float] = []
    all_delta_cs: List[float] = []
    all_iso_cs: List[float] = []

    for domain, jkey, strata_map in blocks:
        display_judge, fam, cohort = format_judge_label(jkey)
        if not cohort and fam == "anthropic_haiku":
            display_judge = "Claude Haiku (v2 science)"
        short_judge = display_judge.replace("Claude ", "").replace("Prereg", "P").replace("Corrected", "C")
        for stratum in ("UNSOLVED", "SOLVED"):
            sdata = strata_map.get(stratum)
            if not isinstance(sdata, dict):
                continue
            iso = sdata.get("ISO")
            pick = sdata.get("PICK")
            if not (isinstance(iso, dict) and isinstance(pick, dict)):
                continue
            if iso.get("d_prime") is None or pick.get("d_prime") is None:
                continue

            iso_f = iso.get("F_raw", iso.get("F_adj"))
            pick_f = pick.get("F_raw", pick.get("F_adj"))
            if iso_f is None or pick_f is None:
                continue

            diffs = sdata.get("diffs", {})
            pm = diffs.get("PICK_minus_ISO", {})
            dc_val = float(pm["c_diff"]) if pm.get("c_diff") is not None else float(pick["c"]) - float(iso["c"])
            all_iso_cs.append(float(iso["c"]))
            all_delta_cs.append(dc_val)
            if cohort:
                # v1 cells (Prereg / Corrected cohorts) define the reference curves
                iso_cs.append(float(iso["c"]))
                delta_cs.append(dc_val)

            points.append(
                {
                    "domain": domain,
                    "judge_key": jkey,
                    "judge_label": display_judge,
                    "short_judge": short_judge,
                    "family": fam,
                    "cohort": cohort,
                    "stratum": stratum,
                    "iso_dp": float(iso["d_prime"]),
                    "iso_c": float(iso["c"]),
                    "iso_f": float(iso_f),
                    "pick_dp": float(pick["d_prime"]),
                    "pick_c": float(pick["c"]),
                    "pick_f": float(pick_f),
                }
            )

    if not points:
        canvas = render_placeholder(
            title="Figure 2: SDT Criterion-Shift Law",
            subtitle="No paired ISO/PICK SDT points found in input JSON.",
            note="Expected sdt_aligned.<judge>.<UNSOLVED|SOLVED>.<ISO|PICK>",
        )
        return canvas, "placeholder (no SDT curve points)"

    if not iso_cs:
        iso_cs, delta_cs = all_iso_cs, all_delta_cs
    c_iso_mean = sum(iso_cs) / len(iso_cs)
    delta_c_mean = sum(delta_cs) / len(delta_cs)
    dc_lo, dc_hi = min(delta_cs), max(delta_cs)
    c_pick_pred = c_iso_mean + delta_c_mean

    # Canvas geometry
    width = 880.0
    height = 540.0
    margin_left = 74.0
    margin_right = 32.0
    margin_top = 82.0
    margin_bottom = 66.0
    plot_x0 = margin_left
    plot_x1 = width - margin_right
    plot_y0 = margin_top
    plot_y1 = height - margin_bottom
    plot_w = plot_x1 - plot_x0
    plot_h = plot_y1 - plot_y0

    dp_min, dp_max = -1.5, 4.0
    f_min, f_max = 0.0, 0.85

    def x_px(dp: float) -> float:
        return linear_scale(dp, dp_min, dp_max, plot_x0, plot_x1)

    def y_px(f: float) -> float:
        return linear_scale(f, f_min, f_max, plot_y1, plot_y0)

    canvas = SvgCanvas(width, height, status="live")

    # Title and subtitle
    canvas.text(
        24.0,
        28.0,
        "A Lower Bar Hurts Most Where Skill Is Low: Wrong-Pick Rate F = 1 minus Phi(d'/2 + c)",
        size=14.0,
        weight="700",
        fill=INK,
    )
    canvas.text(
        24.0,
        46.0,
        f"Blue curve: ISO (first-study mean bar c = {c_iso_mean:+.3f}). Orange curve: PICK with the bar lowered by {abs(delta_c_mean):.3f} (c = {c_pick_pred:+.3f})",
        size=10.5,
        fill=MUTED,
    )

    # Shaded regime bands: UNSOLVED (steep) and SOLVED (tail)
    unsolved_dps = [p["iso_dp"] for p in points if p["stratum"] == "UNSOLVED"] + [p["pick_dp"] for p in points if p["stratum"] == "UNSOLVED"]
    solved_dps = [p["iso_dp"] for p in points if p["stratum"] == "SOLVED"] + [p["pick_dp"] for p in points if p["stratum"] == "SOLVED"]
    if unsolved_dps:
        u0 = max(dp_min, min(unsolved_dps) - 0.14)
        u1 = min(dp_max, max(unsolved_dps) + 0.14)
        canvas.rect(x_px(u0), plot_y0, x_px(u1) - x_px(u0), plot_h, fill=OKABE_ITO["orange"], fill_opacity=0.07)
        canvas.text(x_px(-0.25), plot_y0 + 16.0, "HARD problems", size=9.5, weight="700", fill="#9A5B00", anchor="middle")
        canvas.text(x_px(-0.25), plot_y0 + 28.0, "(steep part)", size=8.8, fill="#9A5B00", anchor="middle")
    if solved_dps:
        s0 = max(dp_min, min(solved_dps) - 0.15)
        s1 = min(dp_max, max(solved_dps) + 0.15)
        canvas.rect(x_px(s0), plot_y0, x_px(s1) - x_px(s0), plot_h, fill=OKABE_ITO["green"], fill_opacity=0.06)
        canvas.text(x_px(1.50), plot_y0 + 16.0, "EASY problems", size=9.5, weight="700", fill="#006B4E", anchor="middle")
        canvas.text(x_px(1.50), plot_y0 + 28.0, "(flat part)", size=8.8, fill="#006B4E", anchor="middle")

    # Gridlines & axes
    for xt in nice_ticks(dp_min, dp_max, 0.5):
        xp = x_px(xt)
        canvas.line(xp, plot_y0, xp, plot_y1, stroke=GRID_COLOR, stroke_width=0.8)
        canvas.line(xp, plot_y1, xp, plot_y1 + 4.5, stroke=AXIS_COLOR, stroke_width=1.0)
        canvas.text(xp, plot_y1 + 17.0, f"{xt:.1f}", size=10.0, fill=AXIS_COLOR, anchor="middle")

    for yt in nice_ticks(f_min, f_max, 0.1):
        yp = y_px(yt)
        canvas.line(plot_x0, yp, plot_x1, yp, stroke=GRID_COLOR, stroke_width=0.8)
        canvas.line(plot_x0 - 4.5, yp, plot_x0, yp, stroke=AXIS_COLOR, stroke_width=1.0)
        canvas.text(plot_x0 - 9.0, yp, f"{yt:.1f}", size=10.0, fill=AXIS_COLOR, anchor="end", baseline="middle")

    canvas.rect(plot_x0, plot_y0, plot_w, plot_h, fill="none", stroke=AXIS_COLOR, stroke_width=1.2)

    # Axis labels
    canvas.text(0.5 * (plot_x0 + plot_x1), plot_y1 + 42.0, "Skill d' (how well the judge tells right from wrong)", size=11.5, weight="600", fill=INK, anchor="middle")
    canvas.text(
        22.0,
        0.5 * (plot_y0 + plot_y1),
        "Wrong-pick rate F on all-wrong pools",
        size=11.5,
        weight="600",
        fill=INK,
        anchor="middle",
        transform=f"rotate(-90 22.0 {0.5 * (plot_y0 + plot_y1):.2f})",
    )

    # Theoretical curves across d' in [-0.5, 4.0]
    n_grid = 180
    dp_grid = [dp_min + (dp_max - dp_min) * i / n_grid for i in range(n_grid + 1)]

    # Shaded band around the shifted PICK curve: the range of the v1 delta c point estimates
    upper_pts = [(x_px(d), y_px(sdt_false_alarm(d, c_iso_mean + dc_lo))) for d in dp_grid]
    lower_pts = [(x_px(d), y_px(sdt_false_alarm(d, c_iso_mean + dc_hi))) for d in reversed(dp_grid)]
    canvas.polygon(upper_pts + lower_pts, fill=OKABE_ITO["vermilion"], fill_opacity=0.13)

    iso_curve = [(x_px(d), y_px(sdt_false_alarm(d, c_iso_mean))) for d in dp_grid]
    pick_curve = [(x_px(d), y_px(sdt_false_alarm(d, c_pick_pred))) for d in dp_grid]

    canvas.polyline(iso_curve, stroke=OKABE_ITO["blue"], stroke_width=2.4)
    canvas.polyline(pick_curve, stroke=OKABE_ITO["vermilion"], stroke_width=2.4)

    # Direct curve labels placed where curves are well separated and clear of the legend box
    lbl_dp_iso = 1.35
    canvas.text(
        x_px(lbl_dp_iso) - 6.0,
        y_px(sdt_false_alarm(lbl_dp_iso, c_iso_mean)) + 16.0,
        f"ISO curve (c={c_iso_mean:+.2f})",
        size=10.0,
        weight="700",
        fill=OKABE_ITO["blue"],
        anchor="end",
    )
    lbl_dp_pick = 0.85
    canvas.text(
        x_px(lbl_dp_pick) + 8.0,
        y_px(sdt_false_alarm(lbl_dp_pick, c_pick_pred)) - 12.0,
        f"PICK curve (c={c_pick_pred:+.2f})",
        size=10.0,
        weight="700",
        fill=OKABE_ITO["vermilion"],
        anchor="start",
    )

    # Determine marker shapes per judge
    unique_judges: List[str] = []
    for p in points:
        if p["judge_label"] not in unique_judges:
            unique_judges.append(p["judge_label"])
    # One shape per model; hollow marks the v1 corrected cohort; the v2 Haiku run gets its own shape
    family_shape = {
        "anthropic_haiku": "circle",
        "anthropic_sonnet": "square",
        "gpt_oss": "inv_triangle",
        "google_flash": "diamond",
        "google_flash_low": "triangle",
        "google_hydrogen": "hexagon",
    }
    judge_shape: Dict[str, str] = {}
    for p in points:
        if p["judge_label"] in judge_shape:
            continue
        if p["judge_label"].startswith("Claude Haiku (v2"):
            judge_shape[p["judge_label"]] = "plus"
        else:
            judge_shape[p["judge_label"]] = family_shape.get(p["family"], "circle")
    assert len({(judge_shape[j], "(Corrected)" in j) for j in unique_judges}) == len(unique_judges), "legend markers must be unique"

    # Paired ISO -> PICK connector lines
    for p in points:
        canvas.line(
            x_px(p["iso_dp"]),
            y_px(p["iso_f"]),
            x_px(p["pick_dp"]),
            y_px(p["pick_f"]),
            stroke="#9CA3AF",
            stroke_width=1.0,
            stroke_dasharray="2,2",
        )

    # Empirical points & label anchors
    label_anchors: List[Dict[str, Any]] = []
    for p in points:
        shp = judge_shape[p["judge_label"]]
        is_corr = p["cohort"] == "Corrected"

        ix, iy = x_px(p["iso_dp"]), y_px(p["iso_f"])
        px, py = x_px(p["pick_dp"]), y_px(p["pick_f"])

        if is_corr:
            canvas.marker(shp, ix, iy, 4.4, fill="#FFFFFF", stroke=OKABE_ITO["blue"], stroke_width=1.8)
            canvas.marker(shp, px, py, 4.4, fill="#FFFFFF", stroke=OKABE_ITO["vermilion"], stroke_width=1.8)
        else:
            canvas.marker(shp, ix, iy, 4.8, fill=OKABE_ITO["blue"], stroke="#FFFFFF", stroke_width=1.1)
            canvas.marker(shp, px, py, 4.8, fill=OKABE_ITO["vermilion"], stroke="#FFFFFF", stroke_width=1.1)

        # Label primary (non-corrected) points or all distinct families cleanly to keep plot legible
        if False:  # point labels removed for legibility; the legend encodes judge and arm
            tag = p["short_judge"].replace(" (P)", "")
            label_anchors.append({"px": ix, "py": iy, "label": f"{tag} ISO", "color": OKABE_ITO["blue"]})
            label_anchors.append({"px": px, "py": py, "label": f"{tag} PICK", "color": OKABE_ITO["vermilion"]})

    placed_labels = _place_labels_greedy(label_anchors, (plot_x0, plot_y0, plot_x1, plot_y1))
    for anchor_info, (lx, ly, t_anchor) in zip(label_anchors, placed_labels):
        # Short leader line when label offset is larger than 13px
        dist = math.hypot(lx - anchor_info["px"], ly - anchor_info["py"])
        if dist > 14.0:
            canvas.line(anchor_info["px"], anchor_info["py"], lx, ly - 3.0, stroke="#D1D5DB", stroke_width=0.7)
        canvas.text(lx, ly, anchor_info["label"], size=8.8, weight="600", fill=anchor_info["color"], anchor=t_anchor)

    # Legend box at top-right inside plot area (in empty upper-right tail space)
    leg_w = 248.0
    leg_h = 26.0 + 18.0 * len(unique_judges) + 22.0
    leg_x = plot_x1 - leg_w - 10.0
    leg_y = plot_y0 + 8.0
    canvas.rect(leg_x, leg_y, leg_w, leg_h, fill="#FFFFFF", fill_opacity=0.94, stroke=GRID_COLOR, stroke_width=1.0, rx=4.0)

    canvas.text(leg_x + 10.0, leg_y + 15.0, "Legend (colour = arm, shape = judge)", size=9.5, weight="700", fill=INK)
    canvas.line(leg_x + 10.0, leg_y + 28.0, leg_x + 26.0, leg_y + 28.0, stroke=OKABE_ITO["blue"], stroke_width=2.4)
    canvas.text(leg_x + 31.0, leg_y + 31.0, "ISO", size=9.2, weight="600", fill=OKABE_ITO["blue"])
    canvas.line(leg_x + 68.0, leg_y + 28.0, leg_x + 84.0, leg_y + 28.0, stroke=OKABE_ITO["vermilion"], stroke_width=2.4)
    canvas.text(leg_x + 89.0, leg_y + 31.0, "PICK", size=9.2, weight="600", fill=OKABE_ITO["vermilion"])
    canvas.rect(leg_x + 128.0, leg_y + 22.0, 14.0, 10.0, fill=OKABE_ITO["vermilion"], fill_opacity=0.16, stroke=OKABE_ITO["vermilion"], stroke_width=0.6)
    canvas.text(leg_x + 146.0, leg_y + 31.0, f"first-study range", size=8.8, fill=MUTED)

    cy = leg_y + 49.0
    for jlabel in unique_judges:
        shp = judge_shape[jlabel]
        is_corr = "(Corrected)" in jlabel
        if is_corr:
            canvas.marker(shp, leg_x + 18.0, cy - 3.0, 4.0, fill="#FFFFFF", stroke=INK, stroke_width=1.5)
        else:
            canvas.marker(shp, leg_x + 18.0, cy - 3.0, 4.2, fill=INK, stroke="#FFFFFF", stroke_width=0.9)
        canvas.text(leg_x + 30.0, cy, jlabel, size=9.2, fill=INK)
        cy += 17.5

    return canvas, f"live ({len(points)} judge x stratum pairs)"


# ---------------------------------------------------------------------------
# Figure 3: Cross-Vendor & Multi-Domain Grouped Bar Chart
# ---------------------------------------------------------------------------


def _extract_domain_panel(raw_panel: Any) -> List[Dict[str, Any]]:
    """Normalize a domain panel dict into list of judge records."""
    records: List[Dict[str, Any]] = []
    if not isinstance(raw_panel, dict):
        return records
    for jkey, jval in raw_panel.items():
        if not isinstance(jval, dict):
            continue
        arms: Dict[str, Tuple[float, float, float, bool]] = {}
        for arm_name, aliases in (
            ("ISO", ("ISO", "ISO_any", "iso", "iso_any")),
            ("EACH", ("EACH", "each")),
            ("PICK", ("PICK", "pick")),
        ):
            for ak in aliases:
                if ak in jval and isinstance(jval[ak], dict):
                    ad = jval[ak]
                    val = ad.get("rate", ad.get("fa", ad.get("F_raw", ad.get("F"))))
                    ci = ad.get("ci95", ad.get("fa_ci95", ad.get("F_ci95")))
                    if val is not None:
                        v = float(val)
                        has_ci = isinstance(ci, list) and len(ci) == 2
                        lo, hi = (float(ci[0]), float(ci[1])) if has_ci else (v, v)
                        arms[arm_name] = (v, lo, hi, has_ci)
                    break
        if arms:
            display, _, _ = format_judge_label(jkey)
            records.append({"judge": display, "arms": arms, "n": jval.get("n")})
    return records


def build_fig3_crossvendor_domains(data: Dict[str, Any]) -> Tuple[SvgCanvas, str]:
    cv = data.get("crossvendor_domains") or data.get("c6_crossvendor") or data.get("domains") or {}
    panel_a_raw = cv.get("math_unsolved") or cv.get("matharena_unsolved") or cv.get("math")
    panel_b_raw = cv.get("researchbench") or cv.get("researchbench_unsolved") or cv.get("science")

    panel_a = _extract_domain_panel(panel_a_raw)
    panel_b = _extract_domain_panel(panel_b_raw)

    if not panel_a and not panel_b:
        canvas = render_placeholder(
            title="Figure 3: Cross-Vendor & Multi-Domain False-Choice Rates",
            subtitle="Placeholder awaiting v2 cross-vendor MathArena UNSOLVED and ResearchBench results.",
            note="Will populate automatically when crossvendor_domains.{math_unsolved,researchbench} lands.",
        )
        return canvas, "placeholder (awaiting v2 C6/C9 results)"

    width = 960.0
    height = 480.0
    margin_top = 104.0
    margin_bottom = 96.0
    margin_left = 68.0
    margin_right = 28.0
    panel_gap = 44.0
    panel_w = (width - margin_left - margin_right - panel_gap) / 2.0
    plot_y0 = margin_top
    plot_y1 = height - margin_bottom
    plot_h = plot_y1 - plot_y0

    canvas = SvgCanvas(width, height, status="live")
    canvas.text(
        24.0,
        28.0,
        "Wrong-Pick Rates on All-Wrong Pools, by Judge and Task (95% ranges)",
        size=14.0,
        weight="700",
        fill=INK,
    )
    canvas.text(
        24.0,
        46.0,
        "ISO, EACH and PICK in math and in science ideas; first-study bars have no ranges",
        size=10.5,
        fill=MUTED,
    )

    arm_colors = {
        "ISO": OKABE_ITO["blue"],
        "EACH": OKABE_ITO["orange"],
        "PICK": OKABE_ITO["vermilion"],
    }

    # Shared legend positioned well above panel titles
    lx = width - margin_right - 220.0
    for arm_name in ("ISO", "EACH", "PICK"):
        canvas.rect(lx, 58.0, 12.0, 12.0, fill=arm_colors[arm_name], rx=1.5)
        canvas.text(lx + 17.0, 68.0, arm_name, size=10.5, weight="600", fill=INK)
        lx += 74.0

    panels = [
        ("(a) Math, hard problems", panel_a, margin_left),
        ("(b) Science ideas (ResearchBench)", panel_b, margin_left + panel_w + panel_gap),
    ]

    for title, recs, px0 in panels:
        px1 = px0 + panel_w
        canvas.text(px0, plot_y0 - 10.0, title, size=11.0, weight="700", fill=INK)
        canvas.rect(px0, plot_y0, panel_w, plot_h, fill="#FFFFFF", stroke=AXIS_COLOR, stroke_width=1.1)

        for yt in nice_ticks(0.0, 1.0, 0.2):
            yp = linear_scale(yt, 0.0, 1.0, plot_y1, plot_y0)
            canvas.line(px0, yp, px1, yp, stroke=GRID_COLOR, stroke_width=0.8)
            canvas.line(px0 - 4.0, yp, px0, yp, stroke=AXIS_COLOR, stroke_width=1.0)
            if px0 == margin_left:
                canvas.text(px0 - 8.0, yp, f"{yt:.1f}", size=9.8, fill=AXIS_COLOR, anchor="end", baseline="middle")

        if px0 == margin_left:
            canvas.text(
                20.0,
                0.5 * (plot_y0 + plot_y1),
                "Wrong-pick rate on all-wrong pools",
                size=11.0,
                weight="600",
                fill=INK,
                anchor="middle",
                transform=f"rotate(-90 20.0 {0.5 * (plot_y0 + plot_y1):.2f})",
            )

        if not recs:
            canvas.text(0.5 * (px0 + px1), 0.5 * (plot_y0 + plot_y1), "No panel data yet", size=10.5, fill=MUTED, anchor="middle")
            continue

        n_groups = len(recs)
        group_w = panel_w / max(1, n_groups)
        bar_w = min(22.0, (group_w * 0.72) / 3.0)

        for g_idx, rec in enumerate(recs):
            cx = px0 + (g_idx + 0.5) * group_w
            start_x = cx - 1.5 * bar_w
            for a_idx, arm_name in enumerate(("ISO", "EACH", "PICK")):
                if arm_name not in rec["arms"]:
                    continue
                val, lo, hi, has_ci = rec["arms"][arm_name]
                bx = start_x + a_idx * bar_w
                by = linear_scale(val, 0.0, 1.0, plot_y1, plot_y0)
                bh = plot_y1 - by
                canvas.rect(bx + 1.0, by, bar_w - 2.0, bh, fill=arm_colors[arm_name])
                if not has_ci:
                    continue  # no interval available (v1 reference bars): draw none

                y_lo = linear_scale(lo, 0.0, 1.0, plot_y1, plot_y0)
                y_hi = linear_scale(hi, 0.0, 1.0, plot_y1, plot_y0)
                ex = bx + 0.5 * bar_w
                canvas.line(ex, y_lo, ex, y_hi, stroke=INK, stroke_width=1.4)
                canvas.line(ex - 3.0, y_lo, ex + 3.0, y_lo, stroke=INK, stroke_width=1.2)
                canvas.line(ex - 3.0, y_hi, ex + 3.0, y_hi, stroke=INK, stroke_width=1.2)

            name, _, qual = rec["judge"].partition(" (")
            parts = [qual.rstrip(")").replace("Corrected", "v1 corrected")] if qual else []
            if rec.get("n") is not None:
                parts.append(f"n={rec['n']}")
            sub_lbl = "(" + ", ".join(parts) + ")"
            if n_groups >= 5 and len(name) > 13 and "-" in name:
                # Wrap long hyphenated model names cleanly onto two lines so adjacent ticks never collide
                split_idx = name.rfind("-")
                line1 = name[: split_idx + 1]
                line2 = name[split_idx + 1 :]
                canvas.text(cx, plot_y1 + 16.0, line1, size=8.4, weight="600", fill=INK, anchor="middle")
                canvas.text(cx, plot_y1 + 27.5, line2, size=8.4, weight="600", fill=INK, anchor="middle")
                canvas.text(cx, plot_y1 + 40.5, sub_lbl, size=8.0, fill=MUTED, anchor="middle")
            else:
                canvas.text(cx, plot_y1 + 18.0, name, size=8.6, weight="600", fill=INK, anchor="middle")
                canvas.text(cx, plot_y1 + 32.0, sub_lbl, size=8.2, fill=MUTED, anchor="middle")

    return canvas, f"live ({len(panel_a)} math, {len(panel_b)} researchbench judges)"


# ---------------------------------------------------------------------------
# Figure 4: Mitigation Operating-Point Frontier + C4/C5 Comparison Inset
# ---------------------------------------------------------------------------


def build_fig4_mitigation_frontier(data: Dict[str, Any]) -> Tuple[SvgCanvas, str]:
    mit = data.get("mitigation_frontier") or data.get("c7_mitigation") or data.get("mitigation") or {}
    arms_raw = mit.get("arms") if isinstance(mit, dict) and "arms" in mit else mit
    c4_c5 = mit.get("controls") or data.get("c4_c5_controls") or {}

    points: List[Dict[str, Any]] = []
    if isinstance(arms_raw, dict):
        for key in ("M0", "PICK", "M1", "M2", "M3", "ISO"):
            val = arms_raw.get(key)
            if not isinstance(val, dict):
                continue
            fa = val.get("fa", val.get("F"))
            tp = val.get("tp", val.get("tp_hit", val.get("H")))
            if fa is None or tp is None:
                continue
            fa_ci = val.get("fa_ci95", val.get("F_ci95"))
            tp_ci = val.get("tp_ci95", val.get("H_ci95"))
            points.append(
                {
                    "key": key,
                    "label": val.get("label", key),
                    "fa": float(fa),
                    "tp": float(tp),
                    "fa_ci": [float(fa_ci[0]), float(fa_ci[1])] if isinstance(fa_ci, list) and len(fa_ci) == 2 else None,
                    "tp_ci": [float(tp_ci[0]), float(tp_ci[1])] if isinstance(tp_ci, list) and len(tp_ci) == 2 else None,
                }
            )

    if not points:
        canvas = render_placeholder(
            title="Figure 4: Mitigation Operating-Point Frontier (TA False Choice vs TP Selection)",
            subtitle="Placeholder awaiting v2 C7 mitigation (M0 to M3, ISO) and C4/C5 control results.",
            note="Will populate automatically when mitigation_frontier.{arms,controls} lands.",
        )
        return canvas, "placeholder (awaiting v2 C4/C5/C7 results)"

    width = 900.0
    height = 540.0
    margin_left = 74.0
    margin_right = 240.0 if c4_c5 else 34.0
    margin_top = 82.0
    margin_bottom = 66.0
    plot_x0 = margin_left
    plot_x1 = width - margin_right
    plot_y0 = margin_top
    plot_y1 = height - margin_bottom
    plot_w = plot_x1 - plot_x0
    plot_h = plot_y1 - plot_y0

    def x_px(fa: float) -> float:
        return linear_scale(fa, 0.0, 0.85, plot_x0, plot_x1)

    def y_px(tp: float) -> float:
        return linear_scale(tp, 0.0, 1.0, plot_y1, plot_y0)

    canvas = SvgCanvas(width, height, status="live")
    canvas.text(
        24.0,
        28.0,
        "The Three Fixes: Wrong Picks Against Right Picks",
        size=14.0,
        weight="700",
        fill=INK,
    )
    canvas.text(
        24.0,
        46.0,
        "Top-left is best (few wrong picks, many right picks); crosses show 95% ranges",
        size=10.5,
        fill=MUTED,
    )

    canvas.rect(plot_x0, plot_y0, plot_w, plot_h, fill="#FFFFFF", stroke=AXIS_COLOR, stroke_width=1.2)
    for xt in nice_ticks(0.0, 0.85, 0.1):
        xp = x_px(xt)
        canvas.line(xp, plot_y0, xp, plot_y1, stroke=GRID_COLOR, stroke_width=0.8)
        canvas.line(xp, plot_y1, xp, plot_y1 + 4.5, stroke=AXIS_COLOR, stroke_width=1.0)
        canvas.text(xp, plot_y1 + 17.0, f"{xt:.1f}", size=9.8, fill=AXIS_COLOR, anchor="middle")
    for yt in nice_ticks(0.0, 1.0, 0.2):
        yp = y_px(yt)
        canvas.line(plot_x0, yp, plot_x1, yp, stroke=GRID_COLOR, stroke_width=0.8)
        canvas.line(plot_x0 - 4.5, yp, plot_x0, yp, stroke=AXIS_COLOR, stroke_width=1.0)
        canvas.text(plot_x0 - 8.0, yp, f"{yt:.1f}", size=9.8, fill=AXIS_COLOR, anchor="end", baseline="middle")

    canvas.text(0.5 * (plot_x0 + plot_x1), plot_y1 + 42.0, "Wrong-pick rate on all-wrong pools (lower is better)", size=11.5, weight="600", fill=INK, anchor="middle")
    canvas.text(
        22.0,
        0.5 * (plot_y0 + plot_y1),
        "Right-pick rate on one-right pools (higher is better)",
        size=11.5,
        weight="600",
        fill=INK,
        anchor="middle",
        transform=f"rotate(-90 22.0 {0.5 * (plot_y0 + plot_y1):.2f})",
    )

    # Ideal operating corner marker
    canvas.circle(x_px(0.02), y_px(0.98), 4.5, fill=OKABE_ITO["green"], stroke="#FFFFFF", stroke_width=1.0)
    canvas.text(x_px(0.03), y_px(0.965), "Ideal (0, 1)", size=9.2, weight="700", fill=OKABE_ITO["green"])

    # Compute Pareto-undominated points (lower FA, higher TP)
    pareto: List[Dict[str, Any]] = []
    for pt in sorted(points, key=lambda p: p["fa"]):
        dominated = any(
            other is not pt and other["fa"] <= pt["fa"] and other["tp"] >= pt["tp"] and (other["fa"] < pt["fa"] or other["tp"] > pt["tp"])
            for other in points
        )
        if not dominated:
            pareto.append(pt)
    if len(pareto) >= 2:
        canvas.polyline(
            [(x_px(p["fa"]), y_px(p["tp"])) for p in pareto],
            stroke=MUTED,
            stroke_width=1.6,
            stroke_dasharray="4,3",
        )

    arm_style = {
        "M0": (OKABE_ITO["vermilion"], "circle"),
        "PICK": (OKABE_ITO["vermilion"], "circle"),
        "M1": (OKABE_ITO["green"], "diamond"),
        "M2": (OKABE_ITO["purple"], "triangle"),
        "M3": (OKABE_ITO["orange"], "square"),
        "ISO": (OKABE_ITO["blue"], "circle"),
    }

    anchors: List[Dict[str, Any]] = []
    for pt in points:
        color, shape = arm_style.get(pt["key"], (OKABE_ITO["sky"], "circle"))
        px, py = x_px(pt["fa"]), y_px(pt["tp"])
        if pt["fa_ci"]:
            canvas.line(x_px(pt["fa_ci"][0]), py, x_px(pt["fa_ci"][1]), py, stroke=color, stroke_width=1.5, stroke_opacity=0.75)
        if pt["tp_ci"]:
            canvas.line(px, y_px(pt["tp_ci"][0]), px, y_px(pt["tp_ci"][1]), stroke=color, stroke_width=1.5, stroke_opacity=0.75)
        canvas.marker(shape, px, py, 5.4, fill=color, stroke="#FFFFFF", stroke_width=1.3)
        anchors.append({"px": px, "py": py, "label": pt["label"], "color": color})

    placed = _place_labels_greedy(anchors, (plot_x0, plot_y0, plot_x1, plot_y1))
    for anc, (lx, ly, t_anchor) in zip(anchors, placed):
        canvas.text(lx, ly, anc["label"], size=9.8, weight="700", fill=anc["color"], anchor=t_anchor)

    # C4/C5 comparison inset panel on the right if available
    if isinstance(c4_c5, dict) and c4_c5:
        ix0 = plot_x1 + 20.0
        ix1 = width - 20.0
        iy0 = plot_y0
        iy1 = plot_y1
        canvas.rect(ix0, iy0, ix1 - ix0, iy1 - iy0, fill="#F9FAFB", stroke=GRID_COLOR, stroke_width=1.0, rx=4.0)
        canvas.text(ix0 + 12.0, iy0 + 20.0, "Checks C4, C5: wrong picks", size=10.5, weight="700", fill=INK)
        cy = iy0 + 48.0
        for ck, cv in c4_c5.items():
            if not isinstance(cv, dict) or cv.get("fa") is None:
                continue
            fa = float(cv["fa"])
            ci = cv.get("fa_ci95")
            lbl = cv.get("label", ck)
            canvas.text(ix0 + 12.0, cy, lbl, size=9.2, weight="600", fill=INK)
            bar_x0 = ix0 + 12.0
            bar_x1 = ix1 - 16.0
            bx = linear_scale(fa, 0.0, 0.85, bar_x0, bar_x1)
            canvas.rect(bar_x0, cy + 7.0, bx - bar_x0, 9.0, fill=OKABE_ITO["sky"], rx=1.5)
            if isinstance(ci, list) and len(ci) == 2:
                cx_lo = linear_scale(float(ci[0]), 0.0, 0.85, bar_x0, bar_x1)
                cx_hi = linear_scale(float(ci[1]), 0.0, 0.85, bar_x0, bar_x1)
                canvas.line(cx_lo, cy + 11.5, cx_hi, cy + 11.5, stroke=INK, stroke_width=1.4)
            canvas.text(bar_x1, cy, f"{fa:.2f}", size=9.0, fill=MUTED, anchor="end")
            cy += 34.0

    return canvas, f"live ({len(points)} operating points)"


# ---------------------------------------------------------------------------
# Clean Academic Placeholder Renderer
# ---------------------------------------------------------------------------


def render_placeholder(title: str, subtitle: str, note: str) -> SvgCanvas:
    width = 860.0
    height = 360.0
    canvas = SvgCanvas(width, height, status="placeholder")
    canvas.text(28.0, 34.0, title, size=14.0, weight="700", fill=INK)
    canvas.text(28.0, 54.0, subtitle, size=10.5, fill=MUTED)
    canvas.rect(
        48.0,
        78.0,
        width - 96.0,
        height - 118.0,
        fill="#F9FAFB",
        stroke="#D1D5DB",
        stroke_width=1.2,
        stroke_dasharray="6,4",
        rx=6.0,
    )
    canvas.text(
        0.5 * width,
        0.5 * height + 2.0,
        "Awaiting v2 Experimental Results",
        size=13.5,
        weight="700",
        fill=AXIS_COLOR,
        anchor="middle",
    )
    canvas.text(0.5 * width, 0.5 * height + 24.0, note, size=10.2, fill=MUTED, anchor="middle")
    return canvas


# ---------------------------------------------------------------------------
# Entrypoint & Validation
# ---------------------------------------------------------------------------


def validate_svg_xml(svg_text: str, out_path: Path) -> None:
    """Verify generated SVG parses as well-formed XML with root <svg>."""
    root = ET.fromstring(svg_text)
    if not root.tag.endswith("svg"):
        raise ValueError(f"{out_path.name}: unexpected root XML tag {root.tag!r}")
    if "\u2014" in svg_text or "\u2013" in svg_text:
        raise ValueError(f"{out_path.name}: forbidden em/en dash found in SVG output")


def adapt_v2_results(data: Dict[str, Any], sdt_companion: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Merge v1 SDT companion data and normalize v2 results_b/results_a schema for all 4 figures."""
    merged: Dict[str, Any] = dict(data)

    # 1. Bring in v1 SDT aligned baseline if not already present
    if "sdt_aligned" not in merged and isinstance(sdt_companion, dict):
        if "sdt_aligned" in sdt_companion:
            merged["sdt_aligned"] = json.loads(json.dumps(sdt_companion["sdt_aligned"]))

    # 2. Append v2 C6 cross-vendor math SDT cells (if complete/available) into sdt_aligned
    c6 = merged.get("c6_math")
    if isinstance(c6, dict) and isinstance(c6.get("models"), dict):
        sdt_al = merged.setdefault("sdt_aligned", {})
        for mkey, mval in c6["models"].items():
            if not isinstance(mval, dict):
                continue
            strata = mval.get("strata") or {}
            entry: Dict[str, Any] = {}
            for src_s, dst_s in (("UNSOLVED_M", "UNSOLVED"), ("SOLVED_M", "SOLVED")):
                sblk_raw = strata.get(src_s)
                if not isinstance(sblk_raw, dict):
                    continue
                sblk = sblk_raw.get("all") if isinstance(sblk_raw.get("all"), dict) else sblk_raw
                sdt = sblk.get("sdt") or {}
                diffs = sblk.get("sdt_diffs") or {}
                if isinstance(sdt.get("PICK"), dict) and isinstance(sdt.get("ISO"), dict):
                    entry[dst_s] = {
                        "PICK": sdt["PICK"],
                        "ISO": sdt["ISO"],
                        "diffs": diffs,
                    }
            if entry:
                sdt_al[mkey] = entry

    # 3. Append v2 C9 ResearchBench Science SDT cells into sdt_researchbench
    c9 = merged.get("c9_science")
    if isinstance(c9, dict) and isinstance(c9.get("models"), dict):
        sdt_sci = merged.setdefault("sdt_researchbench", {})
        for mkey, mval in c9["models"].items():
            if not isinstance(mval, dict):
                continue
            met = mval.get("metrics") or {}
            sdt = met.get("sdt") or {}
            diffs = met.get("sdt_diffs") or {}
            if isinstance(sdt.get("PICK"), dict) and isinstance(sdt.get("ISO"), dict):
                sdt_sci[mkey] = {
                    "UNSOLVED": {
                        "PICK": sdt["PICK"],
                        "ISO": sdt["ISO"],
                        "diffs": diffs,
                    }
                }

    # 4. Populate crossvendor_domains for Figure 3
    if "crossvendor_domains" not in merged:
        math_panel: Dict[str, Any] = {}
        sci_panel: Dict[str, Any] = {}

        # Include C3 corrected Haiku and Sonnet as Math reference alongside C6 cross-vendor
        if isinstance(merged.get("sdt_aligned"), dict):
            for ref_key in ("haiku_corrected", "sonnet_corrected"):
                rblk = merged["sdt_aligned"].get(ref_key, {}).get("UNSOLVED", {})
                if isinstance(rblk, dict) and isinstance(rblk.get("PICK"), dict):
                    rec: Dict[str, Any] = {"n": rblk["PICK"].get("n")}
                    for arm in ("ISO", "EACH", "PICK"):
                        ad = rblk.get(arm)
                        if isinstance(ad, dict) and ad.get("F_raw") is not None:
                            rec[arm] = {
                                "rate": ad["F_raw"],
                                "ci95": ad.get("F_raw_ci95"),
                            }
                    math_panel[ref_key] = rec

        if isinstance(c6, dict) and isinstance(c6.get("models"), dict):
            for mkey, mval in c6["models"].items():
                if not isinstance(mval, dict):
                    continue
                ublk_raw = (mval.get("strata") or {}).get("UNSOLVED_M") or {}
                ublk = ublk_raw.get("all") if isinstance(ublk_raw.get("all"), dict) else ublk_raw
                ta_fc = ublk.get("ta_false_choice") or {}
                rec = {}
                for dst_arm, src_arm in (("ISO", "ISO_any"), ("EACH", "EACH_any"), ("PICK", "PICK")):
                    ad = ta_fc.get(src_arm) or ta_fc.get(dst_arm)
                    if isinstance(ad, dict) and ad.get("mean") is not None:
                        rec[dst_arm] = {"rate": ad["mean"], "ci95": ad.get("ci95")}
                        rec["n"] = ad.get("n")
                if rec:
                    math_panel[mkey] = rec

        if isinstance(c9, dict) and isinstance(c9.get("models"), dict):
            for mkey, mval in c9["models"].items():
                if not isinstance(mval, dict):
                    continue
                ta_fc = (mval.get("metrics") or {}).get("ta_false_choice") or {}
                rec = {}
                for dst_arm, src_arm in (("ISO", "ISO_any"), ("EACH", "EACH_any"), ("PICK", "PICK")):
                    ad = ta_fc.get(src_arm) or ta_fc.get(dst_arm)
                    if isinstance(ad, dict) and ad.get("mean") is not None:
                        rec[dst_arm] = {"rate": ad["mean"], "ci95": ad.get("ci95")}
                        rec["n"] = ad.get("n")
                if rec:
                    sci_panel[mkey] = rec

        if math_panel or sci_panel:
            merged["crossvendor_domains"] = {
                "math_unsolved": math_panel,
                "researchbench": sci_panel,
            }

    # 5. Populate mitigation_frontier for Figure 4 (Haiku UNSOLVED C7 N=40 + C4/C5 inset)
    if "mitigation_frontier" not in merged:
        c7 = merged.get("c7_mitigation") or {}
        arms: Dict[str, Any] = {}

        m1 = c7.get("math_haiku_m1") or {}
        if isinstance(m1.get("sdt"), dict):
            for key, src_k, lbl in (
                ("M0", "PICK", "M0: PICK"),
                ("ISO", "ISO", "ISO (3x)"),
                ("M1", "M1", "M1: ISO->PICK"),
            ):
                s = m1["sdt"].get(src_k)
                if isinstance(s, dict) and s.get("F_raw") is not None and s.get("H_raw") is not None:
                    arms[key] = {
                        "label": lbl,
                        "fa": s["F_raw"],
                        "tp": s["H_raw"],
                        "fa_ci95": s.get("F_raw_ci95"),
                        "tp_ci95": s.get("H_raw_ci95"),
                    }

        m2h = (c7.get("math_m2") or {}).get("haiku") or {}
        if isinstance(m2h.get("sdt"), dict):
            s = m2h["sdt"].get("M2_gate4") or m2h["sdt"].get("M2_raw")
            if isinstance(s, dict) and s.get("F_raw") is not None and s.get("H_raw") is not None:
                arms["M2"] = {
                    "label": "M2: Error hunt",
                    "fa": s["F_raw"],
                    "tp": s["H_raw"],
                    "fa_ci95": s.get("F_raw_ci95"),
                    "tp_ci95": s.get("H_raw_ci95"),
                }

        m3h = c7.get("math_haiku_m3_foil") or {}
        if isinstance(m3h.get("sdt"), dict):
            s = m3h["sdt"].get("M3_any_fa")
            if isinstance(s, dict) and s.get("F_raw") is not None and s.get("H_raw") is not None:
                arms["M3"] = {
                    "label": "M3: Known decoy",
                    "fa": s["F_raw"],
                    "tp": s["H_raw"],
                    "fa_ci95": s.get("F_raw_ci95"),
                    "tp_ci95": s.get("H_raw_ci95"),
                }

        controls: Dict[str, Any] = {}
        c4 = merged.get("c4_compute") or {}
        ta_r = c4.get("ta_rates") or {}
        for ck, src_k, lbl in (
            ("pick_1x", "PICK_1X", "C4 PICK 1x (n=68)"),
            ("pick_maj3", "PICK_MAJ3", "C4 PICK MAJ3 (3x)"),
            ("pick_any3", "PICK_ANY3", "C4 PICK ANY3 (3x)"),
            ("iso_any", "ISO_any", "C4 ISO-any (3x)"),
        ):
            r = ta_r.get(src_k)
            if isinstance(r, dict) and r.get("mean") is not None:
                controls[ck] = {"label": lbl, "fa": r["mean"], "fa_ci95": r.get("ci95")}

        c5_own = ((merged.get("c5_own_removal") or {}).get("subsets") or {}).get("all_38") or {}
        if c5_own.get("fa_pick2") is not None:
            controls["c5_own_pick2"] = {
                "label": "C5 own out, PICK (n=38)",
                "fa": c5_own["fa_pick2"],
                "fa_ci95": c5_own.get("fa_pick2_ci95"),
            }
            controls["c5_own_iso2"] = {
                "label": "C5 own out, ISO (n=38)",
                "fa": c5_own["fa_iso2"],
                "fa_ci95": c5_own.get("fa_iso2_ci95"),
            }

        c5_w = merged.get("c5_wells_removal") or {}
        if c5_w.get("choosing_rate_pick2") is not None:
            controls["c5_wells_pick2"] = {
                "label": "C5 first pick out, PICK (n=43)",
                "fa": c5_w["choosing_rate_pick2"],
                "fa_ci95": c5_w.get("choosing_rate_pick2_ci95"),
            }

        if arms:
            merged["mitigation_frontier"] = {
                "arms": arms,
                "controls": controls,
            }

    return merged


def generate_all(input_path: Path, out_dir: Path, sdt_path: Optional[Path] = None) -> Dict[str, str]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected top-level JSON object in {input_path}")

    sdt_companion: Optional[Dict[str, Any]] = None
    if sdt_path is not None and sdt_path.is_file() and sdt_path.resolve() != input_path.resolve():
        sdt_companion = json.loads(sdt_path.read_text(encoding="utf-8"))
    data = adapt_v2_results(data, sdt_companion=sdt_companion)

    out_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        ("fig1_criterion_shift.svg", build_fig1_criterion_shift),
        ("fig2_sdt_law_curve.svg", build_fig2_sdt_law_curve),
        ("fig3_crossvendor_domains.svg", build_fig3_crossvendor_domains),
        ("fig4_mitigation_frontier.svg", build_fig4_mitigation_frontier),
    ]

    summary: Dict[str, str] = {}
    for fname, builder in specs:
        canvas, status_msg = builder(data)
        svg_text = canvas.render()
        out_path = out_dir / fname
        validate_svg_xml(svg_text, out_path)
        out_path.write_text(svg_text, encoding="utf-8")
        summary[fname] = status_msg
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    root = Path(__file__).resolve().parent.parent
    default_input = root / "results" / "results_b.json"
    if not default_input.is_file():
        default_input = root / "results" / "sdt_and_subgroups.json"
    default_sdt = root / "results" / "sdt_and_subgroups.json"
    default_out = root / "paper" / "figures"

    parser = argparse.ArgumentParser(
        description="Generate NeurIPS/ICML/TMLR-style vector SVG figures from results JSON."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=default_input,
        help=f"Path to unified results JSON (default: {default_input})",
    )
    parser.add_argument(
        "--sdt",
        type=Path,
        default=default_sdt,
        help=f"Optional companion v1 SDT JSON (default: {default_sdt})",
    )
    parser.add_argument(
        "--out-dir",
        "-o",
        type=Path,
        default=default_out,
        help=f"Output directory for SVG files (default: {default_out})",
    )
    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"ERROR: input JSON not found: {args.input}", file=sys.stderr)
        return 1

    summary = generate_all(args.input, args.out_dir, sdt_path=args.sdt)
    print(f"Generated 4 SVG figures in {args.out_dir} from {args.input}:")
    for fname, status_msg in summary.items():
        print(f"  - {fname}: {status_msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
