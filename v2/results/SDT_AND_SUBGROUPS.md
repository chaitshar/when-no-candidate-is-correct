# Track 1: SDT (d', c) and Subgroup Breakdowns on C3

Pure Python 3.9 stdlib recomputation from `exps/c3` raw replies, `banks/locked_c3/pools.json`, `results_aligned.json`, `results_a4.json`, `results_review.json`, and `own_answer_checks.csv`.
Hautus (1995) log-linear correction: `H_adj = (sum(H) + 0.5) / (n + 1)`, `F_adj = (sum(F) + 0.5) / (n + 1)`.
Bootstrap: 5,000 problem resamples (percentile 95% CI). Positive `d'` indicates signal sensitivity; negative `c` indicates liberal choosing bias (low abstention threshold).

## 1. Signal Detection Theory (Aligned Output Space: Primary)

Hit rate `H` and false-alarm rate `F` match `results_aligned.json` (EACH and ISO choose uniformly among accepted candidates on TP; `F` is any non-abstention on TA).

| Model & Stratum Set | Stratum | Arm | N | H_raw | F_raw | d' [95% CI] | c [95% CI] |
|---|---|---|---:|---:|---:|---|---|
| haiku_prereg | UNSOLVED | PICK | 78 | 0.615 | 0.590 | +0.066 [-0.336, +0.473] | -0.257 [-0.454, -0.065] |
| haiku_prereg | UNSOLVED | EACH | 77 | 0.593 | 0.455 | +0.345 [-0.032, +0.753] | -0.060 [-0.254, +0.134] |
| haiku_prereg | UNSOLVED | ISO | 78 | 0.524 | 0.321 | +0.518 [+0.091, +0.979] | +0.201 [+0.045, +0.369] |
| haiku_prereg | SOLVED | PICK | 136 | 0.993 | 0.118 | +3.465 [+2.957, +4.111] | -0.560 [-0.838, -0.356] |
| haiku_prereg | SOLVED | EACH | 136 | 0.967 | 0.074 | +3.221 [+2.787, +3.851] | -0.182 [-0.424, +0.046] |
| haiku_prereg | SOLVED | ISO | 136 | 0.919 | 0.059 | +2.917 [+2.463, +3.519] | +0.079 [-0.072, +0.266] |
| haiku_corrected | UNSOLVED | PICK | 56 | 0.536 | 0.625 | -0.225 [-0.716, +0.227] | -0.200 [-0.437, +0.023] |
| haiku_corrected | UNSOLVED | EACH | 55 | 0.509 | 0.527 | -0.045 [-0.452, +0.365] | -0.045 [-0.304, +0.206] |
| haiku_corrected | UNSOLVED | ISO | 56 | 0.440 | 0.304 | +0.357 [-0.130, +0.877] | +0.326 [+0.140, +0.536] |
| haiku_corrected | SOLVED | PICK | 143 | 0.993 | 0.126 | +3.445 [+2.953, +4.060] | -0.589 [-0.859, -0.385] |
| haiku_corrected | SOLVED | EACH | 143 | 0.967 | 0.070 | +3.255 [+2.834, +3.874] | -0.173 [-0.408, +0.050] |
| haiku_corrected | SOLVED | ISO | 143 | 0.922 | 0.056 | +2.961 [+2.514, +3.565] | +0.082 [-0.065, +0.262] |
| sonnet_prereg | UNSOLVED | PICK | 78 | 0.692 | 0.603 | +0.239 [-0.203, +0.684] | -0.376 [-0.558, -0.197] |
| sonnet_prereg | UNSOLVED | EACH | 78 | 0.671 | 0.538 | +0.341 [-0.093, +0.810] | -0.266 [-0.442, -0.108] |
| sonnet_prereg | UNSOLVED | ISO | 78 | 0.511 | 0.474 | +0.090 [-0.336, +0.535] | +0.019 [-0.122, +0.172] |
| sonnet_prereg | SOLVED | PICK | 136 | 0.978 | 0.140 | +3.021 [+2.549, +3.856] | -0.440 [-0.755, -0.275] |
| sonnet_prereg | SOLVED | EACH | 135 | 0.948 | 0.089 | +2.926 [+2.489, +3.504] | -0.134 [-0.334, +0.048] |
| sonnet_prereg | SOLVED | ISO | 134 | 0.945 | 0.082 | +2.943 [+2.491, +3.544] | -0.100 [-0.243, +0.047] |
| sonnet_corrected | UNSOLVED | PICK | 56 | 0.607 | 0.661 | -0.140 [-0.637, +0.367] | -0.337 [-0.572, -0.132] |
| sonnet_corrected | UNSOLVED | EACH | 56 | 0.589 | 0.625 | -0.091 [-0.598, +0.403] | -0.267 [-0.483, -0.066] |
| sonnet_corrected | UNSOLVED | ISO | 56 | 0.405 | 0.518 | -0.281 [-0.790, +0.198] | +0.096 [-0.085, +0.292] |
| sonnet_corrected | SOLVED | PICK | 143 | 0.986 | 0.140 | +3.181 [+2.687, +3.939] | -0.521 [-0.845, -0.335] |
| sonnet_corrected | SOLVED | EACH | 142 | 0.951 | 0.085 | +2.978 [+2.565, +3.555] | -0.132 [-0.336, +0.054] |
| sonnet_corrected | SOLVED | ISO | 141 | 0.944 | 0.085 | +2.919 [+2.477, +3.496] | -0.106 [-0.240, +0.042] |

