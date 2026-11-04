# C2 confirmatory preregistration (date -u 2026-11-03 ~23:30 UTC), before any C2 call

## Claims under test (from screens S1 and S6; exploratory there, confirmatory here)
- H1 (no lineup penalty): for a judge that may answer NONE, choosing a wrong candidate from a target-absent (TA) pool of 3 is not more frequent than accepting at least one of the same candidates in 3 isolated calls. Test: TOST equivalence with margin 0.10 on D = choosing(PICK) - choosing(ISO-any), paired by problem; 90% percentile bootstrap CI (10000 resamples over problems) inside [-0.10, +0.10]. Directional fallback reported: one-sided test of D > 0.
- H2 (selection then verification): within a TA pool, the wrong candidate chosen by a forced choice (FORCED, no NONE) is accepted by the same model's isolated verification more often than the pool's other wrong candidates. Test: mean within-pool difference (accept(picked) - mean accept(unpicked)) > 0, one-sided bootstrap p < 0.05 over problems.

## Items (locked by an independent agent; banks/locked_ma/LOCK.md, LOCK.sha256)
- Confirmation set: banks/locked_ma/confirm_pools.json (hmmt_feb_2026, aime_2026; candidates from MathArena's 2026 lineup, official grading).
- Replication set: banks/locked_ma/replication_pools.json (arxivmath-0826, arxivmath-0926; candidates from all models MathArena ran on those sets).
- Bank justification: MathArena final-answer competitions are the field's standard uncontaminated math evaluation, with official answers and official grading of every candidate; these are the newest sets available (February 2026 contests; problems from August and September 2026 arXiv papers). Hard: chosen because 3 or more current frontier models erred. Mechanism fit: target-absent pools of real current-model errors. Limits: math final-answer tasks only; subject training cutoffs unknown, so 2026 contest items may be in training data; the arXiv sets postdate most published cutoffs but are generated from papers.

## Subjects
claude-haiku-5-5 on all TA pools of both sets (and TP pools for descriptives). claude-sonnet-5-5 on the confirmation set only (24 problems), cost cap 12 USD. claude -p 2.1.317 defaults (adaptive extended thinking on), no tools, fixed system prompt; resolved model id recorded per call. Results are reported per model and per set; never pooled across models.

## Arms
ISO (each candidate alone), PICK (pool, NONE allowed), FORCED (pool, no NONE), SOLVE (one per problem, calibration). Prompts: harness/lineup_prompts.py (unchanged since S1).

## Gates (per model and set, applied before looking at H1 or H2)
Interpret only if: SOLVE rate in [0.2, 0.8]; ISO parse rate >= 0.9; ISO accept(right) - accept(wrong) >= 0.10; ISO false accept on wrong candidates > 0.

## Primary analysis
H1 and H2 per model on the union of both sets for haiku (problem is the unit; the two sets are disjoint), and separately per set as replication checks (same direction required). Sonnet: confirmation set only, reported as a low-power check (24 problems; the 90% CI half-width is expected near 0.15, so equivalence at 0.10 is unlikely to be shown even if true; stated in advance).
Multiplicity: 2 hypotheses x 2 models = 4 primary tests, Holm at 0.05. Screens are reported separately and never as findings; the ledger total is reported.

## Power (haiku)
About 103 TA problems (24 + 79). With a discordance rate near 0.2 (S1 had 12 of 60), the SD of the paired difference is about 0.45, giving a 90% CI half-width near 0.073, so equivalence at 0.10 is detectable if the true D is within about +-0.03. H2: S1 effect +0.13 with SD near 0.45 gives power above 0.9 at n = 103.

## Kill criteria
H1 fails if the 90% CI leaves [-0.10, 0.10]; if D > 0 significantly, the lineup penalty exists for that model and set, reported as such. H2 fails if the one-sided p >= 0.05; then S6 was noise.

## Analysis code
analyze.py in this folder, written and committed before any C2 call.
