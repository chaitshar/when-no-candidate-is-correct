# S9 screen note (exploratory): peer-note contamination, claude-haiku-5-5
Same 60 S1 problems; control = haiku SOLVE without a note. Numbers from results.json.
- Wrong note (a real, officially wrong answer from a 2026-lineup model): accuracy 0.525 vs 0.610 control, difference -0.085 (95% CI -0.186 to 0.000, n 59); the wrong note's answer was adopted in 0.169 of problems.
- Right note: 0.672 vs 0.603, +0.069 (-0.052 to +0.190, n 58).
Kill rule (|diff| < 0.05) not met for the wrong note. Direction matches the known anchoring and sycophancy literature; not surprising.
