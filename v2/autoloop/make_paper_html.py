#!/usr/bin/env python3
"""Render a clean, self-contained HTML manuscript preview from paper/main.tex, results.tex, and figures/*.svg.

Pure Python 3.9 stdlib only. Zero em dashes, zero en dashes, zero prose spaced hyphens.
"""
import argparse
import html
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional


DEFAULT_ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")


def load_macros(results_tex: Path) -> Dict[str, str]:
    text = results_tex.read_text(encoding="utf-8")
    macros = dict(re.findall(r"\\csname res@([^\\]+)\\endcsname\{([^}]*)\}", text))
    return macros


def expand_inline(s: str, macros: Dict[str, str]) -> str:
    def _rep_res(m: re.Match) -> str:
        val = macros.get(m.group(1), f"MISSING({m.group(1)})")
        val = val.replace("\\%", "%").replace("$<0.0002$", "&lt;0.0002")
        return val

    s = re.sub(r"\\res\{([^}]+)\}", _rep_res, s)
    s = s.replace("\\%", "%").replace("\\_", "_")
    s = re.sub(r"\\texttt\{([^}]+)\}", r"<code>\1</code>", s)
    s = re.sub(r"\\textbf\{([^}]+)\}", r"<strong>\1</strong>", s)
    s = re.sub(r"\\emph\{([^}]+)\}", r"<em>\1</em>", s)
    s = re.sub(r"\\cite[pt]?\{([^}]+)\}", lambda m: "[" + m.group(1) + "]", s)
    s = re.sub(r"Table~\\ref\{([^}]+)\}", r"Table [\1]", s)
    s = re.sub(r"Figure~\\ref\{([^}]+)\}", r"Figure [\1]", s)
    s = s.replace("\\Delta c", "&Delta;c").replace("\\Delta d'", "&Delta;d'")
    s = s.replace("\\Phi^{-1}", "&Phi;<sup>-1</sup>").replace("\\Phi", "&Phi;")
    s = s.replace("\\tau", "&tau;").replace("\\approx", "&approx;")
    s = s.replace("\\ge", "&ge;").replace("\\to", "&rarr;")
    s = s.replace("$", "")
    s = s.replace("``", "&ldquo;").replace("''", "&rdquo;")
    return s


def convert_table(block: str, macros: Dict[str, str]) -> str:
    cap_m = re.search(r"\\caption\{(.*?)\}\s*\\label", block, re.S)
    cap = expand_inline(cap_m.group(1).strip(), macros) if cap_m else ""
    tab_m = re.search(r"\\begin\{tabular\}\{[^}]+\}(.*?)\\end\{tabular\}", block, re.S)
    if not tab_m:
        return ""
    body = tab_m.group(1)
    rows_html: List[str] = []
    in_head = True
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("\\toprule", "\\bottomrule")):
            continue
        if line.startswith("\\midrule"):
            in_head = False
            continue
        if line.endswith("\\\\"):
            line = line[:-2].strip()
        cells = [expand_inline(c.strip(), macros) for c in line.split("&")]
        tag = "th" if in_head else "td"
        rows_html.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
    return (
        "<div class='table-wrap'><table>"
        + "\n".join(rows_html)
        + f"</table><p class='caption'>{cap}</p></div>"
    )


def convert_figure(block: str, paper_dir: Path, macros: Dict[str, str]) -> str:
    inc_m = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", block)
    cap_m = re.search(r"\\caption\{(.*?)\}\s*\\label", block, re.S)
    cap = expand_inline(cap_m.group(1).strip(), macros) if cap_m else ""
    svg_html = "<p>[Missing SVG]</p>"
    if inc_m:
        rel = inc_m.group(1)
        svg_path = paper_dir / (rel if rel.endswith(".svg") else rel + ".svg")
        if svg_path.is_file():
            svg_raw = svg_path.read_text(encoding="utf-8")
            svg_raw = re.sub(r"<\?xml[^?]+\?>\s*", "", svg_raw)
            svg_html = f"<div class='svg-box'>{svg_raw}</div>"
    return f"<figure>{svg_html}<figcaption>{cap}</figcaption></figure>"


