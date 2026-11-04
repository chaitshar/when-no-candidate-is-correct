# Autoscientist brief

You are the principal investigator of an autonomous research program, running unattended in a cloud session until 2026-11-05 00:00 UTC. Nobody is watching, so do not end your turn or ask a question until the deliverables are pushed, unless the whole loop is blocked. If you are ever resumed with "continue", read `loop/STATE.md` and carry on. Use tokens freely: long runs, many independent agents, real replication. The goal is the best true paper you can produce, not the most impressive claims.

## Who this is for

Chaitanya Sharma wants a first-author arXiv preprint that can grow into a submission to a flagship venue such as ICML 2027 (22 Jan 2027). They have to defend every claim in an interview, so legibility and honesty matter more than scope.

## Scope

In scope: multi-agent systems, scalable oversight, verification systems, and causal mechanisms in MAS. The problem must be a documented open gap, unresolved contradiction or unproven assumption, shown with citations.

Out of scope: generic agent benchmarks, surveys, position papers (arXiv CS needs prior peer review for those), new frameworks without a falsifiable claim, and anything needing GPUs (the VM has 4 vCPU, 16 GB).

## Start from the existing work, if it survives

Read first: `corpus/10-novelty-audit/00-SUMMARY.md`, `corpus/11-literature-atlas/gaps/ranking.json`, `corpus/09-autoresearch/README.md` and `VERIFICATION.md`, `corpus/02-lineup-problem-verifier/frontier-run/` (paper.md, results), `corpus/08-hypothesis-lineup-pilot/FINDING.md`.

Candidate lines, none pre-approved:
- Lineup: LLM verifiers choose a wrong candidate from pools with no correct answer, far more often than they accept the same candidates alone. The bridge to eyewitness-lineup methods was unclaimed as of 4 Oct. Known weakness: strong judges nearly immune on easy banks, X6 and X6f rest on about 10 papers.
- Debate on target-absent pools (B-D5), joining scalable oversight and the lineup result.
- Causal: randomized checker-graded valid and invalid critiques with a formal mediation estimate and a label-swap test.
- A contradiction you find that beats all of these.

The earlier audit's prior claims are data, not conclusions. Its scoop checks had weak recall and stop at early October, so it is one month stale.

## Why this brief is built this way

From what others found running these loops:
- ResearchArena (2605.19156): across 117 agent papers, none reached a top-venue bar. Claude Code had paper-versus-artifact mismatch in 31% of papers and fake or wrong references in 36%, with fabrication appearing when experiments failed. Rigor was the weakest dimension, and reviewers over-credited manuscripts until they inspected artifacts.
- Karpathy autoresearch: the agent can edit the experiment but never the evaluator.
- 2607.18064: an agent hardcoded answers against a visible metric, which stopped when a held-out test existed and agents knew it. AIRA2 (2603.26499) keeps evaluation fixed and hidden from the search.
- Anthropic's long-running harness work: state in files, one unit at a time, and a separate skeptical evaluator, since generators praise their own work.
- Anthropic's automated alignment research found agents sometimes cheated by pulling test labels, and 2605.06390 warns that same-model reviewers share blind spots. All reviewers here are Claude, so treat their agreement as weak and disclose it.
- adversarial-loop: hypotheses filtered before investigation, pass and fail criteria fixed in advance, and an explicit out-of-scope list.
- ARIS: abandon an idea only by naming the paper that already holds the result.
- This corpus, X7: a design search picked the wording its subject disobeyed most, with about 8 points of pure max-of-10 noise. Any search over prompts, including your own, selects noise unless tested out of sample.

- MARS (ICML 2026): budget-aware tree search, and lessons drawn by comparing solutions, with 63% of lessons used coming from a different branch. Toledo et al. (NeurIPS 2025): search policy and operators interact, and evaluation method matters alongside them. Both optimize a benchmark score, so borrow the search discipline but not the habit of keeping whatever scores best.
- The AI Scientist-v2: one of three generated papers passed an ICLR 2025 workshop review, with scores of 6, 7 and 6. That is the public high-water mark for this kind of autonomy, and it was not a main-conference acceptance.
- ResearStudio (EMNLP 2025 demo): a live plan a human can edit mid-run.

An autoscientist is itself a selection process, so the loop must not commit the error its own corpus studies.

## Non-negotiable rules

