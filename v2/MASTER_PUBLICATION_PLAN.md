# MASTER PUBLICATION PLAN (v2, locked after Co-PI Round 2)

Co-PIs: Claude Code and Antigravity. Owner: Chaitanya. Date: 20 Nov 2026.
Supersedes CLAUDE_CODE_PLAN_DRAFT.md where they conflict. PREREGISTRATION_V2.md (C4 to C7 on the C3 bank) stays untouched; everything new is an append-only amendment (Section 7).
Style rule: no em dashes, en dashes or spaced hyphens. Ranges are written "a to b". Bullets use asterisks.

Working title: "Lineups Without a Culprit: A Criterion-Shift Law for LLM Selection Among Candidates, and What Fixes It"

---

## 1. Central theory: the SDT Criterion-Shift Law (replaces the broken raw-proportion H1 interaction)

### 1.1 Evidence base (all from results/SDT_AND_SUBGROUPS.md, aligned output space, Hautus 1995, 5,000 problem bootstraps)

PICK minus ISO, paired, delta c (criterion):

| Judge | Stratum | prereg delta c [95% CI] | corrected delta c [95% CI] |
|---|---|---|---|
| Haiku | UNSOLVED | -0.458 [-0.643, -0.288] | -0.526 [-0.756, -0.315] |
| Haiku | SOLVED | -0.639 [-0.928, -0.445] | -0.671 [-0.966, -0.474] |
| Sonnet | UNSOLVED | -0.395 [-0.599, -0.214] | -0.433 [-0.689, -0.202] |
| Sonnet | SOLVED | -0.342 [-0.655, -0.142] | -0.416 [-0.726, -0.225] |

All 8 cells: delta c between -0.34 and -0.67, every 95% CI strictly below 0. This is invariant across both models and both strata.

