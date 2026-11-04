# S1 and S6 screen note (exploratory), claude-haiku-5-5, MathArena screen split

Subject parameters: claude -p 2.1.317 defaults (adaptive extended thinking on), no tools, fixed system prompt (harness/run_jobs.py). Resolved id claude-haiku-5-5 on every call. 60 problems (smt_2025, cmimc_2025, brumo_2025, apex_2025, hmmt_nov_2025, arxivmath-0626) each with a TA pool of 3 officially graded wrong solutions from MathArena's 2026 model lineup and a TP pool (2 of those + 1 graded right). Numbers from results.txt and results_solve.json (recomputed from raw).

Calibration gate (amendment A2): haiku solve rate on these 60 problems 0.60 (1 no-answer); ISO false accept on wrong candidates 0.111; accept of right candidates 0.85. Gate passed.

S1 (lineup): TA choosing ISO-any 0.30, PICK 0.267, EACH 0.317, FORCED 1.0 by construction. PICK minus ISO -0.033 (95% CI -0.15 to +0.083; McNemar 5 vs 7, p 0.77). EACH minus ISO +0.017 (-0.117 to +0.15). PICK minus EACH -0.05 (-0.167 to +0.067). Kill rule (|diff| < 0.05 with CI within +-0.15): met at the boundary (lower bound -0.15). No sign that simultaneous presentation raises false choosing for this model on these items.
TP: hit PICK 0.867, EACH 0.90, ISO 0.85; false choice (any wrong accepted or chosen) PICK 0.083, EACH 0.05, ISO-any 0.30. ISO-any lets several candidates pass, PICK at most one, so the TP false comparison favours single-choice formats by construction; reported descriptively.

S6 (selection then verification): wrong candidates that FORCED picked were accepted by isolated verification at 0.20, unpicked wrong candidates at 0.067; within-pool difference +0.133 (95% CI +0.025 to +0.25, 60 pools). Kill rule (|diff| < 0.05) not met. Reading: a forced choice concentrates on exactly the wrong candidates that the same judge's own verification would pass, so "rank, then verify with the same model" verifies the most dangerous candidate. Plausibly a known selection effect; needs a prior-art check before any weight.

Sonnet S1 not yet run (cost); sonnet solve rate on its 23 problems 0.435 (3 no-answer), so it is calibrated.
