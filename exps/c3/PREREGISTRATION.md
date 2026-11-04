# C3 confirmatory preregistration: does the lineup penalty depend on whether the judge can solve the problem?

Written 2026-11-04T08:29:04Z (date -u), before any C3 subject call. Analysis code (analyze.py, stratify.py) is committed with this file. Items are used once.

## Why C3, and what changed from C2
C2 could not be interpreted: after a parser fix, neither held-out set fell inside the solve-rate band, the union passed only by pooling, and the rule for combining per-set and union gates was resolved after the data (exps/c2_confirm/AMENDMENTS.md A2, A3). A post hoc split over S1 and C2 suggested the pooled format adds false choices on problems the judge cannot solve (+0.15) and not on problems it solves (-0.04), but solvability rested on one attempt, one parser with a known bug, and was confounded with item source. C3 fixes each of these: solvability is measured first with two attempts and two independently written graders, the problems are stratified on it before any arm call, the gate is a single rule stated here, and item source enters the primary model as fixed effects.

## Subject
claude-haiku-5-5 only (resolved id recorded per call), via harness/run_jobs.py: Claude Code 2.1.318 print mode (S1 and C2 ran on 2.1.317; the CLI updated in between), defaults (adaptive extended thinking on), no tools, fixed system prompt, empty working directory. No claim extends to any other model, version or setting.

## Items (locked by an independent agent before this file; banks/locked_c3/LOCK.md and LOCK.sha256)
All target-absent (TA) pools buildable with banks/matharena_pools.py (MA_ALL_MODELS=1: candidates are officially graded outputs of every model MathArena ran on that competition) from smt_2025, cmimc_2025, brumo_2025, apex_2025, hmmt_nov_2025, arxivmath-0626, arxivmath-1225, arxivmath-0126, arxivmath-0226, arxivmath-0326, arxivmath-0426, arxivmath-0526 and apex-shortlist, excluding every problem used in S1 to S9 or C2. Bank justification: MathArena is the field's standard recent-competition benchmark with official answers and official grading of every candidate; these problems were never shown to any subject in this project; the arXiv-derived sets (December 2025 to June 2026 papers) are hard for the subject, the contest problems easier, which gives both strata. Limit: math final-answer problems only; candidate generators include older and smaller models, so the wrong candidates are of mixed quality.

## Stage 1: solvability (before any arm)
Two SOLVE calls per TA problem (prompt solve in harness/lineup_prompts.py). Each reply is graded by grader A (harness/parse.py answer + harness/mathgrade.py grade) and grader B (harness/grader_b.py, written by a separate agent that did not see grader A). Where A and B disagree, the PI decides by reading the reply's final answer against the official answer, records each decision in hand_checks.csv with a one-line reason, and commits that file before any arm call. Stratum: SOLVED if both attempts are correct, UNSOLVED if both are wrong, MIXED otherwise (MIXED problems get no arm calls and are reported only by count). If a stratum has more than 150 problems, 150 are sampled with random.Random(3).

## Stage 2: arms on SOLVED and UNSOLVED problems
ISO (each of the 3 wrong candidates alone, plus the first right candidate of the problem's TP pool when one exists, for the gate), PICK (pool with NONE allowed), FORCED (pool, no NONE). Prompts unchanged from S1 and C2.

## Gate (one rule, applied to the whole C3 sample before looking at any hypothesis)
Interpret C3 only if all hold: ISO parse rate >= 0.90; ISO accept rate on right candidates minus on wrong candidates >= 0.10; ISO false accept on wrong candidates > 0; at least 40 problems in each of SOLVED and UNSOLVED. There is no per-source or per-stratum gate and no solve-rate band (stratification replaces it). If the gate fails, C3 is reported as not interpretable.

## Estimates and tests (unit: problem)
d_i = 1[PICK chose a wrong candidate] - 1[at least one ISO verdict on the 3 wrong candidates is ACCEPT]; h_i = ISO accept of the FORCED-picked wrong candidate minus the mean ISO accept of the other two.
- H1 (primary): the lineup penalty is larger on UNSOLVED than SOLVED problems. Estimate b from OLS d_i = a + b*UNSOLVED_i + competition fixed effects, HC3 standard errors; one-sided p for b > 0. Robustness, reported but not tested: unadjusted difference with a problem bootstrap, and b within the contest family and within the arXiv family separately.
- H1u: mean d on UNSOLVED > 0 (one-sided, problem bootstrap, 10000 resamples).
- H2s, H2u: mean h > 0 within SOLVED and within UNSOLVED (one-sided bootstrap).
Holm correction over these four at familywise alpha 0.05.

## What counts as confirmed, refuted, inconclusive
- H1 confirmed: Holm-adjusted p < 0.05. Refuted: the 95% CI of b lies entirely below +0.10 and the point estimate is <= 0. Otherwise inconclusive.
- H1u, H2s, H2u: confirmed if Holm-adjusted p < 0.05; refuted if the 95% CI upper bound is below +0.05; otherwise inconclusive.

## Power
Expected counts are unknown until stage 1. With 100 problems per stratum and SD of d about 0.45 (S1, C2), SE(b) is about 0.064 and the effect detectable with 80% power at one-sided alpha 0.05 is about 0.16; the post hoc estimate that motivates C3 is +0.19. With 50 per stratum the detectable effect is about 0.23. The achieved counts and power are reported whatever they are.

## Cost caps (harness/run_jobs.py --max-usd, from C2's haiku cost of 0.0148 USD per call)
SOLVE 12 USD; ISO 20 USD; PICK 6 USD; FORCED 6 USD. A capped arm is reported with the problems it reached; no cap is raised after data without an amendment.

## Later additions (each preregistered by amendment before its data)
H3 cross-model verification; a claude-sonnet-5-5 repeat after a parse-rate pilot on items outside C3; gemma-4-e4b only if it passes its calibration gate.
