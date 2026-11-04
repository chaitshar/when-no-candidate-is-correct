# Current rules (top item added 2026-11-03, user steering received about 22:40 UTC by date -u)

0a. BUDGET: subject-call cap 230 USD total including 56.35 USD already spent (replaces 110 USD). Per-screen limit 10 USD (replaces 3 USD). Credit is 250 USD and agents draw on it too: log best estimates of orchestrator and agent cost in results/cost_ledger.csv and stop subject spending early if subjects plus agents approach 230 USD. Model tiers unchanged: signal first, frontier models after.
0b. BENCHMARKS: do not make up test or training data (reverses the earlier preference for generated tasks, which was an error). S0 stopped; gen/progtrace*.py and gen/countgen.py retired as data sources; S0 stays in the ledger as abandoned, not evidence. Screens are re-preregistered on established benchmarks: popular, citable, official ground truth or scoring, pinned version or commit; hard for the exact subject models (calibration split of the benchmark itself, per model; no interpretation at floor or ceiling); benchmark's own splits, items never edited; fits the mechanism, MAS or oversight benchmarks preferred. Gated or account-only sets go to STATE.md "Needs user". Respect licences. Keep the contamination check as a per-model, per-bank limitation label. Candidates judged are current models' outputs on benchmark items, scored by official ground truth.
0a-note (date -u 2026-11-03 23:50): subjects 129.55 USD plus agent estimate about 96 USD is near 230 USD. Decision: finish the preregistered C2 haiku run (about 4 USD), then no new subject spending. Remaining agent work kept minimal (review panel on Sonnet except area chair and hostile expert on Opus, as calibrated).
0c. Times are taken from `date -u`, never estimated.
0d. OPEN MODEL (user message about 22:50 UTC): the Mac runner is back with one model only, gemma-4-e4b (Q4_K_M, thinking on by default). Tooling check: 21 of 24 calls truncated in thinking at max_tokens 2048, median 97 s per call. First commit a calibration batch of at most 40 calls (max_tokens 6000, prompts under 2000 tokens, context 8192). Plan at most about 500 gemma calls in total. Use only where a benchmark and its inclusion floor make it worthwhile, same per-model scope rules. Queue by pushing exps/<id>/open_jobs.jsonl with model gemma-4-e4b; outputs arrive on branch open-model-results.

# Earlier current rules (consolidated 2026-11-03; still in force unless superseded below)

Non-negotiable rules and gates in PROMPT.md still hold. Full message history: loop/STEER_history.md plus the four steering messages of 22:20 to 22:25 UTC summarized here.

## Cost
1. [SUPERSEDED by 0a] Subject-call cap 110 USD, 3 USD per screening pilot. Hold back 40 USD of agent work for final review and fixes.
2. Model tiers for agents: Haiku for sweeps, extraction, parsing, stimulus building, formatting; Sonnet for code, analysis, hypothesis generation, drafting, most reviewers; Opus or Fable only for final design decisions, the final review panel, hard statistical judgment. Set model explicitly on every Agent call. Lower effort for mechanical agents.
3. Subjects: screen on Haiku and Sonnet. Opus or Fable subjects only after a screen shows signal, on the smallest sample that answers the question.
4. Keep results/cost_ledger.csv (exp, model, resolved id, purpose, calls, cost from total_cost_usd).

## Models and scope
5. Current models only. No outdated or weak models as subjects. Older Claude versions are not used.
6. No generalization across models. Every claim names the exact resolved model id (from the API response, recorded per call as model_used), date, and parameters (claude -p 2.1.317 defaults: temperature not set by us, no extended thinking requested, no tools, fixed system prompt in harness/run_jobs.py). Report per model, never pooled. Never "LLMs do X". Results do not extend to other labs; the paper says so.
7. A claim about a frontier model needs data from that model.
8. Open models: only the current tier in harness/models.json (gemma-4-e4b, qwen3.5-9b, ornith-1.5-9b, nemotron-3.5-bolt-e4b), Mac only, batch, screening or bulk mechanical use, each passing a preregistered inclusion floor on fresh items. [Runner status superseded by 0d.] Data already collected from old small models is kept, reported as a deviation, and carries no weight.

