#!/usr/bin/env python3
"""C3 amendment A4 analysis (written before any A4 call): discriminability (hit minus false-choice)
for PICK, EACH and ISO, per model and haiku stratum; H4 and H5."""
import json, os, sys, glob, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
B = 10000
pools = json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json")))
TA = {p["pid"]: p for p in pools if p["kind"] == "TA"}; TP = {p["pid"]: p for p in pools if p["kind"] == "TP"}
st = json.load(open(os.path.join(HERE, "strata.json")))
R = {}
for f in glob.glob(os.path.join(HERE, "raw/arms/*.json")) + glob.glob(os.path.join(HERE, "raw/a4/*.json")):
    r = json.load(open(f)); R[r["id"]] = r
def iso(m, cid):
    r = R.get(f"{m}__ISO__{cid}"); return None if r is None else parse.verdict(r["result"])
def boot(xs, seed):
    rng = random.Random(seed); return sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(B))
out = {}
for m in ("haiku", "sonnet"):
    rows = []
    for pid in st["selected"]:
        if pid not in TP: continue
        ta, tp = TA[pid], TP[pid]
        r = {"stratum": st["stratum"][pid]}
        vta = [iso(m, c["cid"]) for c in ta["cands"]]; vtp = [iso(m, c["cid"]) for c in tp["cands"]]
        if all(x is not None for x in vta + vtp):
            r["fa_ISO"] = int(any(vta))
            r["hit_ISO"] = int(all(v == (c["role"] == "right") for v, c in zip(vtp, tp["cands"])))
        a = R.get(f"{m}__PICK__{ta['pool']}"); b = R.get(f"{m}__PICK__{tp['pool']}")
        ka = parse.choice(a["result"], 3) if a else None; kb = parse.choice(b["result"], 3) if b else None
        if ka is not None and kb is not None:
            r["fa_PICK"] = int(ka > 0); r["hit_PICK"] = int(kb > 0 and tp["cands"][kb - 1]["role"] == "right")
        a = R.get(f"{m}__EACH__{ta['pool']}"); b = R.get(f"{m}__EACH__{tp['pool']}")
        ea = parse.each(a["result"], 3) if a else None; eb = parse.each(b["result"], 3) if b else None
        if ea and eb and None not in ea and None not in eb:
            r["fa_EACH"] = int(any(ea)); r["hit_EACH"] = int(all(v == (c["role"] == "right") for v, c in zip(eb, tp["cands"])))
        rows.append(r)
    res = {}
    for s in ("SOLVED", "UNSOLVED"):
        R_ = [r for r in rows if r["stratum"] == s]; d = {}
        for X in ("PICK", "EACH", "ISO"):
            xs = [r for r in R_ if f"hit_{X}" in r]
            if xs:
                h = sum(r[f"hit_{X}"] for r in xs) / len(xs); f = sum(r[f"fa_{X}"] for r in xs) / len(xs)
                d[X] = {"n": len(xs), "hit": h, "fa": f, "J": h - f, "diag_ratio": (h / f) if f else None}
        pairs = [(r["hit_PICK"] - r["fa_PICK"]) - (r["hit_ISO"] - r["fa_ISO"]) for r in R_ if "hit_PICK" in r and "hit_ISO" in r]
        if pairs:
            bs = boot(pairs, 41)
            d["J_PICK_minus_J_ISO"] = {"n": len(pairs), "mean": sum(pairs) / len(pairs), "ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]],
                                        "p_one_sided_lt0": sum(1 for x in bs if x >= 0) / B}
        hp = [r["hit_PICK"] - r["hit_ISO"] for r in R_ if "hit_PICK" in r and "hit_ISO" in r]
        if hp:
            bs = boot(hp, 43); d["hit_PICK_minus_hit_ISO"] = {"mean": sum(hp) / len(hp), "ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]]}
        fe = [r["fa_PICK"] - r["fa_EACH"] for r in R_ if "fa_PICK" in r and "fa_EACH" in r]
        if fe:
            bs = boot(fe, 42); d["fa_PICK_minus_fa_EACH"] = {"n": len(fe), "mean": sum(fe) / len(fe), "ci95": [bs[int(.025 * B)], bs[int(.975 * B) - 1]]}
        res[s] = d
    u = res.get("UNSOLVED", {}).get("J_PICK_minus_J_ISO")
    res["H4_verdict"] = None if not u else ("confirmed" if u["p_one_sided_lt0"] < 0.05 else "not confirmed")
    out[m] = res
json.dump(out, open(os.path.join(HERE, "results_a4.json"), "w"), indent=1); print(json.dumps(out, indent=1))
