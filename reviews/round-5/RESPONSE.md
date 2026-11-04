# Response to round-5 reviews (2026-11-04T10:54:25Z)
Blockers fixed:
- Integrity, stale cost_subjects: cost ledger and claims regenerated; make_claims.py --no-run now leaves results/claims.json unchanged.
- Methods, criterion-shift wording too strong: abstract, contributions and A4 text now say "consistent with a criterion shift; does not exclude a loss of discrimination (interval admits about a quarter)"; the A4 quantity on the audited strata is reported (analyze_a4_sensitivity.py, post hoc).
Non-blocking, addressed:
- Area chair: H3 sentence now scoped to "over all judged problems"; question form reported as an untested estimate for both models (sonnet does not replicate clearly); pools with equivalent wrong answers in different forms disclosed.
- Integrity: abstract distinguishes locked (278) from judged (227) problems; missing units (MIXED, unresolved, three sonnet safeguard blocks) and the empty gemma arm disclosed.
- Prior art: Kim and Jung (AACL-IJCNLP 2026 short paper) and Chen et al. (HICSS-60) cited after fetching their abstract pages.
Design objection answered with a new experiment:
- Hostile expert (no confidence ROC; no test of whether instructions move the criterion): amendment A5 preregistered before data (confidence ROC H6, base-rate manipulation H7), running.
