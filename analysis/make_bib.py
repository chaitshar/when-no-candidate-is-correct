#!/usr/bin/env python3
"""Write paper/refs.bib from evidence/citations/<key>.json for every key cited in paper/main.tex.
The title field is the fetched title, verbatim; the status label goes in note."""
import json, re
s = open("paper/main.tex").read()
cited = set()
for c in re.findall(r"\\cite\w*(?:\[[^\]]*\])*\{([^}]+)\}", s):
    cited |= {k.strip() for k in c.split(",")}
out = []
for k in sorted(cited):
    d = json.load(open(f"evidence/citations/{k}.json"))
    au = d.get("authors_bib") or d.get("authors", "")
    if isinstance(au, list):
        au = " and ".join(au)
    out.append(f"@misc{{{k},\n  title = {{{d['fetched_title']}}},\n  author = {{{au}}},\n  year = {{{d.get('year', '')}}},\n"
               f"  note = {{{d.get('venue_clean') or d.get('status', '')}}},\n  howpublished = {{\\url{{{d['url']}}}}}\n}}\n")
open("paper/refs.bib", "w").write("\n".join(out))
print(len(out), "entries")
