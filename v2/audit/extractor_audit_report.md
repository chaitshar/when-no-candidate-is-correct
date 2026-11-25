# MathArena Upstream Answer Extractor Audit

Date: 2026-11-22

## Root Cause Summary

1. **Origin of the extracted field:** Every candidate `answer` field in `banks/locked_c3/pools.json` and the v2 math banks is copied verbatim from the MathArena upstream Hugging Face parquet column `parsed_answer` by `banks/matharena_pools.py` (line 71).
2. **Does it feed labels and prompts, or display only?** It is **NOT** display only. It affects three upstream and harness steps:
   - **Upstream TA/TP label assignment (`r.correct`):** MathArena used its SymPy/LaTeX parser (`parsed_answer`) to grade `correct` vs `wrong`. Across all 5 math banks, **0** wrong-labeled candidates have a `\boxed{}` expression matching `gold` (after LaTeX normalization), and **0** right-labeled candidates lack `\boxed{}`.
   - **Wrong-candidate deduplication in `matharena_pools.py` (line 74):** Wrong candidates were deduplicated by string equality on `str(r.parsed_answer)`. When MathArena's parser emitted distinct strings for identical wrong answers (e.g., `12.566370614359172`, `3`, and `4` all for `4\pi` in `apex_2025_9`; Python memory addresses `<function N at 0x...>` in `arxivmath-0326_30` and `arxivmath-0426_18`; or full essay text in `arxivmath-0826_24` and `arxivmath-0826_3`), duplicate wrong answers entered the same TA pool.
   - **Judge prompt suffix (`Final answer: {cand["answer"]}`):** Both `lineup_prompts.py` and `build_round2_mitigation.py` appended `Final answer: {cand["answer"]}` below each candidate's full reasoning text, so judges saw the parsed string (including evaluated floats, stray fallback digits, SymPy `<function ...>` reprs, or duplicated essay text) at the end of affected candidates.
3. **No locked banks or labels were modified.** Only the human audit display (`scripts/build_human_audit_html.py` -> `audit/human_audit_tool.html`) was updated to show the actual `\boxed{}` answer, preserving the exact 92 items, seed 2026, blinding, and browser storage key.

## locked_c3 (v1 C3, 543 pools)

Affected pools: **68** across **38** unique problem IDs (`wrong_boxed_eq_gold = 0`).

