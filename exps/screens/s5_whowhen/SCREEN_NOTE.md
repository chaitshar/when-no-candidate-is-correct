# S5 screen note (exploratory): failure attribution on Who&When, claude-haiku-5-5 and claude-sonnet-5-5

Setting: all-at-once, ground-truth answer given, adaptive thinking on (CLI default), no tools. 184 failed logs. Numbers from results.json (strict) and results_norm.json (normalized names), recomputed from raw/.

| model | subset | agent acc strict | agent acc normalized | step acc exact | step within 1 |
|---|---|---|---|---|---|
| haiku | algorithm-generated (126) | 0.64 | 0.64 | 0.42 | 0.54 |
| haiku | hand-crafted (58) | 0.17 | 0.43 | 0.17 | 0.28 |
| sonnet | algorithm-generated | 0.63 | 0.63 | 0.47 | 0.57 |
| sonnet | hand-crafted | 0.36 | 0.57 | 0.24 | 0.40 |
| haiku | all | 0.49 | 0.58 | 0.34 | 0.46 |
| sonnet | all | 0.55 | 0.61 | 0.40 | 0.52 |

Baselines: always the most frequent labelled agent 0.17 overall but 0.53 on the hand-crafted subset; uniformly random step 0.10 overall.
Kill rule outcome: the claim "current models attribute failures well" (agent accuracy >= 0.8) does not hold for either model; on hand-crafted Magentic-One logs neither model beats the most-frequent-agent baseline even with normalized names. This matches the direction of the original Who&When paper (failure attribution is hard). Not surprising against the literature; scoped to these two models and this setting.
