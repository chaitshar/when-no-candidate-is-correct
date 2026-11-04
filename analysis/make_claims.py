#!/usr/bin/env python3
"""Regenerate results/claims.json and paper/results.tex from raw data.

Step 1 re-runs every analysis script on its raw outputs (deterministic seeds).
Step 2 reads the results files those scripts write and formats each paper number.
Every claim records its source file. The paper uses \\res{id} only.
"""
import csv
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ANALYSES = [
    "exps/p1_lineup_math/analyze.py", "exps/p2_tournament/analyze.py",
    "exps/screens/s1_lineup/analyze.py", "exps/screens/s1_lineup/analyze_solve.py",
    "exps/screens/s3_tournament/analyze.py", "exps/screens/s4_critique/analyze.py",
    "exps/screens/s5_whowhen/analyze.py", "exps/screens/s5_whowhen/analyze_norm.py",
    "exps/screens/s8_debate/analyze.py", "exps/screens/s9_peernote/analyze.py",
    "exps/screens/s2_s10_free/analyze.py", "exps/screens/cal/analyze.py",
    "exps/c2_confirm/analyze.py", "exps/posthoc/solvability_split.py", "exps/posthoc/solvability_by_source.py", "exps/c3/stratify.py", "exps/c3/analyze.py",
    "exps/c3/analyze_sonnet.py", "exps/c3/analyze_h3.py", "exps/c3/analyze_sensitivity.py", "exps/c3/analyze_gemma.py", "exps/c3/analyze_review.py", "exps/c3/analyze_aligned.py", "exps/c3/analyze_a4.py", "exps/c3/analyze_a4_sensitivity.py", "exps/c3/analyze_a5.py",
]


def run_all():
    for a in ANALYSES:
        p = subprocess.run([sys.executable, a], capture_output=True, text=True)
        if p.returncode:
            sys.exit(f"{a} failed: {p.stderr[-400:]}")


def j(p):
    return json.load(open(p))


def f2(x):
    return f"{x:.2f}"


def pct(x):
    return f"{100 * x:.0f}\\%"


def ci(a, b):
    return f"[{a:+.2f}, {b:+.2f}]"


