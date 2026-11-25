# Preregistration C7: Compute-Matched Eyewitness-Lineup Mitigation Matrix (Round 2)

Generated deterministically by `autoloop/build_round2_mitigation.py` using Python 3.9 stdlib.
Locked before any Round 2 (C7) M2 or M3 subject calls are executed.

## 1. Motivation and Theoretical Anchor

Round 1 and C3 established the SDT Criterion-Shift Law: pooling candidates in `PICK` lowers the judge acceptance criterion relative to independent `ISO` verification (`delta c ~ -0.45` to `-0.53` on Haiku UNSOLVED), inflating target-absent (TA) false alarms without improving target-present (TP) discrimination. Experiment C7 evaluates three compute-matched mitigation arms against `PICK` (M0) and `ISO` baselines across scientific hypotheses and competition math.

## 2. Locked Banks and Deterministic Subsets

* **Leg 1 (Science, ResearchBench):** All 30 items (`30 TA + 30 TP = 60` pools, `4` candidates per pool) from `banks/locked_v2/c9_science_pools.json` (`researchbench_pools`).
* **Leg 2a (Judge-Family-Free Cross-Vendor Math):** Deterministic stratified subset of `40` problems (`20` contest + `20` arxivmath, both TA and TP = `80` pools, `3` candidates per pool) from `banks/locked_v2/c6_crossvendor_math.json` (seeds `20261121` and `20261122`; TP right-position counts: `{1: 14, 2: 13, 3: 13}`; zero Gemini and zero GPT candidates).
* **Leg 2b (Haiku UNSOLVED C3 Math):** Deterministic stratified subset of `40` paired corrected Haiku UNSOLVED C3 problems (both TA and TP = `80` pools, `3` candidates per pool in M2; sources: `{'arxivmath': 37, 'contest': 3}`; TP right-position counts: `{1: 13, 2: 13, 3: 14}`) from `banks/locked_v2/c4_haiku_compute.json` (seed `20261123`).

## 3. Mitigation Arms

* **M0 (Baseline Pooled `PICK`):** Single-call Round 1 `PICK` baseline on the exact matched pools.
* **M1 (Two-Stage `ISO -> PICK` Tie-Breaker):** Stage 1 reads completed `ISO` verdicts per candidate. Pools with `0` accepted candidates resolve deterministically to `NONE` (`0` extra calls). Pools with `1` accepted candidate resolve deterministically to that candidate (`0` extra calls). Pools with `k >= 2` accepted candidates invoke a single Stage 2 `PICK-k` tie-breaker restricted to the accepted subset (`jobs_*_m1_tiebreak.jsonl` generated via `--mode generate_m1`).
* **M2 (Falsification-First Criterion Recalibration Gate):** Single-call pooled prompt requiring independent per-candidate falsification (identifying concrete errors or unsupported leaps) before comparing candidates, coupled with a locked certainty threshold `tau = 4` (`CONFIDENCE >= 4` on the 1 to 5 scale; otherwise `CHOICE: NONE`). Both raw `CHOICE` and threshold-enforced `CHOICE_GATE4` (`NONE` if `CONFIDENCE < 4`) are logged.
* **M3 (Mock-Witness / Known-Foil Calibrated Lineup, Wells C-D3):** Inserts `1` deterministic known-wrong donor foil from another problem in `c4_haiku_compute.json` (verified `math_equal` false against gold and all 3 real candidate answers) into each Haiku C3 pool (`4` candidates total; Latin-balanced `foil_pos` counts `{1: 20, 2: 20, 3: 20, 4: 20}`; TP right-position counts `{1: 11, 2: 10, 3: 8, 4: 11}`). Instructs the judge to first inspect and reject flawed/decoy candidates before selecting among survivors.

## 4. Preregistered Confirmatory Hypotheses (Holm-Corrected at alpha = 0.05, 5,000 Problem Bootstraps)

* **H_C7a (TA False-Alarm Reduction vs PICK):** Paired `FA(M_arm) minus FA(PICK) < 0` on TA pools (one-sided bootstrap) for M1, M2, and M3 across Haiku C3 Math, Cross-Vendor Math, and ResearchBench Science.
* **H_C7b (Criterion Restoration Toward ISO):** Paired `c(M_arm) minus c(PICK) > 0` (shifting `c` back toward `c(ISO)`), quantifying how much of `delta c(PICK minus ISO)` is recovered by M1, M2, and M3.
* **H_C7c (TP Hit Retention vs ISO and PICK):** Non-inferiority of aligned TP hit rate `H_aligned(M_arm) minus H_aligned(ISO) >= -0.05` and net Hautus sensitivity gain `d'(M_arm) minus d'(PICK) > 0`.
* **H_C7d (M3 Foil Rejection Audit):** In M3, the judge selects `foil_pos` at rate `< 0.05` on both TA and TP pools; any foil selection is flagged as an attention/calibration failure.

