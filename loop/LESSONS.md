# Lessons (comparisons between sibling branches)

Format: date, branch compared with sibling, what the difference taught, source branch, and whether it changed a later design.

## 2026-11-03 21:55 UTC: B1 (P1) versus sibling B2 (P2), same 80 pools, same judges
- B1: with a NONE option or one verdict per candidate, haiku, sonnet, opus and fable rejected every wrong candidate in every format (0 of 40 TA pools).
- B2: the same judges asked the tournament's forced pairwise question named a unique Copeland winner in 34 of 40 (haiku) and 37 of 40 (sonnet) of the same TA pools, a unanimous winner (won all 4 of its comparisons) in 29 and 33 of 40; mean decisiveness (top Copeland score over maximum) was 0.925 and 0.956. The tournament's own statistics separated TA from TP only weakly (AUROC 0.59 to 0.67, CIs from a bootstrap that resamples problems, so each problem's TA and TP pools, which share two wrong candidates, move together). [Corrected 2026-11-03 after an auditor note: an earlier wording called the mean decisiveness a share of pools.]
- Lesson (source: B2, applied to B1): for current judges the vulnerability is not co-presentation but the absence of a rejection channel in the aggregation format. Design change: P3 keeps the NONE channel in PICK but must also add a forced-choice arm (no NONE), so the format effect can be measured on hard items too. Recorded as an amendment to P3 before stage B.
- Lesson (source: B1): items inside judge competence put every arm at the floor, which tests nothing. Any further B1 pilot must first show a nonzero ISO false accept rate, which P3 measures in stage A by the judge's own solve rate.

## 2026-11-03 23:40 UTC: S1 (B1 on fresh MathArena pools) versus sibling S3 (B2 tournaments), same pools, haiku
- Same judge, same target-absent pools: with a NONE option it chose a wrong candidate no more often than isolated verification accepted one (0.27 vs 0.30); asked forced pairwise questions it crowned a unique winner in 0.90 of the pools, and the tournament's decisiveness barely separated TA from TP (AUROC 0.56).
- Lesson (source B2, applied to B1 and the confirmation): the failure lives in the aggregation format, so the confirmation tests the null with a NONE option and adds the forced-format consequence (S6, which came from comparing FORCED picks with ISO verdicts inside the S1 data). This changed C2's design: H2 was added because of this comparison.
## 2026-11-03 23:45 UTC: P1 (stale items) versus S1 (fresh, calibrated)
- The only model showing a lineup effect was an outdated 2B model (gemma-2-2b) on stale items. Current judges show none on stale or fresh items. Lesson (source P1 open-model arm): capability is a plausible moderator; calibration gates must precede any arm comparison, which the user's steering also required.
