# Auto-Research Science Loop Evolution Log

Tracking execution rounds from Round 0 through Round 4 for the v2 confirmatory study.
Style rule: zero em dashes, zero en dashes, zero prose spaced hyphens, zero exclamation marks.

## Round 0: Infrastructure, Budget, Locks, and Pilot Gate

* **Date:** 2026-11-20
* **Status:** Complete (blind human label audit `pending_user`)
* **Artifacts verified and locked:**
  * `../budget.env`: locks `ROUTE_MODE=subscription_only` with all paid API caps set to `0`.
  * `runner.py`, `parsers.py`, `preflight.py`, `analysis_a.py`, `analysis_b.py`, `diff_results.py`, `figures_svg.py`, `make_results_tex.py`, `make_paper_html.py`, `LOOP_STATE.json`.
  * `../LOCKED.sha256`: locks v2 banks (`banks/locked_v2/*`), `exps/c7_mitigation/PREREG_C7.md`, `exps/c7_mitigation/C7_LOCKED.sha256`, `autoloop/parsers.py`, `PREREGISTRATION_V2.md`, and `MASTER_PUBLICATION_PLAN.md` (`11/11` verified OK).
  * Pilot parse gate passed at 100% across C5 Haiku, ResearchBench `gpt-oss-120b-medium`, and ResearchBench `gemini-3.8-flash-medium`.
  * Venue CFP and prior-art check recorded in `audit/venue_and_scoop_check.md`.

## Explicit Scope Caveats

1. **C4 and C5 inherit v1 C3 pools:** C4 (`N=68` TA / `56` TP corrected Haiku UNSOLVED) and C5 (`N=38` own-answer removal / `N=43` Wells removal) inherit the original v1 C3 candidate pools rather than fresh cross-vendor pools. To separate own-answer effects from remaining same-vendor candidates, `analysis_a.py` and `analysis_b.py` report separate `d_C5` estimates for remaining 2-candidate pools with `0` Claude candidates (`N=10` all / `N=9` corrected) vs `>=1` Claude candidate (`N=28` all / `N=24` corrected).
2. **ResearchBench tiny split (`N=30` pools per type):** C9 and C7 Science evaluate all `30` TA + `30` TP pools (`4` candidates per pool). Statistical power at `N=30` is limited, and subgroup differences should be interpreted with exact bootstrap intervals.
3. **Gemini ResearchBench TA floor and ceiling effects:** On `gemini-3.8-flash-medium` and `gemini-3.8-flash-low`, ResearchBench TA false choices moved from `0/30` (`0.000` in ISO) to `1/30` (`0.033` in PICK), while TP hit rate rose from `0.600` / `0.500` (ISO) to `1.000` (PICK). Consequently, `delta c` (`-1.188` for medium; `-1.311` for low) reflects Hautus (1995) log-linear smoothing combined with ceiling TP hits rather than a large TA false-alarm surge. Similarly, `gemini-4-hydrogen-medium` scored `0/30` TA in both PICK and ISO while moving TP from `0.500` to `1.000`, yielding `delta c = -1.071` purely from TP ceiling shift under Hautus smoothing.
4. **C6 `gpt-oss-120b-medium` SOLVED stratum size:** On the 100 balanced judge-family-free math problems, `gpt-oss-120b-medium` solved only `6` problems twice (`UNSOLVED_M = 75`, `MIXED_M = 19`, `SOLVED_M = 6`), failing the preregistered `n_solved >= 25` stratum-size gate while passing parse (`99.4%`) and ISO discrimination (`+0.395`). `SOLVED_M` (`N=6`) is reported transparently as underpowered.
5. **Blind human label audit awaits user execution:** `audit/human_audit_tool.html` is prepared and remains `pending_user`.

## Verified Findings (Dual-Script Verified: `analysis_a.py` vs `analysis_b.py`)

1. **C4 Haiku 3x Compute-Matched Control (`claude-haiku-5-5`, 372/372 calls, 100.0% parsed):**
   * On corrected UNSOLVED TA (`N=68`), `PICK_MAJ3` FA is `0.632` and `PICK_ANY3` FA is `0.809` vs `ISO_any` `0.353` (matching single-call `PICK_1X` `0.632`).
   * Median output+thinking token ratio (`PICK_3x / ISO_3x`) across `124` pools is `0.950` (`16622.0 / 17500.5`), passing the `[0.90, 1.10]` compute-matching gate.
