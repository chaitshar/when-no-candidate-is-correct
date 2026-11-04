# P3 pilot preregistration: lineup effect on items beyond judge competence (branch B1, follow-up of P1)

Written 2026-11-03 before any subject call for this experiment. Pilot, exploratory. New ledger rows: B1-P3a (PICK minus ISO on hard items), B1-P3b (F5: choosing depends on judge solvability).

## Why
In P1 (PRM800K, MATH) haiku made no false accept in any arm (see exps/p1_lineup_math/results.txt): a floor. Prior corpus effects came from older or weaker judges. The open question becomes whether the lineup effect returns when the item is beyond the judge's competence, which is the regime of real discovery pools.

## Items
Omni-MATH (github.com/KbsdJames/Omni-MATH, commit 23be225c, Omni-Math.jsonl sha256 7c87be8e...): olympiad problems (HMMT, Canadian contests, IMO shortlist and others) with official answers. Eligible: integer answer and difficulty at least 4 (1355 problems). Seed 20261104 picks 240 for this pilot (problems.json); the other 1115 indices are reserved_idx.txt for confirmation by an independent agent.

## Stage A: candidate generation (jobs_stageA.jsonl)
Each problem is solved by haiku 4 times and sonnet 2 times with the SOLVE prompt (fresh isolated calls, default sampling). A reply's answer is the ANSWER line, stripped of $, \boxed{} and thousands separators. Correct means integer equality with the official answer. Unparseable or non-integer answers are not candidates. Ground truth is the official answer only (user rule 1); no LLM grading.

## Pools (rule fixed now)
For each problem, candidates are taken in solver order (haiku 0 to 3, then sonnet 0 to 1), keeping the first reply for each distinct wrong integer answer. TA pool: the first 3 distinct wrong answers, if 3 exist. TP pool: the first 2 of those plus the first correct reply, if one exists. Candidate text is the solver reply with its ANSWER line removed, followed by "Final answer: <answer>". Order shuffled once per pool with seed f"20261104-{pid}", shared across arms. Haiku generated most candidates, so haiku judges are partly judging their own kind of output; this is reported, and sonnet and opus judges are not judging their own output except for sonnet-generated candidates, which are tagged.

## Stage B arms and judges
ISO, PICK, EACH, SEQ (same prompts as P1, harness/lineup_prompts.py) and SOLVE (opus only, 1 call per problem; haiku and sonnet solvability come from stage A). Judges: haiku and sonnet on all pools; opus on up to 60 problems (cost); fable on up to 16 TA pools, ISO and PICK.

## Metrics, inclusion and decisions
As in P1 (exps/p1_lineup_math/PREREGISTRATION.md), unit problem, bootstrap over problems, McNemar, inclusion floor on ISO parse rate and ISO discrimination. Additional F5 analysis: TA choosing in each arm against the judge's own solve rate on the problem (haiku: fraction of its 4 stage A samples correct; sonnet: of 2; opus: 1 SOLVE call), logistic regression of choosing on arm x solve rate with problem cluster bootstrap.
- Go to confirmation on hard items if for at least 2 of the included Claude models the 95% CI of PICK minus ISO, or of PICK minus EACH, excludes 0.
- Kill the B1 headline on hard items if all |D| < 0.05 with CIs within plus or minus 0.15. Then B1 is reported as a capability-bounded null and the program moves to B2 or B3.

## Analysis code
analyze.py, adapted from P1 (same functions), committed before stage B data.
