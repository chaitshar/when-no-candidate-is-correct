# Evolution log (self-improvement after each cycle)

## Cycle 1 retro (2026-11-03 21:05 to 2026-11-04 00:05 UTC)
What went wrong or wasted effort:
1. Item validity was checked after spending, not before. P1 (34 USD) and P2 ran on public MATH items where every current judge was at the floor; Opus and Fable were run to learn a floor Haiku had already shown (user flagged 19.7 USD on Opus). Fix adopted: calibration gate per model before any arm (now in every preregistration).
2. Generated tasks (S0) were built and then retired by the user as made-up data; about 4 USD and an hour lost. Fix: use established benchmarks; check availability and licence first.
3. Time stamps were written from memory and were wrong (STATE said 23:00 when date -u said 22:27). Fix: always `date -u`.
4. Shell waits that used `pgrep -f` and `pkill -f` matched their own command line and killed the shell twice. Fix: match on `ps -eo args` with awk on the process name.
5. A wording error (mean decisiveness called a share of pools) reached LESSONS.md and was caught by the user's auditor, not by the loop. Fix: numbers in notes come from a script output pasted verbatim, and each note states its unit.
6. Snippet-based prior-art kills: one kill reason (Kenton et al.) was contradicted by the full text once the network opened. Fix: never kill on snippets alone; mark such verdicts provisional.
7. Who&When strict name matching undercounted on hand-crafted logs; found after data. Fix: inspect label formats on a few items before freezing a scorer.

Mutable changes made (playbook v1): role separation, failure taxonomy, reviewer lens prompts (loop/playbook/v1). No reviewer prompt change has been proposed yet, because no reviewer failure has been observed yet (evidence bar: changes only for an observed failure).

Canary detection rates: see the section below once the canary run is done.

## Cycle 2 retro (2026-11-04 00:00 to 01:40 UTC)
8. An answer-parser bug (a greedy \W* swallowed "$\" in LaTeX answers) survived two review rounds and several self-checks. It changed every solve rate and flipped the calibration gates. Only an independent recomputation with the reviewer's own parser found it. Fix: grade with two independently written parsers and require agreement before freezing gates. Add a canary with LaTeX answers to the parser tests.
9. The preregistration did not say how per-set and union gates combine. Fix: every preregistration states its gate-combination rule explicitly.
10. A per-arm cost cap written in the preregistration (sonnet 12 USD) was not enforced by the runner, which led to a 29 USD spend. Fix: the runner takes a --max-usd flag and stops when it is reached.
11. Self-improvement step: no canary study was run (budget), so no reviewer-prompt change is proposed or promoted. Detection rates were not measured.

## Canary study, cycle 3 (2026-11-04T10:35:15Z)
Ten copies of the draft (as of about 10:05 UTC), each with one defect planted by an independent agent (2 each: altered headline number, fake citation, leaked-answer claim, wrong unit of analysis, false novelty), split 5 train and 5 held out (canaries/KEY.json, hash in KEY.sha256, verified by the scorer). Each copy was reviewed blind by a fresh claude-sonnet-5-5 agent with the playbook v1 integrity and methods brief (at most 20 tool calls). Scored by an independent claude-haiku-5-5 agent (canaries/SCORES.json).
- Detection: train 5/5, held-out 5/5, every type 2/2.
- Consequence under the evidence bar: no reviewer failure was observed, so no playbook change is proposed and nothing is promoted; a permutation test against the current version is moot at 100% detection. Regression on earlier canaries: none existed before this study.
- Limits: ten canaries, one defect each, all checkable against artifacts; reviewers were instructed not to read paper/ but could in principle have compared against it; detection of subtle defects (for example the parser bug that two earlier review rounds missed) is not measured by this set.
- Draft-level issues raised in at least 5 copies were fed back into the paper fixes (CLI version, duplicates, arXiv set count, H3 wording).

## Cycle 4 retro (session 2, ended 2026-11-04T12:06:18Z)
1. Round-4 reviewers found two data-quality problems the loop had missed: both graders rejected correct answers written with prefixes, and official MathArena labels contain errors. Fix for the next study: read every non-integer answer pair by hand before freezing strata, and audit official candidate labels symbolically and by hand before judging.
2. The hostile-expert lens, first run in round 4, was the most productive. It forced A4 (target-present pools) and A5 (confidence ROC). Those changed the paper's central claim from "lineup penalty" to "criterion shift with a near-uninformative pick". Run this lens from the first review round.
3. Text added in response to a round introduced the next round's blocker twice (round 7, and the "frontier" wording in round 3). Fix: every sentence added after a review needs a pointer to the artifact that supports it.
4. Convergence was reached in rounds 8 and 9 by freezing the text between them, apart from a one-sentence clarification.