2. **C5 Own-Answer Removal Without Replacement (`claude-haiku-5-5`, 38/38 calls, 100.0% parsed):**
   * Overall `all_38`: `FA(PICK2)=0.447`, `FA(ISO2)=0.184`, `d_C5 = +0.263 [+0.132, +0.395]` (`p < 0.0002`); `corrected_33`: `d_C5 = +0.303 [+0.152, +0.455]` (`p < 0.0002`).
   * Remaining Claude-candidate subgroup split on `all_38`: `0` Claude candidates (`N=10`): `PICK2=0.300`, `ISO2=0.100`, `d_C5 = +0.200 [0.000, +0.500]` (`p = 0.105`); `>=1` Claude candidate (`N=28`): `PICK2=0.500`, `ISO2=0.214`, `d_C5 = +0.286 [+0.143, +0.464]` (`p < 0.0002`).
3. **C5 Wells Removal Without Replacement (`claude-haiku-5-5`, 43/43 calls, 100.0% parsed):**
   * After removing the candidate chosen under C3 PICK, choosing on the remaining `2` wrong candidates stayed at `0.558 [0.419, 0.698]` (vs `0.422` proportional `2/3` baseline, `+0.137`) and `ISO2 = 0.256`, paired difference `+0.302 [+0.163, +0.442]` (`p < 0.0002`).
4. **C9 ResearchBench Science (`N=30` TA + `30` TP, 5 judge configs, 1250/1250 calls complete):**
   * `gpt-oss-120b-medium` (99.2% parsed): TA PICK `0.207` vs ISO `0.034`, TP PICK `0.933` vs ISO `0.569`, `delta c = -1.052 [-1.643, -0.668]`, `delta d' = +0.364 [-0.537, +1.322]`.
   * `gemini-3.8-flash-medium` (100.0% parsed): TA PICK `0.033` (1/30) vs ISO `0.000` (0/30), TP PICK `1.000` vs ISO `0.600`, `delta c = -1.188 [-1.490, -0.771]`, `delta d' = +1.416 [+0.701, +2.222]`.
   * `gemini-3.8-flash-low` (C8 low-thinking, 100.0% parsed): TA PICK `0.033` (1/30) vs ISO `0.000` (0/30), TP PICK `1.000` vs ISO `0.500`, `delta c = -1.311 [-1.605, -0.948]`, `delta d' = +1.661 [+0.895, +2.470]`.
   * `gemini-4-hydrogen-medium` (100.0% parsed): TA PICK `0.000` (0/30) vs ISO `0.000` (0/30), TP PICK `1.000` vs ISO `0.500`, `delta c = -1.071 [-1.279, -0.863]`, `delta d' = +2.141 [+1.725, +2.557]`.
   * `claude-haiku-5-5` (100.0% parsed): TA PICK `0.267` (8/30) vs ISO `0.000` (0/30), TP PICK `0.867` vs ISO `0.500`, `delta c = -1.299 [-1.688, -0.989]`, `delta d' = -0.484 [-1.168, +0.442]`.
5. **C6 Cross-Vendor Judge-Family-Free Math (`gpt-oss-120b-medium`, 1000/1000 complete, 99.4% parsed, zero GPT candidates):**
   * `ALL` (`N=98`): TA PICK `0.663`, EACH `0.616`, ISO `0.717`; TP PICK `0.697`, ISO `0.500`; `delta c = -0.194 [-0.358, -0.036]`, `delta d' = +0.673 [+0.268, +1.113]`.
   * `UNSOLVED_M` (`N=74`, balanced `35` contest + `39` arXivMath): TA PICK `0.716`, ISO `0.747`; TP PICK `0.653`, ISO `0.438`; `delta c = -0.244 [-0.429, -0.064]`, `delta d' = +0.649 [+0.175, +1.175]`.
   * H3 out-of-sample prediction: `F_pred = 0.760` vs observed `0.716 [0.608, 0.811]` (`in_ci95 = true`, `abs_err = 0.044`).
   * Regime dissociation: because `gpt-oss-120b-medium` is a credulous isolated verifier (`ISO_wrong = 0.395`), 3-call `ISO_any` saturates at `0.747` with low TP hit (`0.438`), yet SDT confirms the liberal criterion shift (`delta c = -0.244`) persists without same-vendor candidates.
