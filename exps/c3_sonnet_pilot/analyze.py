import json, os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness")); import parse
out = {}
for arm in ("ISO", "PICK", "FORCED"):
    fs = glob.glob(os.path.join(HERE, f"raw/sonnet__{arm}__*.json"))
    ok = sum((parse.verdict(json.load(open(f))["result"]) is not None) if arm == "ISO" else bool(parse.choice(json.load(open(f))["result"], 3) is not None) for f in fs)
    out[arm] = {"n": len(fs), "parsed": ok, "rate": ok / len(fs) if fs else None, "cost": round(sum(json.load(open(f)).get("cost") or 0 for f in fs), 3)}
out["passed"] = all(v["rate"] is not None and v["rate"] >= 0.95 for v in out.values() if isinstance(v, dict))
json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1); print(out)
