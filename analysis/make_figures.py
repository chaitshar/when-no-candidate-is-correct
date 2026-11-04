#!/usr/bin/env python3
"""Figures for the paper, drawn from experiment results.json files that analyze.py scripts
recompute from raw subject outputs. Run analysis/make_claims.py first (it re-runs the analyses).
95% intervals throughout (bootstrap over problems or Wilson, as stated in each caption)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = "paper/figures"
os.makedirs(OUT, exist_ok=True)


def j(p):
    return json.load(open(p))


def fig_lineup():
    """TA choosing rate by arm with Wilson 95% intervals: S1 (haiku) and C2 sets."""
    from math import sqrt

    def wil(p, n, z=1.96):
        d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        return (c - h) / d, (c + h) / d
    s1 = j("exps/screens/s1_lineup/results.json")["models"]["haiku"]["choosing_TA"]
    panels = [("S1 screen, haiku", {a: s1[a] for a in ("ISO", "PICK", "EACH")})]
    if os.path.exists("exps/c2_confirm/results.json"):
        c2 = j("exps/c2_confirm/results.json")
        for key, lab in (("haiku_conf", "C2 confirm, haiku"), ("haiku_repl", "C2 replication, haiku"), ("sonnet_conf", "C2 confirm, sonnet")):
            if key in c2 and "arms_TA" in c2[key]:
                panels.append((lab, c2[key]["arms_TA"]))
    fig, axes = plt.subplots(1, len(panels), figsize=(3.2 * len(panels), 2.8), sharey=True)
    if len(panels) == 1:
        axes = [axes]
    for ax, (lab, d) in zip(axes, panels):
        names = list(d)
        ps = [d[a][0] for a in names]; ns = [d[a][1] for a in names]
        lo = [p - wil(p, n)[0] for p, n in zip(ps, ns)]; hi = [wil(p, n)[1] - p for p, n in zip(ps, ns)]
        ax.bar(names, ps, yerr=[lo, hi], color=["#7a7a7a", "#3b6ea8", "#8fb3d9"][:len(names)], capsize=3)
        ax.set_title(lab, fontsize=9); ax.set_ylim(0, 1)
    axes[0].set_ylabel("target-absent pools with a wrong\ncandidate chosen or accepted")
    fig.tight_layout(); fig.savefig(f"{OUT}/lineup.pdf"); plt.close(fig)


def fig_attr():
    r = j("exps/screens/s5_whowhen/results.json"); n = j("exps/screens/s5_whowhen/results_norm.json")
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    xs, labs = [], []
    for i, m in enumerate(("haiku", "sonnet")):
        for k, sub in enumerate(("algo", "hand")):
            x = i * 3 + k
            a = r[f"{m}_{sub}"]; b = n[f"{m}_{sub}"]
            ax.errorbar(x - 0.15, a["agent_acc"], yerr=[[a["agent_acc"] - a["agent_ci"][0]], [a["agent_ci"][1] - a["agent_acc"]]], fmt="o", color="#3b6ea8", capsize=3)
            ax.errorbar(x + 0.15, a["step_acc"], yerr=[[a["step_acc"] - a["step_ci"][0]], [a["step_ci"][1] - a["step_acc"]]], fmt="s", color="#c0504d", capsize=3)
            ax.plot([x - 0.4, x], [a["baseline_majority_agent"]] * 2, color="#3b6ea8", lw=1.2, ls="--")
            ax.plot([x, x + 0.4], [a["baseline_random_step"]] * 2, color="#c0504d", lw=1.2, ls=":")
            xs.append(x); labs.append(f"{m}\n{sub}")
    ax.set_xticks(xs); ax.set_xticklabels(labs, fontsize=8); ax.set_ylim(0, 1)
    ax.set_ylabel("accuracy (strict)"); from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color="#3b6ea8", label="agent"), Line2D([], [], marker="s", ls="", color="#c0504d", label="step"),
                       Line2D([], [], ls="--", color="#3b6ea8", label="most frequent agent"), Line2D([], [], ls=":", color="#c0504d", label="random step")],
              fontsize=6, loc="upper right")
    fig.tight_layout(); fig.savefig(f"{OUT}/whowhen.pdf"); plt.close(fig)


def fig_c3():
    """C3: PICK vs ISO-any choosing rate by haiku-solvability stratum (Wilson 95%), and the
    select-then-verify inflation by stratum (bootstrap 95% CI), per model."""
    from math import sqrt
    def wil(p, n, z=1.96):
        d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        return (c - h) / d, (c + h) / d
    files = [("haiku", "exps/c3/results.json"), ("sonnet", "exps/c3/results_sonnet.json")]
    files = [(m, f) for m, f in files if os.path.exists(f)]
    if not files:
        return
    fig, axes = plt.subplots(1, 2 * len(files), figsize=(2.15 * 2 * len(files), 2.7))
    for i, (m, f) in enumerate(files):
        r = j(f); ax = axes[2 * i]
        ns = {"SOLVED": r["gate"]["n_solved"], "UNSOLVED": r["gate"]["n_unsolved"]}
        for k, (lab, key) in enumerate((("ISO-any", "iso_any"), ("PICK", "pick"))):
            xs = [0 + 0.35 * k, 1 + 0.35 * k]
            ps = [r["arms"][s_][key] for s_ in ("SOLVED", "UNSOLVED")]
            lo = [p - wil(p, ns[s_])[0] for p, s_ in zip(ps, ("SOLVED", "UNSOLVED"))]
            hi = [wil(p, ns[s_])[1] - p for p, s_ in zip(ps, ("SOLVED", "UNSOLVED"))]
            ax.bar(xs, ps, width=0.33, yerr=[lo, hi], capsize=3, color=["#7a7a7a", "#3b6ea8"][k], label=lab)
        ax.set_xticks([0.17, 1.17]); ax.set_xticklabels([f"solved\n(n={ns['SOLVED']})", f"unsolved\n(n={ns['UNSOLVED']})"], fontsize=8)
        ax.set_ylim(0, 1); ax.set_title(f"{m}: false choice", fontsize=8); ax.legend(fontsize=7)
        ax = axes[2 * i + 1]
        for k, key in enumerate(("H2s", "H2u")):
            x = r[key]; ax.errorbar(k, x["mean"], yerr=[[x["mean"] - x["ci95"][0]], [x["ci95"][1] - x["mean"]]], fmt="o", color="#c0504d", capsize=3)
        ax.axhline(0, color="#7a7a7a", lw=0.8, ls="--"); ax.set_xticks([0, 1]); ax.set_xticklabels(["solved", "unsolved"], fontsize=8)
        ax.set_xlim(-0.5, 1.5); ax.set_title(f"{m}: forced pick effect", fontsize=8)
    fig.tight_layout(); fig.savefig(f"{OUT}/c3.pdf"); plt.close(fig)


def fig_roc():
    """A5: lineup ROC from confidence for pooled picking (PICKC) and isolated verification (ISOC), haiku."""
    if not os.path.exists("exps/c3/results_a5.json"):
        return
    r = j("exps/c3/results_a5.json")["prereg"]
    fig, axes = plt.subplots(1, 2, figsize=(5.0, 2.9))
    for ax, s_ in zip(axes, ("SOLVED", "UNSOLVED")):
        x = r[s_]
        for key, lab, col, mk in (("roc_pick", "pooled pick", "#3b6ea8", "o"), ("roc_iso", "isolated", "#7a7a7a", "s")):
            pts = x[key]; ax.plot([p[0] for p in pts], [p[1] for p in pts], marker=mk, color=col, label=lab, ms=3)
        ax.plot([0, 1], [0, 1 / 3], ls="--", color="#999999", lw=0.8, label="random chooser")  # picks uniformly when it picks, so hit = false choice / 3
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_xlabel("false-choice rate (all-wrong pools)", fontsize=8)
        ax.set_title(f"haiku, {s_.lower()} (n={x['n_roc']})", fontsize=8)
    axes[0].set_ylabel("hit rate (pools with a right solution)", fontsize=8); axes[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(f"{OUT}/roc.pdf"); plt.close(fig)


if __name__ == "__main__":
    fig_roc()
    fig_c3()
    fig_lineup()
    fig_attr()
    print("figures written")
