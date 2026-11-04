#!/usr/bin/env python3
"""C1 frozen analysis. Reads raw/*.json; writes results.json, results.txt."""
import glob, json, os, random, sys, itertools
from collections import defaultdict
from math import comb
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import parse
B = 4000


def cp_upper(k, n, alpha=0.05):
    """One-sided exact upper bound for a binomial proportion."""
    if n == 0:
        return None
    if k == n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        tail = sum(comb(n, i) * mid ** i * (1 - mid) ** (n - i) for i in range(0, k + 1))
        lo, hi = (mid, hi) if tail > alpha else (lo, mid)
    return hi


def binom_p_below(k, n, p0):
    """P-value for H0: rate >= p0 against rate < p0 (exact)."""
    return sum(comb(n, i) * p0 ** i * (1 - p0) ** (n - i) for i in range(0, k + 1))


def auroc(pos, neg):
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def main():
    pools = json.load(open(os.path.join(HERE, "pools.json")))
    recs = {}
    for f in glob.glob(os.path.join(HERE, "raw/*.json")):
        r = json.load(open(f))
        recs[r["id"]] = r
    out, lines, pvals = {}, [], []
    for m in ("haiku", "sonnet", "opus"):
        for st in ("conf", "repl"):
            P_ = [p for p in pools if p["set"] == st]
            res = {"fail": defaultdict(int), "n": defaultdict(int), "cost": defaultdict(float), "secs": defaultdict(float),
                   "tokens_out": defaultdict(int)}
            def get(key, arm):
                r = recs.get(key)
                if r is not None:
                    res["n"][arm] += 1
                    res["cost"][arm] += r.get("cost") or 0
                    res["secs"][arm] += r.get("secs") or 0
                return r
            iso = {}
            for p in P_:
                for c in p["cands"]:
                    if c["cid"] in iso:
                        continue
                    r = get(f"{m}__ISO__{c['cid']}", "ISO")
                    if r is None:
                        continue
                    v = parse.verdict(r["result"])
                    if v is None:
                        res["fail"]["ISO"] += 1
                    iso[c["cid"]] = (v, c["role"])
            w = [v for v, ro in iso.values() if ro == "wrong" and v is not None]
            rt = [v for v, ro in iso.values() if ro == "right" and v is not None]
            res["iso_acc_wrong"] = sum(w) / len(w) if w else None
            res["iso_acc_right"] = sum(rt) / len(rt) if rt else None
            res["iso_parse"] = 1 - res["fail"]["ISO"] / res["n"]["ISO"] if res["n"]["ISO"] else None
            res["included"] = bool(res["iso_parse"] and res["iso_parse"] >= 0.9 and res["iso_acc_right"] is not None
                                   and res["iso_acc_wrong"] is not None and res["iso_acc_right"] - res["iso_acc_wrong"] >= 0.10)
            ta = [p for p in P_ if p["kind"] == "TA"]
            pick, isoany, tour = {}, {}, {}
            for p in P_:
                n = len(p["cands"])
                r = get(f"{m}__PICK__{p['pool']}", "PICK")
                if r is not None:
                    k = parse.choice(r["result"], n)
                    if k is None:
                        res["fail"]["PICK"] += 1
                    else:
                        pick[p["pool"]] = k
                iv = [iso.get(c["cid"], (None,))[0] for c in p["cands"]]
                if all(v is not None for v in iv):
                    isoany[p["pool"]] = int(any(iv))
                wins, resd, ok = [0] * n, {}, True
                for i, j in itertools.permutations(range(n), 2):
                    r = get(f"{m}__PAIR__{p['pool']}__{i}{j}", "PAIR")
                    if r is None:
                        ok = False
                        continue
                    wv = parse.winner(r["result"])
                    if wv is None:
                        res["fail"]["PAIR"] += 1
                        continue
                    win = i if wv == "A" else j
                    wins[win] += 1
                    resd[(i, j)] = win
                if ok:
                    top = max(wins)
                    cons = [resd.get((i, j)) is not None and resd.get((i, j)) == resd.get((j, i))
                            for i, j in itertools.combinations(range(n), 2)]
                    uniq = wins.count(top) == 1
                    wi = wins.index(top) if uniq else None
                    tour[p["pool"]] = {"dec": top / (2 * (n - 1)), "cons": sum(cons) / len(cons), "uniq": uniq,
                                       "winner_role": p["roles"][wi] if uniq else None,
                                       "winner_iso_rejected": (uniq and iso.get(p["cands"][wi]["cid"], (None,))[0] is False)}
            # H1
            xs = [int(pick[p["pool"]] > 0) for p in ta if p["pool"] in pick]
            k, n = sum(xs), len(xs)
            res["H1"] = {"choosing": k / n if n else None, "k": k, "n": n, "upper95": cp_upper(k, n),
                         "p": binom_p_below(k, n, 0.10) if n else None}
            # H2 TOST paired bootstrap 90% CI
            pairs = [(int(pick[p["pool"]] > 0), isoany[p["pool"]]) for p in ta if p["pool"] in pick and p["pool"] in isoany]
            rng = random.Random(1)
            d = [a - b for a, b in pairs]
            if d:
                mean = sum(d) / len(d)
                bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(B))
                lo, hi = bs[int(0.05 * B)], bs[int(0.95 * B) - 1]
                p_tost = max(sum(1 for x in bs if x >= 0.10) / B, sum(1 for x in bs if x <= -0.10) / B)
                res["H2"] = {"diff": mean, "ci90": [lo, hi], "n": len(d), "p": p_tost}
            # H3/H4
            pids = sorted({p["pid"] for p in P_ if f"{p['pid']}_TA" in tour and f"{p['pid']}_TP" in tour})
            for hname, key in (("H3", "dec"), ("H4", "cons")):
                def au(sel):
                    return auroc([tour[f"{q}_TP"][key] for q in sel], [tour[f"{q}_TA"][key] for q in sel])
                a = au(pids)
                rng = random.Random(2)
                bs = sorted(x for x in (au([rng.choice(pids) for _ in pids]) for _ in range(B)) if x is not None) if pids else []
                res[hname] = {"auroc": a, "ci95": [bs[int(.025 * len(bs))], bs[int(.975 * len(bs)) - 1]] if bs else None,
                              "n_pairs": len(pids), "p": (sum(1 for x in bs if x >= 0.75) / len(bs)) if bs else None}
            tav = [tour[p["pool"]] for p in ta if p["pool"] in tour]
            tpv = [tour[p["pool"]] for p in P_ if p["kind"] == "TP" and p["pool"] in tour]
            res["desc"] = {
                "TA_manufactured_winner_rate": sum(v["winner_iso_rejected"] for v in tav) / len(tav) if tav else None,
                "TA_unique_winner_rate": sum(v["uniq"] for v in tav) / len(tav) if tav else None,
                "TP_winner_right": sum(v["winner_role"] == "right" for v in tpv) / len(tpv) if tpv else None,
                "TP_pick_hit": (lambda L: sum(L) / len(L) if L else None)([int(pick[p["pool"]] > 0 and p["roles"][pick[p["pool"]] - 1] == "right") for p in P_ if p["kind"] == "TP" and p["pool"] in pick]),
                "ISO_TA_any_accept": (lambda L: sum(L) / len(L) if L else None)([isoany[p["pool"]] for p in ta if p["pool"] in isoany]),
            }
            for h in ("H1", "H2", "H3", "H4"):
                if st == "conf" and res.get(h) and res[h].get("p") is not None:
                    pvals.append((res[h]["p"], m, h))
            for k2 in ("fail", "n", "cost", "secs", "tokens_out"):
                res[k2] = dict(res[k2])
            out[f"{m}_{st}"] = res
    # Holm on confirmation set
    pvals.sort()
    holm, prev = {}, 0
    for i, (p, m, h) in enumerate(pvals):
        adj = max(prev, min(1.0, (len(pvals) - i) * p))
        prev = adj
        holm[f"{m}_{h}"] = adj
    out["holm"] = holm
    for m in ("haiku", "sonnet", "opus"):
        for h, thr_side in (("H1", None), ("H2", None), ("H3", None), ("H4", None)):
            c, r = out[f"{m}_conf"].get(h), out[f"{m}_repl"].get(h)
            if not c or not r:
                continue
            if h == "H1":
                same = r["choosing"] is not None and r["choosing"] < 0.10
            elif h == "H2":
                same = abs(r["diff"]) < 0.10
            else:
                same = r["auroc"] is not None and r["auroc"] < 0.75
            out.setdefault("verdicts", {})[f"{m}_{h}"] = {
                "holm_p": holm.get(f"{m}_{h}"), "confirmed": bool(holm.get(f"{m}_{h}", 1) < 0.05 and same
                                                               and out[f"{m}_conf"]["included"]),
                "replication_same_side": same}
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
    for k, v in out.items():
        lines.append(f"== {k}: {json.dumps(v, default=str)}")
    open(os.path.join(HERE, "results.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
