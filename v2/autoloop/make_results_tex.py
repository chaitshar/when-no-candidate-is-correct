#!/usr/bin/env python3
"""Generate LaTeX result macros (paper/results.tex) deterministically from verified JSONs.

Pure Python 3.9 stdlib only. Zero em dashes, zero en dashes, zero prose spaced hyphens.
Every empirical number cited in paper/main.tex is read via \\res{<key>}.
"""
import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path("/Users/chaitanya/research/mas-study/v2-upgrade")


def fmt_dec(val: Optional[float], places: int = 3, signed: bool = False) -> str:
    if val is None:
        return "NA"
    if abs(val) < 0.5 * (10 ** (-places)):
        return f"{0.0:.{places}f}"
    if signed:
        return f"{val:+.{places}f}"
    return f"{val:.{places}f}"


def fmt_pct(val: Optional[float], places: int = 1) -> str:
    if val is None:
        return "NA"
    return f"{100.0 * val:.{places}f}\\%"


def fmt_ci(ci: Optional[List[float]], places: int = 3, signed: bool = False) -> str:
    if not isinstance(ci, list) or len(ci) != 2 or ci[0] is None or ci[1] is None:
        return "[NA, NA]"
    lo = fmt_dec(float(ci[0]), places=places, signed=signed)
    hi = fmt_dec(float(ci[1]), places=places, signed=signed)
    return f"[{lo}, {hi}]"


def fmt_int(val: Optional[int]) -> str:
    if val is None:
        return "NA"
    return f"{int(val)}"


def fmt_p(val: Optional[float]) -> str:
    if val is None:
        return "NA"
    if val < 0.0002:
        return "$<0.0002$"
    if val < 0.001:
        return f"{val:.4f}"
    return f"{val:.3f}"


def add_sdt_arm(macros: Dict[str, str], prefix: str, arm_dict: Dict[str, Any]) -> None:
    macros[f"{prefix}_n"] = fmt_int(arm_dict.get("n"))
    macros[f"{prefix}_h"] = fmt_dec(arm_dict.get("H_raw"), 3)
    macros[f"{prefix}_f"] = fmt_dec(arm_dict.get("F_raw"), 3)
    macros[f"{prefix}_h_ci"] = fmt_ci(arm_dict.get("H_raw_ci95"), 3)
    macros[f"{prefix}_f_ci"] = fmt_ci(arm_dict.get("F_raw_ci95"), 3)
    macros[f"{prefix}_dp"] = fmt_dec(arm_dict.get("d_prime"), 3, signed=True)
    macros[f"{prefix}_dp_ci"] = fmt_ci(arm_dict.get("d_prime_ci95"), 3, signed=True)
    macros[f"{prefix}_c"] = fmt_dec(arm_dict.get("c"), 3, signed=True)
    macros[f"{prefix}_c_ci"] = fmt_ci(arm_dict.get("c_ci95"), 3, signed=True)


def add_sdt_diff(macros: Dict[str, str], prefix: str, diff_dict: Dict[str, Any]) -> None:
    macros[f"{prefix}_n"] = fmt_int(diff_dict.get("n"))
    macros[f"{prefix}_ddp"] = fmt_dec(diff_dict.get("d_prime_diff"), 3, signed=True)
    macros[f"{prefix}_ddp_ci"] = fmt_ci(diff_dict.get("d_prime_diff_ci95"), 3, signed=True)
    macros[f"{prefix}_dc"] = fmt_dec(diff_dict.get("c_diff"), 3, signed=True)
    macros[f"{prefix}_dc_ci"] = fmt_ci(diff_dict.get("c_diff_ci95"), 3, signed=True)
    macros[f"{prefix}_dh"] = fmt_dec(diff_dict.get("H_diff"), 3, signed=True)
    macros[f"{prefix}_dh_ci"] = fmt_ci(diff_dict.get("H_diff_ci95"), 3, signed=True)
    macros[f"{prefix}_df"] = fmt_dec(diff_dict.get("F_diff"), 3, signed=True)
    macros[f"{prefix}_df_ci"] = fmt_ci(diff_dict.get("F_diff_ci95"), 3, signed=True)
    if "c_diff_p_one_sided_lt0" in diff_dict:
        macros[f"{prefix}_dc_plt"] = fmt_p(diff_dict.get("c_diff_p_one_sided_lt0"))
    if "c_diff_p_one_sided_gt0" in diff_dict:
        macros[f"{prefix}_dc_pgt"] = fmt_p(diff_dict.get("c_diff_p_one_sided_gt0"))
    if "F_diff_p_one_sided_lt0" in diff_dict:
        macros[f"{prefix}_df_plt"] = fmt_p(diff_dict.get("F_diff_p_one_sided_lt0"))


