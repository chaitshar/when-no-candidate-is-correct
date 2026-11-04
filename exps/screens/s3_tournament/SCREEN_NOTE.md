# S3 screen note (exploratory): tournaments on MathArena screen pools, claude-haiku-5-5
40 problems (TA and TP pools), every ordered pair judged in a forced-choice call (480 calls, 0 parse failures, 3.13 USD). Numbers from results.json.
- AUROC of decisiveness for TP vs TA: 0.5625 (problem-clustered 95% CI 0.475 to 0.65). Order consistency AUROC 0.48 (0.40 to 0.56).
- TA pools: unique Copeland winner in 0.90, unanimous winner (4 of 4 comparisons) in 0.75. TP pools: unanimous 0.875; winner is the right candidate in 0.825.
Kill rule (AUROC CI lower bound >= 0.75, i.e. tournaments carry an absence signal): not met; the tournament's own statistics carry little signal that no candidate is right. Consistent with pilot P2 (stale MATH items). Prior art to check: tournament-style rankers (AI co-scientist) are known to lack an absolute check; whether this is stated and measured is the novelty question.
