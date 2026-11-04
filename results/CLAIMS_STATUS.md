# Live claims (updated 2026-11-04 ~10:05 UTC; numbers in results/claims.json, regenerated from raw)

Settings for all subject claims: Claude Code 2.1.318 print mode (2.1.317 for S1/C2), defaults with adaptive extended thinking, no tools, fixed system prompt (sonnet in C3: plus a "no tools" sentence), MathArena items, calls on 3 and 4 Nov 2026.

| claim | model | evidence | status |
|---|---|---|---|
| On haiku-unsolved problems, pooled PICK also raises hits on pools containing a right solution; discriminability not detectably lower than ISO (H4 not confirmed): criterion shift; PICK J near 0 for haiku | haiku, sonnet | exps/c3/results_a4.json | CONFIRMATORY ARM (A4): H4 not confirmed; reported as criterion shift |
| Confidence lineup ROC equal for pooled vs isolated on unsolved (pAUC diff +0.002 [-0.030,+0.045]); base-rate statement does not move the criterion (+0.01 [-0.08,+0.12]) | claude-haiku-5-5 | exps/c3/results_a5.json | A5: H6, H7 not confirmed (informative nulls) |
| Post hoc stratum audit and duplicate exclusion leave all conclusions unchanged | haiku, sonnet | exps/c3/results_sensitivity.json | POST HOC sensitivity |
| On problems the judge did not solve in two attempts, PICK (NONE allowed) chooses a wrong solution from an all-wrong pool more often than ISO-any accepts one: 0.60 vs 0.36, d +0.24 [+0.13,+0.36], Holm 0.001 | claude-haiku-5-5 | exps/c3/results.json | CONFIRMED (C3 H1u) |
| Forced pick is the wrong solution own isolated verification accepts most, on unsolved problems: +0.19 [+0.11,+0.28] | claude-haiku-5-5 | exps/c3/results.json | CONFIRMED (C3 H2u) |
| Penalty larger on unsolved than solved after competition fixed effects: b +0.12 [-0.03,+0.27] | claude-haiku-5-5 | exps/c3/results.json | INCONCLUSIVE (C3 H1, primary) |
| Same as H1u and H2u with sonnet judging haiku-defined strata: +0.13 [+0.04,+0.23]; +0.28 [+0.18,+0.38] | claude-sonnet-5-5 | exps/c3/results_sonnet.json | CONFIRMED (strata defined by another model) |
| Sonnet verifying haiku's forced picks reduces the inflation: +0.02 [-0.04,+0.07] | haiku selects, sonnet verifies | exps/c3/results_h3.json | INCONCLUSIVE (no reduction detected) |
| C2 lineup and select-then-verify | claude-haiku-5-5, claude-sonnet-5-5 | exps/c2_confirm | NOT INTERPRETABLE (superseded by C3) |
| No penalty on screen problems the judge mostly solves | claude-haiku-5-5 | exps/screens/s1_lineup | SCREEN |
| Tournaments carry little absence signal (AUROC 0.56) | claude-haiku-5-5 | exps/screens/s3_tournament | SCREEN |
| Who&When attribution below 0.8 | haiku, sonnet | exps/screens/s5_whowhen | SCREEN |
| P1, P2 on PRM800K/MATH | haiku, sonnet, opus, fable | exps/p1_lineup_math, p2_tournament | STALE items; floor |
| Earlier post hoc solvability split (S1+C2) | claude-haiku-5-5 | exps/posthoc | SUPERSEDED by C3 |
| Corpus lineup results | older snapshots | corpus/ | STALE: lineage only |