Sensitivity (delta d'): significant drop only on Haiku UNSOLVED (prereg -0.453 [-0.851, -0.062]; corrected -0.582 [-1.095, -0.106]). Sonnet UNSOLVED and both SOLVED strata have CIs spanning 0.

### 1.2 The law (stated as a falsifiable model)

Equal-variance Gaussian SDT: false-alarm rate F = 1 minus Phi(d'/2 + c). Presenting candidates together (PICK) lowers the acceptance criterion by a roughly constant delta c (about -0.35 to -0.65), independent of problem solvability. The raw false-choice gap then depends only on where the judge sits on the d' curve:

* SOLVED sits in the tail (d' about 3.0 to 3.5): a large criterion shift moves F only a little. Check: Haiku SOLVED ISO d' 2.917, c +0.079 gives F = 0.062 (observed 0.059); PICK d' 3.465, c -0.560 gives F = 0.121 (observed 0.118). Raw rise about +0.06.
* UNSOLVED sits near d' about 0 (range -0.28 to +0.52): the same shift lands on the steep part of the curve. Check: Haiku UNSOLVED ISO d' 0.518, c +0.201 gives F = 0.323 (observed 0.321).

Honest numbers for the raw UNSOLVED gap (PICK F minus ISO F, from the same file): Haiku +0.27 (prereg) and +0.32 (corrected); Sonnet only +0.13 and +0.14. The "+0.24 to +0.35" range is Haiku-specific (the TA-pool subgroup tables give +0.244 and +0.279). The paper must state Haiku and Sonnet separately and must not pool them into one range. Sonnet still shows the predicted ordering (UNSOLVED gap more than 2x SOLVED gap of +0.06).

Status disclosure: the law was identified after seeing C3 data, so it is exploratory in v1 and CONFIRMATORY only in v2. The paper says so in one sentence.

### 1.3 Confirmatory hypotheses (v2)

* H1 (invariant criterion shift): for every judge family j and stratum s, delta c(PICK minus ISO) < 0. Primary test: one-sided paired bootstrap per cell, Holm across cells. Secondary: heterogeneity of delta c across strata, reported with CI of (delta c UNSOLVED minus delta c SOLVED) and an equivalence margin of 0.25 (TOST), so "invariant" is an equivalence claim and not a failure to reject.
* H2 (frontier-specific sensitivity loss): delta d' < 0 on UNSOLVED, tested per judge family, reported as descriptive replication of the Haiku result. Not required for the headline.
* H3 (quantitative prediction, out of sample): fit delta c on SOLVED only, then predict the UNSOLVED raw false-choice gap using each judge's own UNSOLVED ISO d' and c. Pass: predicted gap lies inside the observed 95% CI in at least 2 of 3 judge families. Fail is reported plainly.
* H4 (contamination invariance): the law holds on judge-family-excluded pools (Section 2).
* H5 (mitigation follows the law): a criterion-recalibration arm that shifts c back by the estimated delta c cuts UNSOLVED false choices at no more than 0.05 loss of SOLVED hit rate (Section 5, arm M2).

The old raw-proportion H1 (specificity interaction on false-choice proportions) is retired. Raw gaps are reported as descriptive consequences of the law, never as a test of specificity.

---

## 2. Contamination proof and sampling rule

In v1 corrected UNSOLVED TA pools (N = 68): 63 of 68 (92.6%) contained at least 1 Claude candidate, and only 2 of 68 had zero Claude AND zero own-answer candidates. Prereg set (N = 90): 77 of 90 with at least 1 Claude candidate, 9 of 90 with neither. Subgroup power is therefore nil (the 2-pool cell shows d = 0.000 and 0.500 with degenerate CIs), so v1 cannot separate the law from Claude self-preference.

Mandatory rule for all v2 pools: judge-family-excluded uniform sampling. For judge family J, the pool for J contains zero candidates from family J (no own-family candidate, no own earlier answer), candidates are drawn by seeded uniform RNG over the remaining vendors, no vendor above 1/3 of a pool, positions Latin-squared. Pools are therefore built per judge family, with the family exclusion recorded in the pool manifest. Preflight rejects any pool that violates it.

---

## 3. Budget and feasibility (lean)

Constraint (from Chaitanya): lean budget, targeting 0 to 150 USD out-of-pocket maximum (entered by Chaitanya in `budget.env` as `OOP_MAX_USD` in Phase 0; default recommendation: 15 to 40 USD for `API_SCAFFOLD_CAP_USD`, optional 50 USD for `API_VENDOR4_CAP_USD`, 0 USD incremental on subscription CLIs). The earlier 1,600 to 2,000 USD ceiling in the draft is withdrawn.

Routing:

| Work | Route | Cost model |
|---|---|---|
| Bulk confirmatory matrix, Claude judges | `claude` CLI, `claude-haiku-5-5` and `claude-sonnet-5-5` | existing subscription |
| Bulk confirmatory matrix, other families | `agy` CLI, `gemini-3.8-flash-medium`, `gemini-4-hydrogen-medium`, `gpt-oss-120b-medium` | existing subscription; verified at 2.2 s per call with token telemetry |
| Scaffolding control | raw API, one surgical 60 to 80 pool run, Claude family | paid; cap `API_SCAFFOLD_CAP_USD` set by Chaitanya |
| Optional fourth vendor | raw API | paid; cap `API_VENDOR4_CAP_USD`, default OFF |

Scaffolding tokens are logged transparently, not hidden: about 9.6k tokens per agy call and about 1.3k per claude CLI call are fixed overhead. Every result table carries a "scaffold tokens" column, and compute-matching (C4) is computed on subject tokens net of scaffold.

Right-sized pools (power set by script, `audit/power.md`):

* Math: 180 to 240 pools per judge family, with at least 70 UNSOLVED and 70 SOLVED so each delta c cell has SE near 0.10 (v1 SE at N = 56 to 78 was about 0.10, CI half width about 0.2). Frozen at the power script's output inside that range.
* ResearchBench: 150 to 200 pools per judge family.
* Scaffolding control: 60 to 80 pools, bare API vs CLI, same pools.
* Call estimate (to be converted to dollars only where a paid route applies): about 8 calls per pool for the main arms (PICK x1, ISO x3, EACH x3, plus reliability rerun), so 240 math + 200 science pools times 5 judges is about 17,600 subscription calls; at 2.2 s per agy call this is about 11 hours of wall clock for agy judges, parallelisable within rate limits.

Hard stop: the harness reads `budget.env`; any paid call is refused unless cumulative paid spend plus the next batch estimate is at or below the cap. Chaitanya approves any cap raise in writing in the chat.

---

## 4. Experimental matrix (condensed; full C1 to C9 definitions in CLAUDE_CODE_PLAN_DRAFT.md sections C and A stay in force)

* C1 item bank and solvability panel (3 or more sources, panel solvers not used as judges).
* C2 judge-family-excluded pools (Section 2).
* C3 core: PICK, ISO, EACH, FORCED, SDT per stratum per judge; ISO reliability rerun.
* C4 compute-matched PICK (majority of 3, any of 3), per PREREGISTRATION_V2.
* C5 own-answer removal, per PREREGISTRATION_V2.
* C6 cross-vendor: Claude (2 models), Gemini (2 models), GPT-OSS (1), optional vendor 4.
* C7 mitigation: M0 PICK, M1 ISO-filter-then-PICK, M2 criterion recalibration (H5), M3 isolated sequential.
* C8 thinking off on a 150 pool subset.
* C9 ResearchBench second domain, 150 to 200 pools.
* C10 (new) scaffolding control, 60 to 80 pools, CLI vs bare API.

Primary endpoints, one per leg, Holm across them: delta c (PICK minus ISO) for math, for science, and false choice at matched TP hit for mitigation.

---

## 5. Venue strategy

* Co-primary: TMLR (rolling, open review, suits preregistered empirical and methodology papers) and ICML 2027.
* ICML 2027 deadline: NOT assumed. Phase 0 task: Chaitanya or Antigravity opens the official ICML 2027 CFP and records the abstract and full-paper deadlines, the anonymity rules and the dual-submission policy in `audit/venue_check.md` with the URL and retrieval date.
* Rule: never rush a broken draft into a cliff. Decision gate at Phase 5 entry: if preflight is not green and the review panel scores are below 6 for AC and Hostile, skip the ICML cycle and submit to TMLR when ready.
* TMLR compatibility: check TMLR rules on concurrent submission in `audit/venue_check.md` before submitting to both; submit to one at a time unless the policies explicitly allow otherwise.

---

## 6. Executable runbook (Phase 0 to Phase 5)

Conventions: `ROOT=/Users/chaitanya/research/mas-study/v2-upgrade`. All commands run from `$ROOT`. Scripts marked (BUILD) do not exist yet; building them is the first task of the phase and the gate checks they exist. Every gate is binary: PASS means proceed, FAIL means stop and write `audit/fail_<phase>.md`.

### Phase 0: Lock inputs, access and budget (target 23 to 27 Nov)

Commands:

```
cd /Users/chaitanya/research/mas-study/v2-upgrade
python3 -I scripts/analyze_sdt_and_subgroups.py            # regenerate SDT file, diff against committed copy
shasum -a 256 results/SDT_AND_SUBGROUPS.md results/sdt_and_subgroups.json PREREGISTRATION_V2.md MASTER_PUBLICATION_PLAN.md > LOCKED.sha256
claude -p "Reply with the single word OK" --model claude-haiku-5-5 --output-format json > audit/probe_haiku.json
claude -p "Reply with the single word OK" --model claude-sonnet-5-5 --output-format json > audit/probe_sonnet.json
agy --help > audit/agy_help.txt                            # capture real flags before writing the wrapper
scripts/agy_call.sh gemini-3.8-flash-medium "Reply OK"     # (BUILD) wrapper; repeat for gemini-4-hydrogen-medium, gpt-oss-120b-medium
```

Also: ls `exps/c4_compute exps/c5_removal exps/c6_crossvendor exps/c7_mitigation` and confirm no subject data exists yet (PREREGISTRATION_V2 says locked before any C4 to C7 calls). If data exists, stop and amend the plan.

Tasks: Chaitanya writes `budget.env` (OOP_MAX_USD, API_SCAFFOLD_CAP_USD, API_VENDOR4_CAP_USD); venue check file; power script `scripts/power.py` (BUILD) writes `audit/power.md` and fixes pool counts inside 180 to 240 and 150 to 200.

Gate G0 (all must hold): regenerated SDT file byte-identical to committed (or diff explained); probes return OK for all 5 judge ids with token usage logged; agy ids resolve to the exact strings above (a silently substituted model fails the gate); `budget.env` exists with numeric caps; `audit/venue_check.md` has official URLs; pool counts frozen.

### Phase 1: Pre-registration amendment and item bank (28 Nov to 6 Dec)

Commands:

```
python3 -I scripts/build_item_bank.py --sources matharena arxivmath third --min-per-cell 25 --seed 20261128   # (BUILD)
python3 -I scripts/solver_panel.py --solvers panel.json --attempts 4                                         # (BUILD) panel excludes all judges
python3 -I scripts/dedup.py --bank banks/locked_v2/items.json                                                # (BUILD) normalised hash
python3 -I scripts/test_parser.py                                                                            # (BUILD) garbled-answer unit tests
```

Write `PREREG_V2_AMENDMENT_1.md` containing H1 to H5, the equivalence margin, Holm families, the contamination rule and kill rules. Antigravity adversarially reviews it. Hash it before any Phase 3 call.

Gate G1: panel strata built; each source by stratum cell has at least 25 items or is declared empty; dedup finds 0 duplicates; parser tests pass 100%; amendment reviewed with no open blocker and hashed in `LOCKED.sha256`.

### Phase 2: Pools, label audit and pilot (7 to 18 Dec)

Commands:

```
python3 -I scripts/build_pools.py --exclude-judge-family per_judge --vendor-cap 0.34 --latin-square 3 --seed 20261207   # (BUILD)
python3 -I scripts/preflight.py --stage pools                                                                           # (BUILD)
python3 -I scripts/build_human_audit_html.py                                                                           # exists; regenerate for 120 items
python3 -I scripts/run_arm.py --judge all --arm all --pilot 20 --out exps/pilot                                         # (BUILD)
python3 -I scripts/preflight.py --stage pilot
```

Preflight pool checks: zero own-family candidates in each judge's pool; vendor cap met; position balance chi-square p above 0.05; chosen-vendor rate not different from uniform in the pilot; no duplicates; label-bug regex clean.

Division: Chaitanya audits 120 items blind (40 math UNSOLVED, 40 math SOLVED, 40 science negatives; 20 repeated for self-agreement). Claude Code and Antigravity label the same 120 independently first.

Gate G2: label error at most 3% (else relabel the stratum); pilot parse rate at least 0.90 for every judge and arm; pilot cost and time extrapolation within `budget.env`; Antigravity pilot review passes. Then freeze `banks/locked_v2/` and append hashes to `LOCKED.sha256`.

### Phase 3: Confirmatory data collection (19 Dec to 8 Jan)

Run order: Claude CLI judges, then agy judges (Antigravity, real terminal for sign-in), then C10 scaffolding control (paid, capped), then optional vendor 4 only if cap and budget allow.

```
python3 -I scripts/run_arm.py --judge claude-haiku-5-5 --route claude_cli --bank banks/locked_v2 --out exps/c3_main --verify-hash LOCKED.sha256   # (BUILD)
python3 -I scripts/run_arm.py --judge claude-sonnet-5-5 --route claude_cli --bank banks/locked_v2 --out exps/c3_main --verify-hash LOCKED.sha256
python3 -I scripts/run_arm.py --judge gemini-3.8-flash-medium --route agy --bank banks/locked_v2 --out exps/c6_crossvendor --verify-hash LOCKED.sha256
python3 -I scripts/run_arm.py --judge gemini-4-hydrogen-medium --route agy ... (same flags)
python3 -I scripts/run_arm.py --judge gpt-oss-120b-medium --route agy ... (same flags)
python3 -I scripts/run_arm.py --judge claude-haiku-5-5 --route raw_api --pools 70 --cap-env API_SCAFFOLD_CAP_USD --out exps/c10_scaffold   # (BUILD)
```

Runner rules: refuses to start on hash mismatch; append-only raw output with per-file sha256; logs model id returned, subject tokens and scaffold tokens per call; resumable; stops at the paid cap; retries with backoff on agy 429s.

Gate G3: every judge: parse rate at least 0.90, ISO accept(right) minus accept(wrong) at least 0.10 (calibration gate from PREREGISTRATION_V2, failing judges reported as non-interpretable, not pooled); returned model id equals requested id on at least 99% of calls; token logs complete; raw files hashed; C4 median token ratio inside 0.9 to 1.1.

### Phase 4: Independent analysis (9 to 15 Jan)

```
python3 -I scripts/analysis_a.py --data exps --out results/results_a.json      # (BUILD) Claude Code
python3 -I scripts/analysis_b.py --data exps --out results/results_b.json      # (BUILD) Antigravity, no shared helpers
python3 -I scripts/diff_results.py results/results_a.json results/results_b.json --tol-count 1e-9 --tol-ci 1e-6   # (BUILD)
python3 -I scripts/make_results_tex.py                                          # (BUILD) every paper number is a macro
```

Outputs: SDT table per judge, stratum, source; H1 to H5 verdicts; Gaussian check plot (observed vs predicted F); heterogeneity and TOST for H1; contamination-excluded replication.

Gate G4: diff reports zero differences above tolerance, or every discrepancy explained in `audit/discrepancy_log.md`; all H verdicts written by script before any prose; negative results kept.

### Phase 5: Paper, review, submission (16 Jan onward)

```
python3 -I scripts/preflight.py --stage paper      # (BUILD) dash scan, claim-to-test map, n in text equals n in table, bib, macros
cd paper && latexmk -pdf main.tex && pdftotext main.pdf main.txt && grep -c '??' main.txt    # must print 0
```

Also: citation verification script plus manual read (Zhang NeurIPS 2026 read in full; never guess URLs); rendered page PNG inspection; simulated review panel (AC, Hostile, Methods, Prior Art, Integrity, Citations).

Gate G5: preflight green; no `??`; panel AC and Hostile at least 6; Chaitanya read-through done; venue decision per Section 5. Submission is Chaitanya's action only.

### Zero-mistake preflight list (runs at every stage)

Hash match of banks, prompts, parsers, seeds; no dash violations in any .md, .tex or code comment; judge-family exclusion; vendor cap and position balance; model id returned equals requested; token ratio; duplicate problems; label-bug regex; every number a macro; every claim word ("confirmed", "reduces", "no effect") linked to a test id and stratum; bib entries all verified; paid-spend counter below cap.

### Division of labor

* Claude Code: amendment drafting, item bank and pool builders, `run_arm.py`, all claude CLI runs and the raw API control, `analysis_a.py`, `preflight.py`, `results.tex`, paper writing, PDF check.
* Antigravity: all agy runs (sign-in needs a real terminal), `analysis_b.py` and diff, independent label pass, adversarial review of the amendment, claims and bibliography, 2026 scoop check, official venue CFP verification.
* Chaitanya: fill `budget.env`, approve the amendment and any cap raise, blind label audit and disagreement rulings, sign-ins and CAPTCHAs, final read-through, submission decision. Standing rules hold: no pushes to approved PRs, no unprompted Slack messages, no deletions without approval.

---

## 7. Amendment and integrity log

* PREREGISTRATION_V2.md is not edited. New hypotheses and the lean-budget routing go in `PREREG_V2_AMENDMENT_1.md`, hashed before Phase 3.
* The Criterion-Shift Law is disclosed as post hoc on v1 data.
* Raw C4, C5 and A6c files from the 17 Nov worktree are missing; v1 numbers from those are not citable and are rerun.
* Open items: ICML 2027 deadline (unverified), TMLR concurrent submission policy (unverified), exact agy rate limits, third item source.