| Pool | C3 Status | Role | Cand | Quirk | Gold | Boxed | MathArena parsed_answer |
|---|---|---|---:|---|---|---|---|
| `smt_2025_10_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{4 \pi}{3}+\sqrt{3}` | `2 \arccos\left(1 - \dfrac{3}{2\pi}\right) + \sqr` | `7.399104559200624` |
| `smt_2025_10_TA` | active | wrong | 3 | `no_boxed_fallback_parse` | `\frac{4 \pi}{3}+\sqrt{3}` | `(none)` | `2` |
| `smt_2025_10_TP` | active | wrong | 1 | `no_boxed_fallback_parse` | `\frac{4 \pi}{3}+\sqrt{3}` | `(none)` | `2` |
| `smt_2025_10_TP` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{4 \pi}{3}+\sqrt{3}` | `2 \arccos\left(1 - \dfrac{3}{2\pi}\right) + \sqr` | `7.399104559200624` |
| `smt_2025_10_TP` | active | right | 3 | `symbolic_eval_to_float` | `\frac{4 \pi}{3}+\sqrt{3}` | `\frac{4\pi}{3} + \sqrt{3}` | `5.920841012355268` |
| `smt_2025_23_TA` | active | wrong | 2 | `int_mismatch_vs_boxed` | `55` | `\angle ABC = 70°` | `70` |
| `smt_2025_23_TP` | active | right | 2 | `int_mismatch_vs_boxed` | `55` | `\angle ABC = 55°` | `55` |
| `smt_2025_23_TP` | active | wrong | 3 | `int_mismatch_vs_boxed` | `55` | `\angle ABC = 70°` | `70` |
| `smt_2025_35_TP` | active | right | 2 | `symbolic_eval_to_float` | `\frac{10 \sqrt{3}+\sqrt{6}+\sqrt{2}}{4}` | `S = \frac{5\sqrt{3}}{2} + \frac{1}{2}\sqrt{2+\sq` | `5.296052845211261` |
| `smt_2025_41_TP` | active | right | 3 | `symbolic_eval_to_float` | `\frac{\sin (6 \pi / 13)}{\sin (\pi / 13)` | `1 + 2\cos(2\pi/13) + 2\cos(4\pi/13) + 2\cos(6\pi` | `4.148114905279377` |
| `smt_2025_48_TA` | active | wrong | 1 | `no_boxed_fallback_parse` | `-14` | `(none)` | `875` |
| `smt_2025_48_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `-14` | `(none)` | `39` |
| `smt_2025_48_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `-14` | `00012` | `12` |
| `smt_2025_48_TP` | active | wrong | 1 | `no_boxed_fallback_parse` | `-14` | `(none)` | `875` |
| `smt_2025_48_TP` | active | wrong | 3 | `no_boxed_fallback_parse` | `-14` | `(none)` | `39` |
| `smt_2025_50_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `832038\sqrt{\log_{3} 2}` | `\begin{matrix} \frac{ \\ F_{ \\ 30} \\ - \\ 2 \\` | `3` |
| `smt_2025_50_TP` | active | right | 3 | `symbolic_eval_to_float` | `832038\sqrt{\log_{3} 2}` | `\frac{832038}{\sqrt{\log_2 3}}` | `660896.8252287863` |
| `smt_2025_51_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{29 \pi}{12}` | `\frac{3\pi}{2}` | `4.71238898038469` |
| `smt_2025_51_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{29 \pi}{12}` | `\frac{2\pi}{3}` | `2.0943951023931957` |
| `smt_2025_51_TP` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{29 \pi}{12}` | `\frac{3\pi}{2}` | `4.71238898038469` |
| `smt_2025_51_TP` | active | right | 3 | `symbolic_eval_to_float` | `\frac{29 \pi}{12}` | `\frac{29\pi}{12}` | `7.592182246175334` |
| `smt_2025_9_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `-1013 \ln (2026)` | `-2026 \ln 2026` | `-15425.596655422281` |
| `smt_2025_9_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `-1013 \ln (2026)` | `1013 \ln 2026` | `7712.798327711141` |
| `smt_2025_9_TP` | active | right | 1 | `symbolic_eval_to_float` | `-1013 \ln (2026)` | `\lim_{n \to \infty} d_n = -1013\ln(2026)` | `-7712.798327711141` |
| `smt_2025_9_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `-1013 \ln (2026)` | `1013 \ln 2026` | `7712.798327711141` |
| `cmimc_2025_10_TA` | active | wrong | 2 | `int_mismatch_vs_boxed` | `\frac{1}{2026}` | `\begin{matrix} \frac{ \\ 1 \\ }{ \\ 2026 \\ } \\` | `2` |
| `cmimc_2025_10_TP` | active | wrong | 2 | `int_mismatch_vs_boxed` | `\frac{1}{2026}` | `\begin{matrix} \frac{ \\ 1 \\ }{ \\ 2026 \\ } \\` | `2` |
| `cmimc_2025_13_TA` | active | wrong | 1 | `no_boxed_fallback_parse` | `\frac{2}{17}` | `(none)` | `79` |
| `cmimc_2025_13_TP` | active | wrong | 1 | `no_boxed_fallback_parse` | `\frac{2}{17}` | `(none)` | `79` |
| `cmimc_2025_17_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `\frac{1507^{2}}{360^{2}}` | `\sum_{k=1}^{225} \frac{1}{k}` | `1` |
| `cmimc_2025_17_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `\frac{1507^{2}}{360^{2}}` | `\sum_{k=1}^{225} \frac{1}{k}` | `1` |
| `cmimc_2025_29_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `\frac{11}{3}` | `...` | `535` |
| `cmimc_2025_38_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `10+\frac{40\pi}{3}` | `10 + \dfrac{15\pi}{2}` | `33.56194490192345` |
| `cmimc_2025_38_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `10+\frac{40\pi}{3}` | `10 + \dfrac{80\pi}{3}` | `93.77580409572782` |
| `cmimc_2025_38_TP` | active | wrong | 2 | `symbolic_eval_to_float` | `10+\frac{40\pi}{3}` | `10 + \dfrac{15\pi}{2}` | `33.56194490192345` |
| `cmimc_2025_38_TP` | active | right | 3 | `symbolic_eval_to_float` | `10+\frac{40\pi}{3}` | `10 + \frac{40\pi}{3}` | `51.88790204786391` |
| `cmimc_2025_40_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `2024^{4046}` | `2024^2` | `4096576` |
| `cmimc_2025_40_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `2024^{4046}` | `2024^2` | `4096576` |
| `cmimc_2025_9_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `2851` | `0001397789` | `1397789` |
| `cmimc_2025_9_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `2851` | `(none)` | `13841` |
| `cmimc_2025_9_TP` | active | wrong | 3 | `no_boxed_fallback_parse` | `2851` | `(none)` | `13841` |
| `brumo_2025_21_TA` | active | wrong | 2 | `sympy_func_repr` | `160` | `product` | `<function product at 0x7f60f8466700>` |
| `brumo_2025_21_TP` | active | wrong | 2 | `sympy_func_repr` | `160` | `product` | `<function product at 0x7f60f8466700>` |
| `brumo_2025_26_TA` | active | wrong | 1 | `no_boxed_fallback_parse` | `337` | `(none)` | `9` |
| `brumo_2025_26_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `337` | `(none)` | `5816` |
| `brumo_2025_26_TA` | active | wrong | 3 | `no_boxed_fallback_parse` | `337` | `(none)` | `727` |
| `brumo_2025_26_TP` | active | wrong | 2 | `no_boxed_fallback_parse` | `337` | `(none)` | `727` |
| `brumo_2025_26_TP` | active | wrong | 3 | `no_boxed_fallback_parse` | `337` | `(none)` | `5816` |
| `apex_2025_9_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `4\pi` | `12.566370614359172` |
| `apex_2025_9_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `3` |
| `apex_2025_9_TA` | active | wrong | 3 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `4` |
| `apex_2025_9_TP` | active | wrong | 1 | `symbolic_eval_to_float` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `4\pi` | `12.566370614359172` |
| `apex_2025_9_TP` | active | wrong | 2 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `4` |
| `apex_2025_9_TP` | active | right | 3 | `symbolic_eval_to_float` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `\dfrac{8\pi}{3}+2\sqrt{3}` | `11.841682024710536` |
| `hmmt_nov_2025_16_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `5\pi + 6\sqrt{3}` | `\frac{32\pi}{3} + \frac{141\sqrt{3}}{28} - 12\ar` | `38.2307565665267` |
| `hmmt_nov_2025_16_TP` | active | right | 2 | `symbolic_eval_to_float` | `5\pi + 6\sqrt{3}` | `6\sqrt{3} + 5\pi` | `26.10026811336223` |
| `hmmt_nov_2025_6_TA` | active | wrong | 1 | `no_boxed_fallback_parse` | `81920` | `(none)` | `7700` |
| `hmmt_nov_2025_6_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `81920` | `(none)` | `9240` |
| `hmmt_nov_2025_6_TP` | active | wrong | 2 | `no_boxed_fallback_parse` | `81920` | `(none)` | `9240` |
| `hmmt_nov_2025_6_TP` | active | wrong | 3 | `no_boxed_fallback_parse` | `81920` | `(none)` | `7700` |
| `arxivmath-0626_46_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `9` | `(none)` | `3` |
| `arxivmath-1225_1_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `\frac{r(2d-r-1)}{2}` | `\begin{cases} \frac{d(d-1)}{2} & \text{if } r \g` | `1` |
| `arxivmath-1225_11_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `n` | `\mathbb E[T] = 1+\sum_{s=0}^{\binom n2-2} \frac{` | `2` |
| `arxivmath-1225_11_TP` | active | wrong | 2 | `int_mismatch_vs_boxed` | `n` | `\mathbb E[T] = 1+\sum_{s=0}^{\binom n2-2} \frac{` | `2` |
| `arxivmath-0126_19_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `q+1` | `\begin{cases} q+1 & \text{if } q \text{ is odd o` | `4` |
| `arxivmath-0126_19_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `q+1` | `\begin{cases} q+1 & \text{if } q \text{ is odd o` | `4` |
| `arxivmath-0126_3_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `12\pi` | `6\pi` | `18.84955592153876` |
| `arxivmath-0126_3_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `12\pi` | `8\pi` | `25.132741228718345` |
| `arxivmath-0126_3_TP` | active | right | 1 | `symbolic_eval_to_float` | `12\pi` | `C = 12\pi` | `37.69911184307752` |
| `arxivmath-0126_3_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `12\pi` | `8\pi` | `25.132741228718345` |
| `arxivmath-0226_17_TP` | active | right | 1 | `symbolic_eval_to_float` | `\frac{3\pi}{8}` | `\dfrac{3\pi}{8}` | `1.1780972450961724` |
| `arxivmath-0326_29_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{\log(1/(-\log((1+e^{-1})/2)))}{\lo` | `2\,e^{-(1/2)^q} = 1 + e^{-1}` | `1.3678794411714423` |
| `arxivmath-0326_29_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `\frac{\log(1/(-\log((1+e^{-1})/2)))}{\lo` | `\text{the unique solution of } q(1-2^{-q})=1 \te` | `1` |
| `arxivmath-0326_29_TP` | active | right | 2 | `symbolic_eval_to_float` | `\frac{\log(1/(-\log((1+e^{-1})/2)))}{\lo` | `q_{2m+1} = \log_2\!\left(\frac{1}{\,\ln\!\left(\` | `1.3963634750570457` |
| `arxivmath-0326_29_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{\log(1/(-\log((1+e^{-1})/2)))}{\lo` | `2\,e^{-(1/2)^q} = 1 + e^{-1}` | `1.3678794411714423` |
| `arxivmath-0326_30_TA` | bad_label | wrong | 1 | `sympy_func_repr` | `\frac{N(N-1)}{2}` | `N` | `<function N at 0x74ba7bff1800>` |
| `arxivmath-0326_30_TA` | bad_label | wrong | 3 | `sympy_func_repr` | `\frac{N(N-1)}{2}` | `N` | `<function N at 0x72e8929ed760>` |
| `arxivmath-0326_30_TA` | bad_label | TA_pool | 0 | `duplicate_boxed_in_TA` | `\frac{N(N-1)}{2}` | `['N', '\\frac{N(N+1)}{2}', 'N']` | `dedup_leak` |
| `arxivmath-0326_30_TP` | bad_label | wrong | 1 | `sympy_func_repr` | `\frac{N(N-1)}{2}` | `N` | `<function N at 0x74ba7bff1800>` |
| `arxivmath-0326_30_TP` | bad_label | wrong | 2 | `sympy_func_repr` | `\frac{N(N-1)}{2}` | `N` | `<function N at 0x72e8929ed760>` |
| `arxivmath-0426_18_TA` | bad_label | wrong | 2 | `sympy_func_repr` | `2(N-1)` | `N` | `<function N at 0x75baa1bf58a0>` |
| `arxivmath-0426_18_TA` | bad_label | wrong | 3 | `sympy_func_repr` | `2(N-1)` | `N` | `<function N at 0x7cdffa7d5800>` |
| `arxivmath-0426_18_TA` | bad_label | TA_pool | 0 | `duplicate_boxed_in_TA` | `2(N-1)` | `['\\,Q_{LV}(B_N)=\\dfrac{3N}{2}-1=\\dfrac{3N-2}{` | `dedup_leak` |
| `arxivmath-0426_18_TP` | bad_label | wrong | 1 | `sympy_func_repr` | `2(N-1)` | `N` | `<function N at 0x75baa1bf58a0>` |
| `arxivmath-0426_19_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `3` | `q \;=\; 1 \;+\; \sum_{n=1}^{\infty} \frac{1}{2^{` | `1` |
| `arxivmath-0426_19_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `3` | `q = 1+\ln 2 \approx 1.6931` | `1.6931471805599454` |
| `arxivmath-0426_19_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `3` | `q \;=\; 1 \;+\; \sum_{n=1}^{\infty} \frac{1}{2^{` | `1` |
| `arxivmath-0426_19_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `3` | `q = 1+\ln 2 \approx 1.6931` | `1.6931471805599454` |
| `arxivmath-0426_28_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{2e-3}+2^{e-2}` | `7.058729051101471` |
| `arxivmath-0426_28_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e-2}(e+1)` | `6.117397198890658` |
| `arxivmath-0426_28_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e}-2` | `4.580885991017921` |
| `arxivmath-0426_28_TP` | active | right | 1 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `\mathrm{Skew}(2^e)=\frac{7\cdot 2^{\,2e-5}+4}{3}` | `4.491212739452411` |
| `arxivmath-0426_28_TP` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e}-2` | `4.580885991017921` |
| `arxivmath-0426_28_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{2e-3}+2^{e-2}` | `7.058729051101471` |
| `arxivmath-0426_31_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `3m + 1` | `\begin{cases} 3m+1, & \text{if } n=1,\\ 2(m+n)-2` | `1` |
| `arxivmath-0426_31_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `3m + 1` | `\begin{cases} 3m+1, & \text{if } n=1,\\ 2(m+n)-2` | `1` |
| `arxivmath-0426_6_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `0` | `\,\|\bar\nu\| = 6\,` | `6` |
| `arxivmath-0426_6_TP` | active | wrong | 2 | `int_mismatch_vs_boxed` | `0` | `\,\|\bar\nu\| = 6\,` | `6` |
| `arxivmath-0526_13_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `\sqrt[4]{\frac{1+\sqrt{5}}{2}}` | `\left( 1 + \frac{2}{\sqrt{3}} \right)^{1/4}` | `1.211565031277261` |
| `arxivmath-0526_33_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `(k-1)(k-2)` | `(none)` | `4` |
| `apex-shortlist_27_TA` | dup | wrong | 2 | `symbolic_eval_to_float` | `\frac{4}{9}` | `\dfrac{27(\ln 3 + 2\sqrt{3} - 4)}{22}` | `0.6906034273981062` |
| `apex-shortlist_27_TP` | dup | wrong | 1 | `symbolic_eval_to_float` | `\frac{4}{9}` | `\dfrac{27(\ln 3 + 2\sqrt{3} - 4)}{22}` | `0.6906034273981062` |
| `apex-shortlist_42_TA` | active | wrong | 3 | `no_boxed_fallback_parse` | `180 + 2023 \cdot \frac{180}{2025}` | `(none)` | `2` |
| `apex-shortlist_42_TP` | active | wrong | 3 | `no_boxed_fallback_parse` | `180 + 2023 \cdot \frac{180}{2025}` | `(none)` | `2` |
| `apex-shortlist_47_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `10^{225}-1` | `\text{none exist}` | `1` |
| `apex-shortlist_47_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `10^{225}-1` | `\text{None exist}` | `2025` |
| `apex-shortlist_47_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `10^{225}-1` | `\text{none exist}` | `1` |

## c6_crossvendor_math (v2 C6, 200 pools)

Affected pools: **17** across **9** unique problem IDs (`wrong_boxed_eq_gold = 0`).

| Pool | C3 Status | Role | Cand | Quirk | Gold | Boxed | MathArena parsed_answer |
|---|---|---|---:|---|---|---|---|
| `cmimc_2025_10_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `\frac{1}{2026}` | `\begin{matrix} \frac{ \\ 1 \\ }{ \\ 2026 \\ } \\` | `2` |
| `cmimc_2025_10_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `\frac{1}{2026}` | `\begin{matrix} \frac{ \\ 1 \\ }{ \\ 2026 \\ } \\` | `2` |
| `cmimc_2025_40_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `2024^{4046}` | `2024^2` | `4096576` |
| `cmimc_2025_40_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `2024^{4046}` | `2024^2` | `4096576` |
| `hmmt_nov_2025_16_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `5\pi + 6\sqrt{3}` | `\frac{32\pi}{3} + \frac{141\sqrt{3}}{28} - 12\ar` | `38.2307565665267` |
| `hmmt_nov_2025_16_TP` | active | right | 2 | `symbolic_eval_to_float` | `5\pi + 6\sqrt{3}` | `6\sqrt{3} + 5\pi` | `26.10026811336223` |
| `smt_2025_35_TP` | active | right | 1 | `symbolic_eval_to_float` | `\frac{10 \sqrt{3}+\sqrt{6}+\sqrt{2}}{4}` | `S = \frac{5\sqrt{3}}{2} + \frac{1}{2}\sqrt{2+\sq` | `5.296052845211261` |
| `smt_2025_50_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `832038\sqrt{\log_{3} 2}` | `\begin{matrix} \frac{ \\ F_{ \\ 30} \\ - \\ 2 \\` | `3` |
| `smt_2025_50_TP` | active | right | 1 | `symbolic_eval_to_float` | `832038\sqrt{\log_{3} 2}` | `\frac{832038}{\sqrt{\log_2 3}}` | `660896.8252287863` |
| `smt_2025_9_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `-1013 \ln (2026)` | `-2026 \ln 2026` | `-15425.596655422281` |
| `smt_2025_9_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `-1013 \ln (2026)` | `1013 \ln 2026` | `7712.798327711141` |
| `smt_2025_9_TP` | active | right | 2 | `symbolic_eval_to_float` | `-1013 \ln (2026)` | `\lim_{n \to \infty} d_n = -1013\ln(2026)` | `-7712.798327711141` |
| `smt_2025_9_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `-1013 \ln (2026)` | `1013 \ln 2026` | `7712.798327711141` |
| `arxivmath-0826_21_TA` | active | wrong | 1 | `full_essay_in_parsed_answer` | `\frac{1-10z+20z^2}{1-53z+245z^2-293z^3}` | `\displaystyle \sum_{n=0}^{\infty}N_nz^n=\frac{1-` | `The canonical Ramsey numbers for the Tetris-oper` |
| `arxivmath-0826_21_TA` | active | wrong | 2 | `full_essay_in_parsed_answer` | `\frac{1-10z+20z^2}{1-53z+245z^2-293z^3}` | `\dfrac{1}{1-6z}` | `Based on the structural analysis and computation` |
| `arxivmath-0826_21_TA` | active | wrong | 3 | `full_essay_in_parsed_answer` | `\frac{1-10z+20z^2}{1-53z+245z^2-293z^3}` | `\sum_{n=0}^{\infty}N_n z^n=\frac{1-9z+13z^2}{1-5` | `**Approach.** $N_n$ equals the number of equival` |
| `arxivmath-0826_21_TP` | active | wrong | 1 | `full_essay_in_parsed_answer` | `\frac{1-10z+20z^2}{1-53z+245z^2-293z^3}` | `\sum_{n=0}^{\infty}N_n z^n=\frac{1-9z+13z^2}{1-5` | `**Approach.** $N_n$ equals the number of equival` |
| `arxivmath-0826_21_TP` | active | wrong | 2 | `full_essay_in_parsed_answer` | `\frac{1-10z+20z^2}{1-53z+245z^2-293z^3}` | `\displaystyle \sum_{n=0}^{\infty}N_nz^n=\frac{1-` | `The canonical Ramsey numbers for the Tetris-oper` |
| `arxivmath-0826_21_TP` | active | right | 3 | `full_essay_in_parsed_answer` | `\frac{1-10z+20z^2}{1-53z+245z^2-293z^3}` | `\sum_{n=0}^{\infty}N_nz^n=\frac{1-10z+20z^2}{1-5` | `**Summary of the approach and result**  Working ` |
| `arxivmath-0826_24_TA` | active | wrong | 1 | `full_essay_in_parsed_answer` | `6` | `0` | `**Summary of what I did and found**  Write a par` |
| `arxivmath-0826_24_TA` | active | wrong | 2 | `full_essay_in_parsed_answer` | `6` | `0` | `I didn't find any such matrix for n ≤ 11, and th` |
| `arxivmath-0826_24_TA` | active | wrong | 3 | `full_essay_in_parsed_answer` | `6` | `0` | `After extensive investigation, I could not find ` |
| `arxivmath-0826_24_TA` | active | TA_pool | 0 | `duplicate_boxed_in_TA` | `6` | `['0', '0', '0']` | `dedup_leak` |
| `arxivmath-0826_24_TP` | active | right | 1 | `full_essay_in_parsed_answer` | `6` | `6` | `**Summary of what I found**  *Reduction.* Write ` |
| `arxivmath-0826_24_TP` | active | wrong | 2 | `full_essay_in_parsed_answer` | `6` | `0` | `**Summary of what I did and found**  Write a par` |
| `arxivmath-0826_24_TP` | active | wrong | 3 | `full_essay_in_parsed_answer` | `6` | `0` | `I didn't find any such matrix for n ≤ 11, and th` |
| `arxivmath-0826_3_TA` | active | wrong | 1 | `full_essay_in_parsed_answer` | `4\pi` | `0` | `**Answer: the supremum is 0.** This rests on a k` |
| `arxivmath-0826_3_TA` | active | wrong | 2 | `full_essay_in_parsed_answer` | `4\pi` | `0` | `## Setting up  Write $\sigma(Z(v))=\int_{Z(v)}dS` |
| `arxivmath-0826_3_TA` | active | wrong | 3 | `full_essay_in_parsed_answer` | `4\pi` | `0` | `**Setting up.** Write $f=v\|_{\partial B}$ and $g` |
| `arxivmath-0826_3_TA` | active | TA_pool | 0 | `duplicate_boxed_in_TA` | `4\pi` | `['0', '0', '0']` | `dedup_leak` |
| `arxivmath-0826_3_TP` | active | wrong | 1 | `full_essay_in_parsed_answer` | `4\pi` | `0` | `**Setting up.** Write $f=v\|_{\partial B}$ and $g` |
| `arxivmath-0826_3_TP` | active | right | 2 | `full_essay_in_parsed_answer` | `4\pi` | `4\pi` | `**Answer: \(4\pi\)** (the supremum is not attain` |
| `arxivmath-0826_3_TP` | active | wrong | 3 | `full_essay_in_parsed_answer` | `4\pi` | `0` | `## Setting up  Write $\sigma(Z(v))=\int_{Z(v)}dS` |

## c6_claude_free_math (v2 C6, 70 pools)

Affected pools: **10** across **5** unique problem IDs (`wrong_boxed_eq_gold = 0`).

| Pool | C3 Status | Role | Cand | Quirk | Gold | Boxed | MathArena parsed_answer |
|---|---|---|---:|---|---|---|---|
| `arxivmath-0426_28_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{2e-3}+2^{e-2}` | `7.058729051101471` |
| `arxivmath-0426_28_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e}-2` | `4.580885991017921` |
| `arxivmath-0426_28_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e-2}(e+1)` | `6.117397198890658` |
| `arxivmath-0426_28_TP` | active | right | 1 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `\mathrm{Skew}(2^e)=\frac{7\cdot 2^{\,2e-5}+4}{3}` | `4.491212739452411` |
| `arxivmath-0426_28_TP` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{2e-3}+2^{e-2}` | `7.058729051101471` |
| `arxivmath-0426_28_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e}-2` | `4.580885991017921` |
| `cmimc_2025_28_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{97-3\sqrt{1001}}{2}` | `\sqrt{\frac{28209-891\sqrt{1001}}{2}}` | `3.08396020974173` |
| `cmimc_2025_28_TP` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{97-3\sqrt{1001}}{2}` | `\sqrt{\frac{28209-891\sqrt{1001}}{2}}` | `3.08396020974173` |
| `hmmt_nov_2025_16_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `5\pi + 6\sqrt{3}` | `\frac{32\pi}{3} + \frac{141\sqrt{3}}{28} - 12\ar` | `38.2307565665267` |
| `hmmt_nov_2025_16_TP` | active | right | 1 | `symbolic_eval_to_float` | `5\pi + 6\sqrt{3}` | `6\sqrt{3} + 5\pi` | `26.10026811336223` |
| `hmmt_nov_2025_6_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `81920` | `(none)` | `9240` |
| `hmmt_nov_2025_6_TA` | active | wrong | 3 | `no_boxed_fallback_parse` | `81920` | `(none)` | `7700` |
| `hmmt_nov_2025_6_TP` | active | wrong | 1 | `no_boxed_fallback_parse` | `81920` | `(none)` | `7700` |
| `hmmt_nov_2025_6_TP` | active | wrong | 3 | `no_boxed_fallback_parse` | `81920` | `(none)` | `9240` |
| `smt_2025_27_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{65 \sqrt{6}-65 \sqrt{2}}{32}` | `\dfrac{\sqrt{65}(8-3\sqrt{3})}{\sqrt{30}+3\sqrt{` | `2.0406296667429062` |
| `smt_2025_27_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{65 \sqrt{6}-65 \sqrt{2}}{32}` | `\dfrac{\sqrt{65}(8-3\sqrt{3})}{\sqrt{30}+3\sqrt{` | `2.0406296667429062` |

## c4_haiku_compute (v2 C4, 124 pools)

Affected pools: **9** across **5** unique problem IDs (`wrong_boxed_eq_gold = 0`).

| Pool | C3 Status | Role | Cand | Quirk | Gold | Boxed | MathArena parsed_answer |
|---|---|---|---:|---|---|---|---|
| `apex_2025_9_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `4\pi` | `12.566370614359172` |
| `apex_2025_9_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `3` |
| `apex_2025_9_TA` | active | wrong | 3 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `4` |
| `apex_2025_9_TP` | active | wrong | 1 | `symbolic_eval_to_float` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `4\pi` | `12.566370614359172` |
| `apex_2025_9_TP` | active | wrong | 2 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `4` |
| `apex_2025_9_TP` | active | right | 3 | `symbolic_eval_to_float` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `\dfrac{8\pi}{3}+2\sqrt{3}` | `11.841682024710536` |
| `arxivmath-0426_19_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `3` | `q \;=\; 1 \;+\; \sum_{n=1}^{\infty} \frac{1}{2^{` | `1` |
| `arxivmath-0426_19_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `3` | `q = 1+\ln 2 \approx 1.6931` | `1.6931471805599454` |
| `arxivmath-0426_19_TP` | active | wrong | 1 | `int_mismatch_vs_boxed` | `3` | `q \;=\; 1 \;+\; \sum_{n=1}^{\infty} \frac{1}{2^{` | `1` |
| `arxivmath-0426_19_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `3` | `q = 1+\ln 2 \approx 1.6931` | `1.6931471805599454` |
| `arxivmath-0426_28_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{2e-3}+2^{e-2}` | `7.058729051101471` |
| `arxivmath-0426_28_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e-2}(e+1)` | `6.117397198890658` |
| `arxivmath-0426_28_TA` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e}-2` | `4.580885991017921` |
| `arxivmath-0426_28_TP` | active | right | 1 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `\mathrm{Skew}(2^e)=\frac{7\cdot 2^{\,2e-5}+4}{3}` | `4.491212739452411` |
| `arxivmath-0426_28_TP` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e}-2` | `4.580885991017921` |
| `arxivmath-0426_28_TP` | active | wrong | 3 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{2e-3}+2^{e-2}` | `7.058729051101471` |
| `arxivmath-0426_6_TA` | active | wrong | 3 | `int_mismatch_vs_boxed` | `0` | `\,\|\bar\nu\| = 6\,` | `6` |
| `arxivmath-0426_6_TP` | active | wrong | 2 | `int_mismatch_vs_boxed` | `0` | `\,\|\bar\nu\| = 6\,` | `6` |
| `arxivmath-0626_46_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `9` | `(none)` | `3` |

## c5_haiku_removal (v2 C5, 81 pools)

Affected pools: **6** across **6** unique problem IDs (`wrong_boxed_eq_gold = 0`).

| Pool | C3 Status | Role | Cand | Quirk | Gold | Boxed | MathArena parsed_answer |
|---|---|---|---:|---|---|---|---|
| `apex_2025_9_TA` | active | wrong | 1 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `3` |
| `apex_2025_9_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `4` |
| `arxivmath-0326_29_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{\log(1/(-\log((1+e^{-1})/2)))}{\lo` | `2\,e^{-(1/2)^q} = 1 + e^{-1}` | `1.3678794411714423` |
| `arxivmath-0326_29_TA` | active | wrong | 2 | `int_mismatch_vs_boxed` | `\frac{\log(1/(-\log((1+e^{-1})/2)))}{\lo` | `\text{the unique solution of } q(1-2^{-q})=1 \te` | `1` |
| `arxivmath-0326_30_TA` | bad_label | wrong | 1 | `sympy_func_repr` | `\frac{N(N-1)}{2}` | `N` | `<function N at 0x74ba7bff1800>` |
| `arxivmath-0326_30_TA` | bad_label | wrong | 2 | `sympy_func_repr` | `\frac{N(N-1)}{2}` | `N` | `<function N at 0x72e8929ed760>` |
| `arxivmath-0326_30_TA` | bad_label | TA_pool | 0 | `duplicate_boxed_in_TA` | `\frac{N(N-1)}{2}` | `['N', 'N']` | `dedup_leak` |
| `arxivmath-0426_19_TA` | active | wrong | 1 | `int_mismatch_vs_boxed` | `3` | `q \;=\; 1 \;+\; \sum_{n=1}^{\infty} \frac{1}{2^{` | `1` |
| `arxivmath-0426_19_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `3` | `q = 1+\ln 2 \approx 1.6931` | `1.6931471805599454` |
| `arxivmath-0426_28_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e-2}(e+1)` | `6.117397198890658` |
| `arxivmath-0426_28_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e}-2` | `4.580885991017921` |
| `arxivmath-0626_46_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `9` | `(none)` | `3` |
| `apex_2025_9_TA` | active | wrong | 1 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `3` |
| `apex_2025_9_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `2 \sqrt{3}+\frac{8 \pi}{3}` | `(none)` | `4` |
| `arxivmath-0426_28_TA` | active | wrong | 1 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{2e-3}+2^{e-2}` | `7.058729051101471` |
| `arxivmath-0426_28_TA` | active | wrong | 2 | `symbolic_eval_to_float` | `\frac{7 \cdot 4^{e-2} + 8}{6}` | `2^{e-2}(e+1)` | `6.117397198890658` |
| `arxivmath-0626_46_TA` | active | wrong | 2 | `no_boxed_fallback_parse` | `9` | `(none)` | `3` |

