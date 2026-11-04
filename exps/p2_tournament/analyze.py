#!/usr/bin/env python3
"""Analysis for pilot P2 (written before data)."""
import glob, json, os, random, sys, itertools
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import parse


def auroc(pos, neg):
    if not pos or not neg:
        return None
    s = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return s / (len(pos) * len(neg))


def main():
    pools = json.load(open(os.path.join(HERE, "../p1_lineup_math/pools.json")))
    recs = {json.load(open(f))["id"]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, "raw/*.json"))}
    out, lines = {}, []
    for m in sorted({k.split("__")[0] for k in recs}):
        stats, fails, n, cost = {}, 0, 0, 0.0
        for p in pools:
            k = len(p["cands"])
            wins = [0] * k
            ok = True
            res = {}
            for i, j in itertools.permutations(range(k), 2):
                r = recs.get(f"{m}__PAIR__{p['pool']}__{i}{j}")
                if r is None:
                    ok = False
                    continue
                n += 1
                cost += r.get("cost") or 0
                w = parse.winner(r["result"])
                if w is None:
                    fails += 1
                    continue
                win = i if w == "A" else j
                wins[win] += 1
                res[(i, j)] = win
            if not ok:
                continue
            cons = [res.get((i, j)) is not None and res.get((i, j)) == res.get((j, i))
                    for i, j in itertools.combinations(range(k), 2)]
            top = max(wins)
            stats[p["pool"]] = {"kind": p["kind"], "pid": p["pid"], "dec": top / (2 * (k - 1)),
                                "cons": sum(cons) / len(cons), "tie": wins.count(top) > 1,
                                "winner_right": (not wins.count(top) > 1) and p["roles"][wins.index(top)] == "right"}
        ta = [v for v in stats.values() if v["kind"] == "TA"]
        tp = [v for v in stats.values() if v["kind"] == "TP"]
        pids = sorted({v["pid"] for v in stats.values()})
        rng = random.Random(0)
        def au(key, sel_pids):
            pos = [stats[f"{q}_TP"][key] for q in sel_pids if f"{q}_TP" in stats]
            neg = [stats[f"{q}_TA"][key] for q in sel_pids if f"{q}_TA" in stats]
            return auroc(pos, neg)
        res = {}
        for key in ("dec", "cons"):
            a = au(key, pids)
            bs = sorted(x for x in (au(key, [rng.choice(pids) for _ in pids]) for _ in range(2000)) if x is not None)
            res[key] = {"auroc": a, "ci": [bs[int(.025 * len(bs))], bs[int(.975 * len(bs)) - 1]] if bs else None}
        mean = lambda xs: sum(xs) / len(xs) if xs else None
        res.update({"n_calls": n, "parse_fail": fails, "cost": cost,
                    "TA_dec": mean([v["dec"] for v in ta]), "TP_dec": mean([v["dec"] for v in tp]),
                    "TA_cons": mean([v["cons"] for v in ta]), "TP_cons": mean([v["cons"] for v in tp]),
                    "TA_tie": mean([v["tie"] for v in ta]), "TP_tie": mean([v["tie"] for v in tp]),
                    "TP_winner_right": mean([v["winner_right"] for v in tp]), "n_TA": len(ta), "n_TP": len(tp)})
        out[m] = res
        lines.append(f"== {m}: " + json.dumps(res, default=str))
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
    open(os.path.join(HERE, "results.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
