# Response to round-4 reviews (2026-11-04T10:42:50Z)

Design flaw, answered with new experiments (rubric step 5):
- Hostile expert (criterion vs discriminability; no TP pools, no EACH arm): pre-registered amendment A4 (exps/c3/AMENDMENTS.md) ran PICK on the target-present pools and EACH on both pool types, for haiku and sonnet. H4 (pooling lowers discriminability) was not confirmed for either model; PICK raised hits as well as false choices. The paper now reports the C3 effect as a criterion shift under which the pick is nearly uninformative on unsolved problems. Title, abstract, contributions and conclusion were rewritten. EACH vs PICK is reported (question form matters for haiku).

Blockers fixed:
- Methods, stage-1 grading: the PI audited all 90 UNSOLVED problems (exps/c3/audit_unsolved.csv): 14 solved, 6 mixed. A post hoc sensitivity analysis (analyze_sensitivity.py) with audited strata and duplicates removed changes no conclusion. Reported in the paper; the pre-registered strata stay primary; "UNSOLVED" is now defined as "both attempts graded wrong".
- Integrity, duplicates: 5 duplicates found by text similarity (reviewer said 6; the next-closest match has similarity 0.65 and is not a duplicate); exclusion sensitivity reported; wording changed from "never shown" to "excluded by identifier, with 5 later found to repeat".
- Integrity, CLI version: now stated per experiment (2.1.317 for the screens and C2, 2.1.318 for C3).
- Area chair and integrity, H3 overstatement: H3 is described as a non-detection; the mirror analysis (sonnet selects, haiku verifies) is reported as descriptive.
- Prior art: Rho and Lee (preprint) and Ma et al. (workshop) are cited; the Wang et al. description is aligned with its full text (Secs 3.3, 4.1, 4.2).
- Area chair, title overclaimed specificity: the title now states what was found without claiming exclusivity; the solved-stratum effect (+0.06) is reported.
- Area chair, seven arXiv sets (not six), December 2025 to June 2026: fixed.
