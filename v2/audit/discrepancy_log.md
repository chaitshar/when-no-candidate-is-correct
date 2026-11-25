# Gate G4 Dual-Script Discrepancy Log (`analysis_a.py` vs `analysis_b.py`)

Date: 2026-11-22 (final synchronized post-completion run).
Comparator: `autoloop/diff_results.py --a results/results_a.json --b results/results_b.json --json-out results/diff_report.json`.
Lock invariant: `autoloop/parsers.py` remains untouched at its SHA-256 locked digest (`63fa55bd236fed97253634f43fc2ca3e51422f5ec77fe01ae647fc46518e70a8` in `LOCKED.sha256`).

## 1. Full-Suite Deterministic Agreement (All Modules Complete)

With all v2 experimental modules 100% complete (`incomplete=0`: C4 compute-matched, C5 own-answer and Wells removal, C6 cross-vendor math for both `gpt-oss-120b-medium` and `gemini-3.8-flash-medium` at 1,000/1,000 calls each, C9/C8 ResearchBench science across 5 judge configurations, and all C7 mitigation arms):

* **`count_or_rate` leaves checked:** `2,529` | **Mismatches:** `0` (`max_abs_diff = 0`).
* **`stat` leaves checked** (Hautus `d'`, `c`, `zH`, `zF`, `delta d'`, `delta c`, exact McNemar p-values, 3-rule clipping sensitivity): `1,453` | **Mismatches:** `0` (`max_abs_diff = 4.68e-09`, purely floating-point rounding between independent `norm_ppf` implementations).

## 2. Post-Lock Parser Addendum (`autoloop/parsers_extended.py`)

During the 120-file stratified extractor audit (`audit/extractor_audit_report.md`) and full C6 math completion check, we identified two strictly mechanical parser edge cases in the pre-lock `autoloop/parsers.py`:

1. **Symbolic algebraic equivalence on `SOLVE` grading (`14` files: `11` Gemini, `3` GPT-OSS):** Subjects produced algebraically identical multi-variable LaTeX expressions written in factored/expanded form (e.g., `(d+1)^{-1} 2^{-d} - 4^{-d}` vs `\frac{2^d - d - 1}{(d+1)4^d}`, `2st - 2s^2 + s` vs `s(2t - 2s + 1)`, or `\binom{2024}{990}` float overflow). Without symbolic multi-point evaluation, the locked numeric-only evaluator falsely graded correct solves as wrong, misclassifying `SOLVED_M` items into `UNSOLVED_M`.
2. **Inline bold tags and bare `\boxed{...}` (`10` GPT-OSS files):** `2` PICK calls (`**Choice:** CHOICE: 1`), `1` ISO call (`**Verdict:** VERDICT: ACCEPT`), and `7` SOLVE calls (`1` inline `ANSWER: 4` and `6` bare `\boxed{...}`).

**Resolution:** To preserve the SHA-256 lock on `autoloop/parsers.py` untouched (passing `preflight.py --stage paper` with zero lock errors), the mechanical fixes live in `autoloop/parsers_extended.py` (imported by `analysis_a.py`), independently matched by `analysis_b.py`'s standalone parser and symbolic evaluator. Across all 400 C6 `SOLVE` attempts (`200` Gemini + `200` GPT-OSS), independent graders A and B have `0/400` disagreements.

## 3. Expected Independent-Seed Bootstrap Jitter (`ci` tier)

* **Cause:** `analysis_a.py` (`seed=20261120`) and `analysis_b.py` (`B=5000`, separate RNG stream) intentionally draw independent bootstrap resamples. On small strata (`n=11` to `38`), a single-item discrete step at the 2.5% or 97.5% quantile equals `1/n` (`0.026` to `0.091`), exceeding `tol_ci=0.02`. Near floor/ceiling rates on ResearchBench (`n=30`, `0/30` or `30/30`), a 1-item Hautus step shifts `d'` by `Phi^-1(29.5/31) - Phi^-1(28.5/31) = 0.25345`.
* **Resolution:** Expected Monte Carlo behavior under independent seeds; all `3,982` deterministic numeric leaves (`2,529` counts/rates + `1,453` SDT and exact test statistics) agree to `<= 4.68e-09`.