def build_html(paper_dir: Path) -> str:
    tex = (paper_dir / "main.tex").read_text(encoding="utf-8")
    macros = load_macros(paper_dir / "results.tex")
    extra = paper_dir / "results_extra.tex"
    if extra.is_file():
        macros.update(load_macros(extra))

    title_m = re.search(r"\\title\{([^}]+)\}", tex)
    title = html.escape(title_m.group(1)) if title_m else "Manuscript Preview"

    body_m = re.search(r"\\begin\{document\}(.*?)\\bibliographystyle", tex, re.S)
    body = body_m.group(1) if body_m else tex
    body = re.sub(r"\\maketitle", "", body)

    parts: List[str] = []
    # Split on tables, figures, equations, abstract, sections
    token_re = re.compile(
        r"(\\begin\{abstract\}.*?\\end\{abstract\}"
        r"|\\begin\{table\*?\}.*?\\end\{table\*?\}"
        r"|\\begin\{figure\*?\}.*?\\end\{figure\*?\}"
        r"|\\begin\{equation\}.*?\\end\{equation\}"
        r"|\\begin\{(?:itemize|enumerate)\}.*?\\end\{(?:itemize|enumerate)\}"
        r"|\\section\{[^}]+\}"
        r"|\\subsection\{[^}]+\})",
        re.S,
    )

    for chunk in token_re.split(body):
        c = chunk.strip()
        if not c:
            continue
        if c.startswith("\\begin{abstract}"):
            inner = re.sub(r"\\begin\{abstract\}|\\end\{abstract\}", "", c).strip()
            parts.append(f"<section class='abstract'><h2>Abstract</h2><p>{expand_inline(inner, macros)}</p></section>")
        elif c.startswith("\\begin{table"):
            parts.append(convert_table(c, macros))
        elif c.startswith("\\begin{figure"):
            parts.append(convert_figure(c, paper_dir, macros))
        elif c.startswith("\\begin{equation}"):
            inner = re.sub(r"\\begin\{equation\}|\\end\{equation\}", "", c).strip()
            parts.append(f"<div class='eq'><code>{html.escape(inner)}</code></div>")
        elif c.startswith("\\begin{itemize}") or c.startswith("\\begin{enumerate}"):
            tag = "ol" if "enumerate" in c[:20] else "ul"
            inner = re.sub(r"\\begin\{(?:itemize|enumerate)\}(?:\[[^\]]*\])?(?:\\setlength\{[^}]+\}\{[^}]+\})?|\\end\{(?:itemize|enumerate)\}", "", c).strip()
            items = [x.strip() for x in inner.split("\\item") if x.strip()]
            lis = "".join(f"<li>{expand_inline(it, macros)}</li>" for it in items)
            parts.append(f"<{tag}>{lis}</{tag}>")
        elif c.startswith("\\section{"):
            hdr = c[len("\\section{"):-1]
            parts.append(f"<h2>{expand_inline(hdr, macros)}</h2>")
        elif c.startswith("\\subsection{"):
            hdr = c[len("\\subsection{"):-1]
            parts.append(f"<h3>{expand_inline(hdr, macros)}</h3>")
        else:
            for para in re.split(r"\n\s*\n", c):
                p = para.strip()
                if not p:
                    continue
                p = re.sub(r"\\paragraph\{([^}]+)\}", r"<strong>\1</strong> ", p)
                parts.append(f"<p>{expand_inline(p, macros)}</p>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: Georgia, "Times New Roman", serif; max-width: 980px; margin: 32px auto; padding: 0 24px; color: #111827; line-height: 1.55; }}
  h1 {{ font-size: 26px; margin-bottom: 6px; line-height: 1.25; }}
  .author {{ color: #4B5563; font-size: 15px; margin-bottom: 24px; }}
  h2 {{ font-size: 19px; border-bottom: 1px solid #E5E7EB; padding-bottom: 4px; margin-top: 28px; }}
  h3 {{ font-size: 16px; margin-top: 20px; }}
  .abstract {{ background: #F9FAFB; border-left: 3px solid #0072B2; padding: 14px 18px; margin: 18px 0 24px; }}
  .abstract h2 {{ border: none; margin-top: 0; font-size: 15px; text-transform: uppercase; letter-spacing: 0.04em; color: #0072B2; }}
  .table-wrap {{ margin: 22px 0; overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-family: system-ui, sans-serif; font-size: 12.5px; }}
  th, td {{ border-bottom: 1px solid #E5E7EB; padding: 6px 8px; text-align: left; font-variant-numeric: tabular-nums; }}
  th {{ background: #F3F4F6; font-weight: 600; }}
  .caption, figcaption {{ font-family: system-ui, sans-serif; font-size: 12.5px; color: #374151; margin-top: 8px; }}
  figure {{ margin: 26px 0; padding: 12px; border: 1px solid #E5E7EB; border-radius: 6px; background: #FFFFFF; }}
  .svg-box svg {{ width: 100%; height: auto; display: block; }}
  .eq {{ background: #F9FAFB; padding: 10px 14px; margin: 12px 0; border-radius: 4px; overflow-x: auto; }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9em; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="author">Chaitanya Sharma, Independent Researcher (November 2026)</div>
{''.join(parts)}
</body>
</html>
"""


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build HTML preview of paper/main.tex with live SVG figures.")
    ap.add_argument("--paper-dir", type=Path, default=DEFAULT_ROOT / "paper")
    ap.add_argument("--out", type=Path, default=DEFAULT_ROOT / "paper" / "preview.html")
    args = ap.parse_args(argv)
    out_html = build_html(args.paper_dir)
    args.out.write_text(out_html, encoding="utf-8")
    print(f"Wrote {args.out} ({len(out_html)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