### Paired SDT Contrasts (Aligned Output Space)

| Model & Stratum Set | Stratum | Contrast | N | delta d' [95% CI] | delta c [95% CI] |
|---|---|---|---:|---|---|
| haiku_prereg | UNSOLVED | PICK_minus_ISO | 78 | -0.453 [-0.851, -0.062] | -0.458 [-0.643, -0.288] |
| haiku_prereg | UNSOLVED | PICK_minus_EACH | 77 | -0.245 [-0.658, +0.162] | -0.200 [-0.403, +0.005] |
| haiku_prereg | UNSOLVED | EACH_minus_ISO | 77 | -0.178 [-0.591, +0.225] | -0.247 [-0.445, -0.057] |
| haiku_prereg | SOLVED | PICK_minus_ISO | 136 | +0.548 [-0.090, +1.277] | -0.639 [-0.928, -0.445] |
| haiku_prereg | SOLVED | PICK_minus_EACH | 136 | +0.244 [-0.370, +0.897] | -0.377 [-0.734, -0.057] |
| haiku_prereg | SOLVED | EACH_minus_ISO | 136 | +0.304 [-0.178, +0.825] | -0.262 [-0.524, -0.045] |
| haiku_corrected | UNSOLVED | PICK_minus_ISO | 56 | -0.582 [-1.095, -0.106] | -0.526 [-0.756, -0.315] |
| haiku_corrected | UNSOLVED | PICK_minus_EACH | 55 | -0.138 [-0.669, +0.363] | -0.159 [-0.416, +0.094] |
| haiku_corrected | UNSOLVED | EACH_minus_ISO | 55 | -0.406 [-0.954, +0.112] | -0.353 [-0.608, -0.103] |
| haiku_corrected | SOLVED | PICK_minus_ISO | 143 | +0.483 [-0.141, +1.193] | -0.671 [-0.966, -0.474] |
| haiku_corrected | SOLVED | PICK_minus_EACH | 143 | +0.190 [-0.421, +0.853] | -0.416 [-0.761, -0.104] |
| haiku_corrected | SOLVED | EACH_minus_ISO | 143 | +0.294 [-0.173, +0.794] | -0.255 [-0.515, -0.040] |
| sonnet_prereg | UNSOLVED | PICK_minus_ISO | 78 | +0.149 [-0.194, +0.523] | -0.395 [-0.599, -0.214] |
| sonnet_prereg | UNSOLVED | PICK_minus_EACH | 78 | -0.102 [-0.420, +0.195] | -0.110 [-0.263, +0.040] |
| sonnet_prereg | UNSOLVED | EACH_minus_ISO | 78 | +0.251 [-0.092, +0.596] | -0.284 [-0.459, -0.124] |
| sonnet_prereg | SOLVED | PICK_minus_ISO | 134 | +0.062 [-0.456, +0.802] | -0.342 [-0.655, -0.142] |
| sonnet_prereg | SOLVED | PICK_minus_EACH | 135 | +0.087 [-0.436, +0.771] | -0.307 [-0.639, -0.093] |
| sonnet_prereg | SOLVED | EACH_minus_ISO | 133 | +0.046 [-0.451, +0.591] | -0.069 [-0.272, +0.135] |
| sonnet_corrected | UNSOLVED | PICK_minus_ISO | 56 | +0.141 [-0.284, +0.567] | -0.433 [-0.689, -0.202] |
| sonnet_corrected | UNSOLVED | PICK_minus_EACH | 56 | -0.049 [-0.424, +0.339] | -0.070 [-0.264, +0.119] |
| sonnet_corrected | UNSOLVED | EACH_minus_ISO | 56 | +0.190 [-0.246, +0.645] | -0.364 [-0.595, -0.151] |
| sonnet_corrected | SOLVED | PICK_minus_ISO | 141 | +0.248 [-0.350, +1.025] | -0.416 [-0.726, -0.225] |
| sonnet_corrected | SOLVED | PICK_minus_EACH | 142 | +0.196 [-0.372, +0.899] | -0.389 [-0.737, -0.163] |
| sonnet_corrected | SOLVED | EACH_minus_ISO | 140 | +0.122 [-0.379, +0.660] | -0.061 [-0.262, +0.137] |