def build_macros(sdt_data: Dict[str, Any], v2_data: Dict[str, Any]) -> Dict[str, str]:
    macros: Dict[str, str] = {}
    macros["lvl95"] = "95\\%"

    # ------------------------------------------------------------------
    # 1. Track 1 C3 SDT & Subgroup Anchors (v1 exploratory law base)
    # ------------------------------------------------------------------
    sdt_al = sdt_data.get("sdt_aligned", {})
    for jkey, jtag in (
        ("haiku_prereg", "c3hp"),
        ("haiku_corrected", "c3hc"),
        ("sonnet_prereg", "c3sp"),
        ("sonnet_corrected", "c3sc"),
    ):
        jblk = sdt_al.get(jkey, {})
        for sname, stag in (("UNSOLVED", "u"), ("SOLVED", "s")):
            sblk = jblk.get(sname, {})
            for arm, atag in (("PICK", "pick"), ("EACH", "each"), ("ISO", "iso")):
                if isinstance(sblk.get(arm), dict):
                    add_sdt_arm(macros, f"{jtag}_{stag}_{atag}", sblk[arm])
            diffs = sblk.get("diffs", {})
            if isinstance(diffs.get("PICK_minus_ISO"), dict):
                add_sdt_diff(macros, f"{jtag}_{stag}_pi", diffs["PICK_minus_ISO"])
            if isinstance(diffs.get("PICK_minus_EACH"), dict):
                add_sdt_diff(macros, f"{jtag}_{stag}_pe", diffs["PICK_minus_EACH"])
            if isinstance(diffs.get("EACH_minus_ISO"), dict):
                add_sdt_diff(macros, f"{jtag}_{stag}_ei", diffs["EACH_minus_ISO"])

    # ------------------------------------------------------------------
    # 2. Experiment C4: 3x Compute-Matched Control (claude-haiku-5-5)
    # ------------------------------------------------------------------
    c4 = v2_data.get("c4_compute", {})
    macros["c4_calls_ok"] = fmt_int(c4.get("n_ok"))
    macros["c4_calls_exp"] = fmt_int(c4.get("n_expected_calls"))
    macros["c4_parse_pct"] = fmt_pct(c4.get("parse_rate_calls"), 1)
    macros["c4_n_ta"] = fmt_int(c4.get("n_ta_analyzed"))
    macros["c4_n_tp"] = fmt_int(c4.get("n_tp_paired_analyzed"))

    for key, tag in (
        ("PICK_MAJ3", "maj3"),
        ("PICK_MAJ3_TIEUNIF", "maj3u"),
        ("PICK_ANY3", "any3"),
        ("ISO_any", "iso"),
        ("PICK_1X", "pick1x"),
    ):
        r = (c4.get("ta_rates") or {}).get(key, {})
        macros[f"c4_ta_{tag}"] = fmt_dec(r.get("mean"), 3)
        macros[f"c4_ta_{tag}_ci"] = fmt_ci(r.get("ci95"), 3)

    for key, tag in (
        ("PICK_MAJ3_minus_ISO_any", "maj3_iso"),
        ("PICK_ANY3_minus_ISO_any", "any3_iso"),
        ("PICK_MAJ3_minus_PICK_1X", "maj3_p1x"),
    ):
        r = (c4.get("ta_contrasts") or {}).get(key, {})
        macros[f"c4_d_{tag}"] = fmt_dec(r.get("mean"), 3, signed=True)
        macros[f"c4_d_{tag}_ci"] = fmt_ci(r.get("ci95"), 3, signed=True)
        macros[f"c4_d_{tag}_p"] = fmt_p(r.get("p_one_sided_gt0"))

    for key, tag in (("PICK_MAJ3", "maj3"), ("PICK_ANY3", "any3"), ("ISO", "iso"), ("PICK_1X", "pick1x")):
        s = (c4.get("sdt_aligned") or {}).get(key, {})
        if isinstance(s, dict) and s:
            add_sdt_arm(macros, f"c4_sdt_{tag}", s)

    for key, tag in (("PICK_MAJ3_minus_ISO", "maj3_iso"), ("PICK_ANY3_minus_ISO", "any3_iso")):
        s = (c4.get("sdt_diffs") or {}).get(key, {})
        if isinstance(s, dict) and s:
            add_sdt_diff(macros, f"c4_sdtd_{tag}", s)

    tr = c4.get("token_ratio") or {}
    tr_all = tr.get("all") if isinstance(tr.get("all"), dict) else tr
    tr_ta = tr.get("ta") if isinstance(tr.get("ta"), dict) else {}
    macros["c4_tok_ratio"] = fmt_dec(tr_all.get("median_ratio", tr.get("median_ratio_pick3x_over_iso3x")), 3)
    macros["c4_tok_pick"] = fmt_dec(tr_all.get("pick_3x_median_tokens", tr.get("median_pick3x_tokens")), 1)
    macros["c4_tok_iso"] = fmt_dec(tr_all.get("iso_3x_median_tokens", tr.get("median_iso3x_tokens")), 1)
    macros["c4_tok_n"] = fmt_int(tr_all.get("n_pools", tr.get("n_pools_with_tokens")))
    macros["c4_tok_ratio_ta"] = fmt_dec(tr_ta.get("median_ratio"), 3)

    # ------------------------------------------------------------------
    # 3. Experiment C5: Own-Answer Removal & Wells Removal
    # ------------------------------------------------------------------
    c5o = v2_data.get("c5_own_removal", {})
    macros["c5o_ok"] = fmt_int(c5o.get("n_ok"))
    macros["c5o_exp"] = fmt_int(c5o.get("n_expected"))
    macros["c5o_parse_pct"] = fmt_pct(c5o.get("parse_rate"), 1)

    for skey, stag in (("all_38", "all"), ("corrected_33", "corr")):
        sub = (c5o.get("subsets") or {}).get(skey, {})
        macros[f"c5o_{stag}_n"] = fmt_int(sub.get("n_analyzed"))
        macros[f"c5o_{stag}_pick2"] = fmt_dec(sub.get("fa_pick2"), 3)
        macros[f"c5o_{stag}_pick2_ci"] = fmt_ci(sub.get("fa_pick2_ci95"), 3)
        macros[f"c5o_{stag}_iso2"] = fmt_dec(sub.get("fa_iso2"), 3)
        macros[f"c5o_{stag}_iso2_ci"] = fmt_ci(sub.get("fa_iso2_ci95"), 3)
        macros[f"c5o_{stag}_dc5"] = fmt_dec(sub.get("d_c5"), 3, signed=True)
        macros[f"c5o_{stag}_dc5_ci"] = fmt_ci(sub.get("d_c5_ci95"), 3, signed=True)
        macros[f"c5o_{stag}_dc5_p"] = fmt_p(sub.get("d_c5_p_one_sided"))
        macros[f"c5o_{stag}_dc3"] = fmt_dec(sub.get("d_c3"), 3, signed=True)
        macros[f"c5o_{stag}_red"] = fmt_dec(sub.get("effect_reduction_d_c3_minus_d_c5"), 3, signed=True)
        macros[f"c5o_{stag}_red_ci"] = fmt_ci(sub.get("effect_reduction_ci95"), 3, signed=True)

        cc = sub.get("claude_candidate_subgroups") or {}
        for gkey, gtag in (("zero_claude", "cl0"), ("ge1_claude", "cl1")):
            g = cc.get(gkey, {})
            macros[f"c5o_{stag}_{gtag}_n"] = fmt_int(g.get("n_analyzed", g.get("n")))
            macros[f"c5o_{stag}_{gtag}_pick2"] = fmt_dec(g.get("fa_pick2"), 3)
            macros[f"c5o_{stag}_{gtag}_iso2"] = fmt_dec(g.get("fa_iso2"), 3)
            macros[f"c5o_{stag}_{gtag}_dc5"] = fmt_dec(g.get("d_c5"), 3, signed=True)
            macros[f"c5o_{stag}_{gtag}_dc5_ci"] = fmt_ci(g.get("d_c5_ci95"), 3, signed=True)
            macros[f"c5o_{stag}_{gtag}_dc5_p"] = fmt_p(g.get("d_c5_p_one_sided"))

    c5w = v2_data.get("c5_wells_removal", {})
    macros["c5w_n"] = fmt_int(c5w.get("n_analyzed"))
    macros["c5w_ok"] = fmt_int(c5w.get("n_ok"))
    macros["c5w_parse_pct"] = fmt_pct(c5w.get("parse_rate"), 1)
    macros["c5w_pick2"] = fmt_dec(c5w.get("choosing_rate_pick2"), 3)
    macros["c5w_pick2_ci"] = fmt_ci(c5w.get("choosing_rate_pick2_ci95"), 3)
    macros["c5w_iso2"] = fmt_dec(c5w.get("fa_iso2_c3"), 3)
    macros["c5w_iso2_ci"] = fmt_ci(c5w.get("fa_iso2_c3_ci95"), 3)
    macros["c5w_diff"] = fmt_dec(c5w.get("diff_pick2_minus_iso2"), 3, signed=True)
    macros["c5w_diff_ci"] = fmt_ci(c5w.get("diff_pick2_minus_iso2_ci95"), 3, signed=True)
    macros["c5w_diff_p"] = fmt_p(c5w.get("diff_pick2_minus_iso2_p_one_sided"))
    macros["c5w_prop_base"] = fmt_dec(c5w.get("proportional_2_of_3_baseline"), 3)
    macros["c5w_vs_prop"] = fmt_dec(c5w.get("diff_vs_proportional_2_of_3"), 3, signed=True)

    # ------------------------------------------------------------------
    # 4. Experiment C9 (and C8 Low-Thinking): ResearchBench Science
    # ------------------------------------------------------------------
    c9 = v2_data.get("c9_science", {})
    macros["c9_n_items"] = fmt_int(c9.get("n_items"))
    for mkey, mtag in (
        ("gptoss", "gptoss"),
        ("gemini", "gemini"),
        ("gemini_low", "gemlow"),
        ("hydrogen", "hydro"),
        ("haiku", "haiku"),
    ):
        m = (c9.get("models") or {}).get(mkey, {})
        pr = m.get("parse_rates") or {}
        macros[f"c9_{mtag}_parse_pct"] = fmt_pct(pr.get("total"), 1)
        cal = m.get("calibration") or {}
        macros[f"c9_{mtag}_cal_r"] = fmt_dec(cal.get("iso_right"), 3)
        macros[f"c9_{mtag}_cal_w"] = fmt_dec(cal.get("iso_wrong"), 3)
        met = m.get("metrics") or {}
        ta_fc = met.get("ta_false_choice") or {}
        tp_h = met.get("tp_hit_aligned") or {}
        for arm, src_a in (("pick", "PICK"), ("each", "EACH_any"), ("iso", "ISO_any")):
            a_ta = ta_fc.get(src_a) or ta_fc.get(arm.upper()) or {}
            macros[f"c9_{mtag}_ta_{arm}"] = fmt_dec(a_ta.get("mean"), 3)
            macros[f"c9_{mtag}_ta_{arm}_ci"] = fmt_ci(a_ta.get("ci95"), 3)
        for arm, src_a in (("pick", "PICK"), ("each", "EACH"), ("iso", "ISO")):
            a_tp = tp_h.get(src_a) or {}
            macros[f"c9_{mtag}_tp_{arm}"] = fmt_dec(a_tp.get("mean"), 3)
            macros[f"c9_{mtag}_tp_{arm}_ci"] = fmt_ci(a_tp.get("ci95"), 3)
        sdt = met.get("sdt") or {}
        for arm, src_a in (("pick", "PICK"), ("each", "EACH"), ("iso", "ISO")):
            if isinstance(sdt.get(src_a), dict):
                add_sdt_arm(macros, f"c9_{mtag}_sdt_{arm}", sdt[src_a])
        sdiffs = met.get("sdt_diffs") or {}
        if isinstance(sdiffs.get("PICK_minus_ISO"), dict):
            add_sdt_diff(macros, f"c9_{mtag}_pi", sdiffs["PICK_minus_ISO"])
        if isinstance(sdiffs.get("EACH_minus_ISO"), dict):
            add_sdt_diff(macros, f"c9_{mtag}_ei", sdiffs["EACH_minus_ISO"])
        raw = m.get("raw_counts_and_exact_tests") or {}
        rarms = raw.get("arms") or {}
        for arm, src_a in (("pick", "PICK"), ("each", "EACH"), ("iso", "ISO")):
            ra = rarms.get(src_a) or {}
            macros[f"c9_{mtag}_{arm}_ta_k"] = fmt_int(ra.get("ta_k"))
            macros[f"c9_{mtag}_{arm}_ta_n"] = fmt_int(ra.get("ta_n"))
            macros[f"c9_{mtag}_{arm}_tp_k"] = fmt_int(ra.get("tp_aligned_k"))
            macros[f"c9_{mtag}_{arm}_tp_n"] = fmt_int(ra.get("tp_aligned_n"))
        mcn = raw.get("exact_mcnemar") or {}
        macros[f"c9_{mtag}_mcn_ta_p"] = fmt_p((mcn.get("TA_PICK_vs_ISO_any") or {}).get("exact_mcnemar_p"))
        macros[f"c9_{mtag}_mcn_tp_p"] = fmt_p((mcn.get("TP_aligned_PICK_vs_ISO") or {}).get("exact_mcnemar_p"))
        clip = raw.get("sdt_clipping_sensitivity_PICK_minus_ISO") or {}
        macros[f"c9_{mtag}_clip_mac_dc"] = fmt_dec((clip.get("macmillan_05_n") or {}).get("aligned_delta_c"), 3, signed=True)
        macros[f"c9_{mtag}_clip_qtr_dc"] = fmt_dec((clip.get("quarter_025_n") or {}).get("aligned_delta_c"), 3, signed=True)

    # ------------------------------------------------------------------
    # 5. Experiment C6: Cross-Vendor Judge-Family-Free Math
    # ------------------------------------------------------------------
    c6 = v2_data.get("c6_math", {})
    macros["c6_n_problems"] = fmt_int(c6.get("n_problems"))
    for mkey, mtag in (("gptoss", "gptoss"), ("gemini", "gemini")):
        m = (c6.get("models") or {}).get(mkey, {})
        pr = m.get("parse_rates") or {}
        macros[f"c6_{mtag}_parse_pct"] = fmt_pct(pr.get("total"), 1)
        sc = m.get("stratum_counts") or {}

        def _sc_int(key: str, sub: str = "all") -> Optional[int]:
            v = sc.get(key)
            if isinstance(v, dict):
                return v.get(sub)
            return v

        macros[f"c6_{mtag}_n_all"] = fmt_int(_sc_int("ALL"))
        macros[f"c6_{mtag}_n_s"] = fmt_int(_sc_int("SOLVED_M"))
        macros[f"c6_{mtag}_n_u"] = fmt_int(_sc_int("UNSOLVED_M"))
        macros[f"c6_{mtag}_n_m"] = fmt_int(_sc_int("MIXED_M"))
        macros[f"c6_{mtag}_n_u_contest"] = fmt_int(_sc_int("UNSOLVED_M", "contest"))
        macros[f"c6_{mtag}_n_u_arxiv"] = fmt_int(_sc_int("UNSOLVED_M", "arxivmath"))
        cal = m.get("calibration") or {}
        macros[f"c6_{mtag}_cal_r"] = fmt_dec(cal.get("iso_right"), 3)
        macros[f"c6_{mtag}_cal_w"] = fmt_dec(cal.get("iso_wrong"), 3)
        strata = m.get("strata") or {}
        for sname, stag in (("ALL", "all"), ("UNSOLVED_M", "u"), ("SOLVED_M", "s")):
            sblk_raw = strata.get(sname) or {}
            sblk = sblk_raw.get("all") if isinstance(sblk_raw.get("all"), dict) else sblk_raw
            ta_fc = sblk.get("ta_false_choice") or {}
            tp_h = sblk.get("tp_hit_aligned") or {}
            for arm, src_a in (("pick", "PICK"), ("each", "EACH_any"), ("iso", "ISO_any")):
                a_ta = ta_fc.get(src_a) or ta_fc.get(arm.upper()) or {}
                macros[f"c6_{mtag}_{stag}_ta_{arm}"] = fmt_dec(a_ta.get("mean"), 3)
                macros[f"c6_{mtag}_{stag}_ta_{arm}_ci"] = fmt_ci(a_ta.get("ci95"), 3)
            for arm, src_a in (("pick", "PICK"), ("each", "EACH"), ("iso", "ISO")):
                a_tp = tp_h.get(src_a) or {}
                macros[f"c6_{mtag}_{stag}_tp_{arm}"] = fmt_dec(a_tp.get("mean"), 3)
            sdt = sblk.get("sdt") or {}
            for arm, src_a in (("pick", "PICK"), ("each", "EACH"), ("iso", "ISO")):
                if isinstance(sdt.get(src_a), dict):
                    add_sdt_arm(macros, f"c6_{mtag}_{stag}_{arm}", sdt[src_a])
            sdiffs = sblk.get("sdt_diffs") or {}
            add_sdt_diff(
                macros,
                f"c6_{mtag}_{stag}_pi",
                sdiffs.get("PICK_minus_ISO") if isinstance(sdiffs.get("PICK_minus_ISO"), dict) else {},
            )
        h3 = m.get("h3_out_of_sample_prediction") or {}
        macros[f"c6_{mtag}_h3_fpred"] = fmt_dec(h3.get("F_pred"), 3)
        macros[f"c6_{mtag}_h3_fobs"] = fmt_dec(h3.get("F_obs"), 3)
        macros[f"c6_{mtag}_h3_err"] = fmt_dec(h3.get("abs_err"), 3)

    # ------------------------------------------------------------------
    # 6. Experiment C7: Compute-Matched Mitigation Matrix
    # ------------------------------------------------------------------
    c7 = v2_data.get("c7_mitigation", {})

    # C7 Haiku Math M1
    m1 = c7.get("math_haiku_m1") or {}
    macros["c7_m1_n"] = fmt_int(m1.get("n_problems"))
    macros["c7_m1_tb_ok"] = fmt_int(m1.get("n_tiebreak_ok"))
    macros["c7_m1_extra_calls"] = fmt_dec(m1.get("extra_calls_per_pool"), 2)
    macros["c7_m1_crec"] = fmt_pct(m1.get("criterion_recovery_frac"), 1)
    for arm, src_a in (("m1", "M1"), ("pick", "PICK"), ("iso", "ISO")):
        s = (m1.get("sdt") or {}).get(src_a)
        if isinstance(s, dict):
            add_sdt_arm(macros, f"c7_m1_{arm}", s)
    for key, tag in (("M1_minus_PICK", "mp"), ("M1_minus_ISO", "mi")):
        d = (m1.get("sdt_diffs") or {}).get(key)
        if isinstance(d, dict):
            add_sdt_diff(macros, f"c7_m1_{tag}", d)

    # C7 Haiku Math M2
    m2h = (c7.get("math_m2") or {}).get("haiku") or {}
    macros["c7_m2h_n"] = fmt_int(m2h.get("n_paired_m2_gate4"))
    macros["c7_m2h_parse_pct"] = fmt_pct(m2h.get("parse_rate_choice"), 1)
    macros["c7_m2h_crec"] = fmt_pct((m2h.get("criterion_recovery_frac") or {}).get("M2_gate4"), 1)
    for arm, src_a in (("raw", "M2_raw"), ("g4", "M2_gate4")):
        s = (m2h.get("sdt") or {}).get(src_a)
        if isinstance(s, dict):
            add_sdt_arm(macros, f"c7_m2h_{arm}", s)
    for key, tag in (("M2_gate4_minus_PICK", "mp"), ("M2_gate4_minus_ISO", "mi")):
        d = (m2h.get("sdt_diffs") or {}).get(key)
        if isinstance(d, dict):
            add_sdt_diff(macros, f"c7_m2h_{tag}", d)

    # C7 Cross-Vendor Math M2
    for mkey, mtag in (("gptoss", "gptoss"), ("gemini", "gemini")):
        m2m = (c7.get("math_m2") or {}).get(mkey) or {}
        macros[f"c7_m2m_{mtag}_n"] = fmt_int(m2m.get("n_paired_m2_gate4"))
        macros[f"c7_m2m_{mtag}_parse_pct"] = fmt_pct(m2m.get("parse_rate_choice"), 1)
        s = (m2m.get("sdt") or {}).get("M2_gate4")
        if isinstance(s, dict):
            add_sdt_arm(macros, f"c7_m2m_{mtag}_g4", s)
        d = (m2m.get("sdt_diffs") or {}).get("M2_gate4_minus_PICK")
        if isinstance(d, dict):
            add_sdt_diff(macros, f"c7_m2m_{mtag}_mp", d)

    # C7 Haiku Math M3 Known-Foil
    m3 = c7.get("math_haiku_m3_foil") or {}
    macros["c7_m3_n"] = fmt_int(m3.get("n_paired_m3"))
    macros["c7_m3_parse_pct"] = fmt_pct(m3.get("parse_rate"), 1)
    macros["c7_m3_foil_all"] = fmt_dec((m3.get("foil_pick_rate_all") or {}).get("mean"), 3)
    s = (m3.get("sdt") or {}).get("M3_any_fa")
    if isinstance(s, dict):
        add_sdt_arm(macros, "c7_m3", s)
    for key, tag in (("M3_any_fa_minus_PICK", "mp"), ("M3_any_fa_minus_ISO", "mi")):
        d = (m3.get("sdt_diffs") or {}).get(key)
        if isinstance(d, dict):
            add_sdt_diff(macros, f"c7_m3_{tag}", d)

    # C7 Science M2 across all 5 judge configs
    for mkey, mtag in (
        ("gptoss", "gptoss"),
        ("gemini", "gemini"),
        ("gemini_low", "gemlow"),
        ("hydrogen", "hydro"),
        ("haiku", "haiku"),
    ):
        m2s = (c7.get("science_m2") or {}).get(mkey) or {}
        macros[f"c7_m2s_{mtag}_parse_pct"] = fmt_pct(m2s.get("parse_rate_choice"), 1)
        s = (m2s.get("sdt") or {}).get("M2_gate4")
        if isinstance(s, dict):
            add_sdt_arm(macros, f"c7_m2s_{mtag}_g4", s)
        d = (m2s.get("sdt_diffs") or {}).get("M2_gate4_minus_PICK")
        if isinstance(d, dict):
            add_sdt_diff(macros, f"c7_m2s_{mtag}_mp", d)

    return macros


