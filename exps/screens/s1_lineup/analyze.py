#!/usr/bin/env python3
"""Analysis for screen S1 (copied from P1 analyze.py before S1 data; FORCED arm and S6/S7 added). Reads raw/claude/*.json and
raw/open/<model>/*.json, writes results.json and results.txt next to this file."""
import glob
import json
import os
import random
import sys
from collections import defaultdict
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../harness"))
sys.path.insert(0, os.path.join(HERE, "../../../banks"))
import parse  # noqa: E402
from build_prm_bank import norm, sym_equal  # noqa: E402

B = 10000


def load():
    recs = {}
    for f in glob.glob(os.path.join(HERE, "raw/claude/*.json")) + glob.glob(os.path.join(HERE, "raw/open/*/*.json")):
        r = json.load(open(f))
        recs[r["id"]] = r
    return recs


def boot_ci(pairs, seed=0):
    """pairs: list of (a, b) per problem, a and b in {0,1}. CI of mean(a - b)."""
    if not pairs:
        return None, None, None
    rng = random.Random(seed)
    d = [a - b for a, b in pairs]
    m = sum(d) / len(d)
    bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(B))
    return m, bs[int(0.025 * B)], bs[int(0.975 * B) - 1]


def mcnemar(pairs):
    b = sum(1 for x, y in pairs if x == 1 and y == 0)
    c = sum(1 for x, y in pairs if x == 0 and y == 1)
    n = b + c
    if n == 0:
        return 1.0, b, c
    k = min(b, c)
    p = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p), b, c


