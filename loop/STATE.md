# State (cold-reader handoff). Updated 2026-11-04 12:06 UTC

FINISHED. All gates pass; loop/DONE exists. Rubric convergence is met (review rounds 8 and 9: six fresh lenses, all minor, no blockers). The calibration bar is NOT met (area chair 4 against a flagship median of 6). Task 2 was not started (user instruction).

Final paper: paper/main.pdf, built from main.tex, results.tex, refs.bib and figures/; the bundle is paper/arxiv-bundle.tar.gz.

Main result (C3, claude-haiku-5-5, pre-registered):
- On 90 problems the judge did not solve, pooled PICK chose a wrong solution from all-wrong pools in 0.60 of pools, against 0.36 for isolated verification (confirmed).
- On those problems, the forced pick is the wrong candidate that its own verification accepts more often (confirmed).
- Primary solvability interaction: inconclusive.
- A4 and A5: consistent with a criterion shift. Same lineup ROC, and a base-rate statement does not detectably move it. On these problems the pick is nearly uninformative.
- Sonnet repeats H1u and H2u. Cross-model verification (H3): no reduction detected.

Read FINAL_REPORT.md for everything else. Known non-blocking issues are listed at the top of FINAL_REPORT.md.
Needs user: hand checks in AUDIT_SAMPLE.md, including exps/c3/hand_checks.csv, audit_unsolved.csv and candidate_label_audit.csv; the full text of the NeurIPS 2026 selected-tail poster; the gated datasets (HLE, GPQA, GAIA).
