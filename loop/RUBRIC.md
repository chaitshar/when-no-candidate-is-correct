# Locked review rubric

The loop may not edit this file. Reviewers get the manuscript and read-only artifact paths, never the author's notes, STATE.md, or a prior round's scores.

Default to skepticism. Prior work shows automated reviewers over-credit agent papers compared with humans, and scores drop once artifacts are inspected (2605.19156). A paper you cannot fault is more likely a sign you did not look hard enough.

## Reviewer lenses (one independent agent each, fresh context)

1. Area chair: is this a real contribution, or a known result in new clothes? Score against the calibration set below.
2. Methods and statistics: recompute every headline number from `exps/*/raw/` with code you write yourself, without running `analysis/`. Check the unit of analysis, clustering, power, multiplicity across `results/hypothesis_ledger.csv`, and pre-registration deviations.
3. Integrity auditor: match every paper claim to an artifact. Look for results mismatch, settings the code does not implement, plan versus execution mismatch, answer leakage in prompts, and subject agents that saw study context.
4. Prior-art red team: try to find a published paper that already contains the main result. An ABANDON verdict must name that paper and quote the overlapping claim. Concurrent work is a race and must be cited, not a veto.
5. Citation auditor: open every reference and confirm it exists and says what the citing sentence claims.
6. Hostile field expert: write the most damaging fair objection a domain researcher would make, and the experiment that would test it.

## Verdict file

`reviews/round-N/<lens>.json`, then `reviews/FINAL/<lens>.json` for the last round:

{"verdict": "accept|minor|major|reject", "score_1_10": 0, "blockers": ["..."], "non_blocking": ["..."], "evidence": ["file:line or url"]}

A blocker is anything that makes a claim false, unsupported, unoriginal or unreproducible. Style is never a blocker.

## Calibration

Before scoring the first draft, the area chair and hostile expert blind-score at least six papers from the same subfield: three published at the target venue or a peer flagship, and three non-flagship or workshop papers. Only score real papers you fetched. Record this in `reviews/calibration.json`. Our paper clears the bar only if it scores at or above the median of the flagship papers from the same reviewers in the same format, with the identity of each paper removed where feasible.

## Convergence

Release needs two consecutive rounds with no new blockers, every FINAL verdict at accept or minor, and the calibration bar met. Otherwise the paper is released with its true status and the honest venue in FINAL_REPORT.md.

Passing this panel is not evidence that the paper would be accepted. Reports must say "passed simulated review", never "ready for" or "will clear" a venue.
