# Preregistration V2: Follow-Up Studies C4 through C7

Locked before any C4, C5, C6, or C7 subject calls are run. All V2 experiments build on the C3 locked pool bank (`when-no-candidate-is-correct-chaitshar/banks/locked_c3/pools.json`), C3 strata (`exps/c3/strata.json`), and Track 1 SDT/subgroup baseline (`v2-upgrade/results/sdt_and_subgroups.json`).

## Baseline Empirical Anchors from C3 Track 1

- **Haiku UNSOLVED (aligned SDT, Hautus 1995):** Prereg (`N=78`) `PICK` `d'=+0.066 [-0.336, +0.473]`, `c=-0.257 [-0.454, -0.065]`; `ISO` `d'=+0.518 [+0.091, +0.979]`, `c=+0.201 [+0.045, +0.369]`; paired `PICK minus ISO` `delta d'=-0.453 [-0.851, -0.062]`, `delta c=-0.458 [-0.643, -0.288]`. Corrected (`N=56`) `delta d'=-0.582 [-1.095, -0.106]`, `delta c=-0.526 [-0.756, -0.315]`.
- **Sonnet UNSOLVED (aligned SDT, Hautus 1995):** Prereg (`N=78`) `delta d'=+0.149 [-0.194, +0.523]`, `delta c=-0.395 [-0.599, -0.214]`. Corrected (`N=56`) `delta d'=+0.141 [-0.284, +0.567]`, `delta c=-0.433 [-0.689, -0.202]`.
- **Confound coverage in C3 UNSOLVED TA (`N=90` prereg / `N=68` corrected):** Only `N=9` prereg (`N=2` corrected) pools have 0 Claude candidates AND no Haiku own answer (`d=+0.111 [+0.000, +0.333]` prereg; `d=+0.000` corrected for Haiku). `N=46` prereg (`N=40` corrected) UNSOLVED TA pools contain Haiku's own wrong SOLVE answer (`d=+0.326 [+0.174, +0.478]` vs `+0.159 [+0.000, +0.318]` on `N=44` no-own pools).

---

## C4: Repeat-PICK 3x Compute-Matched Control (`exps/c4_compute/`)

### Motivation
In C3, `ISO` uses 3 independent model calls per pool (median `16,698.5` output tokens on Haiku UNSOLVED TA) whereas `PICK` uses 1 call (median `5,143.5` output tokens). C4 matches call count (`3` calls per pool) by repeating `PICK` 3 times independently and aggregating.

### Subject & Sample Size
- **Model:** `claude-haiku-5-5` (matching C3 Haiku prompt, harness, thinking mode, temperature/seed rules).
- **Items:** All C3 pre-registered `UNSOLVED` pools (`N=90` TA pools; `N=78` paired TP pools). Primary reporting uses pre-registered strata; sensitivity reporting uses corrected strata (`N=68` TA, `N=56` TP).
- **Calls:** `3` independent `PICK` calls per pool (`3 x (90 + 78) = 504` subject calls).

### Protocol & Aggregation Rules
1. Each of the 3 calls uses the exact C3 `pick(problem, cands)` prompt.
2. **Majority-of-3 (`PICK_MAJ3`):** On a given pool, let `k_1, k_2, k_3 in {0, 1, 2, 3}` (where `0` is `NONE`) be the parsed choices. If any outcome `m in {0, 1, 2, 3}` occurs at least 2 times, `PICK_MAJ3` outputs `m`. If all 3 outcomes are distinct (e.g. `1, 2, 0` or `1, 2, 3`), primary scoring sets `PICK_MAJ3 = 0` (`NONE`/abstain, requiring consensus to commit); secondary sensitivity scoring assigns uniform probability `1/3` to each of the 3 distinct choices.
3. **Any-of-3 (`PICK_ANY3`):** Mirrors `ISO-any` union aggregation. On TA, `FA = 1` if at least one of the 3 calls picks a candidate (`max(k_r > 0)`). On TP, aligned `H` chooses uniformly among the unique candidates picked across the 3 calls (`0` if all 3 output `NONE`), and strict `hit` requires all non-NONE picks to be the right candidate with at least 1 pick.