def main():
    pools = json.load(open(os.path.join(HERE, "pools.json")))
    recs = load()
    models = sorted({k.split("__")[0] for k in recs})
    out = {"models": {}}
    lines = []
    for m in models:
        R = {k: v for k, v in recs.items() if k.startswith(m + "__")}
        res = {"n_records": len(R), "parse_fail": defaultdict(int), "n": defaultdict(int)}
        cost = defaultdict(float)
        secs = defaultdict(float)
        for k, v in R.items():
            arm = k.split("__")[1]
            cost[arm] += v.get("cost") or 0
            secs[arm] += v.get("secs") or 0
        iso = {}
        for p in pools:
            for c in p["cands"]:
                r = R.get(f"{m}__ISO__{c['cid']}")
                if r is not None and c["cid"] not in iso:
                    v = parse.verdict(r["result"])
                    res["n"]["ISO"] += 1
                    if v is None:
                        res["parse_fail"]["ISO"] += 1
                    iso[c["cid"]] = (v, c["role"])
        acc_w = [v for v, role in iso.values() if role == "wrong" and v is not None]
        acc_r = [v for v, role in iso.values() if role == "right" and v is not None]
        res["iso_accept_wrong"] = sum(acc_w) / len(acc_w) if acc_w else None
        res["iso_accept_right"] = sum(acc_r) / len(acc_r) if acc_r else None
        res["iso_parse_rate"] = 1 - res["parse_fail"]["ISO"] / res["n"]["ISO"] if res["n"]["ISO"] else None
        floor = 0.90 if m in ("haiku", "sonnet", "opus", "fable") else 0.80
        res["included"] = bool(res["iso_parse_rate"] is not None and res["iso_parse_rate"] >= floor and
                               res["iso_accept_right"] is not None and res["iso_accept_wrong"] is not None and
                               res["iso_accept_right"] - res["iso_accept_wrong"] >= 0.10)
        # per pool outcomes
        choose = defaultdict(dict)   # arm -> pool -> outcome dict
        for p in pools:
            n = len(p["cands"])
            ids = [c["cid"] for c in p["cands"]]
            iv = [iso.get(i, (None, None))[0] for i in ids]
            if all(v is not None for v in iv):
                acc = [i for i, v in enumerate(iv) if v]
                choose["ISO"][p["pool"]] = {"any": int(bool(acc)), "accepted": acc}
            for arm in ("PICK", "BASE"):
                r = R.get(f"{m}__{arm}__{p['pool']}")
                if r is None:
                    continue
                res["n"][arm] += 1
                k = parse.choice(r["result"], n)
                if k is None:
                    res["parse_fail"][arm] += 1
                    continue
                choose[arm][p["pool"]] = {"any": int(k > 0), "accepted": [k - 1] if k else []}
            r = R.get(f"{m}__FORCED__{p['pool']}")
            if r is not None:
                res["n"]["FORCED"] += 1
                k = parse.choice(r["result"], n)
                if not k:
                    res["parse_fail"]["FORCED"] += 1
                else:
                    choose["FORCED"][p["pool"]] = {"any": 1, "accepted": [k - 1]}
            r = R.get(f"{m}__EACH__{p['pool']}")
            if r is not None:
                res["n"]["EACH"] += 1
                v = parse.each(r["result"], n)
                if any(x is None for x in v):
                    res["parse_fail"]["EACH"] += 1
                else:
                    acc = [i for i, x in enumerate(v) if x]
                    choose["EACH"][p["pool"]] = {"any": int(bool(acc)), "accepted": acc}
            r = R.get(f"{m}__SEQ__{p['pool']}")
            if r is not None:
                res["n"]["SEQ"] += 1
                v = [parse.verdict(t) for t in r.get("results", [])]
                if len(v) != n or any(x is None for x in v):
                    res["parse_fail"]["SEQ"] += 1
                else:
                    acc = [i for i, x in enumerate(v) if x]
                    choose["SEQ"][p["pool"]] = {"any": int(bool(acc)), "accepted": acc,
                                                "first": acc[0] if acc else None}
        # SOLVE
        solved = {}
        for p in pools:
            if p["kind"] != "TA":
                continue
            r = R.get(f"{m}__SOLVE__{p['pid']}")
            if r is None:
                continue
            res["n"]["SOLVE"] += 1
            a = parse.answer(r["result"])
            if a is None:
                res["parse_fail"]["SOLVE"] += 1
                continue
            solved[p["pid"]] = int(norm(a) == norm(p["gold"]) or sym_equal(a, p["gold"]))
        res["solve_rate"] = sum(solved.values()) / len(solved) if solved else None
        ta = [p for p in pools if p["kind"] == "TA"]
        tp = [p for p in pools if p["kind"] == "TP"]
        res["choosing_TA"] = {}
        for arm in choose:
            xs = [choose[arm][p["pool"]]["any"] for p in ta if p["pool"] in choose[arm]]
            res["choosing_TA"][arm] = (sum(xs) / len(xs), len(xs)) if xs else None
        # TP: hit = right candidate accepted/chosen; false = any wrong accepted/chosen
        res["TP"] = {}
        for arm in choose:
            hit = fal = n = 0
            for p in tp:
                o = choose[arm].get(p["pool"])
                if o is None:
                    continue
                n += 1
                ri = p["roles"].index("right")
                hit += int(ri in o["accepted"])
                fal += int(any(p["roles"][i] == "wrong" for i in o["accepted"]))
            if n:
                res["TP"][arm] = {"hit": hit / n, "false": fal / n, "n": n}
        # contrasts on TA, paired by problem
        res["contrasts"] = {}
        for a, b in (("PICK", "ISO"), ("EACH", "ISO"), ("SEQ", "ISO"), ("BASE", "PICK"), ("PICK", "EACH"),
                     ("BASE", "ISO"), ("SEQ", "EACH")):
            pairs = [(choose[a][p["pool"]]["any"], choose[b][p["pool"]]["any"]) for p in ta
                     if p["pool"] in choose.get(a, {}) and p["pool"] in choose.get(b, {})]
            mean, lo, hi = boot_ci(pairs)
            pm, nb, nc = mcnemar(pairs)
            res["contrasts"][f"{a}-{b}"] = {"diff": mean, "ci": [lo, hi], "n": len(pairs),
                                           "mcnemar_p": pm, "a_only": nb, "b_only": nc}
        # F5: choosing by solved
        res["by_solved"] = {}
        for arm in ("ISO", "PICK", "EACH", "SEQ"):
            for s in (0, 1):
                xs = [choose[arm][p["pool"]]["any"] for p in ta
                      if p["pool"] in choose.get(arm, {}) and solved.get(p["pid"]) == s]
                res["by_solved"][f"{arm}_solved{s}"] = (sum(xs) / len(xs), len(xs)) if xs else None
        picked, unpicked = [], []
        s6pairs = []
        for p in ta:
            o = choose.get("FORCED", {}).get(p["pool"])
            ids = [c["cid"] for c in p["cands"]]
            if o is None or any(iso.get(i, (None,))[0] is None for i in ids):
                continue
            k = o["accepted"][0]
            a_p = int(iso[ids[k]][0])
            a_u = [int(iso[ids[j]][0]) for j in range(len(ids)) if j != k]
            picked.append(a_p); unpicked += a_u
            s6pairs.append(a_p - sum(a_u) / len(a_u))
        rng = random.Random(6)
        if s6pairs:
            bs = sorted(sum(rng.choice(s6pairs) for _ in s6pairs) / len(s6pairs) for _ in range(B))
            res["S6"] = {"iso_accept_picked": sum(picked) / len(picked), "iso_accept_unpicked": sum(unpicked) / len(unpicked),
                         "diff": sum(s6pairs) / len(s6pairs), "ci": [bs[int(.025 * B)], bs[int(.975 * B) - 1]], "n": len(s6pairs)}
        res["iso_wrong_verdicts"] = {cid: v for cid, (v, role) in iso.items() if role == "wrong" and v is not None}
        res["cost_usd"] = dict(cost)
        res["secs"] = dict(secs)
        res["parse_fail"] = dict(res["parse_fail"])
        res["n"] = dict(res["n"])
        out["models"][m] = res
        lines.append(f"== {m}: included={res['included']} iso_parse={res['iso_parse_rate']} "
                     f"iso_acc_wrong={res['iso_accept_wrong']} iso_acc_right={res['iso_accept_right']} solve={res['solve_rate']}")
        for arm, v in sorted(res["choosing_TA"].items()):
            lines.append(f"   TA choosing {arm:5s} {v}")
        for arm, v in sorted(res["TP"].items()):
            lines.append(f"   TP {arm:5s} {v}")
        for k, v in res["contrasts"].items():
            lines.append(f"   {k:10s} diff={v['diff']} ci={v['ci']} n={v['n']} mcnemar_p={v['mcnemar_p']:.4f} ({v['a_only']} vs {v['b_only']})"
                         if v["diff"] is not None else f"   {k} no data")
        for k, v in res["by_solved"].items():
            lines.append(f"   {k}: {v}")
        lines.append(f"   parse_fail={res['parse_fail']} n={res['n']}")
        lines.append(f"   cost={ {k: round(v, 3) for k, v in res['cost_usd'].items()} }")
    if "haiku" in out["models"] and "sonnet" in out["models"]:
        h, so = out["models"]["haiku"]["iso_wrong_verdicts"], out["models"]["sonnet"]["iso_wrong_verdicts"]
        common = sorted(set(h) & set(so))
        if common:
            a = [int(h[c]) for c in common]; b = [int(so[c]) for c in common]
            n11 = sum(x and y for x, y in zip(a, b)); n10 = sum(x and not y for x, y in zip(a, b))
            n01 = sum(y and not x for x, y in zip(a, b)); n00 = len(a) - n11 - n10 - n01
            den = ((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00)) ** 0.5
            out["S7"] = {"n": len(common), "n11": n11, "n10": n10, "n01": n01, "n00": n00,
                         "phi": (n11 * n00 - n10 * n01) / den if den else None}
            lines.append(f"S7 {out['S7']}")
    for m in out["models"]:
        out["models"][m].pop("iso_wrong_verdicts", None)
        if "S6" in out["models"][m]:
            lines.append(f"S6 {m} {out['models'][m]['S6']}")
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
    open(os.path.join(HERE, "results.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