## Items
9. Benchmarks must be hard for current models and unlikely to be memorized. MATH, PRM800K, GSM8K, CRUXEval are not valid evidence for a current-model claim. P1 and P2 are reported as limited to those (GPT-4-era) items.
10. [SUPERSEDED by 0b] Item source preference: (a) procedurally generated tasks from a seeded generator written for this study, machine-checkable answers, instances created after the code is frozen, difficulty tuned on a separate calibration split; (b) material dated after each subject's training cutoff with checkable ground truth (record dates and the cutoff relied on); (c) public sets only as secondary evidence after a contamination check (no-working accuracy and verbatim continuation versus matched fresh items, exclusion rule fixed in advance). Omni-MATH (P3) is category (c).
11. Difficulty calibration per model before spending on arms: solve rate roughly 0.2 to 0.8 and isolated false accept rate above zero on a calibration split. If a model cannot be calibrated off the floor, say so and do not interpret that bank for that model.
12. Candidates judged by subjects are errors from current models on the same fresh items, verified wrong by machine.
13. Each bank gets a one-paragraph justification in its prereg: why fresh, why hard, why it measures the mechanism. Report the representativeness limit of generated tasks and prefer a second source for replication.
14. The MATH-based locked banks (banks/locked/) cannot support a confirmatory claim; they are kept and replaced by an independent agent, recorded in an amendment, before any confirmatory analysis is frozen.

## Breadth and claims
15. Screening portfolio of at least 10 distinct MAS questions across mechanisms (rejection channels in voting, ranking, planner-critic and debate; causal mediation with checkable critiques; failure attribution by counterfactual replay; error propagation across topologies; handoff information loss; correlated verifier blind spots; weak judge with hidden evidence; memory contamination; shared-budget incentives; heterogeneous vs homogeneous teams). Each screen: written prereg, ledger row, kill rule, cheap. Include at least one screen that retests a claim the MAS field relies on, with current models.
16. Rank survivors by surprise against stated literature beliefs, then prior-art check before spending more. Breakthrough bar: contradicts or sharply limits a relied-on claim, changes what a builder should do, survives a prior-art red team, replicates on fresh locked items. Correct across the whole ledger; never report a screen as a finding. If nothing clears the bar, say so and write the strongest honest paper.
17. Earlier corpus results are lineage, not evidence. Older-model papers can still scoop the idea: cite them and state the model difference.

## Practice
18. Role separation (Research Director, Investigators, Critic, Evidence Verifier); claim-evidence-source table with VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, CONTRADICTED; never silently replace a dead citation; failure taxonomy (loop/playbook/v1/failure_taxonomy.md); ablations; full distributions, not best runs.
19. No LLM judge as sole ground truth; matched compute comparisons; tokens, cost, wall time, retries, failure rates per arm; exact status label for every citation; PROVENANCE.md lists human inputs; AUDIT_SAMPLE.md with 30 claims and 20 citations; self-improvement changes need regression on earlier canaries and a downstream-adherence check.
20. Network is full (arxiv, openreview, aclanthology, huggingface returned 200 at 22:25 UTC). Re-open every paper behind a snippet-based scoop verdict or kill; log reversals.
21. Context: agents get small briefs with paths, return under 200 words, write details to files; numbers always recomputed from raw; STATE.md updated after every step; results/CLAIMS_STATUS.md lists live claims with model id and evidence file; mark STALE when rules or data change.
22. Do not pace to the PROMPT.md time budget; finish as fast as quality allows. After MAS deliverables are pushed, task2/README.md on origin/main may be done, never at MAS's expense. Stop at 2026-11-05 00:00 UTC.

# Superseded
- Cap 110 USD and 3 USD per screen: replaced by 0a.
- Procedurally generated tasks as the preferred item source (rule 10a) and S0 calibration on gen/*: replaced by 0b; reported as abandoned.
- Timestamps written from memory in STATE.md and DECISION.md (for example STATE said 23:00 UTC when date -u read about 22:27): replaced by 0c.
- "Use tokens freely" (PROMPT.md): replaced by the cost caps above.
- Small open models (135M to 3.8B) as required subjects: replaced by rule 8.
- Open models for first-pass screens on the Mac: runner stopped.
- PRM800K / MATH pools as primary evidence and the MATH-based locked banks for C1: replaced by rules 9 to 14. C1 as preregistered is withdrawn (see exps/c1_confirm/AMENDMENTS.md).
- Omni-MATH as primary evidence for P3: now secondary only, after a contamination check.