### Hypotheses & Tests (Holm family of 3 at alpha = 0.05, 5,000-resample problem bootstrap)
- **H_C4a:** `FA(PICK_MAJ3) - FA(ISO_any) > 0` on UNSOLVED TA (`N=90`), one-sided bootstrap. Tests whether the lineup penalty survives compute matching under majority consensus.
- **H_C4b:** `FA(PICK_ANY3) - FA(ISO_any) > 0` on UNSOLVED TA (`N=90`), one-sided bootstrap.
- **H_C4c:** `d'(PICK_MAJ3) - d'(ISO) < 0` on UNSOLVED TA+TP (`N=78`), one-sided bootstrap (Hautus log-linear `d'`). Also report `delta c` and single-call `PICK` vs `PICK_MAJ3` (`delta d'`, `delta c`).

### Kill Rules
- **Gate:** Parse rate across the `504` calls must be `>= 0.90`. If `< 0.90`, C4 is halted and flagged not interpretable.
- **Refutation / Mechanism Kill:** If `FA(PICK_MAJ3) <= FA(ISO_any)` with 95% CI upper bound of `FA(PICK_MAJ3) - FA(ISO_any)` below `+0.05`, the C3 lineup penalty is killed as a 1x-vs-3x compute/variance artifact rather than a structural pooling bias.
- **Cost Cap:** `15 USD` hard cap via `--max-usd`.

---

## C5: Own-Answer Removal Without Replacement (`exps/c5_removal/`)

### Motivation
In C3, Haiku chose its own wrong SOLVE answer in `23/35` (`65.7%`) of parsed UNSOLVED TA `PICK` selections when present (`N=46` pools). C5 removes own-answer candidates without replacement to measure whether the `PICK` vs `ISO` gap persists when Haiku cannot self-anchor on its own wrong solution.

### Subject & Sample Size
- **Model:** `claude-haiku-5-5` (same prompt and harness as C3).
- **Items (from `exps/c3/own_answer_checks.csv`):** Among the 46 own-answer UNSOLVED TA pools:
  - `38` pools contain exactly `1` own-answer candidate, leaving `2` non-own wrong candidates.
  - `7` pools contain `2` own-answer candidates, leaving `1` non-own wrong candidate.
  - `1` pool (`arxivmath-0526_10`) has all `3` candidates matching own answer and is also flagged `SOLVED` / `mislabelled_correct` in C3 audits; it is excluded from C5.
- **Primary Clean 2-Candidate Set (`N=38`):** All `38` single-own-answer UNSOLVED TA pools, reduced to `2` candidates (`PICK-2` and `ISO-2` reusing C3 ISO verdicts for the 2 retained candidates, or fresh `ISO-2` verification calls if blind parity is required; we run fresh `PICK-2` calls and also run `2` fresh `ISO-2` calls per pool on a 10-pool drift check, reusing C3 ISO verdicts as primary and reporting fresh ISO as drift check).
- **Secondary Augmented 2-Candidate Sensitivity (`N=45`):** Includes the `7` two-own-answer pools by removing `1` own-answer candidate (lowest position index) to preserve `k=2` pool size, while explicitly flagging the retained second own-answer candidate.

### Protocol
- Candidate order preserves relative order from C3 (`Solution 1`, `Solution 2`).
- Prompt uses `pick(problem, cands_2)` (`CHOICE: <solution number from 1 to 2> or CHOICE: NONE`).
- `ISO-2` false-alarm is `1[at least one of the 2 retained candidates is accepted in ISO]`.
- Calls: `38 + 7 = 45` `PICK-2` TA calls (plus `20` drift-check ISO calls on 10 random pools, seed 2026).

### Hypotheses & Tests (alpha = 0.05, 5,000-resample problem bootstrap)
- **H_C5a (Primary, `N=38`):** `mean(FA(PICK-2) - FA(ISO-2)) > 0`, one-sided problem bootstrap.
- **H_C5b (Effect Reduction, `N=38`):** Compare `d_C5 = FA(PICK-2) - FA(ISO-2)` against the original 3-candidate `d_C3` on the exact same `38` pools (`paired delta = d_C3 - d_C5`, two-sided 95% CI).

