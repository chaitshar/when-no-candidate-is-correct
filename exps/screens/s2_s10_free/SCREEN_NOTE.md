# S2 and S10 screen notes (exploratory; numbers from results.json, recomputed by analyze.py from MathArena parquet files)

S2 (self-consistency agreement as confidence, MathArena runs, screen split, 4 samples per model and problem):
- For the 10 models with at least 150 screen-split problems (DeepSeek-v3.2, GLM 5, GPT-5.2, Gemini 3 Flash, Gemini 3 Pro, Grok 4.1 Fast, Kimi K2.5, QED-Nano, Step 3.5 Flash) plus GPT-5.5 (60 problems), AUROC of the modal vote share ranged 0.75 to 0.98 and unanimous answers were wrong in 0 to 6.2 percent: the field's claim holds for these runs.
- The newest models were run by MathArena on only about 12 screen problems (apex and arXiv-derived sets). There, unanimous (4 of 4) answers were wrong in 2 of 4 (Opus 4.6), 4 of 8 (Opus 4.7), 4 of 6 (DeepSeek v4 Flash and Pro), 3 of 4 (Gemini 3.5 Flash), 5 of 7 (Gemini 3.6 Flash), 3 of 4 (Kimi K2.6), 4 of 5 (Nemotron 3 Super). Tiny n and confounded with problem difficulty (different problem subsets per model). New hypothesis S2b, ledger row: on research-level arXiv-derived problems, unanimous self-consistency is frequently wrong. Testable on held-out arxivmath-0826 and 0926 outputs.
- These are other labs' and older Claude models run by MathArena; no claim here concerns claude-haiku-5-5 or claude-sonnet-5-5.

S10 (error correlation, homogeneous vs heterogeneous):
- 28 accuracy-matched model pairs: mean error phi between different models 0.54, within a model across its own samples 0.67, difference -0.14 (descriptive bootstrap over pairs -0.20 to -0.08; pairs share models, so not a valid test). Kill rule (|diff| < 0.05) not met: real model diversity lowers error correlation on these runs, but errors stay strongly correlated across vendors. Not surprising against the literature; low priority.
