# P2 pilot preregistration: pairwise tournaments on target-absent pools (branch B2, hypotheses U1, U2, K7)

Written 2026-11-03 before any subject call for this experiment. Pilot, exploratory.

## Question
Tournament-style rankers (pairwise forced-choice comparisons aggregated into a ranking, as in AI co-scientist Elo tournaments) always produce a winner. When no candidate is correct (TA pool), does the tournament look any different from when one is (TP pool)? If not, the ranker cannot signal that the pool should be rejected.

## Items
The 80 pools of pilot P1 (exps/p1_lineup_math/pools.json): 40 TA pools of 3 human-verified wrong GPT-4 MATH solutions and 40 TP pools (2 of those wrong + 1 right) from the same 40 problems.

## Procedure
Every ordered pair (i, j), i != j, of a pool is judged in one fresh isolated call (6 calls per pool), prompt `pair` in harness/lineup_prompts.py: forced choice WINNER A or B. Models: haiku and sonnet.

## Metrics (unit: pool; TA and TP pools pair by problem)
- Copeland wins per candidate (0 to 4). Decisiveness = max wins / 4.
- Order consistency = fraction of the 3 unordered pairs whose two orders name the same winner.
- Cycle or tie = no unique Copeland maximum.
- Primary: AUROC of decisiveness for telling TA from TP (higher decisiveness taken as evidence of TP), 95% CI by bootstrap over problems. Secondary: the same for order consistency; P(winner is the right candidate) on TP; TA versus TP difference in consistency, paired by problem.
- Parse failures counted; a pair with an unparseable call counts as no win for either side, reported.
- Cost and wall time per model.

## Decisions
- U1 supported (pilot level) if AUROC of decisiveness <= 0.65 for both models.
- U1 refuted if AUROC >= 0.75 with CI lower bound above 0.6 for both models: tournaments carry an absence signal.
- If order consistency separates TA from TP (AUROC >= 0.75), record it as a candidate cheap absence detector, a new ledger row, to be tested out of sample.

## Analysis code
analyze.py in this folder, committed before raw data.