def render_tex(macros: Dict[str, str]) -> str:
    lines = [
        "% Auto-generated by autoloop/make_results_tex.py. Do not hand-edit.",
        "% Every empirical number in paper/main.tex is accessed via \\res{<key>}.",
        "",
    ]
    for k in sorted(macros.keys()):
        val = macros[k]
        if "\u2014" in val or "\u2013" in val:
            raise ValueError(f"Forbidden em/en dash in macro {k}: {val!r}")
        lines.append(f"\\expandafter\\def\\csname res@{k}\\endcsname{{{val}}}")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Generate paper/results.tex from verified results JSONs.")
    ap.add_argument("--sdt", type=Path, default=DEFAULT_ROOT / "results" / "sdt_and_subgroups.json")
    ap.add_argument("--v2", type=Path, default=DEFAULT_ROOT / "results" / "results_b.json")
    ap.add_argument("--out", type=Path, default=DEFAULT_ROOT / "paper" / "results.tex")
    args = ap.parse_args(argv)

    sdt_data = json.loads(args.sdt.read_text(encoding="utf-8"))
    v2_data = json.loads(args.v2.read_text(encoding="utf-8"))
    macros = build_macros(sdt_data, v2_data)
    tex = render_tex(macros)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(tex, encoding="utf-8")
    print(f"Wrote {len(macros)} macros to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
