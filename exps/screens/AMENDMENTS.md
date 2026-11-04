# Screens amendments

## A1 (date -u about 22:40 UTC 2026-11-03): withdrawn before any screen data
The S1 to S10 preregistration relied on gen/progtrace (retired by the user). No screen data were collected. It is replaced by exps/screens/PREREGISTRATION_v2.md on established benchmarks.

## A2 (date -u 2026-11-03 ~23:20 UTC): calibration outcome and S1 calibration on pool problems
- Calibration split (aime_2025, hmmt_feb_2025; cal/results.json): claude-haiku-5-5 solved 52/60 (0.87), claude-sonnet-5-5 49/60 (0.82). Both are above the [0.2, 0.8] band on this split, so the 2025 February contests are not interpreted for either model.
- Contamination check invalid as designed: usage records show the CLI runs these models with adaptive extended thinking by default (median thinking tokens with "answer only": haiku 1916, sonnet 352; with working: 2219 and 442). "No working" therefore does not remove reasoning, and answer-only accuracy (0.88 and 0.87) cannot separate memorization from reasoning. Recorded as a limitation; the subject parameters are now stated as "claude -p 2.1.317 defaults, adaptive extended thinking on, no tools, fixed system prompt".
- Added before any S1 analysis: a SOLVE call per S1 problem for each S1 judge (haiku 60 problems, sonnet 25). S1 is interpreted for a model only if its solve rate on the S1 problems is in [0.2, 0.8] and its ISO false accept rate on wrong candidates is above 0.

## A3 (date -u 2026-11-03 ~23:30 UTC): S5 scoring sensitivity and cost overrun
- After S5 data: hand-crafted Who&When labels use base agent names ("Orchestrator") while logs name roles with suffixes ("Orchestrator (thought)"), and one label is spelled "Websurfer". Strict scoring (analyze.py, preregistered) stays primary; analyze_norm.py adds a sensitivity score that strips a trailing parenthetical and lowercases. Step scoring unchanged.
- S5 cost 11.16 USD (haiku 0.69, sonnet 10.48), over the 10 USD per-screen limit by 1.16 USD. Deviation recorded; caused by long hand-crafted logs (median 42k characters).
