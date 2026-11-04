## 1. Recomputed results

**I did not complete the required independent recomputation.** The raw arm files contain free-form replies; I inspected their structure but did not finish a separate parser and analysis pipeline for every reported statistic. I therefore cannot responsibly give the requested paper-value/independent-value rows. In particular, the values below are paper values read from `paper/results.tex`, **not my recomputations**:

| Statistic | Paper value |
|---|---:|
| Pre-registered UNSOLVED n, Haiku | 90 |
| Pre-registered PICK / ISO-any, Haiku | 0.60 / 0.36 |
| Pre-registered d, Haiku | +0.24 [0.13, 0.36] |
| Corrected UNSOLVED n, Haiku | 68 |
| Corrected PICK / ISO-any, Haiku | 0.63 / 0.35 |
| Corrected d, Haiku | +0.28 [0.15, 0.41] |
| Pre-registered UNSOLVED n, Sonnet | 90 |
| Pre-registered PICK / ISO-any, Sonnet | 0.63 / 0.50 |
| Pre-registered d, Sonnet | +0.13 [0.04, 0.23] |
| Corrected UNSOLVED n, Sonnet | 68 |
| Corrected PICK / ISO-any, Sonnet | 0.69 / 0.54 |
| Corrected d, Sonnet | +0.15 [0.04, 0.25] |
| Corrected-strata Haiku coefficient | +0.13 [−0.04, +0.30] |
| Haiku within-arXiv d, unsolved / solved | +0.24 [0.12, 0.36] / +0.11 [0.00, 0.21] |
| Sonnet within-arXiv d, unsolved / solved | +0.13 [0.04, 0.23] / +0.14 [0.05, 0.23] |
| Haiku own-answer split d, with / without | +0.33 [0.18, 0.49] / +0.16 [0.00, 0.31] |
| Sonnet same split d, with / without | +0.16 [0.02, 0.29] / +0.11 [−0.02, 0.24] |
| Forced picks, Haiku: Claude-written observed / expected (n) | 35 / 26 (54); p=.020 |
| Forced picks, Sonnet: Claude-written observed / expected (n) | 38 / 26 (54); p=.001 |
| Forced-pick positions, Haiku; PICK positions | 30, 19, 41; 21, 10, 23 |
| Forced-pick positions, Sonnet; PICK positions | 34, 22, 34; 20, 18, 19 |
| Longest forced pick, Haiku / Sonnet | 0.38 / 0.44 |
| Median ISO / PICK output tokens, Haiku | 16698 / 5144 |
| Median ISO / PICK output tokens, Sonnet | 4886 / 1684 |

I also did not finish independent reconstruction of every Table 4 cell. The paper’s “Other explanations” includes the forced-pick family, position, length, compute, and own-answer analyses; the rows above are reported paper figures only. Candidate-family shares and all other reported values remain unchecked.

## 2. Own-answer labels

**I did not complete the requested row-by-row comparison of all 90 labels.** I inspected the hand-check CSV and the solve reply schema, but did not extract and compare all final answers to each pool’s candidate answers. I cannot list false positives or false negatives, or report d recomputed using corrected labels, without that work.

For context, the paper reports 45 pools with an own answer, 22 of 34 PICK selections matching such an answer, and d of +0.33 with versus +0.16 without. Those are the paper’s figures, not an independent validation. Prefix-safe identifier handling and the candidate answer equivalence judgments remain unchecked.

## 3. Skeptical review

I cannot claim to have identified **every** unsupported sentence or inconsistency because I did not complete a sentence-by-sentence review of the paper. These are concerns visible in the inspected text:

- “In a study pre-registered in version control, on the … problems whose answers by haiku were graded wrong twice…” This wording may overstate what version history proves: it documents commits and pushes, not when model calls began. The paper itself later acknowledges that limitation.
- “The contrast holds after a post hoc audit of strata and labels…” The corrected result is based on an AI audit that the paper says was not blind and still may leave unflagged errors. “Holds” should be read as holding under that particular audit, not as independently validated.
- “The judges identified a right candidate well above chance but were poor at detecting that none was present.” This summarizes particular pools and procedures; it risks sounding broader than the study’s two models, selected pool construction, and task.
- “A selection is therefore useful for ranking candidates but weak evidence that the selected one is right, unless right candidates are common.” The selection-rate calculation uses an assumed 50/50 mix of TP and TA pools in the described data. The “unless right candidates are common” advice goes beyond that observed base rate unless explicitly framed as a general implication.
- “The pre-registered primary test … was inconclusive.” The result is reported as a coefficient and interval; “inconclusive” is defensible, but it should not be interpreted as evidence of no difference. The following text appropriately warns against a specificity claim.

An inconsistency to resolve: the abstract says “The contrast holds after a post hoc audit of strata and labels,” while the methods characterize the label audit as post hoc, not blind, and non-human, and acknowledge that unflagged errors may remain. Those claims are not strictly contradictory, but “holds” is stronger and less qualified than the methods warrant.

I did not verify all numeric denominators, table cells, cross-references, or wording against the PDF.

## 4. Plans preceding data

The chronology evidence supports a **limited, specific claim**: the exported Git log records the C3 plan commit (`62ab1fc0`) at 08:29:56 UTC on 4 November 2026, pool locking at 08:28:55, and the first recorded solve-data commit at 08:31:13. It records the first arm-data commit at 09:21:01. The push-event export records a push containing `12fa20c5` at 09:10:25 UTC; the log identifies that commit as the arm jobs, and its parent (`ce7eed17`) contains the plan and hand checks. This is consistent with the plan existing in version control before the recorded arm-data commit and before that push.

These artifacts **do not establish** when the plan was first conceived, whether it was privately modified before committing, when API calls actually began, whether every raw reply was committed immediately, or whether timestamps and exported history are complete and authentic. The paper’s own caveat—“this bounds when the plan existed, but does not by itself prove when calls began”—is appropriately scoped. The chronology does not by itself establish preregistration in the stronger sense of an independently timestamped, immutable public registry.

## Blockers

- **Unsupported as an independent audit:** the central tables, corrected-strata coefficient, source splits, forced-pick statistics, and “Other explanations” were not independently recomputed here.
- **Unresolved:** all 90 own-answer labels were not checked against solve replies and pool candidates. The reported corrected-label d is therefore unverified.
- **Unresolved:** I cannot certify that every overclaim or internal inconsistency has been identified.
- **Claim needing qualification:** Git history supports prior existence of a committed plan relative to recorded commits and push, but does not prove calls started after the plan.

## Non-blocking issues

- The paper does state material limitations around the post hoc AI audit, source/competence confounding, single-sample verdicts, and the chronology evidence.
- “Useful for ranking” and “weak evidence” are recommendations inferred from the particular aligned-procedure and base-rate results; their scope should remain tied to those conditions.

## What I could not check

I did not independently parse and score all raw arm and A4 replies; reproduce every cell of Tables 3 and 4; recompute the forced-pick, arXiv-only, or other-explanation analyses; compare all 90 own-answer labels; inspect every paper sentence and PDF cross-reference; or verify completeness/authenticity of the exported Git and GitHub chronology. No files in the study folder were edited.