## 2. Signal Detection Theory (Strict A4 Identification Sensitivity)

In `results_a4.json`, strict identification requires EACH and ISO to accept the right candidate and reject both wrong candidates on TP.

| Model & Stratum Set | Stratum | Arm | N | hit_raw | fa_raw | d' [95% CI] | c [95% CI] |
|---|---|---|---:|---:|---:|---|---|
| haiku_prereg | UNSOLVED | PICK | 78 | 0.615 | 0.590 | +0.066 [-0.336, +0.473] | -0.257 [-0.454, -0.065] |
| haiku_prereg | UNSOLVED | EACH | 77 | 0.571 | 0.455 | +0.290 [-0.097, +0.723] | -0.032 [-0.223, +0.161] |
| haiku_prereg | UNSOLVED | ISO | 78 | 0.436 | 0.321 | +0.301 [-0.201, +0.820] | +0.310 [+0.177, +0.454] |
| haiku_prereg | SOLVED | PICK | 136 | 0.993 | 0.118 | +3.465 [+2.957, +4.111] | -0.560 [-0.838, -0.356] |
| haiku_prereg | SOLVED | EACH | 136 | 0.956 | 0.074 | +3.098 [+2.654, +3.761] | -0.121 [-0.356, +0.095] |
| haiku_prereg | SOLVED | ISO | 136 | 0.897 | 0.059 | +2.787 [+2.287, +3.431] | +0.144 [+0.024, +0.300] |
| haiku_corrected | UNSOLVED | PICK | 56 | 0.536 | 0.625 | -0.225 [-0.716, +0.227] | -0.200 [-0.437, +0.023] |
| haiku_corrected | UNSOLVED | EACH | 55 | 0.509 | 0.527 | -0.045 [-0.452, +0.365] | -0.045 [-0.304, +0.206] |
| haiku_corrected | UNSOLVED | ISO | 56 | 0.357 | 0.304 | +0.145 [-0.439, +0.746] | +0.432 [+0.277, +0.610] |
| haiku_corrected | SOLVED | PICK | 143 | 0.993 | 0.126 | +3.445 [+2.953, +4.060] | -0.589 [-0.859, -0.385] |
| haiku_corrected | SOLVED | EACH | 143 | 0.958 | 0.070 | +3.148 [+2.697, +3.806] | -0.120 [-0.353, +0.094] |
| haiku_corrected | SOLVED | ISO | 143 | 0.902 | 0.056 | +2.841 [+2.357, +3.488] | +0.143 [+0.024, +0.296] |
| sonnet_prereg | UNSOLVED | PICK | 78 | 0.692 | 0.603 | +0.239 [-0.203, +0.684] | -0.376 [-0.558, -0.197] |
| sonnet_prereg | UNSOLVED | EACH | 78 | 0.654 | 0.538 | +0.295 [-0.137, +0.772] | -0.243 [-0.418, -0.084] |
| sonnet_prereg | UNSOLVED | ISO | 78 | 0.397 | 0.474 | -0.193 [-0.684, +0.295] | +0.160 [+0.033, +0.295] |
| sonnet_prereg | SOLVED | PICK | 136 | 0.978 | 0.140 | +3.021 [+2.549, +3.856] | -0.440 [-0.755, -0.275] |
| sonnet_prereg | SOLVED | EACH | 135 | 0.941 | 0.089 | +2.863 [+2.408, +3.434] | -0.103 [-0.296, +0.074] |
| sonnet_prereg | SOLVED | ISO | 134 | 0.918 | 0.082 | +2.742 [+2.256, +3.405] | -0.000 [-0.121, +0.116] |
| sonnet_corrected | UNSOLVED | PICK | 56 | 0.607 | 0.661 | -0.140 [-0.637, +0.367] | -0.337 [-0.572, -0.132] |
| sonnet_corrected | UNSOLVED | EACH | 56 | 0.589 | 0.625 | -0.091 [-0.598, +0.403] | -0.267 [-0.483, -0.066] |
| sonnet_corrected | UNSOLVED | ISO | 56 | 0.286 | 0.518 | -0.599 [-1.230, -0.045] | +0.255 [+0.094, +0.447] |
| sonnet_corrected | SOLVED | PICK | 143 | 0.986 | 0.140 | +3.181 [+2.687, +3.939] | -0.521 [-0.845, -0.335] |
| sonnet_corrected | SOLVED | EACH | 142 | 0.944 | 0.085 | +2.916 [+2.477, +3.529] | -0.101 [-0.293, +0.073] |
| sonnet_corrected | SOLVED | ISO | 141 | 0.915 | 0.085 | +2.706 [+2.217, +3.322] | -0.000 [-0.115, +0.114] |

