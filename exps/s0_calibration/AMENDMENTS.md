# S0 amendments

## A1, 2026-11-03 ~22:55 UTC: v1 at ceiling, calibrate generator v2
Result of the preregistered grid (results.json): haiku solved 16/16 at every level up to 26 iterations; sonnet 10/10 up to 18 and 9/10 at 26. One haiku reply reports detecting a cycle in the state (mod 97), a shortcut. v1 is declared uncalibrated (ceiling) for both models. gen/progtrace2.py (v2, committed before this calibration) removes cycles: modulus 1009, every update depends on the loop index, 4 variables, 4 statements per iteration, return a*10000+b. New grid on fresh calibration seeds 101000 to 101999: haiku iterations {10, 20, 40, 80}, 10 tasks each; sonnet {20, 40, 80}, 6 tasks each. Same choice rule. Harness now also records usage tokens per call.

## A2, 2026-11-03 ~23:05 UTC: v2 also near ceiling; calibrate counting tasks
Round 2 (results2.json): haiku 10/10, 9/10, 8/10, 9/10 at 10, 20, 40, 80 iterations; sonnet 6/6, 6/6, 5/6 at 20, 40, 80. Linear program tracing is declared at ceiling for both models (no level in [0.2, 0.8] that is affordable; 80 iterations already cost about 0.01 USD per haiku call). New task family gen/countgen.py (committed before this round): count integers in a range satisfying 2 to 4 random arithmetic conditions, ground truth by enumeration. Round 3 on calibration seeds 102000 to 102999: haiku levels (HI, k) in {(2000,2), (20000,3), (200000,3), (200000,4)}, 10 tasks each; sonnet the last three levels, 6 each. Same choice rule.

## A3 (date -u about 22:40 UTC 2026-11-03): S0 abandoned
User ruling: do not make up test data; procedurally generated tasks are retired as a data source. Round 3 had completed (results3.json: haiku 0.5 to 0.9, sonnet 0.5 to 0.83 by level). S0 is recorded in the ledger as ABANDONED and is not evidence for any claim. gen/ files are kept for the record only.
