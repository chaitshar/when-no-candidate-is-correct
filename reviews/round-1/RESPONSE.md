# Response to round-1 reviews (date -u 2026-11-04)

ACTIONABLE and fixed:
1. Gate passed by pooling (area_chair B1, methods B1 and B4, integrity B2). Accepted. Conservative ruling recorded in exps/c2_confirm/AMENDMENTS.md A2, which states that it was made after the data. The paper now reports the confirmation as inconclusive, interprets only the gated 2026 contest set, and reports union and arXiv-set numbers as uninterpretable context. H2 is no longer called confirmed.
2. Competence account post hoc and confounded with source (area_chair B2, methods B3). Accepted. It is now labelled exploratory throughout. A within-source split was added (exps/posthoc/solvability_by_source.py), and the overall pooled difference (+0.06, CI includes 0) is reported. Single-attempt solvability and the source confound are stated.
3. No positioning against none-of-the-above and abstention work (area_chair B3). Added Kadavath et al. 2022, Wen et al. 2024 (TACL), and the contrast with Wang et al. 2025, section 4.2.
4. The study-context probe has no artifact (integrity B1). The claim was removed. The paper now states only what the prompts contain.
5. TP PICK vs ISO-any comparison without its caveat (integrity B3). The caveat was added: favours PICK by construction, descriptive only.
6. gemma-2-2b used as support after being declared no-weight (integrity B4). Removed from the argument.
7. Stale Gottweis record (citations B1). Updated to the current arXiv title from a curl fetch on 2026-11-04. The reviewer's "Nature (2026)" comment was not visible on our fetch; the record says so.
8. Call date (integrity, non-blocking). Now 3 and 4 November 2026 (UTC).
9. Undisclosed deviations (integrity, non-blocking). Sonnet cost-cap overrun, the safeguard-blocked call and the timeout are now in Threats to validity and in AMENDMENTS D1 to D3.

Not changed:
- H2 informative pools (methods B2: only 29 of 103 pools vary). Correct and important. With H2 no longer claimed, this now explains why the gated set is underpowered. Noted in DEFENSE.md.
