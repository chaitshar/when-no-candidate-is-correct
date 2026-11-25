# Locked V2 Banks and Round 1 Job Manifest

Generated deterministically by `scripts/build_v2_banks.py` using Python 3.9 stdlib.

## 1. Deduplicated MathArena Universe

* Raw pool rows scanned across 4 sources: 866
* Excluded pid records (7 label audit + 5 duplicates of used): 12
* Dropped unpaired pid records (missing TA or TP): 15
* Dropped normalized text duplicates: 2
* Surviving unique paired TA+TP problems: 412 (contest: 154, arxivmath: 258)

## 2. Locked Banks Summary

| Bank file | Description | Problems | TA pools | TP pools | Total pools |
|---|---|---:|---:|---:|---:|
| `c6_crossvendor_math.json` | Balanced Gemini-free and GPT-free math (seed 20261120) | 100 | 100 | 100 | 200 |
| `c6_claude_free_math.json` | All Claude-free paired math (32 contest, 3 arxivmath) | 35 | 35 | 35 | 70 |
| `c4_haiku_compute.json` | Corrected Haiku UNSOLVED (56 paired + 12 TA only) | 68 | 68 | 56 | 124 |
| `c5_haiku_removal.json` | Own-answer removal (38) + Wells PICK removal (43) | 38 + 43 | 38 + 43 | 0 | 81 |
| `c9_science_pools.json` (ResearchBench) | Real published abstracts (10 papers x 3 slices) | 30 | 30 | 30 | 60 |
| `c9_science_pools.json` (x1c synthetic) | Synthetic calibration companion (48 subset flagged inside 72) | 72 | 72 | 72 | 144 |

## 3. Vendor Breakdown Tables

### 3.1 c6_crossvendor_math.json (zero gemini, zero gpt)

| Vendor | TA contest | TA arxivmath | TP contest | TP arxivmath | Total | Share |
|---|---:|---:|---:|---:|---:|---:|
| claude | 56 | 61 | 90 | 97 | 304 | 0.507 |
| deepseek | 63 | 35 | 46 | 21 | 165 | 0.275 |
| qwen | 4 | 29 | 2 | 17 | 52 | 0.087 |
| glm | 3 | 19 | 1 | 11 | 34 | 0.057 |
| grok | 8 | 1 | 4 | 1 | 14 | 0.023 |
| kimi | 2 | 3 | 0 | 2 | 7 | 0.012 |
| other | 14 | 2 | 7 | 1 | 24 | 0.040 |
| Total | 150 | 150 | 150 | 150 | 600 | 1.000 |

### 3.2 c6_claude_free_math.json (zero claude)

| Vendor | TA contest | TA arxivmath | TP contest | TP arxivmath | Total | Share |
|---|---:|---:|---:|---:|---:|---:|
| gemini | 13 | 2 | 7 | 1 | 23 | 0.110 |
| gpt | 8 | 1 | 7 | 3 | 19 | 0.090 |
| deepseek | 40 | 6 | 60 | 5 | 111 | 0.529 |
| glm | 7 | 0 | 9 | 0 | 16 | 0.076 |
| grok | 9 | 0 | 6 | 0 | 15 | 0.071 |
| kimi | 2 | 0 | 0 | 0 | 2 | 0.010 |
| other | 17 | 0 | 7 | 0 | 24 | 0.114 |
| Total | 96 | 9 | 96 | 9 | 210 | 1.000 |

### 3.3 c4_haiku_compute.json

| Vendor | TA contest | TA arxivmath | TP contest | TP arxivmath | Total | Share |
|---|---:|---:|---:|---:|---:|---:|
| claude | 6 | 118 | 11 | 113 | 248 | 0.667 |
| gemini | 2 | 1 | 1 | 2 | 6 | 0.016 |
| gpt | 0 | 0 | 0 | 3 | 3 | 0.008 |
| deepseek | 6 | 46 | 3 | 24 | 79 | 0.212 |
| qwen | 0 | 4 | 0 | 2 | 6 | 0.016 |
| glm | 0 | 19 | 0 | 9 | 28 | 0.075 |
| kimi | 1 | 1 | 0 | 0 | 2 | 0.005 |
| Total | 15 | 189 | 15 | 153 | 372 | 1.000 |

## 4. Target-Present Right-Answer Position Balance

| Bank / Subset | TP N | Counts [Pos 1..k] | Chi2 | p-value |
|---|---:|---|---:|---:|
| c6_crossvendor_math (all) | 100 | [33, 34, 33] | 0.020 | 0.9900 |
| c6_crossvendor_math (contest) | 50 | [17, 17, 16] | 0.040 | 0.9802 |
| c6_crossvendor_math (arxivmath) | 50 | [16, 17, 17] | 0.040 | 0.9802 |
| c6_claude_free_math (all) | 35 | [12, 12, 11] | 0.057 | 0.9718 |
| c9_science ResearchBench (k=4) | 30 | [4, 9, 7, 10] | 2.800 | 0.4235 |
| c9_science x1c synthetic (all 72, k=4) | 72 | [25, 13, 17, 17] | 4.222 | 0.2384 |
| c9_science x1c synthetic (48 subset, k=4) | 48 | [16, 11, 11, 10] | 1.833 | 0.6077 |

## 5. Round 1 Job JSONLs

| Job file (under `exps/`) | Job count | SHA-256 (first 16 hex) |
|---|---:|---|
| `c4_compute/jobs_haiku.jsonl` | 372 | `0eea540e423e2358` |
| `c5_removal/jobs_haiku_own_removal.jsonl` | 38 | `9c4c92c06d0a1e2d` |
| `c5_removal/jobs_haiku_wells.jsonl` | 43 | `9ee3758d36421ed1` |
| `c6_crossvendor/jobs_math_solve.jsonl` | 200 | `10564838bc0b7e3c` |
| `c6_crossvendor/jobs_math_iso.jsonl` | 400 | `71c5af38c83f6fef` |
| `c6_crossvendor/jobs_math_pick.jsonl` | 200 | `a0be93f1ba315a43` |
| `c6_crossvendor/jobs_math_each.jsonl` | 200 | `de86c7a07b30e17b` |
| `c6_crossvendor/jobs_science_iso.jsonl` | 130 | `adc04b7ed230b043` |
| `c6_crossvendor/jobs_science_pick.jsonl` | 60 | `353e826509084995` |
| `c6_crossvendor/jobs_science_each.jsonl` | 60 | `4eaf40d12f9cdeb5` |
