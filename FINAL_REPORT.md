# READ FIRST: paper rewritten after external review (2026-11-04)

The paper was restructured after two external AI reviews. Reviews in `reviews/FINAL/` and the convergence statement below apply to the EARLIER text, not this one. The review gate passing does not cover the rewrite.

Corrected error: earlier text said a pick carried almost no information and read the ROC diagonal as chance. A judge that picks uniformly has hit = false choice / 3. Given a selection on a pool with a right candidate, haiku's pick was right 0.72 of the time on UNSOLVED problems, against 1/3 by chance. The judges identify but detect absence poorly.

New post hoc analyses: exps/c3/analyze_aligned.py, exps/c3/analyze_review.py. The Data availability section deliberately says the archive is not yet public; replace that text with the real link before release.

Codex audit (OpenAI, independent code, exps/c3 only): 132 values compared, 128 match. The 4 differences are in EACH rows, where it counted one reply that imitated tool calls as abstaining and the paper counts it as missing. Its arXiv-only rows are not usable. On own-answer labels it disagreed on 5 of 90 rows: 1 was a real miss, which also exposed a new MathArena mislabel (arxivmath-0526_24); 4 did not survive a check against raw replies. Codex did not review the whole paper sentence by sentence and could not verify citations (no network).

Own-answer correction: the first analysis had an identifier-prefix bug. On hand-checked labels, d is +0.33 with and +0.16 [+0.00, +0.32] without such a candidate.

Public archive: https://github.com/chaitshar/when-no-candidate-is-correct/tree/v1.0. Outstanding: human audit of labels and methods, and a fresh review of this rewritten text.

# Final report (updated 2026-11-04, end of session 2)

**Gates: all pass** (`python3 loop/gates.py` after copying review round 9 to `reviews/FINAL/`). `loop/DONE` exists.

**Rubric convergence: met.** Rounds 8 and 9 each ran six fresh lenses (area chair, hostile expert, methods with independent recomputation, integrity, citations, prior art). Both rounds returned minor with no blockers, so these are two consecutive rounds with no new blockers. The last blocker was in round 7 and was fixed.

**Calibration bar: not met.** The Opus area chair scored this paper 4 in rounds 4 to 9. The median for the three flagship papers in `reviews/calibration.json` is 6.

Every reviewer is a Claude model, so their agreement counts as weak evidence. The paper passed simulated review for claim accuracy, not as a flagship contribution. No claim here says it will clear any venue.

**Honest venue:** a workshop on LLM evaluation, oversight or multi-agent systems, or an arXiv preprint. It is a careful, pre-registered measurement paper with modest novelty: the closest prior work is Wang et al. (COLING 2025) and Kim and Jung (AACL-IJCNLP 2026). Before it is ICML-ready it needs:
- a design that separates competence from item source;
- a regime of intermediate discriminability.

Gated datasets that need the user: Humanity's Last Exam, GPQA, GAIA.

**Changes after review round 9 (local audit, not re-reviewed):** fixed an unescaped underscore that garbled part of Section 4.4 in the PDF and stopped the bundle compiling under a stricter engine; "did not move" became "did not detectably move"; the conclusion's H3 sentence now states its scope; Threats now states the HC3 singleton point.

**Known non-blocking issues from round 9:**
- **HC3 and a singleton competition.** The C3 primary model's HC3 errors are undefined for the competition that has a single judged problem. The reported H1 p (0.065) reproduces only when that competition is dropped. The verdict (inconclusive) does not change. The post hoc sensitivity script handles singletons explicitly.
- **Wording strength.**
  - The base-rate and ROC results are non-detections with intervals of about plus or minus 0.1 and 0.04. Read "did not move" as "did not detectably move".
  - H1u is a within-stratum test, and d is also positive on solved problems.
