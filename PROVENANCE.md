# Provenance

Run: 2026-11-03 21:05 UTC onward, one Claude Code cloud session (branch claude/execute-loop-prompt-doyhzw). This was not a fully autonomous process: humans designed its scaffolding and steered it repeatedly.

## What humans supplied
- **Idea lineage (Chaitanya Sharma's earlier corpus, `corpus/`):** the Lineup Problem idea (LLM verifiers choosing from target-absent pools, the bridge to eyewitness lineups), the earlier pilots (August to October 2026, older model snapshots, synthetic items), the novelty audit and literature atlas, and the harness the subject runner was adapted from. Under the current rules these results are lineage only, not evidence.
- **The brief and guard rails:** `loop/PROMPT.md` (research brief), `loop/gates.py` and `loop/RUBRIC.md` (locked release gates and review rubric), `loop/setup.sh`, `harness/models.json` and the open-model runners.
- **Steering during the run:** recorded in `loop/STEER.md` (current rules) and `loop/STEER_history.md`. It covered cost caps; current models only and no generalization across models; a ban on made-up data, with established benchmarks only; the 230 USD budget; open network access; the gemma-4-e4b runner; and an auditor's correction of a wording error in the P2 notes.
- **Open-model runs:** executed on the user's Mac by a local agent (branch `open-model-results`).

## What the AI did
Claude (Claude Code, Opus-tier orchestrator; subagents on Haiku, Sonnet and Opus) did the following:
- the scoop sweeps, hypothesis generation (34 hypotheses), kill panels and branch choice;
- the preregistrations, item-bank construction, subject runs, analysis and figures;
- the paper draft and the review orchestration.

The independent agents' roles:
- Locking held-out pools: `banks/locked_ma/LOCK.md`.
- Re-checking prior art: `evidence/scoop/`.
- Calibration reviewing: `reviews/calibration.json`.

**Where the main ideas came from.**
- Target-absent lineup test: Chaitanya's corpus.
- Rejection-channel framing, select-then-verify (S6) and the screen portfolio: agents in this run, prompted by the brief and the user's breadth steering.
- Benchmark choice (MathArena, Who&When): the user required established benchmarks; the agent chose these.

## Models
Subjects:
- claude-haiku-5-5, claude-sonnet-5-5 (all MathArena and Who&When work).
- claude-opus-5-5 and claude-fable-5-1 (only in pilot P1 on stale items).

Every subject call ran through Claude Code print mode (2.1.317 on 3 November; 2.1.318 for C3 on 4 November) with these settings:
- fixed system prompt (`harness/run_jobs.py`); for claude-sonnet-5-5 in C3 only, one added sentence ("You have no tools and cannot run code. Reason in plain text and end with the requested final line."), validated in exps/c3_sonnet_pilot
- no tools, `--setting-sources ""`, `--strict-mcp-config`, empty working directory
- adaptive extended thinking on by default
- temperature not set

Resolved model ids are stored per call in every raw record (`model_used`).

Outdated open models (pilot P1 only, user's Mac, Q4_K_M): smollm2-135m, qwen2.5-0.5b, qwen3-0.6b, qwen2.5-1.5b, smollm2-1.7b, granite-3.3-2b, gemma-2-2b, partial phi-3.5-mini. They carry no weight. gemma-4-e4b (user's Mac, Q4_K_M) ran its calibration batch (`exps/screens/cal`) and a descriptive C3 arm of 100 calls (`exps/c3/raw/open/gemma-4-e4b`, amendment A3); the paper reports it as uninformative.

## How to reproduce
1. Data, as fetched 2026-11-03:
   - MathArena parquet files from `huggingface.co/api/datasets/MathArena/<comp>/parquet` into /home/user/data/ma.
   - Who&When at commit 59b9fcba into /home/user/data/ww.
   - PRM800K from media.githubusercontent.com.
2. Pools: `banks/matharena_pools.py` (screens), `banks/locked_ma/` (held out, hashes in LOCK.sha256).
3. Subject runs: `python3 harness/run_jobs.py <jobs.jsonl> <raw dir>` per experiment (resumable).
4. Numbers: `python3 analysis/make_claims.py` re-runs every analysis on raw data and writes `results/claims.json` and `paper/results.tex`. Then run `python3 analysis/make_figures.py` and `python3 analysis/make_bib.py`, and compile `paper/main.tex`.
5. Gates: `python3 loop/gates.py`.

## What a human must check before submitting
- Every reference in `paper/refs.bib`, opened by hand. Several records were obtained from search snippets or GitHub READMEs while scholarly hosts were blocked; each record states how it was obtained (`fetched_via`). See AUDIT_SAMPLE.md.
- Prior art:
  - arXiv 2402.01349 section 4.2 (none-of-the-above variant), not fully read.
  - The unverified NeurIPS 2026 poster "Selected-Tail Reliability in Verifier-Guided Best-of-N Inference", which may overlap the select-then-verify result (`evidence/scoop/SURVIVORS_PRIOR_ART.md`).
- Licensing: MathArena data are CC BY-NC-SA 4.0 (research use, attribution).
- Recompute the headline numbers from `exps/*/raw/` independently.
- The AI-assistance statement in the paper, and authorship: sole author Chaitanya Sharma; no AI listed as author.
- That the subject settings (adaptive thinking on) are acceptable for the claims made.

## Session 2 (2026-11-04, user instruction to use the remaining credit)
- Repairs: committed extract data/s2s10_extract.csv.gz and a pinned, hash-checked fetch script (data/fetch_matharena.py, data/matharena_pins.json) so claims regenerate without the 1 GB parquet files (other analyses read committed pools.json files); setup.sh now installs pyarrow, sympy and antlr4-python3-runtime==4.11.1, and the grader raises an error if sympy's LaTeX parser is missing.
- C3 (exps/c3): preregistered before data; pools locked by an independent agent (banks/locked_c3); a second grader (harness/grader_b.py) written by a separate agent that did not see the first; 22 grader disagreements hand-checked by the orchestrating AI against official answers (exps/c3/hand_checks.csv), not by a human. A human should spot-check that file.
- Idea source for C3: the solvability hypothesis came from this run's tournament (F5) and the user's instruction to test it with stratification; the cross-model test (H3) was requested by the user because the paper had recommended it untested.
- To reproduce C3: python3 data/fetch_matharena.py /home/user/data/ma (needed only to rebuild pools), then python3 exps/c3/stratify.py and python3 exps/c3/analyze.py, analyze_sonnet.py, analyze_h3.py on the committed raw files.
- After review round 4 (hostile expert), amendments A4 (target-present pools and the EACH arm) and A5 (confidence ROC and base-rate instruction) were pre-registered before their data; their ideas came from the reviewers' objections. The stratum audit (exps/c3/audit_unsolved.csv) was done by the orchestrating AI after a reviewer found grading errors; a human should check it.
- Canary study (canaries/): defects planted by an independent agent, reviewed blind by ten fresh agents, scored by another agent against a hashed key.
- Review rounds 4 to 7 used fresh agents with no access to earlier rounds (Opus for area chair and hostile expert, Sonnet for the other lenses).
