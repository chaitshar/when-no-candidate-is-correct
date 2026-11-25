# v2: Lineups Without a Culprit

Data, code and records for the second paper, "Lineups Without a Culprit: AI Judges Pick a Wrong Answer More Often When They See All the Answers Together" by Chaitanya Sharma (`paper/main.pdf`). Release tag: `v2.1` (`v2.0` is the same study before the explanatory diagrams were added).

The first study (in the folders one level up, tag `v1.0`) showed that two Claude judges pick a wrong answer more often when they see all candidate answers together (PICK) than when they check each answer alone (ISO). This second study asks why, whether it holds for other judges and for science ideas, and what fixes it.

## Experiment codes

The letter C stands for "confirmation": a test that was planned before it was run.

| Code | What it tests | Folder |
|---|---|---|
| C3 | First study: PICK, ISO and EACH on math, two Claude judges | `../exps/c3/` |
| C4 | Same compute: three PICK calls against three ISO calls | `exps/c4_compute/` |
| C5 | Removal: take out the judge's own answer, or its first pick | `exps/c5_removal/` |
| C6 | Two judges from other companies on new math pools | `exps/c6_crossvendor/` |
| C7 | Three fixes, called M1, M2 and M3 | `exps/c7_mitigation/` |
| C8 | One Gemini judge with less thinking | `exps/c6_crossvendor/` (the `gemini_low` files) |
| C9 | Science ideas (ResearchBench) instead of math | `exps/c6_crossvendor/` (the `science` files) |

## Where things are

| Path | Contents |
|---|---|
| `paper/` | Paper source (`main.tex`), PDF, generated numbers (`results.tex`, `results_extra.tex`), references, figures, and the arXiv source bundle. `main_technical_26nov.tex` is an earlier wording of the same paper with more technical terms; its numbers are the same |
| `PREREGISTRATION_V2.md`, `MASTER_PUBLICATION_PLAN.md`, `exps/c7_mitigation/PREREG_C7.md` | Plan documents, fixed before the judge calls |
| `LOCKED.sha256`, `banks/locked_v2/LOCKED.sha256`, `exps/c7_mitigation/C7_LOCKED.sha256` | SHA-256 fingerprints of the locked files |
| `banks/locked_v2/` | Locked candidate pools and `BANK_MANIFEST.md` |
| `exps/` | Job files (the exact prompts) and raw judge replies for every experiment |
| `autoloop/` | Runner, parsers, the two analysis programs (`analysis_a.py`, `analysis_b.py`), the table generator, the data figures (`figures_svg.py`) and the explanatory diagrams (`figures_explain.py`) |
| `scripts/` | Pool builder, audit helpers, and `final_sensitivity.py` (extra checks added at the end) |
| `results/` | Outputs of both analysis programs, their value-by-value comparison, and the extra checks |
| `audit/` | Parser audit, list of differences between the two analysis programs, and a tool for a human label check (not yet done) |

## Check the locks and rebuild the numbers

Run these from this `v2/` folder with Python 3.9 or newer.

```
shasum -a 256 -c LOCKED.sha256
python3 autoloop/make_results_tex.py
python3 scripts/final_sensitivity.py
python3 autoloop/figures_svg.py
python3 autoloop/figures_explain.py
git diff --stat paper/
```

The last command should show no change in `paper/results.tex`, `paper/results_extra.tex` and the `.svg` figures. The PDF figures were made from the SVG files with a headless browser.

## Limits to keep in mind

- The mechanism checks (C4, C5) and two of the three fixes use one judge, claude-haiku-5-5.
- The planned main test of C6 is not supported, and both C6 judges miss the planned minimum group size.
- The science test (C9) uses pools from only 10 papers.
- Labels were checked by AI agents. No human has audited them.
- "Planned" or "preregistered" means fixed in a locally hashed file before the calls, not filed with an outside registry.
- Some files contain absolute paths from the author's computer. They are kept unchanged because the locked files must keep their fingerprints.

## Licences and sources

Math problems and candidate solutions derive from [MathArena](https://arxiv.org/abs/2505.23281) (CC BY-NC-SA 4.0), as in v1. The science pools in `banks/locked_v2/c9_science_pools.json` and the `science` job files derive from [ResearchBench](https://arxiv.org/abs/2503.21248); the paper abstracts and hypotheses in them belong to their original authors and are included here only so that the study can be checked. Please cite the original datasets.

## Use of AI

AI coding agents (Google Antigravity and Claude Code) wrote the programs, ran the experiments and analysis, and drafted the paper under rules set by the author. See the paper's "Use of AI" section.
