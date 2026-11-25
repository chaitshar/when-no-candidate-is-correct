#!/usr/bin/env python3
"""Unified, resumable, append-only subject runner for Auto-Research Science Loop.

Supports subscription CLI routes (`claude_cli` and `agy`) in isolated empty
working directory `/tmp/mas_subj_cwd` using Python 3.9 stdlib only.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple


SUBJ_CWD = "/tmp/mas_subj_cwd"
VALID_ROUTES = ("claude_cli", "agy")
CLAUDE_SYSTEM_PROMPT = (
    "You have no tools and cannot run code. "
    "Reason in plain text and end with the requested final line."
)
AGY_PROMPT_PREFIX = (
    "IMPORTANT: You have no tools and must NOT call any tools or read any files. "
    "Reason in plain text only and end with the requested final line.\n\n"
)
MAX_RETRIES = 3
BACKOFF_BASE_S = 2.0
TRANSIENT_MARKERS = (
    "429",
    "rate limit",
    "rate_limit",
    "ratelimit",
    "too many requests",
    "resource_exhausted",
    "overloaded",
    "temporarily unavailable",
    "service unavailable",
    "502",
    "503",
    "504",
    "timed out",
    "timeout",
    "connection reset",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_locked_hashes(lockfile: Path) -> Tuple[bool, List[str]]:
    """Verify every sha256 line in LOCKED.sha256 relative to lockfile parent."""
    errors: List[str] = []
    if not lockfile.is_file():
        return False, [f"lockfile not found: {lockfile}"]
    base_dir = lockfile.resolve().parent
    lines = [ln.strip() for ln in lockfile.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return False, [f"lockfile is empty: {lockfile}"]
    for lineno, line in enumerate(lines, 1):
        if line.startswith("#"):
            continue
        m = re.match(r"^([0-9a-fA-F]{64})\s+\*?(.+)$", line)
        if not m:
            errors.append(f"line {lineno}: invalid sha256 manifest line")
            continue
        expected_hex, rel_path = m.group(1).lower(), m.group(2).strip()
        target = Path(rel_path) if os.path.isabs(rel_path) else (base_dir / rel_path)
        if not target.is_file():
            errors.append(f"missing file: {rel_path}")
            continue
        actual_hex = sha256_file(target)
        if actual_hex != expected_hex:
            errors.append(f"hash mismatch for {rel_path}: expected {expected_hex[:12]} got {actual_hex[:12]}")
    return len(errors) == 0, errors


def load_budget_env(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path.is_file():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def sanitize_job_id(job_id: str) -> str:
    if not job_id or "/" in job_id or "\\" in job_id or ".." in job_id:
        raise ValueError(f"unsafe job_id: {job_id!r}")
    return job_id


def load_and_validate_jobs(
    jobs_path: Path,
    default_route: Optional[str],
    default_model: Optional[str],
) -> List[Dict[str, Any]]:
    if not jobs_path.is_file():
        raise FileNotFoundError(f"jobs file not found: {jobs_path}")
    jobs: List[Dict[str, Any]] = []
    seen_ids = set()
    with jobs_path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{jobs_path}:{lineno}: invalid JSON: {exc}") from exc
            if not isinstance(rec, dict):
                raise ValueError(f"{jobs_path}:{lineno}: JSON line must be an object")
            jid = rec.get("job_id") or rec.get("id")
            if not isinstance(jid, str) or not jid.strip():
                raise ValueError(f"{jobs_path}:{lineno}: missing non-empty 'job_id' or 'id'")
            jid = sanitize_job_id(jid.strip())
            if jid in seen_ids:
                raise ValueError(f"{jobs_path}:{lineno}: duplicate job_id {jid!r}")
            seen_ids.add(jid)
            prompt = rec.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError(f"{jobs_path}:{lineno}: job {jid!r} missing non-empty 'prompt'")
            route = default_route or rec.get("route")
            if route not in VALID_ROUTES:
                raise ValueError(
                    f"{jobs_path}:{lineno}: job {jid!r} has invalid or missing route {route!r}"
                )
            model = default_model or rec.get("model")
            if not isinstance(model, str) or not model.strip():
                raise ValueError(f"{jobs_path}:{lineno}: job {jid!r} missing 'model'")
            jobs.append(
                {
                    "job_id": jid,
                    "prompt": prompt,
                    "route": route,
                    "model": model.strip(),
                    "timeout": rec.get("timeout"),
                }
            )
    if not jobs:
        raise ValueError(f"no jobs found in {jobs_path}")
    return jobs


def is_already_ok(out_path: Path) -> bool:
    if not out_path.is_file():
        return False
    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
        return isinstance(data, dict) and data.get("status") == "ok"
    except Exception:
        return False


def build_command(route: str, model: str, prompt: str) -> List[str]:
    if route == "claude_cli":
        return [
            "claude",
            "--model",
            model,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--setting-sources",
            "",
            "--strict-mcp-config",
            "--system-prompt",
            CLAUDE_SYSTEM_PROMPT,
        ]
    if route == "agy":
        return [
            "agy",
            "-p",
            AGY_PROMPT_PREFIX + prompt,
            "--model",
            model,
            "--output-format",
            "json",
        ]
    raise ValueError(f"unsupported route: {route!r}")


def _parse_json_stdout(stdout: str) -> Optional[Dict[str, Any]]:
    s = (stdout or "").strip()
    if not s:
        return None
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    for line in reversed(s.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue
    return None


def _first_int(*vals: Any) -> Optional[int]:
    for v in vals:
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            return int(v)
    return None


def _extract_fields(
    route: str,
    payload: Optional[Dict[str, Any]],
    stdout: str,
    stderr: str,
    returncode: int,
) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[int], Optional[int], Dict[str, Any], Optional[str]]:
    raw_meta: Dict[str, Any] = {"returncode": returncode}
    if stderr.strip():
        raw_meta["stderr_tail"] = stderr.strip()[-800:]

    if payload is None:
        err = f"non-JSON output (rc={returncode}): {(stdout or stderr).strip()[-400:]}"
        return None, None, None, None, None, raw_meta, err

    # Preserve metadata without duplicating large text fields if present.
    for k, v in payload.items():
        if k not in ("result", "response", "text", "output", "content"):
            raw_meta[k] = v

    text = None
    for key in ("result", "response", "text", "output", "content"):
        val = payload.get(key)
        if isinstance(val, str):
            text = val
            break

    usage = payload.get("usage")
    if not isinstance(usage, dict):
        usage = payload.get("token_usage") if isinstance(payload.get("token_usage"), dict) else {}
    stats = payload.get("stats") if isinstance(payload.get("stats"), dict) else {}
    model_usage = payload.get("modelUsage") if isinstance(payload.get("modelUsage"), dict) else {}

    model_returned = None
    for key in ("model_returned", "model", "model_id", "modelName", "model_name"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            model_returned = val.strip()
            break
    if model_returned is None and model_usage:
        keys = sorted(model_usage.keys())
        model_returned = keys[0] if len(keys) == 1 else ",".join(keys)

    mu_first = next(iter(model_usage.values()), {}) if model_usage else {}
    if not isinstance(mu_first, dict):
        mu_first = {}

    input_tokens = _first_int(
        usage.get("input_tokens"),
        usage.get("prompt_tokens"),
        usage.get("promptTokenCount"),
        stats.get("input_tokens"),
        stats.get("prompt_tokens"),
        mu_first.get("inputTokens"),
        mu_first.get("input_tokens"),
        payload.get("input_tokens"),
    )
    output_tokens = _first_int(
        usage.get("output_tokens"),
        usage.get("completion_tokens"),
        usage.get("candidatesTokenCount"),
        stats.get("output_tokens"),
        stats.get("completion_tokens"),
        mu_first.get("outputTokens"),
        mu_first.get("output_tokens"),
        payload.get("output_tokens"),
    )
    thinking_tokens = _first_int(
        usage.get("thinking_tokens"),
        usage.get("thoughts_tokens"),
        usage.get("thoughtsTokenCount"),
        usage.get("reasoning_tokens"),
        stats.get("thinking_tokens"),
        stats.get("reasoning_tokens"),
        mu_first.get("thinkingTokens"),
        mu_first.get("reasoningTokens"),
        payload.get("thinking_tokens"),
    )

    is_err = bool(payload.get("is_error")) or returncode != 0 or bool(payload.get("error"))
    if is_err:
        err_msg = payload.get("error") or payload.get("message") or text or stderr or f"returncode={returncode}"
        return model_returned, text, input_tokens, output_tokens, thinking_tokens, raw_meta, str(err_msg)[:500]
    if text is None:
        return model_returned, None, input_tokens, output_tokens, thinking_tokens, raw_meta, "missing response text"
    return model_returned, text, input_tokens, output_tokens, thinking_tokens, raw_meta, None


def _is_transient_error(err_text: str) -> bool:
    low = (err_text or "").lower()
    return any(marker in low for marker in TRANSIENT_MARKERS)


_QUOTA_RESET_RE = re.compile(
    r"resets?\s+in\s+(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?",
    re.IGNORECASE,
)


def _parse_quota_wait_seconds(err_text: str) -> Optional[int]:
    low = (err_text or "").lower()
    if "quota reached" not in low and "quota exceeded" not in low:
        return None
    m = _QUOTA_RESET_RE.search(err_text or "")
    if not m or not any(m.groups()):
        return 300
    hours = int(m.group(1) or 0)
    mins = int(m.group(2) or 0)
    secs = int(m.group(3) or 0)
    total = hours * 3600 + mins * 60 + secs
    return max(30, min(total + 30, 4 * 3600))


class QuotaGate:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._resume_at = 0.0

    def wait_if_paused(self) -> None:
        while True:
            with self._lock:
                rem = self._resume_at - time.monotonic()
            if rem <= 0:
                return
            time.sleep(min(rem, 15.0))

    def trigger_pause(self, wait_s: int, job_id: str) -> None:
        with self._lock:
            target = time.monotonic() + wait_s
            if target > self._resume_at + 5.0:
                self._resume_at = target
                print(
                    f"[QUOTA] Pausing all workers for {wait_s}s after {job_id} hit quota limit.",
                    file=sys.stderr,
                    flush=True,
                )


def execute_single_job(
    job: Dict[str, Any],
    default_timeout: int,
    quota_gate: Optional[QuotaGate] = None,
) -> Dict[str, Any]:
    job_id = job["job_id"]
    route = job["route"]
    model = job["model"]
    prompt = job["prompt"]
    timeout = int(job["timeout"] or default_timeout)
    cmd = build_command(route, model, prompt)

    t0 = time.monotonic()
    last_err: Optional[str] = None
    last_meta: Dict[str, Any] = {}
    model_returned: Optional[str] = None
    text: Optional[str] = None
    in_tok: Optional[int] = None
    out_tok: Optional[int] = None
    think_tok: Optional[int] = None

    attempt = 0
    quota_waits = 0
    max_quota_waits = 6
    while attempt <= MAX_RETRIES:
        if quota_gate is not None:
            quota_gate.wait_if_paused()
        try:
            proc = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=SUBJ_CWD,
                timeout=timeout,
            )
            payload = _parse_json_stdout(proc.stdout)
            model_returned, text, in_tok, out_tok, think_tok, last_meta, err = _extract_fields(
                route, payload, proc.stdout, proc.stderr, proc.returncode
            )
            last_meta["attempts"] = attempt + 1
            if err is None:
                return {
                    "job_id": job_id,
                    "route": route,
                    "model_requested": model,
                    "model_returned": model_returned,
                    "timestamp_utc": utc_now_iso(),
                    "duration_s": round(time.monotonic() - t0, 3),
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "thinking_tokens": think_tok,
                    "text": text,
                    "raw_meta": last_meta,
                    "status": "ok",
                    "error": None,
                }
            last_err = err
            combined = f"{err} {proc.stderr} {proc.stdout}"
            wait_s = _parse_quota_wait_seconds(combined)
            if wait_s is not None and quota_gate is not None and quota_waits < max_quota_waits:
                quota_waits += 1
                quota_gate.trigger_pause(wait_s, job_id)
                quota_gate.wait_if_paused()
                continue
            if attempt < MAX_RETRIES and _is_transient_error(combined):
                time.sleep(BACKOFF_BASE_S * (2 ** attempt))
                attempt += 1
                continue
            break
        except subprocess.TimeoutExpired as exc:
            last_err = f"timeout after {timeout}s"
            last_meta = {"attempts": attempt + 1, "timeout_s": timeout}
            if exc.stderr:
                last_meta["stderr_tail"] = str(exc.stderr)[-400:]
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE_S * (2 ** attempt))
                attempt += 1
                continue
            break
        except Exception as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            last_meta = {"attempts": attempt + 1}
            break

    return {
        "job_id": job_id,
        "route": route,
        "model_requested": model,
        "model_returned": model_returned,
        "timestamp_utc": utc_now_iso(),
        "duration_s": round(time.monotonic() - t0, 3),
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "thinking_tokens": think_tok,
        "text": text,
        "raw_meta": last_meta,
        "status": "error",
        "error": last_err or "unknown error",
    }


def write_record_and_manifest(
    out_dir: Path,
    record: Dict[str, Any],
    manifest_lock: threading.Lock,
) -> None:
    job_id = record["job_id"]
    target = out_dir / f"{job_id}.json"
    tmp = out_dir / f".{job_id}.{threading.get_ident()}.tmp"
    encoded = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tmp.write_bytes(encoded)
    os.replace(tmp, target)
    digest = sha256_bytes(encoded)
    manifest_path = out_dir / "MANIFEST.sha256"
    with manifest_lock:
        with manifest_path.open("a", encoding="utf-8") as mf:
            mf.write(f"{digest}  {target.name}\n")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Resumable, append-only subject runner for claude_cli and agy routes."
    )
    p.add_argument("--jobs", required=True, help="Path to input jobs JSONL file.")
    p.add_argument("--out", required=True, help="Output directory for per-job JSON and MANIFEST.sha256.")
    p.add_argument("--route", choices=VALID_ROUTES, default=None, help="Subject CLI route (claude_cli or agy).")
    p.add_argument("--model", default=None, help="Model ID to pass to the CLI route.")
    p.add_argument("--workers", type=int, default=4, help="Parallel worker threads (default: 4).")
    p.add_argument("--verify-hash", default=None, help="Optional path to LOCKED.sha256 to verify before running.")
    p.add_argument("--max-calls", type=int, default=None, help="Optional cap on new model calls in this run.")
    p.add_argument("--timeout", type=int, default=180, help="Per-call timeout in seconds (default: 180).")
    p.add_argument("--budget-env", default=None, help="Optional path to budget.env to enforce route mode.")
    p.add_argument("--dry-run", action="store_true", help="Validate jobs JSONL and print summary without calling models.")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.workers < 1:
        print("ERROR: --workers must be >= 1", file=sys.stderr)
        return 2
    if args.timeout < 1:
        print("ERROR: --timeout must be >= 1", file=sys.stderr)
        return 2
    if args.max_calls is not None and args.max_calls < 0:
        print("ERROR: --max-calls must be >= 0", file=sys.stderr)
        return 2

    budget_path = (
        Path(args.budget_env)
        if args.budget_env
        else Path(__file__).resolve().parent.parent / "budget.env"
    )
    budget_cfg = load_budget_env(budget_path)
    route_mode = budget_cfg.get("ROUTE_MODE", "subscription_only")
    if route_mode == "subscription_only" and args.route and args.route not in VALID_ROUTES:
        print(f"ERROR: budget.env forbids route {args.route!r} under ROUTE_MODE=subscription_only", file=sys.stderr)
        return 2

    if args.verify_hash:
        ok_hash, hash_errors = verify_locked_hashes(Path(args.verify_hash))
        if not ok_hash:
            print("ERROR: LOCKED.sha256 verification failed:", file=sys.stderr)
            for e in hash_errors:
                print(f"  * {e}", file=sys.stderr)
            return 2

    try:
        jobs = load_and_validate_jobs(Path(args.jobs), args.route, args.model)
    except Exception as exc:
        print(f"ERROR: job validation failed: {exc}", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    already_ok = 0
    pending: List[Dict[str, Any]] = []
    for job in jobs:
        if is_already_ok(out_dir / f"{job['job_id']}.json"):
            already_ok += 1
        else:
            pending.append(job)

    to_run = pending[: args.max_calls] if args.max_calls is not None else pending
    capped_count = len(pending) - len(to_run)

    if args.dry_run:
        routes_used = sorted({j["route"] for j in jobs})
        models_used = sorted({j["model"] for j in jobs})
        summary = {
            "dry_run": True,
            "jobs_file": str(args.jobs),
            "out_dir": str(out_dir),
            "total_jobs": len(jobs),
            "already_ok": already_ok,
            "pending": len(pending),
            "will_run": len(to_run),
            "capped": capped_count,
            "routes": routes_used,
            "models": models_used,
            "workers": args.workers,
            "timeout_s": args.timeout,
            "verify_hash": args.verify_hash,
            "route_mode": route_mode,
        }
        print(json.dumps(summary, indent=2))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    os.makedirs(SUBJ_CWD, exist_ok=True)
    manifest_lock = threading.Lock()
    ok_new = 0
    err_new = 0

    if not to_run:
        print(f"FINISHED total={len(jobs)} skipped_ok={already_ok} ran=0 ok=0 error=0 capped={capped_count}")
        return 0

    quota_gate = QuotaGate()
    last_done_ts = [time.monotonic()]
    watchdog_stop = threading.Event()
    stall_warn_s = 600.0

    def _stall_watchdog() -> None:
        last_warn_ts = 0.0
        while not watchdog_stop.wait(timeout=30.0):
            now = time.monotonic()
            idle_s = now - last_done_ts[0]
            if idle_s >= stall_warn_s and (now - last_warn_ts) >= stall_warn_s:
                last_warn_ts = now
                print(
                    f"[WARN] {utc_now_iso()} No call completed for {int(idle_s)}s "
                    f"(ok={ok_new}, error={err_new}, remaining={len(to_run) - ok_new - err_new})",
                    file=sys.stderr,
                    flush=True,
                )

    watchdog_thread = threading.Thread(target=_stall_watchdog, name="stall-watchdog", daemon=True)
    watchdog_thread.start()
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            future_map = {pool.submit(execute_single_job, job, args.timeout, quota_gate): job["job_id"] for job in to_run}
            for fut in as_completed(future_map):
                rec = fut.result()
                write_record_and_manifest(out_dir, rec, manifest_lock)
                last_done_ts[0] = time.monotonic()
                if rec["status"] == "ok":
                    ok_new += 1
                else:
                    err_new += 1
                    print(f"ERROR job={rec['job_id']} err={rec['error']}", file=sys.stderr)
    finally:
        watchdog_stop.set()
        watchdog_thread.join(timeout=2.0)

    print(
        f"FINISHED total={len(jobs)} skipped_ok={already_ok} ran={len(to_run)} "
        f"ok={ok_new} error={err_new} capped={capped_count}"
    )
    return 1 if err_new > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