## 5. Gate and Kill Rules

* **Parse Gate:** Parsed `CHOICE` rate `>= 0.90` (and parsed `CONFIDENCE` rate `>= 0.90` for M2) per model and bank.
* **Calibration / Failure Kill:** An intervention arm is flagged as ineffective if on UNSOLVED math or science it fails to reduce TA false alarms by at least `0.10` relative to `PICK` (`FA(M_arm) minus FA(PICK) > -0.10`), OR if it reduces `FA` only by collapsing `TP` hits (`H_aligned(M_arm) minus H_aligned(ISO) < -0.05` with 95% CI upper bound `< 0`), yielding no net improvement in `d'`.
* **Budget Guard:** Subscription CLI routes only (`claude_cli` and `agy`, `OOP_MAX_USD=0`).

## 6. Locked Job Files and SHA-256 Digests (`C7_LOCKED.sha256`)

| File | Jobs | SHA-256 |
|---|---:|---|
| `jobs_science_m2.jsonl` | 60 | `8cd9dd4d2527ed9ed4975d74b9d32cbb164fc7777973e907c94bc6b117598060` |
| `jobs_math_haiku_m2.jsonl` | 80 | `6188f6c4a71709c9ca9d718b887298f9f139eec193e80c8438756fb9c9623807` |
| `jobs_math_cross_m2.jsonl` | 80 | `7865ce12fcc771185191384e6647b2bdddf23781065e06533920e75bd1b63018` |
| `jobs_math_haiku_m3_foil.jsonl` | 80 | `87abdbe1e823ffb50349ab4b8b63ef20db22ee8cb342b19cdd8b7463393124c9` |

### Selected Problem IDs

* `c6_crossvendor_math` (40 problems): `apex-shortlist_14, apex-shortlist_16, apex-shortlist_18, apex-shortlist_43, apex-shortlist_8, apex_2025_10, apex_2025_5, brumo_2025_24, cmimc_2025_40, hmmt_feb_2026_18, hmmt_feb_2026_20, hmmt_feb_2026_31, hmmt_nov_2025_16, hmmt_nov_2025_22, hmmt_nov_2025_27, smt_2025_17, smt_2025_36, smt_2025_38, smt_2025_39, smt_2025_50, arxivmath-0126_20, arxivmath-0226_4, arxivmath-0326_1, arxivmath-0426_13, arxivmath-0426_15, arxivmath-0426_16, arxivmath-0426_17, arxivmath-0426_21, arxivmath-0426_23, arxivmath-0426_26, arxivmath-0426_27, arxivmath-0426_37, arxivmath-0526_12, arxivmath-0526_32, arxivmath-0526_9, arxivmath-0626_15, arxivmath-0626_48, arxivmath-0826_24, arxivmath-0826_3, arxivmath-1225_9`
* `c4_haiku_compute` (40 problems): `apex-shortlist_22, apex-shortlist_36, apex_2025_9, arxivmath-0126_17, arxivmath-0226_12, arxivmath-0226_2, arxivmath-0226_25, arxivmath-0226_31, arxivmath-0226_32, arxivmath-0326_1, arxivmath-0326_10, arxivmath-0326_15, arxivmath-0326_16, arxivmath-0326_2, arxivmath-0326_24, arxivmath-0326_3, arxivmath-0326_5, arxivmath-0326_7, arxivmath-0326_8, arxivmath-0426_15, arxivmath-0426_19, arxivmath-0426_2, arxivmath-0426_3, arxivmath-0426_37, arxivmath-0426_6, arxivmath-0526_14, arxivmath-0526_17, arxivmath-0526_18, arxivmath-0526_25, arxivmath-0526_27, arxivmath-0526_30, arxivmath-0526_32, arxivmath-0526_34, arxivmath-0626_11, arxivmath-0626_20, arxivmath-1225_10, arxivmath-1225_2, arxivmath-1225_3, arxivmath-1225_4, arxivmath-1225_5`
