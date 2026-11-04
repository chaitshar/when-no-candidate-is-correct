# C2 amendments

## A1 (date -u 2026-11-03 ~23:30 UTC), before any C2 analysis was run
analyze.py now also outputs arms_TA (TA choosing rate per arm on the pairs entering H1), a descriptive used by analysis/make_figures.py. No test, gate or threshold changed.

## D1 (date -u 2026-11-03 ~23:58 UTC): one sonnet call blocked by an API safeguard
sonnet__PICK__hmmt_feb_2026_9_TA failed twice with "API Error: Sonnet 5.5's safeguards flagged this message". Classified API_ERROR (failure taxonomy class 7). The unit is missing for sonnet H1 and is reported, not imputed.

## D2 (date -u 2026-11-04 00:48 UTC), before running analyze.py
Four haiku SOLVE calls (arxivmath-0826 problems 12, 29, 34, 52) timed out at 900 s twice (failure class TIMEOUT). They are missing for the solve-rate gate only. Sensitivity reported: counting them as unsolved.

## D2 correction (date -u 2026-11-04 00:55 UTC)
The retry recovered 3 of the 4 timed-out SOLVE calls; 1 haiku SOLVE remains missing (817 of 818 haiku records). Gate sensitivity with the missing call counted as unsolved: 21/103 = 0.204, still inside the band. analysis/posthoc/solvability_split.json records this.

## D3 (date -u 2026-11-04 00:55 UTC): sonnet cost cap exceeded
The preregistration capped sonnet at 12 USD; the sonnet arm cost 29.10 USD (191 calls with long candidate solutions). The cap was not enforced by the runner. Deviation recorded; total subject spending now exceeds the user's 230 USD stop line when agent estimates are included, so no further subject calls are made.

## Outcome as preregistered (after analysis)
- haiku, union of sets (gate passed, solve 0.206): H1 equivalence NOT shown (D +0.117, 90% CI +0.039 to +0.194); directional fallback D > 0, one-sided p 0.007. H2 confirmed (+0.117, 95% CI +0.044 to +0.194, one-sided p 0.0013, Holm 0.0052).
- haiku, confirmation set (gate passed, solve 0.71): H1 D 0.00 (90% CI -0.125 to +0.125), equivalence not shown (n 24); H2 +0.125, p 0.043.
- haiku, replication set: gate FAILED (solve 0.05, below band), not interpreted; reported: H1 D +0.152, H2 +0.114.
- sonnet, confirmation set: gate FAILED (ISO parse rate 0.896 < 0.90; 10 unparseable ISO replies), not interpreted; reported descriptively.

## A2 (date -u 2026-11-04 ~01:25 UTC), AFTER data and after round-1 review: gate conflict ruling
The preregistration named the union of sets as primary but also gated "per model and set". The arXiv replication set failed its gate (haiku solve 0.05) and supplies 79 of 103 problems; the union passes (0.206) only by pooling. Ruling, made after seeing the data and prompted by three reviewers: conservative. The arXiv set is not interpretable, so the union is not either; only the 2026 contest set (24 problems) is interpreted. Under this ruling H1 is inconclusive (D 0.00, 90% CI -0.125 to +0.125) and H2 is not confirmed (+0.125, one-sided p 0.043, not significant after Holm over the four preregistered tests). The earlier "Outcome as preregistered" section above used the union reading; it is superseded by this ruling, and both are reported in the paper.

## A3 (date -u 2026-11-04 ~01:55 UTC), AFTER data, from round-3 methods review: answer-parser bug
harness/parse.py answer() used r"^\W*ANSWER\W*:?\s*(.+?)\s*$"; the \W* after ANSWER swallowed a leading "$\" of LaTeX answers, so correct answers such as "$\sqrt{17}-1$" were graded wrong. Fixed to r"^\W*ANSWER\s*:\s*(.+?)\s*$" with markdown asterisks stripped. This changes every SOLVE-based number (calibration gates, solvability splits, S9, P1 SOLVE). All analyses were re-run. Consequence for C2 under ruling A2: see the regenerated results.json; the contest set's haiku solve rate now exceeds the band's upper edge, so no held-out set passes its gate for haiku.
A3 addendum: with the fixed parser, some LaTeX answers made the sympy equivalence check hang; sym_equal (banks/build_prm_bank.py) now gives up after 5 seconds and returns False (counted as not equal). The PRM800K bank file was built earlier and is unchanged.

## Timestamp correction (written 2026-11-04T08:22:47Z)
The headers of A2 and A3 give estimated times that are wrong; the headers are left as written. Git times of first commit: A2 at 2026-11-04T01:01:08Z (commit f9cb323), A3 at 2026-11-04T01:27:45Z (commit 3875fe1). From now on all times come from date -u.
A1/A3 note on code: harness/parse.py and banks/build_prm_bank.py are shared by every experiment; banks/build_prm_bank.py now raises an error if sympy's LaTeX parser (antlr4-python3-runtime 4.11) is unavailable, instead of silently treating LaTeX answers as unequal.