def main():
    if "--no-run" not in sys.argv:
        run_all()
    C = {}

    def add(cid, value, source, note=""):
        C[cid] = {"value": value, "source": source, "note": note}

    # P1 (stale MATH items)
    p1 = j("exps/p1_lineup_math/results.json")["models"]
    src = "exps/p1_lineup_math/results.json"
    for m in ("haiku", "sonnet", "opus"):
        add(f"p1_{m}_solve", f2(p1[m]["solve_rate"]), src)
        add(f"p1_{m}_isowrong", f2(p1[m]["iso_accept_wrong"]), src)
        add(f"p1_{m}_pick", f2(p1[m]["choosing_TA"]["PICK"][0]), src)
    add("p1_gemma2_pickiso", f2(p1["gemma-2-2b"]["contrasts"]["PICK-ISO"]["diff"]), src)
    g = p1["gemma-2-2b"]["contrasts"]["PICK-ISO"]["ci"]
    add("p1_gemma2_pickiso_ci", ci(*g), src)
    # P2
    p2 = j("exps/p2_tournament/results.json"); src = "exps/p2_tournament/results.json"
    for m in ("haiku", "sonnet"):
        add(f"p2_{m}_auroc", f2(p2[m]["dec"]["auroc"]), src)
    # calibration
    cal = j("exps/screens/cal/results.json"); src = "exps/screens/cal/results.json"
    add("cal_haiku", f2(cal["haiku_SOLVE"]["solve"]), src); add("cal_sonnet", f2(cal["sonnet_SOLVE"]["solve"]), src)
    add("cal_haiku_nowork", f2(cal["haiku_NOWORK"]["solve"]), src); add("cal_sonnet_nowork", f2(cal["sonnet_NOWORK"]["solve"]), src)
    # S1 and S6
    s1 = j("exps/screens/s1_lineup/results.json")["models"]["haiku"]; src = "exps/screens/s1_lineup/results.json"
    sv = j("exps/screens/s1_lineup/results_solve.json")
    add("s1_solve", f2(sv["haiku"]["solve"]), "exps/screens/s1_lineup/results_solve.json")
    add("s1_isowrong", f2(s1["iso_accept_wrong"]), src)
    _pl = j("exps/screens/s1_lineup/pools.json"); _seen = {}
    for _p in _pl:
        for _c in _p["cands"]:
            if _c["role"] == "wrong": _seen[_c["cid"]] = _seen.get(_c["cid"], 0) + 1
    add("s1_isowrong_n", str(len(_seen)), "exps/screens/s1_lineup/pools.json")
    add("s1_isowrong_k", str(round(s1["iso_accept_wrong"] * len(_seen))), src)
    add("s1_wrong_appear", str(sum(_seen.values())), "exps/screens/s1_lineup/pools.json"); add("s1_isoright", f2(s1["iso_accept_right"]), src)
    for a in ("ISO", "PICK", "EACH"):
        add(f"s1_ta_{a.lower()}", f2(s1["choosing_TA"][a][0]), src)
    c = s1["contrasts"]["PICK-ISO"]; add("s1_pickiso", f"{c['diff']:+.2f}", src); add("s1_pickiso_ci", ci(*c["ci"]), src)
    c = s1["contrasts"]["PICK-EACH"]; add("s1_pickeach", f"{c['diff']:+.2f}", src); add("s1_pickeach_ci", ci(*c["ci"]), src)
    add("s1_tp_pick_false", f2(s1["TP"]["PICK"]["false"]), src); add("s1_tp_iso_false", f2(s1["TP"]["ISO"]["false"]), src)
    add("s6_picked", f2(s1["S6"]["iso_accept_picked"]), src); add("s6_unpicked", f2(s1["S6"]["iso_accept_unpicked"]), src)
    add("s6_diff", f"{s1['S6']['diff']:+.2f}", src); add("s6_ci", ci(*s1["S6"]["ci"]), src)
    # S3
    s3 = j("exps/screens/s3_tournament/results.json")["haiku"]; src = "exps/screens/s3_tournament/results.json"
    add("s3_auroc", f2(s3["dec"]["auroc"]), src); add("s3_auroc_ci", ci(*s3["dec"]["ci"]), src)
    add("s3_ta_unique", f2(s3["TA_unique_share"]), src); add("s3_ta_unan", f2(s3["TA_unanimous_share"]), src)
    # S4
    s4 = j("exps/screens/s4_critique/results.json"); src = "exps/screens/s4_critique/results.json"
    for k in ("wrong_CHECKER", "wrong_STUDENT", "right_CHECKER", "right_STUDENT"):
        add(f"s4_{k.lower()}", f"{s4[k]['diff_accept']:+.2f}", src); add(f"s4_{k.lower()}_ci", ci(*s4[k]["ci"]), src)
    # S5
    s5 = j("exps/screens/s5_whowhen/results.json"); n5 = j("exps/screens/s5_whowhen/results_norm.json"); src = "exps/screens/s5_whowhen/results.json"
    for m in ("haiku", "sonnet"):
        add(f"s5_{m}_agent", f2(s5[f"{m}_all"]["agent_acc"]), src)
        add(f"s5_{m}_step", f2(s5[f"{m}_all"]["step_acc"]), src)
        add(f"s5_{m}_agentnorm", f2(n5[f"{m}_all"]["agent_acc_norm"]), "exps/screens/s5_whowhen/results_norm.json")
        add(f"s5_{m}_handnorm", f2(n5[f"{m}_hand"]["agent_acc_norm"]), "exps/screens/s5_whowhen/results_norm.json")
    add("s5_hand_majority", f2(s5["haiku_hand"]["baseline_majority_agent"]), src)
    # S8, S9
    s8 = j("exps/screens/s8_debate/results.json"); src = "exps/screens/s8_debate/results.json"
    add("s8_ta_neither", f2(s8["TA"]["neither_rate"]), src); add("s8_tp_right", f2(s8["TP"]["right_rate"]), src)
    s9 = j("exps/screens/s9_peernote/results.json"); src = "exps/screens/s9_peernote/results.json"
    add("s9_wrong_diff", f"{s9['NOTEWRONG']['diff']:+.2f}", src); add("s9_wrong_ci", ci(*s9["NOTEWRONG"]["ci"]), src)
    add("s9_adopt", f2(s9["NOTEWRONG"]["adopted_wrong_note"]), src)
    # S2, S10
    s2 = j("exps/screens/s2_s10_free/results.json"); src = "exps/screens/s2_s10_free/results.json"
    big = [v for v in s2["S2"].values() if v["n_problems"] >= 60]
    add("s2_n_big", str(len(big)), src)
    add("s2_auroc_min", f2(min(v["auroc"] for v in big)), src); add("s2_auroc_max", f2(max(v["auroc"] for v in big)), src)
    add("s2_unan_wrong_max", f2(max(v["unanimous_wrong_rate"] for v in big if v["unanimous_wrong_rate"] is not None)), src)
    add("s10_hetero", f2(s2["S10"]["mean_hetero_phi"]), src); add("s10_homo", f2(s2["S10"]["mean_homo_phi"]), src)
    # C2
    if os.path.exists("exps/c2_confirm/results.json"):
        c2 = j("exps/c2_confirm/results.json"); src = "exps/c2_confirm/results.json"
        for key in ("haiku_all", "haiku_conf", "haiku_repl", "sonnet_conf"):
            r = c2[key]
            add(f"c2_{key}_solve", f2(r["gate"]["solve_rate"]), src)
            add(f"c2_{key}_isowrong", f2(r["gate"]["iso_acc_wrong"]), src)
            add(f"c2_{key}_gate", "passed" if r["gate"]["passed"] else "failed", src)
            if "H1" in r:
                add(f"c2_{key}_h1n", str(r["H1"]["n"]), src)
                add(f"c2_{key}_h1d", f"{r['H1']['D']:+.2f}", src); add(f"c2_{key}_h1ci90", ci(*r["H1"]["ci90"]), src)
                add(f"c2_{key}_h1eq", "inside" if r["H1"]["equivalent"] else "not inside", src)
            if "arms_TA" in r:
                add(f"c2_{key}_ta_iso", f2(r["arms_TA"]["ISO"][0]), src); add(f"c2_{key}_ta_pick", f2(r["arms_TA"]["PICK"][0]), src)
            if "H2" in r:
                add(f"c2_{key}_h2", f"{r['H2']['diff']:+.2f}", src); add(f"c2_{key}_h2ci", ci(*r["H2"]["ci95"]), src)
                add(f"c2_{key}_h2p", f"{r['H2']['p_one_sided']:.3f}", src)
        for k, v in c2["holm"].items():
            add(f"c2_holm_{k}", f"{v:.3f}", src)
    # post hoc solvability split
    ph = j("exps/posthoc/solvability_split.json"); src = "exps/posthoc/solvability_split.json"
    for k in ("solved", "unsolved"):
        add(f"ph_{k}_n", str(ph[k]["n"]), src); add(f"ph_{k}_d", f"{ph[k]['D']:+.2f}", src); add(f"ph_{k}_ci", ci(*ph[k]["ci95"]), src)
        add(f"ph_{k}_pick", f2(ph[k]["pick"]), src); add(f"ph_{k}_iso", f2(ph[k]["iso"]), src)
    if os.path.exists("exps/c2_confirm/results.json"):
        c2 = j("exps/c2_confirm/results.json")
        add("c2_haiku_all_p1", f"{c2['haiku_all']['H1']['p_one_sided_D_gt_0']:.3f}", "exps/c2_confirm/results.json")
        add("c2_sonnet_isoparse", f"{c2['sonnet_conf']['gate']['iso_parse']:.3f}", "exps/c2_confirm/results.json")
        add("c2_conf_h2p", f"{c2['haiku_conf']['H2']['p_one_sided']:.3f}", "exps/c2_confirm/results.json")
    sb = j("exps/posthoc/solvability_by_source.json"); src = "exps/posthoc/solvability_by_source.json"
    for k in ("screen_solved", "screen_unsolved", "conf_solved", "conf_unsolved", "repl_solved", "repl_unsolved"):
        add(f"sb_{k}_n", str(sb[k]["n"]), src); add(f"sb_{k}_d", f"{sb[k]['D']:+.2f}", src); add(f"sb_{k}_ci", ci(*sb[k]["ci95"]), src)
    add("c2_conf_h1n", str(j("exps/c2_confirm/results.json")["haiku_conf"]["H1"]["n"]), "exps/c2_confirm/results.json")
    add("c2_repl_h2", f"{j('exps/c2_confirm/results.json')['haiku_repl']['H2']['diff']:+.2f}", "exps/c2_confirm/results.json")
    add("ph_all_d", f"{ph['all']['D']:+.2f}", "exps/posthoc/solvability_split.json"); add("ph_all_ci", ci(*ph["all"]["ci95"]), "exps/posthoc/solvability_split.json")
    # C3
    if os.path.exists("exps/c3/results.json"):
        ss = j("exps/c3/solve_summary.json"); src = "exps/c3/solve_summary.json"
        for k in ("SOLVED", "UNSOLVED", "MIXED", "UNRESOLVED"):
            add(f"c3_n_{k.lower()}", str(ss["counts"].get(k, 0)), src)
        add("c3_n_ta", str(sum(ss["counts"].values())), src); add("c3_disagree", str(ss["disagreements"]), src)
        for tag, f in (("h", "exps/c3/results.json"), ("s", "exps/c3/results_sonnet.json")):
            if not os.path.exists(f): continue
            r = j(f)
            g = r["gate"]; add(f"c3{tag}_gate", "passed" if g["passed"] else "failed", f)
            add(f"c3{tag}_isoparse", f"{g['iso_parse']:.3f}", f); add(f"c3{tag}_isowrong", f2(g["iso_acc_wrong"]), f); add(f"c3{tag}_isoright", f2(g["iso_acc_right"]), f)
            add(f"c3{tag}_b", f"{r['H1']['b']:+.2f}", f); add(f"c3{tag}_b_ci", ci(*r["H1"]["ci95"]), f); add(f"c3{tag}_b_p", f"{r['H1']['p_one_sided']:.3f}", f)
            add(f"c3{tag}_n", str(r["H1"]["n"]), f)
            for key, lab in (("D_unsolved", "du"), ("D_solved", "ds"), ("H2s", "h2s"), ("H2u", "h2u")):
                if r.get(key):
                    add(f"c3{tag}_{lab}", f"{r[key]['mean']:+.2f}", f); add(f"c3{tag}_{lab}_ci", ci(*r[key]["ci95"]), f)
                    add(f"c3{tag}_{lab}_n", str(r[key]["n"]), f); add(f"c3{tag}_{lab}_p", f"{r[key]['p_one_sided']:.3f}" if r[key]['p_one_sided'] >= 0.001 else "$<$0.001", f)
            if r.get("H1_unadjusted"):
                add(f"c3{tag}_unadj", f"{r['H1_unadjusted']['diff']:+.2f}", f); add(f"c3{tag}_unadj_ci", ci(*r["H1_unadjusted"]["ci95"]), f)
            for fam in ("contest", "arxiv"):
                x = r.get(f"H1_family_{fam}", {})
                if "b" in x:
                    add(f"c3{tag}_fam_{fam}", f"{x['b']:+.2f}", f); add(f"c3{tag}_fam_{fam}_ci", ci(x["b"] - 1.96 * x["se_hc3"], x["b"] + 1.96 * x["se_hc3"]), f)
                    add(f"c3{tag}_fam_{fam}_n", str(x["n"]), f); add(f"c3{tag}_fam_{fam}_nu", str(x["n_unsolved"]), f)
            for st_, a in r["arms"].items():
                if a["pick"] is not None:
                    add(f"c3{tag}_{st_.lower()}_pick", f2(a["pick"]), f); add(f"c3{tag}_{st_.lower()}_iso", f2(a["iso_any"]), f)
            for k, v in r["holm"].items(): add(f"c3{tag}_holm_{k}", f"{v:.3f}" if v >= 0.001 else "$<$0.001", f)
            for k, v in r["verdicts"].items(): add(f"c3{tag}_verdict_{k}", v, f)
            add(f"c3{tag}_cost", f"{sum(r['cost'].values()):.1f}", f)
        if os.path.exists("exps/c3/results_h3.json"):
            h3 = j("exps/c3/results_h3.json"); f = "exps/c3/results_h3.json"
            for sel in ("haiku", "sonnet"):
                x = h3.get(f"select_{sel}")
                if x:
                    add(f"h3_{sel}_d", f"{x['mean_hsame_minus_hcross']:+.2f}", f); add(f"h3_{sel}_ci", ci(*x["ci95"]), f)
                    add(f"h3_{sel}_p", f"{x['p_one_sided']:.3f}", f); add(f"h3_{sel}_n", str(x["n"]), f)
                    for kk, vv in x.items():
                        if kk.startswith("accept_pick_by_"): add(f"h3_{sel}_{kk.replace('accept_pick_by_', 'acc_')}", f2(vv), f)
            add("h3_verdict", str(h3.get("H3_verdict")), f)
    if os.path.exists("exps/c3/results_a4.json"):
        a4 = j("exps/c3/results_a4.json"); f = "exps/c3/results_a4.json"
        for m, t in (("haiku", "h"), ("sonnet", "s")):
            if m not in a4: continue
            for st_ in ("SOLVED", "UNSOLVED"):
                x = a4[m].get(st_, {}); sl = st_.lower()[0]
                for X in ("PICK", "EACH", "ISO"):
                    if X in x:
                        add(f"a4{t}{sl}_{X.lower()}_hit", f2(x[X]["hit"]), f); add(f"a4{t}{sl}_{X.lower()}_fa", f2(x[X]["fa"]), f)
                        add(f"a4{t}{sl}_{X.lower()}_j", f"{x[X]['J']:+.2f}", f); add(f"a4{t}{sl}_{X.lower()}_n", str(x[X]["n"]), f)
                for key, lab in (("J_PICK_minus_J_ISO", "dj"), ("hit_PICK_minus_hit_ISO", "dhit"), ("fa_PICK_minus_fa_EACH", "dform")):
                    if key in x:
                        add(f"a4{t}{sl}_{lab}", f"{x[key]['mean']:+.2f}", f); add(f"a4{t}{sl}_{lab}_ci", ci(*x[key]["ci95"]), f)
                        if "p_one_sided_lt0" in x[key]: add(f"a4{t}{sl}_{lab}_p", f"{x[key]['p_one_sided_lt0']:.3f}", f)
            add(f"a4{t}_h4", str(a4[m].get("H4_verdict")), f)
    if os.path.exists("exps/c3/results_a4_sensitivity.json"):
        x = j("exps/c3/results_a4_sensitivity.json")["haiku"]["UNSOLVED"]; f = "exps/c3/results_a4_sensitivity.json"
        add("a4sens_hu_dj", f"{x['dJ']:+.2f}", f); add("a4sens_hu_dj_ci", ci(*x["dJ_ci95"]), f); add("a4sens_hu_n", str(x["n"]), f)
    if os.path.exists("exps/c3/results_a5.json"):
        a5 = j("exps/c3/results_a5.json"); f = "exps/c3/results_a5.json"
        for st_, t in (("UNSOLVED", "u"), ("SOLVED", "s")):
            x = a5["prereg"][st_]
            add(f"a5{t}_n", str(x["n_roc"]), f); add(f"a5{t}_dpauc", f"{x['pAUC_diff']:+.3f}", f); add(f"a5{t}_dpauc_ci", "[%+.3f, %+.3f]" % tuple(x["ci95"]), f)
            add(f"a5{t}_famax", f2(x["fa_max"]), f)
            add(f"a5{t}_fa_base", f2(x["fa_base"]), f); add(f"a5{t}_fa_pick", f2(x["fa_pick"]), f); add(f"a5{t}_dfa", f"{x['dfa']:+.2f}", f); add(f"a5{t}_dfa_ci", ci(*x["dfa_ci95"]), f)
            add(f"a5{t}_dhit", f"{x['dhit']:+.2f}", f); add(f"a5{t}_dhit_ci", ci(*x["dhit_ci95"]), f)
        for k, v in a5["prereg"]["verdicts"].items(): add(f"a5_verdict_{k}", v, f)
        for k, v in a5["prereg"]["holm"].items(): add(f"a5_holm_{k}", f"{v:.3f}", f)
        y = a5["audited_sensitivity"]["UNSOLVED"]; add("a5sens_dpauc", f"{y['pAUC_diff']:+.3f}", f); add("a5sens_dpauc_ci", "[%+.3f, %+.3f]" % tuple(y["ci95"]), f)
    gm = j("exps/c3/results_gemma.json"); f = "exps/c3/results_gemma.json"
    add("gm_isowrong", f2(gm["iso_acc_wrong"]), f); add("gm_n", str(gm["d"]["UNSOLVED"]["n"]), f)
    add("gm_du", f"{gm['d']['UNSOLVED']['mean']:+.2f}", f); add("gm_ds", f"{gm['d']['SOLVED']['mean']:+.2f}", f)
    add("gm_hu", f"{gm['h']['UNSOLVED']['mean']:+.2f}", f); add("gm_cal", f2(j("exps/screens/cal/results.json")["gemma-4-e4b_SOLVE"]["solve"]), "exps/screens/cal/results.json")
    import csv as _csv
    _au = [r["audited_stratum"] for r in _csv.DictReader(open("exps/c3/audit_unsolved.csv"))]
    _lab = list(_csv.DictReader(open("exps/c3/candidate_label_audit.csv")))
    add("lab_n_pools", str(len({r["pid"] for r in _lab})), "exps/c3/candidate_label_audit.csv")
    add("lab_n_mislab", str(len({r["pid"] for r in _lab if r["finding"] == "mislabelled_correct"})), "exps/c3/candidate_label_audit.csv")
    add("lab_n_garbled", str(len({r["pid"] for r in _lab if r["finding"] == "garbled_answer"})), "exps/c3/candidate_label_audit.csv")
    add("c3_audit_solved", str(_au.count("SOLVED")), "exps/c3/audit_unsolved.csv"); add("c3_audit_mixed", str(_au.count("MIXED")), "exps/c3/audit_unsolved.csv")
    if os.path.exists("exps/c3/results_sensitivity.json"):
        sv = j("exps/c3/results_sensitivity.json"); f = "exps/c3/results_sensitivity.json"
        for m in ("haiku", "sonnet"):
            x = sv[f"{m}_both"]
            add(f"sens_{m}_nu", str(x["n_unsolved"]), f); add(f"sens_{m}_ns", str(x["n_solved"]), f)
            add(f"sens_{m}_du", f"{x['d_unsolved']['mean']:+.2f}", f); add(f"sens_{m}_du_ci", ci(*x["d_unsolved"]["ci95"]), f)
            add(f"sens_{m}_hu", f"{x['h_unsolved']['mean']:+.2f}", f); add(f"sens_{m}_hu_ci", ci(*x["h_unsolved"]["ci95"]), f)
            add(f"sens_{m}_b", f"{x['b']:+.2f}", f); add(f"sens_{m}_b_ci", ci(*x["b_ci95"]), f)
            y = sv.get(f"{m}_all")
            if y:
                add(f"sensall_{m}_nu", str(y["n_unsolved"]), f)
                add(f"sensall_{m}_du", f"{y['d_unsolved']['mean']:+.2f}", f); add(f"sensall_{m}_du_ci", ci(*y["d_unsolved"]["ci95"]), f)
                add(f"sensall_{m}_hu", f"{y['h_unsolved']['mean']:+.2f}", f); add(f"sensall_{m}_hu_ci", ci(*y["h_unsolved"]["ci95"]), f)
    # post hoc checks prompted by external review
    al = j("exps/c3/results_aligned.json"); f = "exps/c3/results_aligned.json"
    for m, mm in (("haiku", "h"), ("sonnet", "s")):
        for kind, kk in (("prereg", "p"), ("corrected", "c")):
            t = al[f"{m}_{kind}"]["ta_unsolved"]
            add(f"ta_{mm}{kk}_n", str(t["n"]), f); add(f"ta_{mm}{kk}_pick", f2(t["pick"]), f); add(f"ta_{mm}{kk}_iso", f2(t["iso"]), f)
            for sname, ss in (("UNSOLVED", "u"), ("SOLVED", "s")):
                x = al[f"{m}_{kind}"][sname]
                for arm in ("PICK", "EACH", "ISO"):
                    a = x[arm]; pre = f"al_{mm}{kk}{ss}_{arm.lower()}"
                    add(pre + "_n", str(a["n"]), f); add(pre + "_f", f2(a["false_choice"]), f); add(pre + "_h", f2(a["correct"]), f)
                    add(pre + "_w", f2(a["wrong_when_present"]), f); add(pre + "_a", f2(abs(a["abstain_when_present"])), f)
                    add(pre + "_sel", f2(a["correct"] + a["wrong_when_present"]), f); add(pre + "_rate", f2(a["correct_given_selection"]), f)
                    add(pre + "_chance", f2(a["random_chooser_hit"]), f); add(pre + "_share", f2(a["right_share_of_selections_equal_base"]), f)
                for c, cc in (("PICK_minus_ISO", "pi"), ("PICK_minus_EACH", "pe"), ("EACH_minus_ISO", "ei")):
                    for nm, nn in (("false", "f"), ("correct", "h")):
                        y = x[f"{c}_{nm}"]; add(f"al_{mm}{kk}{ss}_{cc}{nn}", f"{y['mean']:+.2f}", f); add(f"al_{mm}{kk}{ss}_{cc}{nn}_ci", ci(*y["ci95"]), f)
    rv = j("exps/c3/results_review.json"); f = "exps/c3/results_review.json"
    o = rv["own_answer_haiku_unsolved"]
    add("rv_own_pools", str(o["pools_with_own"]), f); add("rv_own_n", str(o["n"]), f); add("rv_own_with", f"{o['d_with']['mean']:+.2f}", f); add("rv_own_with_ci", ci(*o["d_with"]["ci95"]), f)
    add("rv_own_wo", f"{o['d_without']['mean']:+.2f}", f); add("rv_own_wo_ci", ci(*o["d_without"]["ci95"]), f); add("rv_own_wo_n", str(o["d_without"]["n"]), f)
    add("rv_own_s_with", f"{o['sonnet_d_with']['mean']:+.2f}", f); add("rv_own_s_with_ci", ci(*o["sonnet_d_with"]["ci95"]), f); add("rv_own_s_wo", f"{o['sonnet_d_without']['mean']:+.2f}", f); add("rv_own_s_wo_ci", ci(*o["sonnet_d_without"]["ci95"]), f)
    add("rv_own_with_n", str(o["d_with"]["n"]), f); add("rv_own_pick", f"{o['pick_matches_own']} of {o['pick_n']}", f); add("rv_own_forced", f"{o['forced_matches_own']} of {o['forced_n']}", f)
    for m, mm in (("haiku", "h"), ("sonnet", "s")):
        u = rv[m]["UNSOLVED"]; v = rv[m]["SOLVED"]
        add(f"rv_{mm}_disc_pick", str(u["discordant_pick_only"]), f); add(f"rv_{mm}_disc_iso", str(u["discordant_iso_only"]), f); add(f"rv_{mm}_sign_p", f"{u['sign_test_p']:.4f}", f)
        add(f"rv_{mm}_pos", ", ".join(map(str, u["FORCED_position"]["counts"])), f); add(f"rv_{mm}_pos_p", f"{u['FORCED_position']['p_uniform']:.3f}", f)
        add(f"rv_{mm}_posp", ", ".join(map(str, u["PICK_position"]["counts"])), f); add(f"rv_{mm}_posp_p", f"{u['PICK_position']['p_uniform']:.3f}", f)
        add(f"rv_{mm}_long", f2(u["FORCED_longest"]), f); add(f"rv_{mm}_short", f2(u["FORCED_shortest"]), f)
        cl = u["FORCED_claude_picks"]; add(f"rv_{mm}_cl_obs", str(cl["observed"]), f); add(f"rv_{mm}_cl_exp", f"{cl['expected_if_blind']:.0f}", f); add(f"rv_{mm}_cl_n", str(cl["n_mixed_pools"]), f); add(f"rv_{mm}_cl_p", f"{cl['p']:.3f}", f)
        cs = v["FORCED_claude_picks"]; add(f"rv_{mm}_cls_obs", str(cs["observed"]), f); add(f"rv_{mm}_cls_exp", f"{cs['expected_if_blind']:.0f}", f); add(f"rv_{mm}_cls_p", f"{cs['p']:.3f}", f)
        add(f"rv_{mm}_tok_iso", f"{u['median_output_tokens']['ISO']:.0f}", f); add(f"rv_{mm}_tok_pick", f"{u['median_output_tokens']['PICK']:.0f}", f)
        pm = rv[f"permutation_{m}"]; add(f"rv_{mm}_perm_p", f"{pm['p_one_sided']:.3f}", f)
        add(f"rv_{mm}_ov_u", f"{pm['overlap_unsolved']['mean']:+.2f}", f); add(f"rv_{mm}_ov_u_ci", ci(*pm["overlap_unsolved"]["ci95"]), f); add(f"rv_{mm}_ov_un", str(pm["overlap_unsolved"]["n"]), f)
        add(f"rv_{mm}_ov_s", f"{pm['overlap_solved']['mean']:+.2f}", f); add(f"rv_{mm}_ov_s_ci", ci(*pm["overlap_solved"]["ci95"]), f); add(f"rv_{mm}_ov_sn", str(pm["overlap_solved"]["n"]), f)
    add("rv_claude_share", pct(rv["haiku"]["claude_candidate_share"]), f)
    se = j("exps/c3/results_sensitivity.json"); f = "exps/c3/results_sensitivity.json"
    for m, mm in (("haiku", "h"), ("sonnet", "s")):
        y = se[f"{m}_all"]; add(f"all_{mm}_b", f"{y['b']:+.2f}", f); add(f"all_{mm}_b_ci", ci(*y["b_ci95"]), f); add(f"all_{mm}_ns", str(y["n_solved"]), f); add(f"all_{mm}_ds", f"{y['d_solved']['mean']:+.2f}", f); add(f"all_{mm}_ds_ci", ci(*y["d_solved"]["ci95"]), f)
    # fixed design constants (from preregistrations)
    add("band_lo", "0.2", "exps/screens/PREREGISTRATION_v2.md"); add("band_hi", "0.8", "exps/screens/PREREGISTRATION_v2.md")
    add("c3_gate_parse", "0.90", "exps/c3/PREREGISTRATION.md"); add("c3_gate_diff", "0.10", "exps/c3/PREREGISTRATION.md")
    add("eq_margin", "0.10", "exps/c2_confirm/PREREGISTRATION.md"); add("cli_version", "2.1.317", "loop/STEER.md"); add("cli_version_c3", "2.1.318", "exps/c3/PREREGISTRATION.md")
    add("c3_n_dup", str(len(j("exps/c3/duplicates_of_used.json"))), "exps/c3/duplicates_of_used.json")
    add("lvl95", "95\\%", "exps/c2_confirm/PREREGISTRATION.md"); add("lvl90", "90\\%", "exps/c2_confirm/PREREGISTRATION.md")
    # ledger and cost
    rows = [r for r in csv.DictReader(open("results/hypothesis_ledger.csv"))]
    add("ledger_total", str(len(rows)), "results/hypothesis_ledger.csv")
    cost = [r for r in csv.reader(open("results/cost_ledger.csv")) if r and r[0] == "TOTAL_SUBJECTS"][0]
    add("cost_subjects", f"{float(cost[5]):.0f}", "results/cost_ledger.csv")
    json.dump(C, open("results/claims.json", "w"), indent=1, sort_keys=True)
    with open("paper/results.tex", "w") as f:
        f.write("% generated by analysis/make_claims.py\n")
        for k, v in sorted(C.items()):
            f.write(f"\\expandafter\\def\\csname res@{k}\\endcsname{{{v['value']}}}\n")
    print(len(C), "claims")


if __name__ == "__main__":
    main()