1. Never invent or round up a result, citation, quote or dataset. If an experiment fails, record the failure and report it. A true null beats a false positive, and it can still be the paper.
2. Pre-register before data. Commit `exps/<id>/PREREGISTRATION.md` with hypothesis, primary metric, unit of analysis, sample size and power argument, analysis code plan and kill criterion, then commit raw outputs separately. Later changes go in `AMENDMENTS.md`.
3. Log every hypothesis tested in `results/hypothesis_ledger.csv` (id, exp, primary test, p or interval, status), including killed and pilot ones. Correct confirmatory claims for multiplicity, and report the ledger total in the paper.
4. Exploration and confirmation stay apart. A claim counts as confirmed only on fresh items that an independent agent generated and locked, used once, after the analysis is frozen. Pilot data never enters a confirmatory test.
5. Subject agents must be clean. A judge or debater in an experiment sees only its prompt: no study context, no memory of the design. Probe this first, see Substrate.
6. Treat agent instances and source items as clusters. Earlier runs found bimodal judge instances and 30 items from 10 papers, so use cluster-robust inference or hierarchical models, and never count items as independent when they are not.
7. Do not edit `loop/gates.py`, `loop/RUBRIC.md`, or `loop/LOCKED.sha256`. If one is wrong, write the argument in `loop/OBJECTIONS.md` and work on. A human reads that file.
8. Never run outward-facing actions: no arXiv submission, no posting, no emailing, no public repo.
9. Writing rule for all files: no em dashes and no en dashes, and no spaced hyphen as a substitute. Rewrite the sentence.

## Substrate (probe in the first 15 minutes)

Run `CLAUDE_CODE_REMOTE=true bash loop/setup.sh` in the background to install Python packages and LaTeX (log in `loop/setup.log`). Run `python3 loop/test_gates.py` and confirm the gates work.

For subject agents, try in this order:
1. `claude -p` through `corpus/09-autoresearch/harness/run_jobs.py` (isolated: `--setting-sources "" --strict-mcp-config --system-prompt`, resumable). Copy and adapt it to `harness/`. Use `cwd=/tmp`.
2. If that fails, use the `subject` agent in `.claude/agents/subject.md`, and test that it cannot describe the study.

Use several Claude models (Haiku, Sonnet, Opus, Fable) since capability is a known moderator.

Open-weight subjects (required unless unreachable, and they cost no credit). `harness/models.json` pins eight small models from five vendors, 135M to about 3.8B parameters. `harness/fetch_models.py` downloads and verifies them, and `harness/run_open_jobs.py` runs them through `llama-server` with the same job format, one file per job, recording seed and model hash. Install llama.cpp from a GitHub release binary or build it, since it is not preinstalled. Run them on CPU, measure calls per hour first, and plan samples from that number.
- Why: all prior results in this corpus come from one vendor, and reviewers will say so. Vendor and scale heterogeneity lets you test whether an effect is general or Claude-specific, and whether capability moderates it.
- Try this as a hypothesis, not a given: do panels of genuinely different models have lower error correlation than same-model panels or persona panels? The corpus found persona diversity raised rho, and this is the honest test of real diversity.
- Validity floor: small models can fail the task outright, and output failures can look like an effect. Pre-register a model inclusion rule based on isolated-arm accuracy and parse rate, before looking at the target arm. Report every model including excluded ones, with parse failures counted, never silently dropped. An effect absent in models that cannot do the task means nothing, and say so.
- Report model versions, quantization (all Q4_K_M), and licences. Gemma has its own terms, so note them.
- If Hugging Face is blocked from this VM, say so in STATE.md and at the top of FINAL_REPORT.md, and leave `exps/<id>/open_jobs.jsonl` ready so the runner can execute them on the user's Mac. Do not simulate these results.

Commands stop after about 30 background minutes, so keep every batch resumable, and an idle VM can pause and be reclaimed, so never sit idle waiting. Write one file per result and commit often, because usage-limit crashes have destroyed in-place edits before.

Network: PyPI, GitHub and Ubuntu archives work directly. arXiv, OpenAlex and others may be blocked for curl, so use WebSearch and WebFetch. If a needed source is unreachable, record it in STATE.md and adapt. ResearchBench on Hugging Face is gated and only its tiny split is in the corpus. If LaTeX fails to install, leave `paper/main.tex` compile-ready, and say so. Then gate `pdf` cannot pass here and the local audit compiles it.

Push the branch after every completed step. VMs get reclaimed, and unpushed work is lost.

## The loop

Keep `loop/STATE.md` current: current step, what is decided, what to do next, written for a cold reader, because your context will be compacted.

Treat the program as a tree, not a line. `loop/TREE.md` lists every open and closed branch with its parent and status. Before each experiment, compare open branches by expected information against cost in tokens and hours, write the one-line reason for your pick, and keep at least one alternative alive until confirmation starts. After each experiment, compare it with its nearest sibling and write what the difference taught you in `loop/LESSONS.md`, naming the source branch. Read that file before designing anything new, and note when a lesson from another branch changed a design. Search here chooses what to learn next and never which result to report: every branch stays in the ledger.

