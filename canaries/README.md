# Canary set

Ten copies of the draft (c01 to c10), each a directory with main.tex, results.tex and refs.bib copied from paper/, each carrying exactly one planted defect. Used to measure how well automated reviewers detect defects.

Procedure
- Five defect categories, two copies each: altered headline number, fake citation, leaked-answer claim in the Method, wrong unit of analysis, false novelty claim. Every defect is checkable against repo artifacts (exps/, harness/, analysis code, the paper's own bibliography or text, or a literature lookup).
- Categories were assigned to copies by shuffling with random.Random(77).
- Split: c01-c05 TRAIN, c06-c10 HELDOUT.
- paper/ and everything outside canaries/ was left unchanged. Nothing was committed.
- KEY.json maps each copy to split, type, location, original text, planted text and how to detect it. KEY.sha256 is the sha256 of KEY.json, so the key can be shown to be unchanged. Reviewers must not read KEY.json.
- Note: results.tex was copied from paper/ as it stood in the working tree (it had uncommitted changes).
