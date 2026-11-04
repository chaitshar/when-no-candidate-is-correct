# Response to round-3 reviews (date -u 2026-11-04 ~01:35 UTC)
Fixed, not re-reviewed (budget exhausted):
1. Answer-parser bug (methods B1): fixed in harness/parse.py, recorded in exps/c2_confirm/AMENDMENTS.md A3, and every analysis re-run. Consequence: haiku's solve rate on the 2026 contests is 0.88, above the band, so C2 is not interpretable for haiku. The paper now says so.
2. Solvability split built on mislabelled solves (methods B2): re-run with the fixed parser. The paper reports the pooled split (+0.15 vs -0.04) and states that within-source samples cannot separate solvability from source.
3. "Frontier models" wording (area_chair B1): candidates are described as coming from MathArena's 2026 lineup, which includes smaller open models such as Qwen3-4B.
The FINAL verdicts are the reviewers' last-round files, copied unchanged; their blockers refer to the text before these fixes.
