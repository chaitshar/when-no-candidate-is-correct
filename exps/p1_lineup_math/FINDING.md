# P1 finding (pilot): no lineup effect for current Claude judges on human-verified wrong MATH solutions

Numbers from exps/p1_lineup_math/results.txt (analyze.py on raw/claude, 1640 calls, 0 failed calls, 0 parse failures in any arm).

- Items: 40 MATH test problems, each with 3 GPT-4 solutions whose final answers are wrong and in which PRM800K human labelers marked an erroneous step (TA pools), and TP pools of 2 of those plus a human-approved right solution.
- Judges haiku, sonnet, opus (all arms, 40 problems) and fable (ISO and PICK, 16 problems): all pass the preregistered inclusion floor (ISO parse 1.0; accept right 1.0, accept wrong 0.0).
- TA choosing rate was 0 of 40 (fable 0 of 16) in every arm: ISO, PICK, BASE, EACH, SEQ. TP hit rate 1.0 and false choice 0 in every arm.
- Every preregistered contrast is exactly 0 with CI [0, 0]. The preregistered kill criterion for the B1 headline on these items is met: |D| < 0.05 with CI inside plus or minus 0.15 for all included models.
- Judge solve rate (SOLVE arm): haiku 0.925, sonnet 0.925, opus 0.875. On the problems a judge could not solve, it still rejected every wrong candidate (small n: 3 to 5 problems).
- Cost per model: haiku 0.63 USD, sonnet 9.1 USD, opus 19.7 USD, fable 4.4 USD. SEQ costs about 3.5 times PICK (3 turns).

Reading: on GPT-4-era (2022) errors to MATH problems, current Claude judges are at a floor of zero false acceptance in every presentation format, including the one-call simultaneous PICK format that the corpus found most vulnerable with older haiku-tier judges and synthetic items. The lineup effect, if it exists for these judges, is not visible on items within their competence. This is the capability objection the brief named, answered in its strong form for this item class. Next: P3 on olympiad items beyond judge competence, and the open-weight models (Mac runner) for a capability gradient on these same pools.
