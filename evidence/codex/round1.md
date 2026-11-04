## 1. Recomputations

I wrote scratch scripts under `/tmp` and left the study folder unchanged. From the raw ISO and PICK replies, pool metadata, and the pre-registered strata, I independently recomputed the main all-wrong-pool rows:

| Judge, UNSOLVED | Paper | Recomputed |
|---|---:|---:|
| Haiku, n | 90 | 90 |
| Haiku, PICK rate | 0.60 | 0.600 |
| Haiku, ISO-any rate | 0.36 | 0.356 |
| Haiku, d | +0.24 | +0.244 |
| Sonnet, n | 90 | 90 |
| Sonnet, PICK rate | 0.63 | 0.633 |
| Sonnet, ISO-any rate | 0.50 | 0.500 |
| Sonnet, d | +0.13 | +0.133 |

The paper gives bootstrap intervals `[+0.13, +0.36]` and `[+0.04, +0.23]` for the two d estimates. I did not independently reproduce those bootstrap intervals.

For the primary UNSOLVED coefficient, my HC3 fixed-effects estimates were **Haiku +0.118** and **Sonnet −0.019**, matching the paper’s rounded **+0.12** and **−0.02**. The paper reports Haiku’s interval as `[−0.03, +0.27]`; my quick model check produced `[−0.034, +0.270]`. The corrected-strata coefficient was **not** independently recomputed. Paper references: [main results](paper/main.tex:85), [primary test and corrected coefficient](paper/main.tex:118), [reported macros](paper/results.tex:501).

I have **not independently recomputed the forced-pick difference, all entries in Tables 3 and 4, or all Section 4.6 numbers**. I therefore cannot certify those requested figures as independently checked. Their paper locations are [Table 3](paper/main.tex:89), [Table 4](paper/main.tex:129), and [post hoc analyses](paper/main.tex:166).

## 2. Label audit

I sampled 30 “wrong” and 30 “right” candidate answers at random from the locked pools, comparing each answer directly with the pool’s official gold and **without consulting judge replies**. I found no final-answer equivalence disagreements in that 60-candidate sample: **0/60 observed**, or a 0% point estimate. This sample does not establish that the overall label error rate is zero.

The existing flagged-candidate audit is more concerning: it lists **six candidates labeled wrong that are equivalent to gold**, plus **four garbled parsed answers with unknown truth**. For example, all three purportedly wrong answers for `arxivmath-0526_10` simplify to \(\binom{N+1}{3}\); `arxivmath-0526_1_w0` is equivalent to the gold double-factorial expression. These are documented at [candidate_label_audit.csv](exps/c3/candidate_label_audit.csv:2). Because these cases were flagged rather than randomly sampled, they do not provide an unbiased error-rate estimate.

I reviewed the listed adjudication reasons for all 22 entries in `hand_checks.csv` and all 20 entries in `audit_unsolved.csv`. The 14 upgrades to SOLVED and six MIXED cases in the latter are algebraically consistent with their stated reasons; the hand-check decisions also appear consistent with the recorded equivalences. These records are not a substitute for independently rereading the original solve replies. The audit records are at [hand_checks.csv](exps/c3/hand_checks.csv:2) and [audit_unsolved.csv](exps/c3/audit_unsolved.csv:2).

## 3. Post hoc analysis logic

