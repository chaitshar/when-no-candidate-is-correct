# C1 confirmatory preregistration: rejection channel versus forced-choice tournaments on fresh human-verified items

Written 2026-11-03 ~22:10 UTC, before any C1 subject call and before the PI has read any record of the locked banks. Analysis code (analyze.py) is frozen and committed with this file. Items are used once.

## Background (pilots, not used here)
P1 (exps/p1_lineup_math): on 40 MATH problems, haiku, sonnet, opus and fable chose no wrong candidate in any target-absent (TA) pool in any format that offered a rejection (ISO, PICK with NONE, EACH, SEQ). P2 (exps/p2_tournament): on the same pools, round-robin forced-choice tournaments named a decisive winner in most TA pools; decisiveness separated TA from target-present (TP) pools with AUROC 0.59 to 0.64.

## Items (locked by an independent agent, banks/locked/LOCK.md)
- Confirmation set: banks/locked/confirm_bank.jsonl (MATH test problems not used in P1 or P2).
- Replication set: banks/locked/replication_bank.jsonl (MATH train problems, different items).
- In each set, every problem with at least 3 wrong candidates gives a TA pool (first 3 wrong in file order); every such problem with a right candidate also gives a TP pool (first 2 wrong + first right). Candidate order shuffled with seed f"C1-{pid}-{kind}". For the replication set, at most 120 problems are used: those with a right candidate first (file order), then others, to cap cost.

## Subjects
haiku, sonnet, opus through harness/run_jobs.py (isolated). Arms: ISO (each candidate alone), PICK (pool with NONE option), PAIR (every ordered pair, forced WINNER, 6 calls per pool). Prompts unchanged from P1 and P2 (harness/lineup_prompts.py).

## Hypotheses (per model and per set; confirmation set is primary, replication set must agree in direction)
- H1 (rejection channel holds): TA choosing rate in PICK is below 0.10. Test: one-sided exact (Clopper-Pearson) 95% upper bound of the TA choosing rate < 0.10, unit pool (one TA pool per problem, so pools are independent).
- H2 (no simultaneous-presentation penalty): PICK minus ISO TA choosing lies within plus or minus 0.10. Test: TOST with paired problem bootstrap 90% CI inside [-0.10, 0.10].
- H3 (tournament statistics carry little absence signal): AUROC of tournament decisiveness for TP versus TA pools is below 0.75. Test: upper bound of the 95% bootstrap CI (resampling problems) < 0.75. Only problems with both a TA and a TP pool enter.
- H4 (same for order consistency): AUROC of order consistency < 0.75, same test.
- Descriptive, not tested: TP hit rate per arm; P(tournament winner is right) on TP; fraction of TA pools where the tournament winner is a candidate that the same model rejected in ISO (the "manufactured winner" rate); cost, tokens, wall time and failures per arm (STEER rule 3). Compute: ISO 3 calls per TA pool, PICK 1, PAIR 6.

## Multiplicity
4 hypotheses x 3 models = 12 tests on the confirmation set, Holm correction at familywise alpha 0.05 (bootstrap-CI tests are converted to p-values by bootstrap test inversion in analyze.py). A hypothesis counts as confirmed for a model only if it passes Holm on the confirmation set AND the replication set point estimate is on the same side of the threshold.

## Inclusion floor
As in P1: a model is interpreted only if ISO parse rate >= 0.90 and ISO accept rate on right minus on wrong >= 0.10 (computed on TP pools' candidates of the same set).

## Kill criteria
- H1 or H2 fail for a model: the pilot null does not generalize; report it, the paper's claim about rejection channels is restricted to the models where it held.
- H3 and H4 fail (AUROC significantly >= 0.75 is not the test; failure means the CI upper bound reaches 0.75): tournament statistics may carry a usable absence signal; report as such.

## Power
TA pools: if the true choosing rate is 0.02, with n >= 100 TA pools the 95% upper bound is below 0.10 with probability above 0.95. AUROC: with about 50 TP/TA problem pairs and a true AUROC of 0.62 as in P2, the bootstrap CI half-width is about 0.08, so the upper bound falls below 0.75 with probability around 0.8. Stated limitation: AUROC power is moderate.
