# P1 pilot preregistration: lineup effect on real math with human-verified wrong candidates (branch B1)

Written 2026-11-03 before any subject call for this experiment. Pilot: exploratory, used only to decide whether and how to run a confirmatory study. Pilot data never enters a confirmatory test.

## Question
When an LLM judge sees several candidate solutions to a MATH problem, none of which is correct (a target-absent pool, TA), does it choose a wrong one more often than it accepts any of the same candidates when each is judged alone in a fresh call? And which part of the presentation is responsible: the request to PICK one (F1), co-presentation itself (EACH arm), simultaneity versus a true sequential procedure (SEQ), or the absence of a base-rate cue (BASE, T1)? Does the judge's own ability to solve the problem moderate it (F5)?

## Items
- banks/prm_bank.jsonl built by banks/build_prm_bank.py from PRM800K phase 2 test labels (GPT-4 solutions to MATH test problems, human step labels). A wrong candidate has a human-found error step AND a final answer that differs from the MATH ground truth by string normalization and a sympy check. A right candidate has every step rated acceptable by labelers and a final answer equal to the ground truth.
- Eligible: problems with at least 3 distinct wrong answers and at least 1 right candidate (95 problems). Seed 20261103 picks 40 for this pilot; the other 55 ids are in reserved_ids.txt and are not looked at until the confirmatory build.
- TA pool: 3 wrong candidates. TP pool: 2 of those wrong + 1 right. Candidate order is shuffled once per pool and shared by all arms.

## Arms (prompts in harness/lineup_prompts.py, one fresh isolated call per judgement)
- ISO: each candidate alone, VERDICT ACCEPT or REJECT. 3 calls per TA pool (the TP pool reuses the 2 shared wrongs and adds 1 call for the right one).
- PICK: all candidates in one prompt, "which solution has the correct final answer, if any? It is possible that none is correct", CHOICE k or NONE. 1 call.
- BASE: PICK plus "about half of the problems have no correct solution among those shown" (true for the 50/50 TA/TP mix in this pilot). 1 call.
- EACH: all candidates in one prompt, ACCEPT or REJECT for each. 1 call.
- SEQ: one multi-turn conversation, one candidate per turn, a verdict before the next is shown, no going back, all candidates shown (no stopping rule; the stop-at-first-accept variant is computed from the same data). 3 turns.
- SOLVE: the judge solves the problem alone (ANSWER line), graded programmatically against MATH gold with the same normalization and sympy check. 1 call per problem.

## Subjects
Claude haiku, sonnet, opus via harness/run_jobs.py (isolated `claude -p`: no settings, no MCP, no tools, fixed short system prompt, empty cwd). 40 problems each, all arms. Fable: 16 problems, ISO and PICK on TA pools only (cost). Open-weight models (8, harness/models.json) run on the user's Mac from open_jobs.jsonl: ISO, PICK, EACH, SOLVE (no SEQ, the runner is single turn); qwen3-0.6b gets "/no_think"; temperature 0.7, seed 0, max_tokens 1024.

## Metrics (unit of analysis: problem; pools nest in problems)
- Choosing rate on TA pools: PICK and BASE: CHOICE is not NONE. EACH and SEQ: at least one ACCEPT. ISO reference: at least one of the 3 ISO verdicts is ACCEPT (the "independent judgements" prediction for the same candidates).
- Pilot primary contrast, per model: D_pick = choosing(PICK) minus choosing(ISO) on TA pools, paired by problem, 95% percentile bootstrap over problems (10000 resamples), and an exact McNemar test on discordant problems.
- Secondary contrasts: EACH minus ISO, SEQ minus ISO, BASE minus PICK, PICK minus EACH (F1: format versus co-presentation).
- TP pools: hit rate (right chosen or accepted), false choice rate, and correct rejection on TA (diagnosticity of a choice).
- F5: TA choosing in PICK and ISO split by whether the judge's SOLVE answer is correct.
- Cost, tokens, wall time, failures and retries per arm and model (user rule 3). Compute matching: PICK, EACH and BASE use 1 call; ISO and SEQ use 3. Contrasts are reported with this stated; a confirmatory study will include a compute-matched comparison if a 1-call arm differs from ISO.
- Parse failures: counted per arm; an unparseable reply is neither a choice nor a rejection and is reported. Sensitivity: treating it as a choice and as no choice.

## Model inclusion rule (fixed now, applied before looking at any pooled arm)
A model's pooled-arm data are interpreted only if, in the ISO arm: parse rate is at least 0.90 for Claude and 0.80 for open models, AND accept rate on right candidates minus accept rate on wrong candidates is at least 0.10. Excluded models are still reported with all numbers. An effect absent in a model that fails this floor means nothing.

## Power
Pilot: 40 problems per model. If per-problem choosing differs by 0.25 with a discordance rate of about 0.35, McNemar has roughly 80% power at alpha 0.05 with 40 pairs. Smaller effects will only be estimated. The pilot is for direction, size, and parse rates, not for confirmation.

## Decisions (kill criterion)
- Run a confirmatory B1 study if, for at least 2 of the 3 included Claude models, the 95% CI of D_pick or of PICK minus EACH excludes 0. The sign seen in the pilot fixes the direction of the confirmatory hypothesis.
- Kill the B1 headline if for every included Claude model |D_pick| < 0.05 and its CI lies within plus or minus 0.15. A null here is recorded and reported as a finding about real math with human-verified wrongs.
- Any other pattern: write an amendment that names the next pilot before running it.

## Analysis code
exps/p1_lineup_math/analyze.py, written before data and committed with or before the first raw output; any later change is listed in AMENDMENTS.md.
