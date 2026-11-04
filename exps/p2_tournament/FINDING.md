# P2 finding (pilot, exploratory): pairwise tournaments crown a decisive winner in all-wrong pools

Numbers from exps/p2_tournament/results.txt (analyze.py on raw/, 960 calls, 0 parse failures).

- 40 target-absent (TA) pools of 3 human-verified wrong GPT-4 MATH solutions, 40 target-present (TP) pools (2 of those wrong + 1 right), every ordered pair judged in a fresh forced-choice call.
- Mean decisiveness (top Copeland score / max, a per-pool score averaged over pools, not a share of pools): haiku TA 0.925 vs TP 1.0; sonnet TA 0.956 vs TP 1.0.
- Share of TA pools with a unique Copeland winner: haiku 34/40, sonnet 37/40; with a unanimous winner (4 of 4 comparisons won): haiku 29/40, sonnet 33/40. TP: 40/40 unique and unanimous for both. Computed from raw/ by a one-off script after an auditor note (exploratory, added 2026-11-03 ~22:15 UTC); the C1 analysis computes the unique-winner share as a frozen descriptive.
- AUROC of decisiveness for telling TP from TA: haiku 0.64 (95% CI 0.58 to 0.71), sonnet 0.59 (0.54 to 0.65). Both at or below the preregistered 0.65 threshold: U1 supported at pilot level. The bootstrap resamples problems, so each problem's TA and TP pools (which share two wrong candidates) are resampled together; the CIs are problem-clustered.
- Order consistency: haiku TA 0.80 vs TP 0.96, sonnet 0.83 vs 0.97; AUROC 0.67 (0.59 to 0.76) and 0.67 (0.57 to 0.75). Below the 0.75 threshold for a "cheap absence detector".
- TP winner was the right candidate in 40 of 40 pools for both models.
- Cost: haiku 0.45 USD, sonnet 5.52 USD for 480 calls each.

Juxtaposition with P1 (same pools, same models): in isolation both judges accepted 0 of the wrong candidates and in PICK they chose NONE in every TA pool. The same judges, asked the forced pairwise question a tournament uses, produce a decisive winner in most all-wrong pools. The failure is in the aggregation format, which has no rejection channel, not in the judges' ability to reject.

Caveat: forced choice must name a winner, so decisiveness near 1 is partly by construction. The informative part is how little the tournament's own statistics (decisiveness, order consistency) separate TA from TP pools when the judge would reject every TA candidate if asked.
