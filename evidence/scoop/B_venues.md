# Scoop check B: venue sweep (2026-11-03)

## Access limits (read first)

- **WebFetch could not reach any host.** arxiv.org, pith.science and openreview.net all failed with DNS `ENOTFOUND` (the session's network allowlist blocks them). Following the tool guidance, I stopped trying further hosts after three failures. curl to arXiv was already blocked.
- **Consequence:** I opened **no paper pages** (abstracts, methods or PDFs). Everything below comes from WebSearch result summaries. Those are model-written paraphrases of indexed pages. **No quote here is a verified verbatim quote from a paper.** Text in quotation marks is search-snippet text and must be re-checked against the source before anyone cites it.
- **No `evidence/citations/*.json` files were written.** The brief allows them only for papers actually fetched, and none were.
- **Not reachable or not swept directly:** arXiv listing pages (cs.CL, cs.AI, cs.MA and cs.LG, Oct to Nov 2026), the OpenReview ICLR 2027 submission list, NeurIPS 2026 accepted-paper and workshop listings (seen only through search hits on neurips.cc/virtual), ICML 2026 (one hit only), the ACL 2026 and EMNLP 2026 anthologies (searched indirectly, with few hits), and AAMAS 2026/2027 (no hits). LessWrong, GreaterWrong and Palaestra posts appear only as search summaries.
- About 25 WebSearch queries covered the brief's term list: none-of-the-above, target-absent, lineup/relative judgment, best-of-N all-incorrect, listwise vs pointwise, abstention, both debaters wrong, weak judge, mediation, critique validity, label swap, AAMAS and NeurIPS workshops.

---

## L1 "Lineup": target-absent pools; selection vs single-candidate acceptance; eyewitness methods

| Paper | Venue / date | Overlap | Verdict |
|---|---|---|---|
| Ma, Qu, Salakhutdinov, Morency, Tomasello, Pino. "Selecting or Solving? What Best-of-N Verification Delivers in Video Reasoning", arXiv 2611.00507 | NeurIPS 2026 (neurips.cc/virtual/2026/164955); arXiv ~Nov 2026 | Splits the best-of-N gain into a *Selection Increment* (selection accuracy minus accuracy with candidates withheld). Reports that a weak verifier picks by option position, and that verification hurts on saturated pools. Per the snippets, it does **not** isolate all-incorrect pools or compare false acceptance in a pool vs alone. | partial (adjacent) |
| "When the Judge Should Not Decide: Evidence-Locked, Non-Compensatory Selection Bounds LLM-Judge Failure in Reasoning Pipelines", arXiv 2608.07813 | arXiv Aug 2026 | Judge choosing from a 4-candidate pool is "actively harmful", 10 pts below majority vote (snippet). Mitigation is to restrict what the judge may overrule. No target-absent manipulation and no lineup framing. | partial (weak) |
| "Best of mini-N in-loop Sampling: A Contextual Quality Reward Model ...", arXiv 2510.04087 | arXiv Oct 2025 | Adds a discrete-choice "outside option" (reject all candidates) to the RM and abstains at inference. Reliability failures more than double from N=1 to N=32 (snippet). This is the closest prior work on "selection when none is acceptable", but it is a training/RM method, not a measurement of judge false-ID in a pool vs alone. | partial |
| "Learning Generative Selection for Best-of-N", arXiv 2602.02143 | arXiv Feb 2026 | Filters training to mixed pools, so all-incorrect pools are excluded by design. This supports the gap. | none (supports gap) |
| Kranti & Vajjala, "LLM Judges Can Be Too Generous When There Is No Reference Answer", arXiv 2607.12885 | arXiv 14 Jul 2026 | Single-answer judges over-credit wrong answers without a reference. No pools. | none (background) |
| "Judge, Retrieve, or Abstain", arXiv 2608.17994 | COLM 2026 | Judge abstention with risk control. Single-instance QA, no pools. | none |
| ReFACT, arXiv 2509.25868 | 2025 | Snippet: "comparative judgment is paradoxically harder than independent detection" (GPT-4o F1 0.67 to 0.53). Closest empirical hint at pool vs alone, but it is confabulation detection, not target-absent selection. | partial (weak) |
| Tam et al., "None of the Above, Less of the Right" | ACL 2025 Findings | Accuracy drops 30-50% when NOTA is correct in MCQA. This is model-as-answerer, not judge over candidate solutions. | none (background) |
| Góral et al., "Wait, that's not an option" | ACL 2025 | MCQ with no valid option (answerer setting). | none (background) |
| arXiv 2606.08239 | Jun 2026 | Video MLLMs detect a removed correct answer (NOTA). Answerer setting. | none |
| "Irrelevant Alternatives Bias LLM Hiring Decisions", arXiv 2409.15299 | 2024 | Decoy/attraction effects in LLM choice. Background for relative judgment. | none |

No hit applied eyewitness-lineup methods to LLMs: target-present vs target-absent, simultaneous vs sequential, relative vs absolute judgment, lineup ROC or showup vs lineup. Searches for "lineup" with LLM returned only human eyewitness literature.

**L1 overall: NOT scooped.** The closest work is in the selection-increment and outside-option family. The specific claim (the same candidates are accepted far less often alone than chosen from a target-absent pool) and the lineup methodology appear open. Confidence is moderate, because arXiv and OpenReview listings were not directly reachable.

## L2: debate or deliberation on target-absent pools (no debater correct)

| Paper | Venue / date | Overlap | Verdict |
|---|---|---|---|
| Elasky & Nakasako, "Inference-time Generative Debates on Coding and Reasoning Tasks for Scalable Oversight" | LessWrong/GreaterWrong + palaestraresearch.org (2026); **no arXiv version found** | **Very close.** Dual-proposer debate on BCB+ and ARC-AGI with weak judges. Per the search summaries, the accuracy gap "concentrates in the 'both-wrong' regime, rounds where neither participant produced a correct solution". In that regime judge verdict accuracy is 11% under debate vs 62% under consultancy (BCB+, GPT-5 dual proposer). FPR is 90% for dual-proposer debate vs 39% for dual consultancy vs 30% for no transcript. The no-transcript condition matches or beats debate. Unverified snippet text, needs a fetch. | **partial, close to scooped** for the empirical "debate fails when no debater is right" claim |
| Elasky, Nakasako, Goyal, "Debate Helps Weak Judges Reward Stronger Models", arXiv 2605.27483 | arXiv May 2026 | Proposer-critic. Debate helps only if the critic classifies correctness better than the judge. A single critique recovers most of the benefit. Not target-absent. | partial (adjacent) |
| Kenton et al., "On scalable oversight with weak LLMs judging strong LLMs", arXiv 2407.04622 | NeurIPS 2024 | Snippet suggests future work on debaters with "the truly open choice, and could both choose to argue for the incorrect answers". Raised as future work, not done. | none (prior motivation) |
| Spinelli et al., "Humans Correct Their Judgements Through Debate, but Weaker AI Models Not", arXiv 2610.28539 | NeurIPS 2026 poster | Weak AI judges gain nothing, or lose accuracy, from debate. Not both-wrong. | none |
| Jiang, Chen, ..., Tan, "Collaborative Disagreement Resolution for Scalable Oversight", arXiv 2607.01251 | ICML 2026 (PMLR v306) | Collaborative alternative to debate (62.1% vs 49.2%). Not both-wrong. | none |
| EMNLP 2026 main.830 (conformal social choice for debate) | EMNLP 2026 | Wrong-consensus detection in multi-agent debate: 81.9% of wrong-consensus cases flagged (snippet). Agents converge on a wrong answer, which is related to the deliberation half of L2, but there is no judge over target-absent candidate pools. | partial (weak) |
| arXiv 2510.20963 "When and Why Does Multi-Agent Debate Fail ..." | 2025 | Lists "ambiguous or unanswerable" as a failure category. | none |

**L2 overall: PARTIAL, high scoop risk.** Elasky & Nakasako already report, informally, that debate collapses judge accuracy in the both-wrong regime. A framed treatment is still open: designed target-absent pools, an abstain/"none" option for the judge, and lineup-style metrics. Next step: fetch the LessWrong/Palaestra post and check whether an arXiv or ICLR 2027 version exists, since none was found.

## L3: randomized checker-graded valid vs invalid critiques; causal mediation; label-swap test

| Paper | Venue / date | Overlap | Verdict |
|---|---|---|---|
| Elasky, Nakasako, Goyal, arXiv 2605.27483 | arXiv May 2026 | Programmatically verifiable tasks. Studies whether the judge treats critique as "claims to verify rather than testimony". Correlational (critic F1 vs judge F1). Snippets show no randomization of critique validity and no mediation estimand. | partial (closest) |
| ARGORA, arXiv 2601.21533 | arXiv Jan 2026 | SCM plus counterfactual interventions on argument chains in multi-expert debate. Not critique validity, not mediation. | none/weak |
| "Epistemic Regret Minimization", arXiv 2602.11675 | arXiv Feb 2026 | Causal critique content matters more than judge quality (snippet). No validity-randomized design. | none/weak |
| "Judging Against the Reference", arXiv 2601.07506 | arXiv Jan 2026 | Swapped-reference test: judges fall back on their own beliefs. Analogous to a label swap, but over references, not debate critiques. | none/weak |
| lechmazur/debate (GitHub) | 2026 | Side-swapped debate benchmark (17.3% verdict flips). A side swap, not a critique-validity swap. | none |

No hit randomized checker-graded valid vs invalid critiques, estimated a causal mediation effect (ACME/NIE) of critique validity on judge accuracy in debate, or used a label-swap test of that kind.

**L3 overall: NOT scooped.** The adjacent work is correlational (Elasky et al. 2605.27483). Confidence is moderate, for the same access reasons.

## Summary

| Line | Verdict | Key threat |
|---|---|---|
| L1 | none (open) | Ma et al. 2611.00507 (NeurIPS 2026); outside-option RM 2510.04087 |
| L2 | partial, high risk | Elasky & Nakasako, Inference-time Generative Debates (LessWrong/Palaestra 2026): both-wrong regime, 11% vs 62% |
| L3 | none (open) | Elasky, Nakasako, Goyal 2605.27483 (correlational critic-vs-judge) |

To do once the network allows it: fetch every paper above to verify the quotes and write the citation JSONs. Sweep the OpenReview ICLR 2027 list and the arXiv cs.CL/cs.AI/cs.MA listings for 2026-10 and 2026-11 directly.