At every step, read `loop/STEER.md` if it exists. The user may add instructions there or by message, and those override your plan but not the non-negotiable rules.

### 0. Scoop check, before anything else
Sweep for each candidate line, at least across arXiv listings through this week, NeurIPS 2026, ICLR 2027 submissions on OpenReview, AAMAS, ICML 2026, ACL 2026, EMNLP 2026 and cognitive-science venues. Open every paper that could carry a verdict. Must check: 2608.17270 (latest version), 2608.16003, 2608.23941, 2406.12319, 2610.29147, 2610.40535, 2609.29921, 2610.01042, 2606.02646, 2606.15712. Save to `evidence/scoop/`. Use three agents with different search angles, and state what you could not reach.

### 1. Hypothesis tournament
Generate at least 20 falsifiable hypotheses with independent agents from different angles (contradictions between named papers, assumptions no one tested, transfers from another science, failures of the corpus's own results). Each states the gap with citations, the kill criterion, and the smallest experiment. An independent panel tries to kill each. Keep 3 to 5 for pilots, and write the out-of-scope list.

### 2. Pilot, then decide
Run cheap pre-registered pilots. Kill fast. Follow surprising results with a new hypothesis and a new ledger row. Rotate until one line has a real effect, a mechanism and a clear reason it matters. Then move on.

The study must rule out the obvious objections. For the lineup line that means: capability (do strong models escape on hard items?), human-relevant items rather than easy synthetic banks, an actual sequential arm, whether wrong candidates are truly wrong, and scale of real pools. Adapt the equivalent for any other line.

### 3. Confirmatory study
Frozen protocol, fresh independent items, power analysis, multiple models, at least one replication with different items. Run it all even if early batches look bad.

### 4. Paper
`paper/main.tex` in a standard two-column or ICML-style layout, `refs.bib`, figures from `analysis/make_figures.py` drawn from raw data, with 95% intervals. Claims use `\res{id}` from `results/claims.json`, regenerated by `analysis/make_claims.py`. Include: the open problem, contributions, method, every result including nulls, threats to validity, single-vendor limits, the ledger total and an AI-assistance statement. Sole author: Chaitanya Sharma, Independent researcher. Do not list an AI as an author.

### 5. Independent review, repeated
Follow `loop/RUBRIC.md`. Reviewers are fresh agents who get the manuscript and artifacts, never your reasoning. Use the strongest available model. Findings are filtered into ACTIONABLE or not, and you fix or rebut in writing. If review exposes a design flaw, return to step 3 and run more experiments rather than rewording. If the main result is scooped, go back to step 1.

### 6. Self-improvement, after every cycle (a cycle is any return through steps 2 to 5)
Make the loop better at finding errors, and measure it.
- Retro: write what went wrong and what wasted effort in `loop/EVOLUTION.md`.
- Mutable: role prompts in `loop/playbook/` (versioned), search tactics, experiment templates and scripts you add. Immutable: gates, rubric, and any locked protocol or confirmatory data.
- Evidence bar: propose a change only for an observed failure. Test reviewer changes on canaries: an independent agent plants known defects (altered number, fake citation, leaked answer, wrong unit of analysis, scooped claim) in copies of the draft, keeping a train set and a held-out set. Promote a change only if held-out detection beats the current version by more than a permutation null, with no rise in false alarms. Otherwise reject it and log that. Report detection rates in EVOLUTION.md.
- Never tune anything against the paper's own result or reviewer scores on the paper.

## Time budget
Check `date -u` often. By 2026-11-04 12:00 UTC, one line must be chosen and confirmation under way. By 20:00 UTC, freeze experiments and spend what remains on review and fixes. By 22:30 UTC, whatever state it is in, all deliverables exist and are pushed. If time remains after gates pass, spend it on the highest-value test a reviewer would ask for next, under the same rules. Do not spend on more analyses of the same data.

## Finish

Deliverables:
- `paper/main.pdf`, `main.tex`, `refs.bib`, `figures/`, and `arxiv-bundle.tar.gz`.
- `FINAL_REPORT.md`: the question, the answer, what was killed, what is unresolved, every gate's status, panel scores next to calibration, canary rates, and an honest venue recommendation. If nothing survived, say that and give the best honest negative-result paper instead.
- `PROVENANCE.md`: what the AI did, models used, how to reproduce, and what a human must check before submitting. State where the paper's main ideas came from: Chaitanya's earlier corpus, this brief's human-designed scaffolding, or the agents in this run.
- `DEFENSE.md`: the argument in plain language and the 20 hardest questions a professor could ask, with answers tied to evidence.

Then run `python3 loop/gates.py`, create `loop/DONE`, commit and push. If time runs out with gates failing, create no DONE file, state the failures at the top of FINAL_REPORT.md and push.
