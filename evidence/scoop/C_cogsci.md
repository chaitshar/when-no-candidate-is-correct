# Scoop check C: cognitive science and psychology-of-LLMs angle

Date: 2026-11-03. Angle: cognitive science venues, the machine-psychology and cognitive-bias-in-LLMs literature, and eyewitness-lineup science as applied (or not) to LLMs.

## IMPORTANT: access limitations (read first)

**No paper could be opened in this session.** WebFetch failed with DNS/policy denial (`getaddrinfo ENOTFOUND`, proxy 403 on CONNECT) for every scholarly host tried:
arxiv.org, ar5iv.labs.arxiv.org, www.alphaxiv.org, www.semanticscholar.org, aclanthology.org, escholarship.org, neurips.cc, pmc.ncbi.nlm.nih.gov, link.springer.com, scilit.com, www.stat.cmu.edu. A curl probe of api.crossref.org, api.semanticscholar.org, export.arxiv.org, api.openalex.org, pmc.ncbi.nlm.nih.gov and aclanthology.org also returned no connection (000).

So:
- All evidence below comes from **WebSearch result titles, URLs and the search tool's summaries/snippets**. None of it was read from the source paper.
- Text in quotation marks below is **search-snippet text, not verified against the paper**. Treat it as a pointer, not a quote. No verbatim quotes from opened papers are given, because none were opened.
- **No `evidence/citations/*.json` files were written**, because the brief asks for one per *fetched* paper and none were fetched. Writing them from snippets would make unverified metadata look verified. The "To fetch" table at the end lists the keys and URLs to use once the hosts are allowed.
- These verdicts are **provisional**. A "none" here means "not found by search", not "checked against the full text".

## L1 "Lineup": target-absent pools; relative vs absolute judgment in LLM verifiers

### Direct bridge (eyewitness science applied to LLM judges/verifiers)
Searches combined: LLM/large language model with eyewitness, lineup, culprit-absent or target-absent, relative judgment, sequential lineup, mock witness, filler, diagnosticity ratio, pAUC and lineup ROC; CogSci 2026 with LLM and lineup; "police lineup" analogy with LLM judge.
**Result: nothing found.** No paper treats an LLM judge or verifier as a lineup witness, imports Wells (1984) relative judgment, Steblay's simultaneous vs sequential results, Clark's WITNESS model, Wixted and Mickes lineup ROC/pAUC, diagnosticity ratios, filler siting or the dud-alternative effect into LLM evaluation. The search hits that came closest are in a different direction: AI helping *humans* with lineups (a PNAS 2025 paper from Colorado, "AI assistance improves people's ability to distinguish correct from incorrect eyewitness lineup identifications"), FaceNet compared with human witnesses (Cogn. Res. 2024), ChatGPT used to build blended lineups, and NLP classification of verbal witness confidence (Psychological Science 2024). None of these uses an LLM as the witness.

### Closest papers on the phenomenon (pick a wrong option when none is correct)