## 3. Non-Claude and Non-Own-Answer Subgroups (UNSOLVED TA Pools)

Note: `own_answer_checks.csv` records whether Haiku's wrong SOLVE answer appears among the 3 TA candidates (Sonnet had no SOLVE calls in C3).

### Prereg UNSOLVED TA Pools (N=90)

| Model | Subgroup | N | PICK | ISO-any | d (PICK minus ISO-any) [95% CI] |
|---|---|---:|---:|---:|---|
| haiku | All UNSOLVED TA pools | 90 | 0.600 | 0.356 | +0.244 [+0.133, +0.356] |
| haiku | 0 Claude candidates AND no own answer | 9 | 0.222 | 0.111 | +0.111 [+0.000, +0.333] |
| haiku | 0 Claude candidates | 13 | 0.462 | 0.308 | +0.154 [+0.000, +0.385] |
| haiku | >=1 Claude candidate | 77 | 0.623 | 0.364 | +0.260 [+0.130, +0.377] |
| haiku | No own answer | 44 | 0.432 | 0.273 | +0.159 [+0.000, +0.318] |
| haiku | Has own answer (reference) | 46 | 0.761 | 0.435 | +0.326 [+0.174, +0.478] |
| sonnet | All UNSOLVED TA pools | 90 | 0.633 | 0.500 | +0.133 [+0.044, +0.233] |
| sonnet | 0 Claude candidates AND no own answer | 9 | 0.222 | 0.111 | +0.111 [+0.000, +0.333] |
| sonnet | 0 Claude candidates | 13 | 0.308 | 0.231 | +0.077 [+0.000, +0.231] |
| sonnet | >=1 Claude candidate | 77 | 0.688 | 0.545 | +0.143 [+0.039, +0.260] |
| sonnet | No own answer | 44 | 0.500 | 0.386 | +0.114 [-0.023, +0.250] |
| sonnet | Has own answer (reference) | 46 | 0.761 | 0.609 | +0.152 [+0.022, +0.283] |

### Corrected UNSOLVED TA Pools (N=68)

| Model | Subgroup | N | PICK | ISO-any | d (PICK minus ISO-any) [95% CI] |
|---|---|---:|---:|---:|---|
| haiku | All UNSOLVED TA pools | 68 | 0.632 | 0.353 | +0.279 [+0.147, +0.412] |
| haiku | 0 Claude candidates AND no own answer | 2 | 0.000 | 0.000 | +0.000 [+0.000, +0.000] |
| haiku | 0 Claude candidates | 5 | 0.600 | 0.400 | +0.200 [+0.000, +0.600] |
| haiku | >=1 Claude candidate | 63 | 0.635 | 0.349 | +0.286 [+0.143, +0.429] |
| haiku | No own answer | 28 | 0.500 | 0.321 | +0.179 [-0.036, +0.393] |
| haiku | Has own answer (reference) | 40 | 0.725 | 0.375 | +0.350 [+0.200, +0.500] |
| sonnet | All UNSOLVED TA pools | 68 | 0.691 | 0.544 | +0.147 [+0.044, +0.265] |
| sonnet | 0 Claude candidates AND no own answer | 2 | 0.500 | 0.000 | +0.500 [+0.000, +1.000] |
| sonnet | 0 Claude candidates | 5 | 0.600 | 0.400 | +0.200 [+0.000, +0.600] |
| sonnet | >=1 Claude candidate | 63 | 0.698 | 0.556 | +0.143 [+0.032, +0.254] |
| sonnet | No own answer | 28 | 0.607 | 0.464 | +0.143 [+0.000, +0.321] |
| sonnet | Has own answer (reference) | 40 | 0.750 | 0.600 | +0.150 [+0.000, +0.300] |