### Kill Rules
- **Gate:** `PICK-2` parse rate `>= 0.90` and drift-check `ISO` agreement `>= 0.85` against C3 `ISO`.
- **Mechanism Kill (Own-Answer Sole Driver):** If `H_C5a` is not confirmed (`p >= 0.05`) AND the 95% CI upper bound of `FA(PICK-2) - FA(ISO-2)` is below `+0.10`, own-answer anchoring accounts for the excess penalty on own-answer pools.
- **Cost Cap:** `5 USD` hard cap.

---

## C6: Cross-Vendor Replication & Domain Generalization (`exps/c6_crossvendor/`)

### Motivation
C3 evaluated only Anthropic models (`claude-haiku-5-5`, `claude-sonnet-5-5`) on pools where `38.9%` of candidates were Claude-generated (`77/90` UNSOLVED pools had `>=1` Claude candidate), and `84/90` UNSOLVED problems came from arXiv math sets. C6 tests non-Anthropic judges across MathArena C3 and ResearchBench X6.

### Subject Models (via `agy` / raw API, non-Anthropic)
- At least `2` distinct non-Anthropic vendor families (primary targets: `gpt-5-mini` or `gpt-4.1-mini` from OpenAI, and `gemini-2.5-flash` from Google; optional open-weight comparator `deepseek-r1` or `qwen3` if accessible within budget). Exact resolved model IDs and API endpoints are logged per call.

### Item Banks & Sample Sizes
1. **MathArena C3 Bank (`banks/locked_c3/pools.json`):**
   - All `N=227` C3 selected TA pools plus `N=214` paired TP pools (restricted to `N=205` TA / `N=199` TP after C3 duplicate and label-audit exclusions for corrected analysis).
   - **Own-Solvability Stratification:** Before running `PICK` or `ISO` for a non-Anthropic judge `M`, run `2` `SOLVE` attempts with `M` (using two independent graders plus human spot-check on disagreements) to partition items into `SOLVED_M`, `UNSOLVED_M`, and `MIXED_M`. This breaks C3's competition-vs-competence confound wherever `M` solves arXiv items or fails contest items.
2. **ResearchBench X6 (`30` pools, TA + TP):**
   - `30` locked ResearchBench X6 multi-domain scientific/research-reasoning pools (`30` TA + `30` TP, `3` candidates per pool, 0 Anthropic candidates unless naturally occurring and flagged).
   - Arms per model: `ISO` (all `3` TA wrong candidates + `1` TP right candidate, plus `2` TP wrong candidates if distinct from TA), `PICK` (TA + TP).

### Hypotheses & Tests (per model family, Holm-corrected at alpha = 0.05)
- **H_C6a (MathArena C3 `UNSOLVED_M` TA):** `FA(PICK) - FA(ISO_any) > 0`, one-sided problem bootstrap (`5,000` resamples).
- **H_C6b (Within-Family Competence Slope):** OLS `d_i = a + b * UNSOLVED_M_i + competition_FE` with HC3 standard errors (dropping singleton competitions), one-sided `p` for `b > 0`.
- **H_C6c (SDT Contrast on MathArena `UNSOLVED_M` TA+TP):** Report Hautus `delta d' = d'(PICK) - d'(ISO)` and `delta c = c(PICK) - c(ISO)` with 95% bootstrap CIs.
- **H_C6d (ResearchBench X6 `30` pools):** Descriptive and paired bootstrap of `FA(PICK) - FA(ISO_any)` on TA and `delta d'`, `delta c` on TA+TP.
- **Non-Claude Pool Subset:** Replicate `H_C6a` on pools with `0` candidates from judge `M`'s own model family.

### Kill Rules
- **Calibration Gate (per model & bank):** `ISO` parse rate `>= 0.90`, `ISO_accept(right) - ISO_accept(wrong) >= 0.10`, `ISO_accept(wrong) > 0`, and `>= 25` problems in each of `SOLVED_M` and `UNSOLVED_M` on MathArena C3. Models failing the gate are reported as non-interpretable (not pooled).
- **Vendor-Specificity Kill:** If `2` independent non-Anthropic models pass the calibration gate on MathArena C3 `UNSOLVED_M` and both show `FA(PICK) - FA(ISO_any)` with 95% CI upper bound `< +0.05` (or `delta c > -0.05`), the lineup penalty is killed as Anthropic-specific rather than a general LLM judge property.
- **Domain-Specificity Kill (X6):** If ResearchBench X6 yields `FA(PICK) - FA(ISO_any) <= 0` with 95% CI upper bound `< +0.05` across tested models despite passing the X6 gate, the effect is scoped to competition mathematics.
- **Cost Cap:** `40 USD` per non-Anthropic model across MathArena C3 + X6.