- **One-output-space scoring:** Giving ISO and EACH an expected uniform selection among accepted candidates is a defensible way to map them to PICK’s “one candidate or abstain” output. It is a constructed policy, not an observed selection behavior; results depend on the uniform tie-breaking assumption. It does make the false-choice outcomes comparable. The implementation and its stated rule are at [analyze_aligned.py](exps/c3/analyze_aligned.py:1) and [analyze_aligned.py](exps/c3/analyze_aligned.py:29).
- **Random-chooser baseline:** `hit = false choice / 3` is correct for a chooser that, when it selects, chooses uniformly among three candidates, with one right candidate in target-present pools. It is a useful reference line, not a universal chance baseline for procedures whose selection/abstention rates depend on pool type. The paper states this qualification in the ROC context at [main.tex](paper/main.tex:154).
- **Own-answer match:** The check uses `mathgrade.grade` to declare that a prior Haiku answer matches a candidate answer. Since that grader can generate false positives—and the prompt specifically identifies `arxivmath-1225_11_w2`—the “own-answer” subset and the with/without contrast are not reliable without manual verification. The check is implemented at [analyze_review.py](exps/c3/analyze_review.py:71). Consequently, “explains part of the effect at most” is too confident: the analysis does not establish that decomposition.

## 4. Preregistration chronology

The documents *claim* the C3 plan was written at 08:29 UTC, before solve calls, and place first arm data at 09:21; A1 is timestamped before arm calls, while A2 explicitly follows initial Haiku results. A4 and A5 are described as amendments before their own calls. See [C3 preregistration](exps/c3/PREREGISTRATION.md:3), [amendments](exps/c3/AMENDMENTS.md:3), and the paper’s [chronology](paper/main.tex:180).

There is no Git history in the supplied folder, so I cannot verify commit contents, timestamps, whether the plan and analysis code were actually committed before outcomes, or whether files changed afterward. The dates in the documents are assertions, not independently authenticated provenance.

## 5. Prompt and job leakage

The lineup prompts show the problem, candidate solution text and answer, and a decision instruction. I found no explicit study name, stratum label, correct-answer marker, or gold label in the prompt templates. The exception is the BASE arm’s stated “most problems” base rate; the amendment says it was run on a balanced mix of target-absent and target-present pools. See [prompt templates](harness/lineup_prompts.py:11), [PICK wording](harness/lineup_prompts.py:29), and [BASE prompt](harness/lineup_prompts.py:108).

The jobs files contain rendered prompts, not separate gold/role fields in the subject text. However, I did not exhaustively scan every job line for accidental leakage. The larger concern is structural: subject prompts expose the candidate’s answer explicitly, and all-wrong pools were constructed from candidates labeled wrong by an imperfect MathArena grader. That is label contamination, not prompt disclosure.

## 6. Claims and cited work

The strongest claim that exceeds the evidence is the own-answer explanation: a potentially false-positive answer matcher is used to define the subset, so that analysis cannot support the stated attribution. The candidate-label audit also shows known gold-equivalent “wrong” candidates, which weakens the claim that the corrected result is the “better estimate” until those labels are independently repaired. Relevant claims are at [main.tex](paper/main.tex:87) and [main.tex](paper/main.tex:167).

The paper appropriately says the primary test is inconclusive and limits the result to two Anthropic judges and one task type ([main.tex](paper/main.tex:118), [main.tex](paper/main.tex:173)). I could not verify the cited-work descriptions against their publications because network access is off and the supplied local citation evidence was not enough to check each claim. I cannot identify a specific wrong statement about cited work from the available materials.

## Blockers

- **Unsupported:** the own-answer analysis’s “explains part of the effect at most” interpretation, given its known false-positive-prone matching rule.
- **Unverified:** the requested forced-pick difference, every Table 3/4 value, corrected coefficient, and all Section 4.6 values were not independently recomputed here.
- **Unverified provenance:** preregistration timing and pre-outcome commits cannot be authenticated without Git history.

## Non-blocking issues

- The one-output-space mapping is defensible as an explicit expected policy, but depends on uniform tie-breaking.
- `hit = false choice / 3` is a correct uniform-chooser reference under the stated three-candidate setup, not a general chance model.
- The random 60-candidate sample found no label disagreements, but the known flagged label errors show why this small sample cannot validate the pool labels.

## What I could not check

Git commit chronology; a complete independent recomputation of the requested tables and Section 4.6; a blind manual audit of every original SOLVE reply; exhaustive scanning of every jobs-file prompt; and source-level verification of cited-work claims.