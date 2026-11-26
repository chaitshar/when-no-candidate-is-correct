# When No Candidate Is Correct: study archive

**Update, November 2026 (release `v2.2`).** The follow-up study, "Lineups Without a Culprit: AI Judges Lower Their Bar When They See All the Answers Together", is in [`v2/`](v2/README.md): paper, plans, locked pools, raw replies and analysis code. Everything below describes the first study (release `v1.0`), which is unchanged.

Data, code and records for the preprint "When No Candidate Is Correct: Pooled Selection Raises False Choices by Claude Judges" by Chaitanya Sharma (`paper/main.pdf`).

The study compares three ways of judging model answers when no candidate is correct: separate verdicts (ISO), joint verdicts (EACH) and choosing one candidate or NONE (PICK). Judges are claude-haiku-5-5 and claude-sonnet-5-5. Claims are scoped to those models and settings.

## Where things are

| Path | Contents |
|---|---|
| `paper/` | Manuscript, generated numbers (`results.tex`), references, figures, arXiv bundle |
| `exps/c3/` | Main study: `PREREGISTRATION.md`, `AMENDMENTS.md`, prompts as jobs, raw replies, analysis scripts and results |
| `exps/c3/audit_unsolved.csv`, `candidate_label_audit.csv`, `own_answer_checks.csv`, `hand_checks.csv` | Adjudication records |
| `banks/locked_c3/` | Locked candidate pools and their hash |
| `exps/c2_confirm/`, `exps/screens/`, `exps/p1_lineup_math/`, `exps/p2_tournament/` | Earlier attempts and exploratory screens (paper appendices) |
| `harness/` | Prompts, parsers, graders, runners |
| `analysis/` | `make_claims.py` regenerates every paper number from raw replies, `make_figures.py` the figures |
| `results/` | Claims, hypothesis ledger, cost ledger |
| `reviews/`, `evidence/codex/`, `canaries/` | AI reviews and the Codex audit. The rounds in `reviews/` predate the final rewrite |
| `chronology/`, `evidence/github/` | Export of the development git log and GitHub push events |
| `loop/` | Rules, gates, rubric and session notes for the autonomous research process |

## Reproduce the numbers

```
python3 -m pip install numpy scipy pandas matplotlib statsmodels pyarrow sympy antlr4-python3-runtime==4.11.1
python3 analysis/make_claims.py
python3 analysis/make_figures.py
git diff --stat paper/results.tex
```

The last command should show no change. Volatile fields in some `results` files may reorder or differ in the last float digits.

## Limits to keep in mind

- All interpreted judges are from one vendor, and every task is mathematics with final-answer grading.
- Labels contain errors. Audits were done by AI agents, were not blind, and no human has audited them.
- "Pre-registered" means committed to version control before the relevant data, not filed in a public registry. Commit hashes in the paper refer to the private development repository, which also holds unrelated work. `chronology/development_git_log.txt` is an export of its log, so readers cannot fully verify it from this archive. GitHub push events in `evidence/github/` were recorded for that repository.
- `loop/gates.py` checks git order, so its `prereg` gate needs the development history and cannot pass here.

## What was removed from the development repository

- Unrelated earlier research (`corpus/`) and a stale author note (`DEFENSE.md`).
- Verbatim Who&When logs in `exps/screens/s5_whowhen/jobs.jsonl`. The dataset page lists no licence, so run `build.py` there to regenerate them from the pinned commit. Labels and judge replies are kept.
- A clause in `loop/PROMPT.md` about the author's personal application plans.
- LaTeX build by-products.

## Licences and sources

Unless a file says otherwise, this archive is released under CC BY-NC-SA 4.0 (`LICENSE`), because candidate solutions and problems derive from [MathArena](https://arxiv.org/abs/2505.23281) data under that licence. The data in `banks/locked/`, `banks/prm_bank.jsonl` and the P1 and P2 pools derive from [PRM800K](https://github.com/openai/prm800k) and [MATH](https://github.com/hendrycks/math), both MIT licensed. Please cite the original datasets.

## AI assistance

An AI system (Claude, via Claude Code) wrote the rules and checks at the author's direction, and ran the search, experiments, analysis and drafting. AI agents reviewed the work. See the paper's AI assistance section.