---

## C7: Mitigation Test on TA+TP Pools (`exps/c7_mitigation/`)

### Motivation
In C3, `PICK` shifted `c` liberally (`delta c = -0.458` on Haiku UNSOLVED) and reduced `d'` (`delta d' = -0.453`), while A5's base-rate instruction (`pick_base_most`) failed to shift criterion (`0.60` vs `0.59`). C7 tests structural two-stage and calibration-gate mitigations designed to cut TA false choices while preserving TP hits.

### Subject & Sample Size
- **Models:** `claude-haiku-5-5` (primary) and the strongest non-Anthropic model from C6 that shows a significant lineup penalty (secondary).
- **Items:** C3 `UNSOLVED` + `SOLVED` paired pools with both TA and TP (`N=214` preregistered: `78` UNSOLVED + `136` SOLVED; corrected sensitivity `N=199`: `56` UNSOLVED + `143` SOLVED). Primary mitigation target is `UNSOLVED` (`N=78`); `SOLVED` (`N=136`) serves as the high-competence regression check (verifying mitigation does not destroy hit rate on solvable items).

### Mitigation Arms
1. **Arm M1 (`ISO-Filter-Then-PICK`):**
   - Stage 1: Evaluate each candidate independently with `ISO` (reusing C3/C6 `ISO` verdicts for baseline parity, plus a fresh `ISO` replication on a `20`-pool check).
   - Stage 2:
     - If `0` candidates pass Stage 1 (`ACCEPT`), output `NONE` (`0`).
     - If `1` candidate passes Stage 1, select that candidate directly (deterministic, 0 extra calls).
     - If `>= 2` candidates pass Stage 1, invoke `PICK` restricted to the surviving subset (`PICK-k`, `k in {2, 3}`) so the judge resolves ties without forcing a choice when all failed `ISO`.
2. **Arm M2 (`Mock-Foil Calibration Gate`):**
   - Before judging the target pool, prepend or interleave a calibrated decoy-rejection calibration check (or structured per-candidate falsification rubric requiring explicit error-check verification and a calibrated confidence gate calibrated on held-out `S0`/`S1` items, never C3 items).
   - Exact prompt template and threshold `tau` (locked before C7 execution from `exps/c3/results_a5.json` / `S1` calibration) will be committed alongside `exps/c7_mitigation/` runner before any C7 API call.

### Hypotheses & Tests (Holm family per model on UNSOLVED, alpha = 0.05, 5,000-resample bootstrap)
- **H_C7a (FA reduction vs PICK):** `FA(M1) - FA(PICK) < 0` and `FA(M2) - FA(PICK) < 0` on UNSOLVED TA (`N=78`).
- **H_C7b (Hit retention vs ISO):** `H_aligned(M1) - H_aligned(ISO) >= 0` (and strict `hit(M1) - hit(ISO) > 0` / non-inferiority within `-0.05`) on UNSOLVED TP (`N=78`).
- **H_C7c (Net SDT Sensitivity Gain):** `d'(M1) - d'(PICK) > 0` and `d'(M2) - d'(PICK) > 0` on UNSOLVED TA+TP (`N=78`).
- **H_C7d (SOLVED Safety Check):** On SOLVED TP (`N=136`), verify `H(M1) >= H(ISO)` and `H(M1) >= 0.90` (no catastrophic abstention on solvable items).

### Kill Rules
- **Gate:** Parse rate `>= 0.90` on Stage 2 `PICK-k` and `M2` calls.
- **Mitigation Failure Kill:** An intervention (M1 or M2) is killed if on `UNSOLVED` it fails to reduce TA false choices by at least `0.10` relative to `PICK` (`FA(M) - FA(PICK) > -0.10`), OR if it reduces `FA` only by collapsing `TP` hits below `ISO` (`H(M) - H(ISO) < -0.05` with 95% CI upper bound `< 0`), yielding no net improvement in `d'` (`delta d' <= 0`).
- **Cost Cap:** `20 USD` per model (`40 USD` total).
