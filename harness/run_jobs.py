#!/usr/bin/env python3
"""Parallel, resumable runner for isolated headless Claude subject calls.

Adapted from corpus/09-autoresearch/harness/run_jobs.py.

Each job is one JSONL line:
  {"id": "...", "prompt": "..." | "turns": ["...", "..."], "model": "haiku",
   "system": "...", "timeout": 300}

Isolation: no user settings (--setting-sources ""), no MCP (--strict-mcp-config),
no tools (--tools ""), fixed system prompt, cwd is an empty directory. A subject
therefore sees only its prompt. A job with "turns" is a genuine multi-turn
conversation: the first turn starts a session, every later turn resumes it, so the
subject answers turn k before it has seen turn k+1.

Outputs: <outdir>/<id>.json with {"id","result" or "results","rc","secs","model_used","cost"}.
Jobs whose output exists are skipped, so a crashed run resumes.

usage: run_jobs.py jobs.jsonl outdir [--par 12] [--max-usd X]

--max-usd (added 2026-11-04): spending cap for this jobs file, counting the cost of outputs that
already exist for its job ids plus every new call; once reached, no new job starts (jobs in flight
finish, so the cap can be exceeded by at most par in-flight calls). Capped jobs are reported.
"""
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

SYS = ("You are a careful scientific assistant. Follow the user's instructions "
       "exactly and output only what is asked.")
CWD = "/tmp/subject_cwd"


def call(prompt, model, system, timeout, resume=None, persist=False):
    cmd = ["claude", "-p", "--model", model, "--setting-sources", "", "--strict-mcp-config",
           "--output-format", "json", "--system-prompt", system, "--tools", ""]
    if not persist:
        cmd.append("--no-session-persistence")
    if resume:
        cmd += ["--resume", resume]
    p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout, cwd=CWD)
    try:
        d = json.loads(p.stdout)
    except Exception:
        return p.returncode or 1, {"result": (p.stdout + p.stderr)[-800:]}
    if d.get("is_error"):
        return 2, d
    return p.returncode, d


SPENT = [0.0]
CAP = [None]
LOCK = threading.Lock()


def run(job, outdir):
    path = os.path.join(outdir, f"{job['id']}.json")
    if os.path.exists(path):
        return job["id"], "skip"
    with LOCK:
        if CAP[0] is not None and SPENT[0] >= CAP[0]:
            return job["id"], "CAPPED"
    model, system, to = job.get("model", "haiku"), job.get("system", SYS), job.get("timeout", 300)
    t0 = time.time()
    out = {"id": job["id"]}
    try:
        if "turns" in job:
            sid, results, cost, used = None, [], 0.0, set()
            for k, turn in enumerate(job["turns"]):
                rc, d = call(turn, model, system, to, resume=sid, persist=True)
                if rc:
                    raise RuntimeError(str(d.get("result"))[:300])
                sid = d.get("session_id")
                results.append(d.get("result"))
                cost += d.get("total_cost_usd") or 0
                used |= set((d.get("modelUsage") or {}).keys())
                stop = job.get("stop_regex")
                if stop:
                    import re
                    if re.search(stop, d.get("result") or "", re.I):
                        break
            out.update(results=results, rc=0, cost=round(cost, 6), model_used=sorted(used))
        else:
            rc, d = call(job["prompt"], model, system, to)
            if rc:
                raise RuntimeError(str(d.get("result"))[:300])
            out.update(result=d.get("result"), rc=0, cost=d.get("total_cost_usd"),
                       model_used=sorted((d.get("modelUsage") or {}).keys()), usage=d.get("usage"),
                       duration_api_ms=d.get("duration_api_ms"))
    except subprocess.TimeoutExpired:
        return job["id"], "TIMEOUT"
    except Exception as e:
        return job["id"], f"ERR {e}"[:200]
    out["secs"] = round(time.time() - t0, 1)
    with LOCK:
        SPENT[0] += out.get("cost") or 0
    with open(path + ".tmp", "w") as f:
        json.dump(out, f)
    os.replace(path + ".tmp", path)
    return job["id"], 0


def main():
    jobs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    outdir = sys.argv[2]
    par = int(sys.argv[sys.argv.index("--par") + 1]) if "--par" in sys.argv else 12
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(CWD, exist_ok=True)
    if "--max-usd" in sys.argv:
        CAP[0] = float(sys.argv[sys.argv.index("--max-usd") + 1])
        for j in jobs:
            f = os.path.join(outdir, f"{j['id']}.json")
            if os.path.exists(f):
                try:
                    SPENT[0] += json.load(open(f)).get("cost") or 0
                except Exception:
                    pass
        print(f"cap {CAP[0]} USD, already spent on this file {SPENT[0]:.2f}", flush=True)
    done = fail = 0
    with ThreadPoolExecutor(par) as ex:
        futs = [ex.submit(run, j, outdir) for j in jobs]
        for f in as_completed(futs):
            jid, rc = f.result()
            if rc in (0, "skip"):
                done += 1
            else:
                fail += 1
                print("FAIL", jid, rc, flush=True)
            if (done + fail) % 50 == 0:
                print(f"{done + fail}/{len(jobs)} done={done} fail={fail}", flush=True)
    print(f"FINISHED {done}/{len(jobs)} fail={fail} spent={SPENT[0]:.2f}", flush=True)


if __name__ == "__main__":
    main()
