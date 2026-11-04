# P1 amendments and deviations

## D1, 2026-11-03 22:30 UTC: open-model runner stopped early (deviation)
The user's Mac runner was stopped at the user's request. Final merge (date -u 2026-11-03 ~23:45): complete raw outputs for 7 of 8 models (gemma-2-2b, granite-3.3-2b, qwen2.5-0.5b, qwen2.5-1.5b, qwen3-0.6b, smollm2-1.7b, smollm2-135m) and a partial set for phi-3.5-mini (9 of 360 jobs, stopped at the user's request). Inclusion-floor outcomes are in results.txt. Under the current rules these older small models are outdated subjects: their data are kept and reported but carry no weight in any claim.

## D2, 2026-11-03 22:30 UTC: scope of P1
Per the current rules, P1 is limited to GPT-4-era (2022) PRM800K errors on public MATH problems, which are likely in pretraining data. Its result (no false choices) is reported as a floor on those items for the exact models tested, not as evidence about current-model behaviour on hard or fresh items.
