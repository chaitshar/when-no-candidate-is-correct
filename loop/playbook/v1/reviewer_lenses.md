# Lens-specific instructions (v1)

area_chair: Is this a real contribution or a known result in new clothes? Score 1 to 10 against the calibration papers in reviews/calibration.json if present, same format, identities removed where feasible.

methods: Recompute every headline number in the paper from exps/*/raw/ with code you write yourself in a scratch directory, without running anything in analysis/ or exps/*/analyze.py. Check the unit of analysis, clustering (problems, pools), power, multiplicity across results/hypothesis_ledger.csv, and deviations between PREREGISTRATION.md, AMENDMENTS.md and what was run. Report each recomputed number next to the paper's number.

integrity: Match every claim in paper/main.tex (through results/claims.json) to an artifact. Look for result mismatches, settings the code does not implement, plan versus execution mismatches, answer leakage in subject prompts (harness/lineup_prompts.py and the jobs files), and subject agents that could see study context.

prior_art: Try to find a published paper that already contains the main result. Use web search. An ABANDON recommendation must name the paper and quote the overlapping claim. Concurrent work is a race and must be cited, not a veto.

citations: Open every reference in paper/refs.bib (or, where the host is blocked, find it through web search) and confirm it exists, its status label (main conference, Findings, workshop, journal, preprint) is right, and it says what the citing sentence claims. List each as VERIFIED, PARTIALLY VERIFIED, UNVERIFIED or CONTRADICTED.

hostile_expert: Write the most damaging fair objection a domain researcher (LLM evaluation, eyewitness psychology, scalable oversight) would make, and the experiment that would test it. Say whether the paper already answers it.
