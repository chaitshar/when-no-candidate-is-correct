# Scoop check A: must-check list (2026-11-03)

## Access status, read this first

No paper page could be opened in this session. Every WebFetch failed with DNS `ENOTFOUND` (host outside the session's allowed network domains). Hosts tried and blocked:

- arxiv.org (abs pages for 2608.17270, 2608.16003, 2608.23941, 2406.12319, 2610.29147; the proxy log also shows 403 for arxiv.org and export.arxiv.org)
- www.alphaxiv.org, api.semanticscholar.org, www.semanticscholar.org, api.openalex.org, huggingface.co, doi.org, pith.science, aclanthology.org, www.opentrain.ai, fugumt.com

So arxiv.org/html/<id> was not attempted separately (same host). The only working tool was WebSearch, which returns titles, URLs and a model-written summary of the indexed snippets. Everything below is therefore **search-index evidence, not a read of the paper**. Titles, ids, authors and dates below come from search results that showed the arXiv abs/html page in the result list. No sentence below is a verbatim quote that I read on a page; text in quotation marks is the search tool's snippet and is marked as such. To upgrade this check, allow arxiv.org (and ideally alphaxiv.org, semanticscholar.org) in the session's network settings and re-run.

Because no paper was actually fetched, **no files were written to evidence/citations/** (the brief requires JSON only for papers actually fetched).

## Table

| id | title (from search index) | date / version seen | reached (page opened)? | overlap with L1 / L2 / L3 | verdict |
|---|---|---|---|---|---|
| 2608.17270 | Do LLMs Know a Good Hypothesis When They See One? Logit-Based Energy Scoring Outperforms Prompted LLM-as-Judge for Scientific Hypothesis Ranking (Rajwal, Das, Ghosal) | 18 Aug 2026; search shows only v1 (abs and html/2608.17270v1); no v2 found in index | no | L1: target-present pools only (1 gold + 15 incorrect hypotheses per paper, 1,323 ResearchBench papers). No target-absent condition seen in any snippet. L2/L3: none | partial (adjacent, target-present only); v2 status unverified |
| 2608.16003 | Prior Audit-Repair Context Shifts LLM Verifier Thresholds Toward Leniency (P. Mazaheri, K. Mazaheri) | 17 Aug 2026; v1 only in index | no | L1 (lineup-ROC/SDT angle): context moves the verifier criterion, not d'. Single-candidate verification, no pools, no target-absent, no lineup framing. L2/L3: none | not overlapping (methodological neighbour for SDT reading) |
| 2608.23941 | More Rejective, Not More Discriminative: The Unit of Verification in Pre-Execution LLM Oversight (Y. Han, C. Yan, W. Zhang) | 25 Aug 2026; version not shown | no | L1: presentation unit (1 to 8 actions per verifier call) shifts rejection, informedness peaks at 1 to 2. Reject direction, agent actions, not choice among candidates; no target-absent pools. Cited by 2610.17301 (per search). | not overlapping (adjacent; possible contrary-direction citation) |
| 2406.12319 | The Comparative Trap: Pairwise Comparisons Amplifies Biased Preferences of LLM Evaluators (Jeong, Park, Hong, Lee, Choo) | Jun 2024; v3 and v4 exist in index; published BlackboxNLP 2025 | no | L1: closest precedent for "comparison makes the judge worse than isolated judgment" (pairwise vs pointwise bias; PRePair). No target-absent pools, no pool size, no lineup bridge | partial (prior art for the comparison-vs-isolation contrast only) |
| 2610.29147 | VERDICT: Multi-Agent Parallel Modular Verification (Tengjie Lin et al.) | 21 Oct 2026, v1; listed as ICSE 2027 | no | Formal-spec synthesis for deductive verification, per-function agents. No overlap with L1/L2/L3 | not overlapping |
| 2610.40535 | Efficient Scalable Oversight via Rewinding (Guan, Kalai, Rothblum, Xi) | v1 29 Oct 2026; html references v2 30 Oct 2026 | no | L2 only at the level of "scalable oversight": rewindable interactive proofs, complexity-theoretic, MNIST demo. No debate on target-absent pools, no LLM judge choosing | not overlapping (cite as scalable-oversight context for L2) |
| 2609.29921 | Who Holds the Pen? Let Specifications, Not Agents, Sign Off (Haiqing Li + 9) | 24 Sep 2026, v1 | no | Agent completion claims exceed evaluator pass rates by 28.7 to 37.9 pts; SpecHarness gating. Self-verification over-claiming, not candidate pools. No L1/L2/L3 design overlap | not overlapping |
| 2610.01042 | Beyond Final Accuracy: Auditing Communication in LLM Multi-Agent Systems (S. Li, W. Yang, P. Zhang, A. Cheng, H. Ping, P. Bogdan) | Oct 2026 (1 Oct per earlier audit), version not shown | no | L3: ICR framework, fixed initial trajectories, no-message revision control, correction vs preservation conditional on initial correctness. L2: conditions on initial correctness (includes both-wrong cells) but not designed as target-absent. No checker-graded valid/invalid critiques, no mediation estimate, no label swap seen | partial (L3 control design heavily anticipated; core L3 pieces not seen) |
| 2606.02646 | The Ringelmann Effect in Multi-Agent LLM Systems: A Scaling Law for Effective Team Size (Bertalanic, Fortuna) | 31 May 2026, v1; NeurIPS 2026 poster | no | Effective team size law (Kish design effect). L3 neighbour only: earlier corpus audit records a noise placebo tracking debate gains (not re-verified here). No target-absent, no mediation | not overlapping (context) |
| 2606.15712 | Odds Law: The Decomposition Algebra On How Intelligence Organizes Itself to Solve Difficult Problems Reliably (H. Aksu) | Jun 2026; version not shown | no | Verifier as likelihood ratio, threshold at Lambda > 1. Theory, not L1/L2/L3. Critiqued by 2607.13918 (correlated verifier cascades) | not overlapping |

## Snippet text for the partial rows (search-tool snippets, not read on page)

- 2406.12319 (snippet of abstract): "these biases are exacerbated in pairwise evaluation, where LLMs directly compare two outputs and easily prioritize superficial attributes. In contrast, pointwise evaluation, which assesses outputs independently, is less susceptible to such bias because each output is judged in isolation."
- 2610.01042 (snippet of abstract): "ICR, a controlled framework that evaluates communication as answer revision following independent reasoning"; "similar aggregate accuracy can conceal substantially different revision behaviors."
- 2608.17270: search summary states each paper is "paired with its hypothesis and fifteen incorrect alternatives" (target-present). A search for "2608.17270v2" returned nothing; listing per the search tool "shows only v1". Not confirmed on the abs page.

## Newer or adjacent items surfaced while following the topic (Aug to Oct 2026; none opened)

Found by search only; titles and ids as listed in the index. None claims target-absent lineups, the eyewitness bridge, debate on target-absent pools, or a checker-graded mediation with label swap.

- 2608.25937 Candidate supply and answer selection shape the value of LLM judging in multi-agent systems (Aug 2026). L1-adjacent; search summary says its ranking analysis excluded all-wrong pools.
- 2608.07813 When the Judge Should Not Decide: Evidence-Locked, Non-Compensatory Selection Bounds LLM-Judge Failure in Reasoning Pipelines (Aug 2026). L1-adjacent (judge regressions when correct consensus is absent from evidence).
- 2607.12885 LLM Judges Can Be Too Generous When There Is No Reference Answer (Jul 2026). L1-adjacent (isolated-judge leniency; relevant baseline for "accept alone").
- 2608.31016 LLM Judges Verify Presence, Not Absence: Omission Blindness (Aug 2026). Different "absence" (missing content), not absent target.
- 2608.17994 Judge, Retrieve, or Abstain (COLM 2026). Abstention with risk control; L1 remedy-adjacent.
- 2609.35279 Measuring Collapse and Correction in Homogeneous-Panel LLM Debate (Sep 2026); 2609.35875 Beyond Symmetric Agents (Sep 2026). L2-adjacent (debate correcting wrong majorities), not target-absent by design.
- 2610.35930 Who Convinced Whom? Tracing How LLMs Change Their Minds in Multi-Agent Systems (Oct 2026), 2610.02702 Silent Dissent (Oct 2026), 2610.30491 What the Trace Shows and What the Label Says (Oct 2026). L3-adjacent (influence tracing, label vs trace); not opened, so whether any randomizes critique validity is unknown. 2610.35930 is the one to open first once arxiv.org is reachable.
- 2610.17301 The Agent Knew (Oct 2026) cites 2608.23941; unrelated to L1/L2/L3 by title.

Searches for LLM + eyewitness lineup / simultaneous vs sequential / relative judgment, and for "target-absent" + LLM judge, returned no LLM paper making the bridge.

## Pages I could not reach

All of: arxiv.org/abs/{2608.17270, 2608.16003, 2608.23941, 2406.12319, 2610.29147} (DNS blocked; the remaining five ids were not retried on arxiv.org after the host was confirmed blocked), alphaxiv.org/abs/2608.17270, api.semanticscholar.org (2406.12319), semanticscholar.org/arxiv/2608.17270, api.openalex.org, huggingface.co/papers/2608.17270, doi.org/10.48550/arXiv.2608.17270, pith.science/paper/2608.17270, aclanthology.org/2025.blackboxnlp-1.5, opentrain.ai (2608.16003), fugumt.com (2406.12319v4). "Cited by" lists could not be opened on any service.

## Overall verdict per line (provisional: search-index evidence only)

- **L1 Lineup**: not scooped on the evidence available. Partial prior art for the comparison-vs-isolation contrast (2406.12319) and for target-present hypothesis ranking (2608.17270). Whether 2608.17270 has a v2 with a target-absent condition could not be confirmed on the abs page; the index shows v1 only. Eyewitness bridge: no LLM paper found.
- **L2 Debate on target-absent pools**: not scooped. 2610.40535 is scalable-oversight theory (rewinding), not debate on absent pools; 2610.01042 and 2609.35279 condition on initial correctness without a target-absent design.
- **L3 Causal mediation**: partial. 2610.01042 anticipates the no-message control and conditional correction/preservation design; no paper seen with checker-graded randomized valid/invalid critiques, a formal mediation estimate, or a label-swap test. Open 2610.35930 and 2610.30491 before claiming novelty.
