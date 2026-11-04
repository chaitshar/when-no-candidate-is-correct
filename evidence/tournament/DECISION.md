# Tournament decision, 2026-11-03 21:35 UTC

34 hypotheses from four independent generators (contradictions K1 to K9, untested assumptions U1 to U7, cross-science transfers T1 to T9, corpus failures F1 to F9). Three independent kill panels (prior art, internal validity, feasibility) each judged all 34 without seeing the others. Files: gen_*.json, panel_*.json.

## Kept for pilots
- B1 (lineup on real math, factorial). Merges K1, F1, F2, F5, F6, T1, T2, T9. Every panel kept F1; K1 kept by two and merged into F1 by the third; F5 and T1 kept by two. Arms ISO, SIM-PICK, SIM-EACH, SEQ (true multi-turn), SIM-PICK with base rate, SOLVE. One call per judgement, so F6 (batched judges) is removed by design. Items: PRM800K human-labelled wrong GPT-4 solutions to MATH, so wrongness is checked against MATH ground truth and a human step label (user rule 1).
- B2 (tournament on all-wrong pools, U1 with U2 and K7). Kept by all three panels. Sibling branch, same bank.
- B3 (debate on target-absent pools, U3 and F9, the B-D5 line). Split panel: prior-art lens kills U3 on Elasky and Nakasako (LessWrong 2026, both-wrong regime); validity lens keeps it; feasibility keeps U3 as alternate. Kept alive as an alternative, not piloted first.

## Killed (with the named reason, see panel files)
U4 (2605.29800 and a NeurIPS 2026 paper on correlated judges), K2 (2407.04622, 2605.27483), K4 (ICLR 2027 submission A8fKFiZMnu), K5 (2410.21819 and a NeurIPS 2026 paper), K8 (2602.01120), K9 (2509.14034), plus validity or power kills: K3, K6, K7, U5, U7, F4, F7, F8, T4, T6, T7, T8. Prior-art kills rest on search snippets only, since scholarly hosts are blocked here.

## Parked (kept, not piloted): T3 and T5 (prevalence criterion shift and serial dependence), U6, F3, F9.

## Out of scope for this run
Generic benchmarks; new frameworks; surveys or position pieces; anything with an LLM as sole ground truth; persona or identity effects (K4, K6); confidence sharing in debate (K9); compute scaling laws (K8); prompt searches without an out-of-sample test; GPU training.