- **Other notes.**
  - About 1.3k tokens of harness scaffolding reach the subject besides the task prompt (the CLI's own system context). It contains no study information.
  - One A5 isolated call was lost to a timeout.
  - CLI versions are hard-coded.

## The question
When the candidate pool given to an LLM judge contains no correct answer (a target-absent "lineup"), does the judge pick a wrong one more often than it would accept any of them judged alone? When does this happen, and which selection formats fail?

## The answer
Settings: MathArena items; Claude Code print mode with defaults (adaptive thinking on); 4 Nov 2026. The confirmatory study is C3: 278 fresh locked problems, stratified before judging by whether claude-haiku-5-5 solved them in two attempts.

**claude-haiku-5-5:**
- **Confirmed (H1u):** on the 90 problems it could not solve, it chose a wrong solution from the pool in 0.60 of cases, against 0.36 for any isolated acceptance. The difference was +0.24 [+0.13, +0.36], Holm p 0.001.
- **Confirmed (H2u):** on those problems, its forced pick was the wrong solution its own isolated verification passes most, +0.19 [+0.11, +0.28].
- **Inconclusive (H1, the primary test):** whether the penalty is larger on unsolved than solved problems after competition fixed effects. b = +0.12 [-0.03, +0.27], Holm p 0.13. Unsolved problems came almost entirely from arXiv-derived sets.
- **Inconclusive (H2s):** the forced-pick effect on solved problems.

**claude-sonnet-5-5** (same problems; strata defined by haiku): same pattern.
- H1u: +0.13 [+0.04, +0.23].
- H2u: +0.28 [+0.18, +0.38].
- H1: inconclusive.

**A4, pools that contain a right solution (pre-registered after the round-4 hostile review):** H4 (pooling lowers discriminability) was not confirmed for either model. On haiku-unsolved problems, PICK also raised hits:
- haiku: hit 0.62 vs ISO 0.44; J for PICK +0.03, ISO +0.12; difference -0.09 [-0.26, +0.09].
- sonnet: hit 0.69 vs 0.40; J +0.09 vs -0.08.

The C3 effect is therefore reported as a criterion shift: on problems the judge cannot solve, its pick is nearly uninformative.

**A5, confidence ROC and base-rate instruction (pre-registered after the round-5 hostile review; haiku):** both tests were not confirmed.
- H6: the lineup ROC from confidence ratings is indistinguishable between pooled picking and isolated verification on unsolved problems (pAUC difference +0.002 [-0.030, +0.045]). Pooled picking sits at a more liberal point on the same curve.
- H7: stating that most problems have no correct solution did not move the false-choice rate (0.60 vs 0.59, +0.01 [-0.08, +0.12]).

**Post hoc:** the stratum audit (14 UNSOLVED problems were actually solved, 6 were mixed) and the exclusion of 5 duplicate problems change no conclusion.

**H3, cross-model verification:** inconclusive. Sonnet verifying haiku's forced picks removed none of the selection effect detectably, +0.02 [-0.04, +0.07]. The earlier advice to prefer a different verifier was withdrawn.

**Earlier attempts:**
- The screen (S1) found no penalty on problems haiku mostly solves.
- The first confirmation (C2) could not be interpreted: the calibration band and a gate conflict, plus a parser bug found in review.

## What was killed or retired
- 16 hypotheses killed in the tournament before data (evidence/tournament/DECISION.md). One kill reason was later contradicted by the full text and reopened (U3, tested as screen S8).
- P1 and P2: PRM800K and MATH items sat at the floor for current models. They are stale and scoped down.
- C1: withdrawn before data, because MATH-based banks were ruled invalid.
- P3 (Omni-MATH): parked.
- S0: generated tasks, abandoned on the user's ruling against made-up data.
- Screen results: S2 and S10 unsurprising; S5 (Who&When attribution below 0.8) matches the literature; S8 (debate judge says NEITHER in 0.675 of both-wrong pairs) and S9 (peer-note anchoring) unsurprising; S4 (false critique harms only when labelled "automated checker") is a candidate hypothesis.

## Unresolved
- Whether the penalty is specific to problems beyond the judge's competence. Solvability and item source are entangled: 84 of 90 UNSOLVED problems are arXiv-derived. The next test needs solved and unsolved problems from the same sources.
- Contamination of 2025 to 2026 contests: the answer-only probe was invalid with thinking on.
- The NeurIPS 2026 poster "Selected-Tail Reliability in Verifier-Guided Best-of-N Inference": only its abstract could be read, so overlap with H2 is not excluded. The paper says so.
- gemma-4-e4b (descriptive, 20 problems) accepted 0.80 of wrong solutions in isolation, so its data cannot show a penalty.

## Gates
See the top of this file.

## Panel scores next to calibration (reviews/calibration.json)
| | area chair | hostile expert |
|---|---|---|
| Flagship median, 3 real papers | 6 | 6 |
| Non-flagship median, 3 real papers | 4 | 4 |
| This paper, round 1 | 3 (major) | not run |
| This paper, round 2 | 3 (minor) | not run |
| This paper, round 3 | 3 (minor, 1 blocker since fixed) | not run |
| This paper, round 4 | 4 (minor, 1 blocker, fixed) | 4 (major, no blockers) |
| This paper, round 5 | 4 (minor) | 4 (major, no blockers) |
| This paper, round 6 | 4 (minor, no blockers) | 4 (minor, no blockers) |
| This paper, round 7 | 4 (minor, 1 blocker, fixed) | 4 (minor) |
| This paper, round 8 | 4 (minor, no blockers) | 4 (minor, no blockers) |
| This paper, round 9 (FINAL) | 4 (minor, no blockers) | 4 (minor, no blockers) |

Other lenses:
- Round 1: methods 5 (major), integrity 5 (major), citations 6 (major), prior art 7 (minor, no ABANDON).
- Round 2: methods 5 (major), integrity 6 (minor, no blockers), citations 6 (minor, no blockers).
- Round 3: methods 4 (major: answer-parser bug, since fixed and re-run, not re-reviewed).

The calibration bar (at or above the flagship median) is **not met**. Convergence (two consecutive rounds with no new blockers) is **not met**.

## Canary rates
Canary study (session 2, loop/EVOLUTION.md, canaries/SCORES.json): ten planted defects, two each of five types, split 5 train and 5 held out. Fresh claude-sonnet-5-5 reviewers using playbook v1 detected 10 of 10 (train 5/5, held out 5/5). No reviewer failure was observed, so no reviewer-prompt change was proposed.

## Cost
- Subject calls: 283 USD (results/cost_ledger.csv), computed from each call's reported cost. Treat this as a list-price figure, not a bill.
- Agents and orchestration: about 300 USD by the end of session 2, a rough estimate (results/agent_cost_estimates.csv; review rounds 4 to 9 and the canary study account for about 120 USD of it).
- Earlier overruns: S5 (+1.2 USD over its screen cap) and the C2 Sonnet arm (29 USD against a 12 USD cap). In C3 the runner enforced each cap.

## Venue recommendation
A workshop on LLM evaluation, oversight or multi-agent systems, or an arXiv preprint. It is not ready for ICML. For that it needs solved and unsolved problems from the same sources, a thinking-off condition and a second domain.
