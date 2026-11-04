# Audit sample for hand checking before submission

Regenerated 2026-11-04 (session 2) by a seeded stratified draw (seed 30) over claims used in paper/main.tex, cycling over source files with C3 sources first. Check each value against its source file, then recompute it from that experiment's raw files. For C3 also spot-check exps/c3/hand_checks.csv and exps/c3/audit_unsolved.csv, which were decided by the AI, not a human.

## 30 claims

| # | claim id | value | source file |
|---|---|---|---|
| 1 | c3_audit_solved | 14 | exps/c3/audit_unsolved.csv |
| 2 | c3_n_dup | 5 | exps/c3/duplicates_of_used.json |
| 3 | c3h_fam_contest_nu | 6 | exps/c3/results.json |
| 4 | a4hu_iso_j | +0.12 | exps/c3/results_a4.json |
| 5 | a4sens_hu_dj | -0.14 | exps/c3/results_a4_sensitivity.json |
| 6 | a5u_dfa_ci | [-0.08, +0.12] | exps/c3/results_a5.json |
| 7 | h3_sonnet_d | +0.04 | exps/c3/results_h3.json |
| 8 | sens_haiku_du | +0.27 | exps/c3/results_sensitivity.json |
| 9 | c3s_b_ci | [-0.15, +0.11] | exps/c3/results_sonnet.json |
| 10 | c3_n_ta | 278 | exps/c3/solve_summary.json |
| 11 | c2_haiku_all_h1ci90 | [+0.04, +0.19] | exps/c2_confirm/results.json |
| 12 | p1_haiku_solve | 1.00 | exps/p1_lineup_math/results.json |
| 13 | p2_haiku_auroc | 0.64 | exps/p2_tournament/results.json |
| 14 | ph_solved_d | -0.04 | exps/posthoc/solvability_split.json |
| 15 | cal_haiku_nowork | 0.97 | exps/screens/cal/results.json |
| 16 | s1_wrong_appear | 300 | exps/screens/s1_lineup/pools.json |
| 17 | s1_tp_pick_false | 0.08 | exps/screens/s1_lineup/results.json |
| 18 | s1_solve | 0.73 | exps/screens/s1_lineup/results_solve.json |
| 19 | s2_auroc_min | 0.75 | exps/screens/s2_s10_free/results.json |
| 20 | s3_auroc | 0.56 | exps/screens/s3_tournament/results.json |
| 21 | s4_right_checker_ci | [-0.23, -0.02] | exps/screens/s4_critique/results.json |
| 22 | s5_sonnet_step | 0.40 | exps/screens/s5_whowhen/results.json |
| 23 | s5_sonnet_agentnorm | 0.61 | exps/screens/s5_whowhen/results_norm.json |
| 24 | s8_tp_right | 0.68 | exps/screens/s8_debate/results.json |
| 25 | s9_wrong_diff | -0.12 | exps/screens/s9_peernote/results.json |
| 26 | cost_subjects | 283 | results/cost_ledger.csv |
| 27 | ledger_total | 80 | results/hypothesis_ledger.csv |
| 28 | c3_audit_mixed | 6 | exps/c3/audit_unsolved.csv |
| 29 | c3h_verdict_H1 | inconclusive | exps/c3/results.json |
| 30 | a4s_h4 | not confirmed | exps/c3/results_a4.json |

## 20 citations (of the 29 in paper/refs.bib; the four eyewitness journal articles and every preprint-labelled entry first)