6. **C7 Mitigation Matrix (All Arms 100% Complete):**
   * **Haiku UNSOLVED Math (`N=40` matched pools) dissociation:**
     * **M1 (`ISO -> PICK`, tiebreak `8/8` ok, `0.10` extra calls/pool):** TA FA `0.625 -> 0.175` (`-0.450`), TP hit `0.550` (vs `0.512` ISO, `0.600` PICK), `93.6%` criterion recovery, `d'` `-0.064 -> +1.027`.
     * **M2 (Falsification-First Gate, `80/80` ok):** TA FA `0.025`, but overshoots criterion (`c = +1.449`, `241.5%` recovery) and collapses TP hits to `0.125` (triggers preregistered TP-collapse kill rule on hard math).
     * **M3 (Known-Foil Lineup, `80/80` ok):** `0.000` decoy foil picks across all `80` pools (passes foil audit), yet TA FA on the 3 plausible wrong candidates remains `0.525` (`-0.100` vs PICK, `d' = +0.061`).
   * **Cross-Vendor Math M2 (`80/80` ok each):** `gpt-oss-120b-medium` M2 (`TA = 0.575`, `TP = 0.800`, `d' = +0.631`) beats both ISO (`delta d' = +1.233 [+0.713, +1.865]`, `F_diff = -0.150`) and PICK (`delta d' = +0.496`); `gemini-3.8-flash-medium` M2 (`TA = 0.200`, `TP = 0.775`, `d' = +1.549`) awaits completed Gemini C6 baselines.
   * **Science M2 (`60/60` ok across all 5 configs):** `gptoss` TA FA `0.207 -> 0.100`, TP `0.800`; `gemini` and `gemini_low` TA FA `0.033 -> 0.000`, TP `1.000` (`d' = +4.282`); `hydrogen` TA FA `0.000`, TP `0.833`; `haiku` TA FA `0.267 -> 0.000`, TP `0.433`. Science M1 Stage 1 requires `0` tie-breaker calls on `haiku`, `gemini`, `gemini_low`, and `hydrogen` (`1` call on `gptoss`).

## Gate G4 & Paper Pipeline Status

* **Dual-script verification (`analysis_a.py` vs `analysis_b.py`):** `0` deterministic mismatches (`0` `count_or_rate`, `0` `stat`, `max_abs_diff = 4.68e-09`) across all 5 completed sections (`c4_compute`, `c5_own_removal`, `c5_wells_removal`, `c9_science`, `c7_mitigation`). Parser edge-case sensitivity (`10` inline/boxed `gpt-oss` files) and discrete small-`n` bootstrap quantile steps documented in `audit/discrepancy_log.md`.
* **Paper pipeline:** Live vector SVGs (`paper/figures/fig1..fig4.svg`), `1,416` auto-generated macros (`paper/results.tex`), `paper/main.tex`, `paper/refs.bib`, and `paper/preview.html` built and verified via `preflight.py --stage paper` (`100%` PASS).
* **Remaining active run:** `C6 Math` `gemini-3.8-flash-medium` (`raw_math_gemini_solve` in progress via `run_round1_resume_agy.py`, followed by `pick`, `iso`, `each`). Upon completion, re-run `analysis_b.py`, `analysis_a.py`, `diff_results.py`, `figures_svg.py`, `make_results_tex.py`, `make_paper_html.py`, and `preflight.py --stage paper`.

## Finalisation Audit (22 Nov 2026, Claude Code)

* All runs complete, including C6 Math `gemini-3.8-flash-medium` (1,000/1,000). Locks verify (`11/11`), preflight paper stage passes. The C6 and gate numbers in the sections above predate the parser extension and the Gemini completion; `paper/results.tex` is the current source.
* Raw recount of C4, C5, C6 and C9 rates with a separate parser matches `results_a.json`.
* Paper rewritten for accuracy (`paper/main.tex`; the earlier draft is kept as `paper/main_antigravity_draft_22nov.tex`): abstract cut to arXiv length, deviations paragraph added, C6 primary test reported as unsupported, both C6 judges reported as missing the stratum gate (25, not 20), C9 reported as 10 papers with paper-clustered intervals, M1 reported as equal to ISO at about three times the calls, the favorable 40 problem C7 draw disclosed, the garbled `Final answer:` suffix disclosed, H3 computed and reported.
* New post hoc script `scripts/final_sensitivity.py` writes `results/final_sensitivity.json` and `paper/results_extra.tex`.
* Citations checked on the web: all 27 exist; author lists, venues and one misattribution (Wells 1993) corrected in `paper/refs.bib`.
* Not done: LaTeX compile (no TeX engine on this Mac), human label audit, public release of v2 materials.
