"""C3 gemma-4-e4b descriptive analysis (amendment A3, written before any gemma call)."""
import json, os, sys, glob, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
TA = {p["pid"]: p for p in json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json"))) if p["kind"] == "TA"}
st = json.load(open(os.path.join(HERE, "strata.json"))); sel = json.load(open(os.path.join(HERE, "gemma_selected.json")))
R = {json.load(open(f))["id"]: json.load(open(f)) for f in glob.glob(os.path.join(HERE, "raw/open/gemma-4-e4b/*.json"))}
M = "gemma-4-e4b"; out = {"n_records": len(R)}
n_iso = ok_iso = 0; wrong = []; d = {"SOLVED": [], "UNSOLVED": []}; h = {"SOLVED": [], "UNSOLVED": []}; pf = {"PICK": 0, "FORCED": 0}
for pid in sel:
    p = TA[pid]; v = []
    for c in p["cands"]:
        r = R.get(f"{M}__ISO__{c['cid']}"); x = parse.verdict(r["result"]) if r else None
        if r: n_iso += 1; ok_iso += x is not None
        if x is not None: wrong.append(int(x))
        v.append(x)
    rp = R.get(f"{M}__PICK__{p['pool']}"); rf = R.get(f"{M}__FORCED__{p['pool']}")
    k = parse.choice(rp["result"], 3) if rp else None; kf = parse.choice(rf["result"], 3) if rf else None
    if rp and k is None: pf["PICK"] += 1
    if rf and not kf: pf["FORCED"] += 1
    s = st["stratum"][pid]
    if k is not None and all(x is not None for x in v): d[s].append(int(k > 0) - int(any(v)))
    if kf and all(x is not None for x in v): h[s].append(int(v[kf - 1]) - sum(int(v[j]) for j in range(3) if j != kf - 1) / 2)
def m(xs, seed):
    if not xs: return None
    rng = random.Random(seed); bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(5000))
    return {"n": len(xs), "mean": sum(xs) / len(xs), "ci95": [bs[125], bs[4874]]}
out.update({"iso_parse": ok_iso / n_iso if n_iso else None, "iso_acc_wrong": sum(wrong) / len(wrong) if wrong else None,
            "pick_unparsed": pf["PICK"], "forced_unparsed": pf["FORCED"],
            "d": {s: m(x, 1) for s, x in d.items()}, "h": {s: m(x, 2) for s, x in h.items()},
            "note": "descriptive only; strata defined by claude-haiku-5-5; no gate for interpretation, the C3 gate quantities are reported"})
json.dump(out, open(os.path.join(HERE, "results_gemma.json"), "w"), indent=1); print(json.dumps(out, indent=1))