| Paper (as found by search) | URL | Overlap with L1 | Verdict |
|---|---|---|---|
| Wang, Zhao et al., "LLMs May Perform MCQA by Selecting the Least Incorrect Option", COLING 2025 (arXiv 2402.01349) | https://arxiv.org/abs/2402.01349 | **Closest threat.** Snippets say MCQA+ adds "true/false versions of each question" and versions where the correct answer is "replaced with 'None of the Above'". That is in effect a per-option absolute judgment set against an in-pool relative choice, with a target-absent variant. But it is about **answering** MCQs, not verifying candidate solutions, and has no eyewitness framing. | Partial (needs fetch: check whether they report wrong-option selection in NA-replaced pools against acceptance of the same option in true/false form) |
| Kadavath et al., "Language Models (Mostly) Know What They Know", 2022 (arXiv 2207.05221) | https://arxiv.org/pdf/2207.05221 | Replacing one option with "none of the above" "decreases accuracy very significantly" and "also harms calibration" (snippet). This is the target-absent MCQ effect in answering. | Partial (background) |
| Tam et al., "None of the Above, Less of the Right: Parallel Patterns between Humans and LLMs on Multi-Choice Questions Answering", ACL Findings 2025 (arXiv 2503.01550) | https://arxiv.org/abs/2503.01550 | 28 LLMs on MMLU; snippet: "a consistent 30-50% performance drop across models regardless of scale" when NA is correct; draws a human-LLM parallel (a cognitive framing, but from test-taking, not lineups). | Partial |
| Wang, Lin, Zhu, Liu, Li, Chen (Duke), "When No Answer Is Correct: Diagnosing Absent Answer Detection for MLLMs in Video Understanding", EMNLP 2026 (arXiv 2606.08239) | https://arxiv.org/pdf/2606.08239 ; https://aclanthology.org/2026.emnlp-main.980/ | Snippet: "MLLMs overwhelmingly select plausible distractors rather than detecting the absent answer"; when ground truth is removed, models keep "near-baseline confidence" in the distractor. That resembles the dud/confidence side of lineup science. Answering, not verifying; video MLLMs. | Partial |
| Stephan et al., "From Calculation to Adjudication: Examining LLM Judges on Mathematical Reasoning Tasks", GEM 2025 (arXiv 2409.04168) | https://arxiv.org/html/2409.04168v2 | **Judge setting.** Pairwise math judges, with conditions stratified by whether both, one or neither candidate is correct; per a search summary, judges "struggled most when both were wrong" and favour stronger models "even if their answer is incorrect". It is a two-member target-absent pool, but it has no single-candidate baseline and no lineup framing. | Partial (needs fetch: does it compare a pool-of-2 choice with standalone acceptance?) |
| Contextual quality reward model for BoN (arXiv 2510.04087) | https://arxiv.org/html/2510.04087v1 | Snippet: BoN "may simply select the least bad of many poor options"; reliability failures "more than double" from N=1 to N=32. This is close in spirit to target-absent picking growing with pool size (cf. choice overload). It concerns a reward model, not LLM verifier behaviour, and has no psychology framing. | Partial |
| "LLM-as-an-Improver: Turning Verification into Better Candidates" (arXiv 2609.19515) | https://arxiv.org/pdf/2609.19515 | Stratifies LiveCodeBench pools by "all-incorrect" (117 problems) and notes that fixed-pool selection must fail there. It does not measure verifier false-pick against standalone acceptance. | Weak |
| Valkanova and Yordanov, "Irrelevant Alternatives Bias Large Language Model Hiring Decisions" (arXiv 2409.15299) | https://arxiv.org/html/2409.15299v1 | Attraction/decoy effect in GPT-3.5/4 acting as recruiters; robust to warnings. A context effect from the pool, not target-absent verification. | Weak (supporting context-effect evidence) |
| Xie, Huang and Busemeyer, CogSci 2025 (context effects in GPT models; escholarship 4fv3t754) | https://escholarship.org/uc/item/4fv3t754 | Snippet: LLMs "consistently exhibit all four context effects" (similarity, attraction, repulsion, compromise). This is the cognitive-science venue precedent for pool-composition effects in LLM choice. It is not about verification or target-absent pools. | Weak (cite as related) |
| "The Decoy Dilemma in Online Medical Information Evaluation" (arXiv 2411.15396) | https://arxiv.org/html/2411.15396v1 | A decoy raises the LLM's credibility ratings of misinformation. A rating context effect. | Weak |
| Cacioli, "LLMs as Signal Detectors: Sensitivity, Bias, and the Temperature-Criterion Analogy" (arXiv 2603.14893, Mar 2026) | https://arxiv.org/abs/2603.14893 | Applies SDT and ROC (sensitivity vs criterion) to LLM factual QA, not to judges or lineups. It is precedent for SDT language, not for lineup ROC/pAUC. | Weak |
| "Balanced Accuracy: The Right Metric for Evaluating LLM Judges -- Explained through Youden's J" (arXiv 2512.08121) | https://arxiv.org/abs/2512.08121 | Diagnostic-test metrics for LLM judges. No pAUC, no diagnosticity ratio, no lineups. | Weak |
| Koo et al., CoBBLEr, ACL Findings 2024 (arXiv 2309.17012) | https://arxiv.org/abs/2309.17012 | Six cognitive biases of LLM evaluators (order, egocentric, bandwagon and others). It has no target-absent or relative-vs-absolute condition, as far as the abstract-level snippets show. | Weak |
| Echterhoff et al., "Cognitive Bias in Decision-Making with LLMs" (BiasBuster, arXiv 2403.00811) | https://arxiv.org/abs/2403.00811 | Prompt-induced, *sequential* and inherent biases (anchoring) in admissions decisions. "Sequential" there means order and anchoring across items, not sequential vs simultaneous lineup presentation. | Weak |
| Hagendorff et al., "Machine Psychology" (arXiv 2303.13988); Binz and Schulz, PNAS 2023 | https://arxiv.org/abs/2303.13988 | Methodological umbrella only. | None |
| Pointwise vs pairwise or listwise judge-protocol work (e.g., "Pairwise or Pointwise?" arXiv 2504.14716; "The Comparative Trap" arXiv 2406.12319; "Am I More Pointwise or Pairwise?" arXiv 2602.02219) | see URLs | Engineering analogue of simultaneous vs sequential (comparative judging amplifies superficial preferences; pairwise flips ~35% under distractors vs ~9% absolute, per snippet). They do not test target-absent pools or false identification. | Weak/partial on the presentation-format contrast only |