| # | key | url | venue recorded | how obtained |
|---|---|---|---|---|
| 1 | malpass1981eyewitness | https://doi.org/10.1037/0021-9010.66.4.482 | Journal of Applied Psychology 66(4):482-489, 1981 | WebSearch result snippets (reference lists citing it; APA pa |
| 2 | steblay2001eyewitness | https://doi.org/10.1023/A:1012888715007 | Law and Human Behavior 25(5):459-473, 2001 | WebSearch result snippets (Semantic Scholar result title, ac |
| 3 | steblay2011seventytwo | https://doi.org/10.1037/a0021650 | Psychology, Public Policy, and Law 17(1):99-139, 2011 | WebSearch result snippet (Connecticut task force PDF copy, t |
| 4 | wells1984psychology | https://doi.org/10.1111/j.1559-1816.1984.tb02223.x | Journal of Applied Social Psychology 14(2):89-103, 1984 | WebSearch result snippet (Scilit record, NCJRS abstract), pa |
| 5 | wixted2012field | https://doi.org/10.1177/1745691612442906 | journal article (commentary responding to Clark, 2012) | WebSearch result snippet (psychologicalscience.org journal p |
| 6 | balunovic2025matharena | https://arxiv.org/abs/2505.23281 | arXiv preprint arXiv:2505.23281 | curl https://arxiv.org/abs/2505.23281 2026-11-03 (citation_t |
| 7 | brown2024large | https://arxiv.org/abs/2407.21787 | arXiv preprint arXiv:2407.21787 | github README https://raw.githubusercontent.com/ScalingIntel |
| 8 | cobbe2021training | https://arxiv.org/abs/2110.14168 | arXiv preprint arXiv:2110.14168 | github README https://raw.githubusercontent.com/openai/grade |
| 9 | irving2018ai | https://arxiv.org/abs/1805.00899 | arXiv preprint arXiv:1805.00899 | WebSearch result snippet (arXiv listing), page itself blocke |
| 10 | ji2026candidate | https://arxiv.org/abs/2608.25937 | arXiv preprint arXiv:2608.25937 | curl arxiv.org abs page 2026-11-03 |
| 11 | kadavath2022language | https://arxiv.org/abs/2207.05221 | arXiv preprint arXiv:2207.05221 | curl https://arxiv.org/abs/2207.05221 2026-11-04 (citation_t |
| 12 | rho2025best | https://arxiv.org/abs/2510.04087 | arXiv preprint arXiv:2510.04087 | curl arxiv.org abs page 2026-11-03 |
| 13 | tam2025none | https://arxiv.org/abs/2503.01550 | arXiv preprint arXiv:2503.01550 | curl https://arxiv.org/abs/2503.01550 2026-11-04 (citation m |
| 14 | chen2026beyond | https://arxiv.org/abs/2609.18204 | HICSS-60 (per arXiv comments); arXiv:2609.18204 | curl https://arxiv.org/abs/2609.18204 2026-11-04 (citation m |
| 15 | gottweis2025towards | https://arxiv.org/abs/2502.18864 | Nature, 2026. doi:10.1038/s41586-026-10644-y. Earlier version: arXiv:2 | curl https://arxiv.org/abs/2502.18864 2026-11-04 (citation_t |
| 16 | hendrycks2021measuring | https://arxiv.org/abs/2103.03874 | NeurIPS 2021 Datasets and Benchmarks Track | github README https://raw.githubusercontent.com/hendrycks/ma |
| 17 | jeong2025comparative | https://aclanthology.org/2025.blackboxnlp-1.5 | BlackboxNLP 2025 (workshop) | WebSearch result snippet (ACL Anthology 2025.blackboxnlp-1.5 |
| 18 | kenton2024scalable | https://proceedings.neurips.cc/paper_files/paper/2024/hash/899511e37a8e01e1bd6f6f1d377cc250-Abstract.html | NeurIPS 2024 | WebSearch result snippet (NeurIPS proceedings page and arXiv |
| 19 | khan2024debating | https://proceedings.mlr.press/v235/khan24a.html | ICML 2024 (PMLR 235) | github README https://raw.githubusercontent.com/ucl-dark/llm |
| 20 | kim2026penalty | https://arxiv.org/abs/2610.08153 | AACL-IJCNLP 2026 (short paper, per arXiv comments); arXiv:2610.08153 | curl https://arxiv.org/abs/2610.08153 2026-11-04 (citation m |
