#!/usr/bin/env python3
"""Resumable runner for open-weight subjects through a local llama-server.

Same job format as run_jobs.py, plus optional seed, temperature, max_tokens.
Each subject sees only its prompt and a fixed system message. One file per job.

usage: run_open_jobs.py jobs.jsonl outdir --gguf MODEL.gguf [--par 4] [--port 8091]
Output records carry the model file and its sha256, so results stay traceable.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SYS = ("You are a careful scientific assistant. Follow the user's instructions "
       "exactly and output only what is asked.")


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def post(port, job):
    system = job.get("system", SYS)
    params = {"temperature": job.get("temperature", 0.7), "seed": job.get("seed", 0),
              "max_tokens": job.get("max_tokens", 256)}
    for msgs in ([{"role": "system", "content": system}, {"role": "user", "content": job["prompt"]}],
                 # Some templates (Gemma) reject a system role, so it moves into the user turn.
                 [{"role": "user", "content": system + "\n\n" + job["prompt"]}]):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
                                     json.dumps({"messages": msgs, **params}).encode(),
                                     {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=job.get("timeout", 600)) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            err = e
    raise err


def run(job, outdir, port, model, digest):
    path = os.path.join(outdir, f"{job['id']}.json")
    if os.path.exists(path):
        return "skip"
    t0 = time.time()
    try:
        d = post(port, job)
    except Exception as e:  # recorded as failed and retried on the next run
        print("FAIL", job["id"], repr(e)[:200], flush=True)
        return "fail"
    out = {"id": job["id"], "result": d["choices"][0]["message"]["content"], "rc": 0,
           "secs": round(time.time() - t0, 2), "model": model, "sha256": digest,
           "finish": d["choices"][0].get("finish_reason"), "seed": job.get("seed", 0),
           "tokens": d.get("usage")}
    with open(path + ".tmp", "w") as f:
        json.dump(out, f)
    os.replace(path + ".tmp", path)
    return "ok"


def main():
    jobs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    outdir, gguf = sys.argv[2], arg("--gguf")
    par, port = int(arg("--par", 4)), int(arg("--port", 8091))
    os.makedirs(outdir, exist_ok=True)
    h = hashlib.sha256()
    with open(gguf, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    srv = subprocess.Popen(["llama-server", "-m", gguf, "--port", str(port), "--jinja",
                            "--parallel", str(par), "-c", str(4096 * par)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(240):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
                break
            except Exception:
                time.sleep(1)
        else:
            sys.exit("llama-server did not become healthy")
        with ThreadPoolExecutor(par) as ex:
            res = list(ex.map(lambda j: run(j, outdir, port, os.path.basename(gguf), h.hexdigest()), jobs))
    finally:
        srv.terminate()
    print("FINISHED", {k: res.count(k) for k in set(res)})
    sys.exit(1 if "fail" in res else 0)


if __name__ == "__main__":
    main()