Not reachable even as a snippet: "Overwhelmed by Choice: Studying LLM Decision Making at Scale" (NeurIPS 2026, https://neurips.cc/virtual/2026/178247). Only the title surfaced. **It may bear on choice overload and pool size and should be fetched.**

Not found at all: any LLM study of the dud-alternative effect (adding implausible options raising confidence in the chosen one); any LLM study of sequential vs simultaneous presentation *with stopping rules* (first-yes-counts); any use of lineup pAUC or diagnosticity ratio on LLM judges.

**L1 verdict: PARTIAL.** The underlying phenomenon (LLMs pick a plausible wrong option when the correct one is absent; NOTA degrades accuracy) is well established for **MCQ answering** (Kadavath 2022, Tam 2025, Wang COLING 2025, Wang EMNLP 2026), and pool context effects in LLM choice are established (Valkanova and Yordanov; Xie, Huang and Busemeyer CogSci 2025). Not found:
- (a) verifiers judging candidate *solutions*, with the same candidates' standalone acceptance as the within-item control;
- (b) the eyewitness-lineup bridge (relative judgment, sequential vs simultaneous, filler similarity, dud effect, WITNESS-style modelling, lineup ROC/pAUC and diagnosticity).

The novelty claim must be narrowed to (a) and (b), and it must cite the MCQA-NOTA line as precedent. Highest-priority fetch: Wang et al. COLING 2025 (MCQA+ true/false vs MC), because it is the closest to the absolute-vs-relative contrast.

## L2 Debate on target-absent pools

Searched: multi-agent debate with "none of the above" or no correct answer, and false consensus.
Found only general debate-failure work: ReConcile (arXiv 2309.13007), "Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate" (arXiv 2509.05396), persuasion-driven adversarial influence in MAD (Sci. Rep. 2026, https://www.nature.com/articles/s41598-026-42705-7; per snippet, one persuasive agent "lower[s] overall accuracy by 10–40% while increasing consensus on incorrect answers"), and MAD-Fact (arXiv 2510.22967). None of them constructs target-absent pools or measures debate-induced false picks against rejection. There is also no cognitive-science work on group or jury lineup decisions applied to LLMs (the human literature on collaborative witness identification was not searched in depth from this angle).

**L2 verdict: NONE found** (from this angle). Debate degrading accuracy or entrenching wrong consensus is known, so L2 should cite those papers as context.

## L3 Randomized valid vs invalid critiques with causal mediation

Searched: randomized valid or invalid critiques, causal mediation, judge revision and sycophancy.
Closest: "T3 / Diagnosing and Mitigating Sycophancy and Skepticism in LLM Causal Judgment" (arXiv 2601.08258; ACL Findings 2026, https://aclanthology.org/2026.findings-acl.427/). It tests whether models endorse flawed claims or reject valid ones under challenge (per snippet, frontier models "reversed a high percentage of FLAWED judgments when challenged"). Also "Challenging the Evaluator: LLM Sycophancy Under User ..." (EMNLP Findings 2025, https://aclanthology.org/2025.findings-emnlp.1222.pdf; snippet: "inclusion of reasoning in user feedback increases probability of LLM to accept feedback"). "Reason-Mediated Behavioral Models for Auditing LLM Social Simulators" (arXiv 2607.24649) discusses mediation but in a different setting. Nothing found that randomizes critique validity *and* runs formal causal mediation on verifier revisions.

**L3 verdict: PARTIAL→NONE.** The valid-vs-invalid pushback manipulation exists (T3; Challenging the Evaluator). The randomized-critique-plus-mediation design was not found. The cognitive-science angle adds little here; it defers to the ML-angle scoop checks.

## Classic eyewitness sources (bibliographic, from search only, not fetched)

- Wells (1984), "The Psychology of Lineup Identifications", J. Applied Social Psychology 14(2):89–103, doi:10.1111/j.1559-1816.1984.tb02223.x (search hits: scilit, NCJRS NCJ 95183).
- Steblay, Dysart, Fulero and Lindsay (2001), sequential vs simultaneous meta-analysis (23 reports), Law and Human Behavior (venue from background knowledge, not confirmed by search).
- Steblay, Dysart and Wells (2011), "Seventy-Two Tests of the Sequential Lineup Superiority Effect", Psychology, Public Policy, and Law 17(1):99–139 (a CT task-force PDF was among the search hits).
- Mickes, Flowe and Wixted (2012), "Receiver operating characteristic analysis of eyewitness memory: Comparing the diagnostic accuracy of simultaneous versus sequential lineups", J. Exp. Psych.: Applied 18(4):361–376 (the full title is from background knowledge; search showed the journal and pages).
- Wixted and Mickes (2014), Psychological Review, signal-detection diagnostic-feature-detection model (the exact title was not confirmed by search; a Royal Holloway preprint PDF was among the hits).
- Clark (2003), "A memory and decision model for eyewitness identification" (WITNESS), **Applied Cognitive Psychology** 17:629–654 (not Psychonomic Bulletin and Review).
- Charman, Wells and Joy (2011), "The dud effect: Adding highly dissimilar fillers increases confidence in lineup identifications", Law and Human Behavior 35:479–500.
- Relevant counter-evidence for the framing: "Absolute-judgment models better predict eyewitness decision-making than do relative-judgment models", Cognition 2024 (https://www.sciencedirect.com/science/article/abs/pii/S001002772400163X). **L1 should not assert uncritically that relative judgment explains human lineup errors.** The current human literature disputes it (see also the Wixted and Mickes ROC critique of the diagnosticity ratio).

## To fetch once hosts are allowed (proposed citation keys)

| key | URL |
|---|---|
| wang2024llms (COLING 2025 MCQA+) | https://arxiv.org/abs/2402.01349 |
| kadavath2022language | https://arxiv.org/abs/2207.05221 |
| tam2025none | https://arxiv.org/abs/2503.01550 |
| wang2026when | https://arxiv.org/abs/2606.08239 |
| stephan2024calculation | https://arxiv.org/abs/2409.04168 |
| valkanova2024irrelevant | https://arxiv.org/abs/2409.15299 |
| xie2025 (CogSci context effects; confirm title) | https://escholarship.org/uc/item/4fv3t754 |
| cacioli2026llms | https://arxiv.org/abs/2603.14893 |
| koo2023benchmarking | https://arxiv.org/abs/2309.17012 |
| echterhoff2024cognitive | https://arxiv.org/abs/2403.00811 |
| (Overwhelmed by Choice, NeurIPS 2026) | https://neurips.cc/virtual/2026/178247 |
| wells1984psychology | doi:10.1111/j.1559-1816.1984.tb02223.x |
| steblay2011seventytwo | Psychology, Public Policy, and Law 17(1) |
| mickes2012receiver | J. Exp. Psych.: Applied 18(4) |
| clark2003memory | Applied Cognitive Psychology 17 |
| charman2011dud | Law and Human Behavior 35 |

Hosts that need allowing: arxiv.org, aclanthology.org, escholarship.org, neurips.cc, pmc.ncbi.nlm.nih.gov, link.springer.com, semanticscholar.org.
