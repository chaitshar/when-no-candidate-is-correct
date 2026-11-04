#!/usr/bin/env python3
"""C3 job builder. usage: build.py solve | arms
solve: two SOLVE calls per TA problem of the locked pools.
arms:  ISO/PICK/FORCED jobs for problems in strata.json (written by stratify.py)."""
import json, os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../harness"))
import lineup_prompts as P
pools = json.load(open(os.path.join(HERE, "../../banks/locked_c3/pools.json")))
TA = {p["pid"]: p for p in pools if p["kind"] == "TA"}
TP = {p["pid"]: p for p in pools if p["kind"] == "TP"}
def dump(name, jobs):
    with open(os.path.join(HERE, name), "w") as f:
        for j in jobs:
            j.setdefault("model", "haiku"); j["timeout"] = 900; f.write(json.dumps(j) + "\n")
    print(name, len(jobs))
if sys.argv[1] == "a4":  # amendment A4: PICK on TP pools, EACH on TA and TP pools
    model = sys.argv[2]
    from run_jobs import SYS
    extra = {"model": model}
    if model == "sonnet":
        extra["system"] = SYS + " You have no tools and cannot run code. Reason in plain text and end with the requested final line."
    st = json.load(open(os.path.join(HERE, "strata.json")))
    pick_tp, each = [], []
    for pid in st["selected"]:
        p = TA[pid]
        each.append({"id": f"{model}__EACH__{p['pool']}", "prompt": P.each(p["problem"], p["cands"])})
        if pid in TP:
            q = TP[pid]
            pick_tp.append({"id": f"{model}__PICK__{q['pool']}", "prompt": P.pick(q["problem"], q["cands"])})
            each.append({"id": f"{model}__EACH__{q['pool']}", "prompt": P.each(q["problem"], q["cands"])})
    for L in (pick_tp, each):
        for j in L: j.update(extra)
    dump(f"jobs_a4_picktp_{model}.jsonl", pick_tp); dump(f"jobs_a4_each_{model}.jsonl", each)
    sys.exit(0)
if sys.argv[1] == "a5":  # amendment A5 (haiku only)
    st = json.load(open(os.path.join(HERE, "strata.json")))
    pc, ic, bs = [], [], []
    for pid in st["selected"]:
        p = TA[pid]
        pc.append({"id": f"haiku__PICKC__{p['pool']}", "prompt": P.pick_conf(p["problem"], p["cands"])})
        bs.append({"id": f"haiku__BASE__{p['pool']}", "prompt": P.pick_base_most(p["problem"], p["cands"])})
        for c in p["cands"]:
            ic.append({"id": f"haiku__ISOC__{c['cid']}", "prompt": P.iso_conf(p["problem"], c)})
        if pid in TP:
            q = TP[pid]
            pc.append({"id": f"haiku__PICKC__{q['pool']}", "prompt": P.pick_conf(q["problem"], q["cands"])})
            bs.append({"id": f"haiku__BASE__{q['pool']}", "prompt": P.pick_base_most(q["problem"], q["cands"])})
            r = [c for c in q["cands"] if c["role"] == "right"][0]
            ic.append({"id": f"haiku__ISOC__{r['cid']}", "prompt": P.iso_conf(q["problem"], r)})
    dump("jobs_a5_pickc.jsonl", pc); dump("jobs_a5_isoc.jsonl", ic); dump("jobs_a5_base.jsonl", bs)
    sys.exit(0)
if sys.argv[1] == "solve":
    dump("jobs_solve.jsonl", [{"id": f"haiku__SOLVE__{pid}__{k}", "prompt": P.solve(p["problem"])} for pid, p in sorted(TA.items()) for k in (0, 1)])
else:
    model = sys.argv[2] if len(sys.argv) > 2 else "haiku"
    from run_jobs import SYS
    extra = {"model": model}
    if model == "sonnet":  # amendment A1: prompt validated by exps/c3_sonnet_pilot
        extra["system"] = SYS + " You have no tools and cannot run code. Reason in plain text and end with the requested final line."
    st = json.load(open(os.path.join(HERE, "strata.json")))
    sel = [pid for pid, s in sorted(st["stratum"].items()) if pid in st["selected"]]
    iso, pick, forced = [], [], []
    for pid in sel:
        p = TA[pid]
        for c in p["cands"]:
            iso.append({"id": f"{model}__ISO__{c['cid']}", "prompt": P.iso(p["problem"], c)})
        if pid in TP:
            r = [c for c in TP[pid]["cands"] if c["role"] == "right"][0]
            iso.append({"id": f"{model}__ISO__{r['cid']}", "prompt": P.iso(p["problem"], r)})
        pick.append({"id": f"{model}__PICK__{p['pool']}", "prompt": P.pick(p["problem"], p["cands"])})
        forced.append({"id": f"{model}__FORCED__{p['pool']}", "prompt": P.forced(p["problem"], p["cands"])})
    for L in (iso, pick, forced):
        for j in L: j.update(extra)
    sfx = "" if model == "haiku" else "_" + model
    dump(f"jobs_iso{sfx}.jsonl", iso); dump(f"jobs_pick{sfx}.jsonl", pick); dump(f"jobs_forced{sfx}.jsonl", forced)
