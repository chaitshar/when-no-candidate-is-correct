# Steering from the user (overrides the plan, not the non-negotiable rules)

Received by message during the run. Recorded verbatim in substance.

## 2026-11-03 ~21:15 UTC: open-weight subjects
All eight models from harness/models.json run on the user's Mac. Commit the preregistration first, then commit and push `exps/<id>/open_jobs.jsonl` in run_open_jobs.py format with a `model` field. A local agent pushes raw outputs to branch `open-model-results` under `exps/<id>/raw/open/<model>/`; merge it. Never simulate. Keep the inclusion rule preregistered. Smoke test notes: qwen3-0.6b needs /no_think or larger max_tokens; smollm2-135m produced no JSON.

## 2026-11-03 ~21:25 UTC: additional rules
1. No LLM judge as the only ground truth. Use executable or independently checkable answers; LLM grading only as a supplement with its agreement against ground truth reported.
2. Compare under matched compute. If an arm uses more calls or tokens, say so and test whether extra compute alone explains the gain.
3. Report tokens, cost, wall time, retries and failure rates per arm (total_cost_usd from claude -p).
4. Label every cited work's exact status (main conference, Findings, demo, workshop, journal, preprint, technical report). Never call an arXiv post accepted. MLR-Bench (NeurIPS 2025) reports coding agents often fabricate or invalidate results, so integrity checks stay artifact based.
5. Do not call the process fully autonomous. PROVENANCE.md lists what humans supplied: idea lineage, brief, gates.
6. Write AUDIT_SAMPLE.md: a stratified sample of 30 claims and 20 citations for hand checking, with file paths and URLs.
7. Self-improvement: accept a change only after regression tests on earlier canaries, and check the updated prompt is actually followed downstream (EMNLP 2026). Verify any paper before citing it.
