# P3 amendments

## A1, 2026-11-03 ~21:55 UTC, before any stage B call
Added arm FORCED (prompt `forced` in harness/lineup_prompts.py): the simultaneous pool with no NONE option, one call. Reason: P2 showed that forced-choice aggregation names a winner in all-wrong pools that the same judges reject in isolation (lesson in loop/LESSONS.md). For FORCED, "choosing" is always 1 by construction, so its metrics are: P(choice = right) on TP pools, and on TA pools whether the FORCED choice equals the PICK choice when PICK chose a candidate. FORCED is run for haiku, sonnet and opus on the same pools. No other change to the preregistered analysis.

## A2, 2026-11-03 ~22:00 UTC, before any stage B call and before stage A finished
Observation from partial stage A (no judging data): haiku solved about 83% of its samples, so few problems will have 3 distinct wrong answers. Change: stage A2 draws 8 more haiku and 4 more sonnet SOLVE samples for every problem whose stage A samples include at least one wrong or unparseable answer and fewer than 3 distinct wrong answers. Pool rule order extends to haiku 0 to 3, sonnet 0 to 1, haiku 4 to 11, sonnet 2 to 5; everything else in the pool rule is unchanged. Solvability for F5 stays defined on stage A samples only (haiku 0 to 3, sonnet 0 to 1), so the top-up does not change the moderator. Consequence stated now: the pilot pools are selected toward problems a solver fails, which is the intended regime (beyond competence), and the pool set is smaller.

## A3, 2026-11-03 22:30 UTC: P3 parked after stage A2 was stopped partway
Under the current rules (loop/STEER.md) Omni-MATH is a public set and only secondary evidence after a contamination check, and the subject budget is capped. Stage A2 was stopped partway (raw files kept and committed; 1998 stage A files in total). No stage B call has been made. P3 is parked; it will only resume as secondary evidence after a contamination check, if budget allows.
