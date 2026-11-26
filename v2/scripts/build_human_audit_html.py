#!/usr/bin/env python3
"""Build a self-contained offline HTML/JS human audit tool for Track 1.

Pre-loads:
(a) 50 stratified random UNSOLVED TA pools (seed 2026), blinded to judge verdicts
(b) 22 grader disagreements from exps/c3/hand_checks.csv, blinded to AI decisions
(c) 20 reclassified problems from exps/c3/audit_unsolved.csv, blinded to AI strata

Exports human_audit_results.json via Download JSON button.
Pure Python 3.9 stdlib only.
"""
import csv
import json
import os
import random
import sys

C3_DIR = "/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar/exps/c3"
REPO_DIR = "/Users/chaitanya/research/mas-study/when-no-candidate-is-correct-chaitshar"
OUT_HTML = "/Users/chaitanya/research/mas-study/v2-upgrade/audit/human_audit_tool.html"

sys.path.insert(0, os.path.join(REPO_DIR, "harness"))
import parse  # noqa: E402


def stratified_sample_unsolved(ta_pools, strata, target_n=50, seed=2026):
    """Proportional stratified random sample across competitions from the 90 UNSOLVED TA pools."""
    rng = random.Random(seed)
    unsolved_pids = sorted(pid for pid in strata["selected"] if strata["stratum"][pid] == "UNSOLVED")
    by_comp = {}
    for pid in unsolved_pids:
        comp = ta_pools[pid]["comp"]
        by_comp.setdefault(comp, []).append(pid)

    total = len(unsolved_pids)
    exact = {c: (len(pids) * target_n) / total for c, pids in by_comp.items()}
    alloc = {c: int(v) for c, v in exact.items()}
    rem = target_n - sum(alloc.values())
    # Largest remainder allocation, tie-broken deterministically by competition name
    order = sorted(by_comp.keys(), key=lambda c: (-(exact[c] - alloc[c]), c))
    for c in order[:rem]:
        alloc[c] += 1

    sampled = []
    for c in sorted(by_comp.keys()):
        k = alloc[c]
        if k > 0:
            chosen = rng.sample(by_comp[c], k)
            sampled.extend(chosen)
    rng.shuffle(sampled)
    return sampled


def tail_text(text, max_chars):
    s = (text or "").strip()
    if len(s) <= max_chars:
        return s
    return "..." + s[-max_chars:]


def extract_boxed_answer(text):
    """Extract the last balanced \\boxed{...} or \\fbox{...} expression from candidate text."""
    s = text or ""
    for cmd in ("\\boxed{", "\\fbox{"):
        idx = s.rfind(cmd)
        if idx != -1:
            start = idx + len(cmd)
            depth = 1
            i = start
            while i < len(s) and depth > 0:
                if s[i] == "{":
                    depth += 1
                elif s[i] == "}":
                    depth -= 1
                i += 1
            if depth == 0:
                return s[start : i - 1].strip()
    return None


def display_candidate_answer(cand):
    """Show the candidate's actual \\boxed{} answer; do not display mangled MathArena parsed floats."""
    bx = extract_boxed_answer(cand.get("text", ""))
    if bx:
        return bx
    return "(no \\boxed{} answer in text; read reasoning tail below)"


def load_audit_payload():
    pools = json.load(open(os.path.join(REPO_DIR, "banks/locked_c3/pools.json")))
    ta = {p["pid"]: p for p in pools if p["kind"] == "TA"}
    strata = json.load(open(os.path.join(C3_DIR, "strata.json")))

    # (a) 50 stratified random UNSOLVED TA pools
    sampled_pids = stratified_sample_unsolved(ta, strata, target_n=50, seed=2026)
    sec_a = []
    for idx, pid in enumerate(sampled_pids, start=1):
        p = ta[pid]
        cands = []
        for ci, c in enumerate(p["cands"], start=1):
            cands.append({
                "index": ci,
                "answer": display_candidate_answer(c),
                "tail_reasoning": tail_text(c.get("text", ""), 400),
            })
        sec_a.append({
            "item_id": f"A_{idx:02d}_{pid}",
            "pid": pid,
            "comp": p["comp"],
            "problem": p["problem"],
            "official_answer": p["gold"],
            "candidates": cands,
        })

    # (b) 22 grader disagreements from hand_checks.csv + disagreements.csv
    disag_rows = {
        r["id"]: r
        for r in csv.DictReader(open(os.path.join(C3_DIR, "disagreements.csv")))
    }
    hand_rows = list(csv.DictReader(open(os.path.join(C3_DIR, "hand_checks.csv"))))
    sec_b = []
    for idx, hr in enumerate(hand_rows, start=1):
        rec_id = hr["id"]
        parts = rec_id.split("__")
        pid = parts[2]
        attempt = parts[3] if len(parts) > 3 else "0"
        solve_path = os.path.join(C3_DIR, "raw", "solve", f"{rec_id}.json")
        solve_obj = json.load(open(solve_path))
        dr = disag_rows.get(rec_id, {})
        p = ta[pid]
        extracted = dr.get("extracted_a") or parse.answer(solve_obj.get("result", "")) or ""
        sec_b.append({
            "item_id": f"B_{idx:02d}_{rec_id}",
            "solve_id": rec_id,
            "pid": pid,
            "attempt": attempt,
            "comp": p["comp"],
            "problem": p["problem"],
            "official_answer": p["gold"],
            "extracted_answer": extracted,
            "tail_reply": tail_text(solve_obj.get("result", ""), 600),
        })

    # (c) 20 reclassified problems from audit_unsolved.csv
    audit_rows = list(csv.DictReader(open(os.path.join(C3_DIR, "audit_unsolved.csv"))))
    sec_c = []
    for idx, ar in enumerate(audit_rows, start=1):
        pid = ar["pid"]
        p = ta[pid]
        attempts = []
        for att in ("0", "1"):
            solve_id = f"haiku__SOLVE__{pid}__{att}"
            solve_path = os.path.join(C3_DIR, "raw", "solve", f"{solve_id}.json")
            solve_obj = json.load(open(solve_path))
            res_text = solve_obj.get("result", "")
            attempts.append({
                "attempt": att,
                "extracted_answer": parse.answer(res_text) or "(unparsed)",
                "tail_reply": tail_text(res_text, 600),
            })
        sec_c.append({
            "item_id": f"C_{idx:02d}_{pid}",
            "pid": pid,
            "comp": p["comp"],
            "problem": p["problem"],
            "official_answer": p["gold"],
            "attempts": attempts,
        })

    return {
        "meta": {
            "tool": "C3 V2 Human Audit Tool (Blinded)",
            "seed_section_a": 2026,
            "counts": {
                "section_a": len(sec_a),
                "section_b": len(sec_b),
                "section_c": len(sec_c),
                "total": len(sec_a) + len(sec_b) + len(sec_c),
            },
        },
        "section_a": sec_a,
        "section_b": sec_b,
        "section_c": sec_c,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>C3 Human Audit Tool (Blinded)</title>
<style>
  :root {
    --bg: #f6f7f9;
    --card: #ffffff;
    --border: #d5dbe3;
    --text: #1c2430;
    --muted: #5a6577;
    --accent: #1d4ed8;
    --accent-soft: #e8efff;
    --ok: #15803d;
    --ok-soft: #dcfce7;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }
  header {
    position: sticky;
    top: 0;
    z-index: 20;
    background: #111827;
    color: #f9fafb;
    padding: 12px 20px;
    border-bottom: 1px solid #374151;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  header h1 {
    margin: 0;
    font-size: 17px;
    font-weight: 600;
  }
  .header-controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
  }
  .progress-pill {
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 999px;
    padding: 5px 12px;
    font-size: 13px;
    font-variant-numeric: tabular-nums;
  }
  button {
    cursor: pointer;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 7px 13px;
    font-size: 13px;
    font-weight: 500;
    background: #ffffff;
    color: var(--text);
  }
  button.primary {
    background: #2563eb;
    border-color: #2563eb;
    color: #ffffff;
  }
  button.primary:hover { background: #1d4ed8; }
  button.danger {
    background: #ffffff;
    border-color: #ef4444;
    color: #b91c1c;
  }
  .toolbar {
    max-width: 1080px;
    margin: 16px auto 0;
    padding: 0 16px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }
  .tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .tab-btn {
    background: #ffffff;
    border: 1px solid var(--border);
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
  }
  .tab-btn.active {
    background: var(--accent-soft);
    border-color: var(--accent);
    color: var(--accent);
  }
  .filter-box {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    color: var(--muted);
  }
  main {
    max-width: 1080px;
    margin: 14px auto 48px;
    padding: 0 16px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 16px;
  }
  .card.done {
    border-left: 4px solid var(--ok);
  }
  .card-head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid #eef1f5;
  }
  .badge {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    background: #eef2f7;
    color: #334155;
  }
  .badge.done-badge {
    background: var(--ok-soft);
    color: var(--ok);
  }
  .block-label {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted);
    margin: 10px 0 4px;
  }
  pre.box {
    margin: 0;
    padding: 10px 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12.5px;
    line-height: 1.45;
  }
  .gold-box {
    background: #fffbeb;
    border-color: #fde68a;
  }
  .cand-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
    gap: 10px;
    margin-top: 6px;
  }
  .cand-card {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px;
    background: #fcfdff;
  }
  .cand-title {
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .radios {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }
  .radio-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 11px;
    border: 1px solid var(--border);
    border-radius: 999px;
    font-size: 13px;
    background: #ffffff;
    cursor: pointer;
  }
  .radio-pill.selected {
    background: var(--accent-soft);
    border-color: var(--accent);
    color: var(--accent);
    font-weight: 600;
  }
  .note-input {
    width: 100%;
    margin-top: 10px;
    padding: 7px 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 13px;
    font-family: inherit;
  }
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
<style>
  /* Math display (added 26 Nov 2026). Needs an internet connection to load KaTeX; without it the raw text is shown. */
  div.box { margin: 0; padding: 10px 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; overflow-x: auto; }
  div.box.gold-box { background: #ecfdf5; border-color: #6ee7b7; }
  div.textmath { white-space: pre-wrap; word-break: break-word; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; font-size: 14px; line-height: 1.6; }
  .ans-render { font-size: 19px; line-height: 1.5; padding: 2px 0 6px; }
  .ans-render:empty { display: none; }
  .ans-raw { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11.5px; color: #64748b; white-space: pre-wrap; word-break: break-word; }
  .ans-raw::before { content: "as written: "; color: #94a3b8; }
  .katex-display { margin: 0.5em 0; overflow-x: auto; overflow-y: hidden; }
  .math-note { font-size: 12px; color: #64748b; margin: 6px 0 0; }
</style>
</head>
<body>
<header>
  <h1>C3 V2 Human Audit Tool (Blinded)</h1>
  <div class="header-controls">
    <span id="overall-progress" class="progress-pill">0 / 92 completed</span>
    <button class="primary" onclick="downloadJSON()">Download JSON</button>
    <button class="danger" onclick="resetAll()">Reset All</button>
  </div>
</header>

<div class="toolbar">
  <div class="tabs">
    <button id="tab-a" class="tab-btn active" onclick="setTab('a')">Section A: UNSOLVED Pools (<span id="prog-a">0/50</span>)</button>
    <button id="tab-b" class="tab-btn" onclick="setTab('b')">Section B: Grader Disagreements (<span id="prog-b">0/22</span>)</button>
    <button id="tab-c" class="tab-btn" onclick="setTab('c')">Section C: Reclassified Problems (<span id="prog-c">0/20</span>)</button>
  </div>
  <div class="filter-box">
    <label><input type="checkbox" id="unanswered-only" onchange="render()"> Show unanswered only</label>
  </div>
</div>

<main id="app"></main>

<script>
const AUDIT_DATA = __AUDIT_DATA_JSON__;
const STORAGE_KEY = "c3_v2_human_audit_state_v1";

const OPTIONS = {
  a: [
    "All 3 genuinely wrong",
    "Hidden equivalent right answer",
    "Broken prompt",
    "Unsure"
  ],
  b: [
    "Correct",
    "Wrong",
    "Unsure"
  ],
  c: [
    "SOLVED (both right)",
    "MIXED (one right)",
    "UNSOLVED (both wrong)",
    "Unsure"
  ]
};

let currentTab = "a";
let state = loadState();

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : { responses: {} };
  } catch (e) {
    return { responses: {} };
  }
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {}
}

function setResponse(section, itemId, verdict) {
  if (!state.responses[itemId]) state.responses[itemId] = { section: section, verdict: "", note: "" };
  state.responses[itemId].section = section;
  state.responses[itemId].verdict = verdict;
  state.responses[itemId].updated_at = new Date().toISOString();
  saveState();
  updateProgress();
  render();
}

function setNote(section, itemId, note) {
  if (!state.responses[itemId]) state.responses[itemId] = { section: section, verdict: "", note: "" };
  state.responses[itemId].section = section;
  state.responses[itemId].note = note;
  state.responses[itemId].updated_at = new Date().toISOString();
  saveState();
}

function setTab(tab) {
  currentTab = tab;
  document.getElementById("tab-a").classList.toggle("active", tab === "a");
  document.getElementById("tab-b").classList.toggle("active", tab === "b");
  document.getElementById("tab-c").classList.toggle("active", tab === "c");
  render();
}

function countSection(secKey, items) {
  let done = 0;
  for (const it of items) {
    const r = state.responses[it.item_id];
    if (r && r.verdict) done += 1;
  }
  return done;
}

function updateProgress() {
  const aDone = countSection("a", AUDIT_DATA.section_a);
  const bDone = countSection("b", AUDIT_DATA.section_b);
  const cDone = countSection("c", AUDIT_DATA.section_c);
  const aTot = AUDIT_DATA.section_a.length;
  const bTot = AUDIT_DATA.section_b.length;
  const cTot = AUDIT_DATA.section_c.length;
  const totDone = aDone + bDone + cDone;
  const totAll = aTot + bTot + cTot;
  document.getElementById("prog-a").textContent = aDone + "/" + aTot;
  document.getElementById("prog-b").textContent = bDone + "/" + bTot;
  document.getElementById("prog-c").textContent = cDone + "/" + cTot;
  document.getElementById("overall-progress").textContent = totDone + " / " + totAll + " completed";
}

// ---- Math display (added 26 Nov 2026) ----
const MATH_OPTS = {
  delimiters: [
    { left: "$$", right: "$$", display: true },
    { left: "\\[", right: "\\]", display: true },
    { left: "\\(", right: "\\)", display: false },
    { left: "$", right: "$", display: false }
  ],
  throwOnError: false,
  strict: "ignore"
};

// A text cut at the front ("...") can start in the middle of a formula. Re-open the formula so the rest pairs up.
function fixTail(str) {
  let s = String(str || "");
  if (!s.startsWith("...")) return s;
  const singles = (s.replace(/\\\$/g, "").replace(/\$\$/g, "").match(/\$/g) || []).length;
  if (singles % 2 === 1) return "...$" + s.slice(3);
  const firstClose = s.indexOf("\\)"), firstOpen = s.indexOf("\\(");
  if (firstClose !== -1 && (firstOpen === -1 || firstClose < firstOpen)) return "...\\(" + s.slice(3);
  const firstCloseD = s.indexOf("\\]"), firstOpenD = s.indexOf("\\[");
  if (firstCloseD !== -1 && (firstOpenD === -1 || firstCloseD < firstOpenD)) return "...\\[" + s.slice(3);
  return s;
}

function textBox(str) {
  return `<div class="box textmath">${esc(fixTail(str))}</div>`;
}

// An answer is shown twice: typeset, and exactly as written underneath.
function mathBox(tex, gold) {
  const raw = esc(tex);
  return `<div class="box ${gold ? "gold-box" : ""}"><div class="ans-render" data-tex="${raw}"></div><div class="ans-raw">${raw}</div></div>`;
}

function typeset() {
  if (!window.katex) return;
  document.querySelectorAll(".ans-render").forEach(el => {
    const t = (el.getAttribute("data-tex") || "").trim();
    if (!t) return;
    if (/\$|\\\(|\\\[/.test(t)) {
      el.textContent = t;
      if (window.renderMathInElement) renderMathInElement(el, MATH_OPTS);
    } else if (/[\\^_{}]/.test(t) || /^[\s0-9a-zA-Z+\-*\/().,=<>!|]{1,40}$/.test(t) && !/[a-zA-Z]{4,}/.test(t)) {
      try { katex.render(t, el, { throwOnError: false, displayMode: false, strict: "ignore" }); }
      catch (e) { el.textContent = t; }
    } else {
      el.textContent = t;
    }
  });
  if (window.renderMathInElement) {
    document.querySelectorAll(".textmath").forEach(el => { renderMathInElement(el, MATH_OPTS); renderBareBoxed(el); });
  }
}

// Solutions often end with a bare \boxed{...} outside any $...$; typeset those too.
function renderBareBoxed(el) {
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
    acceptNode: n => (n.parentElement && n.parentElement.closest(".katex")) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
  });
  const nodes = [];
  while (walker.nextNode()) { if (walker.currentNode.nodeValue.indexOf("\\boxed{") !== -1) nodes.push(walker.currentNode); }
  nodes.forEach(node => {
    const text = node.nodeValue;
    const frag = document.createDocumentFragment();
    let pos = 0;
    while (true) {
      const start = text.indexOf("\\boxed{", pos);
      if (start === -1) break;
      let depth = 0, end = -1;
      for (let i = start + 6; i < text.length; i++) {
        if (text[i] === "{") depth++;
        else if (text[i] === "}") { depth--; if (depth === 0) { end = i; break; } }
      }
      if (end === -1) break;
      frag.appendChild(document.createTextNode(text.slice(pos, start)));
      const span = document.createElement("span");
      try { katex.render(text.slice(start, end + 1), span, { throwOnError: false, strict: "ignore" }); }
      catch (e) { span.textContent = text.slice(start, end + 1); }
      frag.appendChild(span);
      pos = end + 1;
    }
    if (pos === 0) return;
    frag.appendChild(document.createTextNode(text.slice(pos)));
    node.parentNode.replaceChild(frag, node);
  });
}
window.addEventListener("load", typeset);

function esc(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderRadios(section, itemId, currentVal) {
  return OPTIONS[section].map(opt => {
    const checked = currentVal === opt;
    const cls = checked ? "radio-pill selected" : "radio-pill";
    const safeOpt = esc(opt);
    return `<label class="${cls}">
      <input type="radio" name="rad_${esc(itemId)}" value="${safeOpt}" ${checked ? "checked" : ""}
        onchange='setResponse("${section}", ${JSON.stringify(itemId)}, ${JSON.stringify(opt)})'>
      <span>${safeOpt}</span>
    </label>`;
  }).join("");
}

function render() {
  const app = document.getElementById("app");
  const filterUnanswered = document.getElementById("unanswered-only").checked;
  const items = currentTab === "a" ? AUDIT_DATA.section_a : (currentTab === "b" ? AUDIT_DATA.section_b : AUDIT_DATA.section_c);
  const visible = items.filter(it => {
    if (!filterUnanswered) return true;
    const r = state.responses[it.item_id];
    return !(r && r.verdict);
  });

  if (visible.length === 0) {
    app.innerHTML = `<div class="card"><p>No items match the current filter.</p></div>`;
    return;
  }

  let html = "";
  for (const it of visible) {
    const resp = state.responses[it.item_id] || { verdict: "", note: "" };
    const isDone = Boolean(resp.verdict);
    const doneBadge = isDone ? `<span class="badge done-badge">Recorded: ${esc(resp.verdict)}</span>` : `<span class="badge">Pending</span>`;

    let bodyHtml = "";
    if (currentTab === "a") {
      const candsHtml = it.candidates.map(c => `
        <div class="cand-card">
          <div class="cand-title">Candidate ${c.index}</div>
          <div class="block-label">Candidate Final Answer</div>
          ${mathBox(c.answer)}
          <div class="block-label">Last 400 Chars of Reasoning</div>
          ${textBox(c.tail_reasoning)}
        </div>
      `).join("");
      bodyHtml = `
        <div class="block-label">Problem</div>
        ${textBox(it.problem)}
        <div class="block-label">Official Answer</div>
        ${mathBox(it.official_answer, true)}
        <div class="block-label">3 Candidate Solutions (Blinded)</div>
        <div class="cand-grid">${candsHtml}</div>
      `;
    } else if (currentTab === "b") {
      bodyHtml = `
        <div class="block-label">Problem</div>
        ${textBox(it.problem)}
        <div class="block-label">Official Answer</div>
        ${mathBox(it.official_answer, true)}
        <div class="block-label">Extracted Subject Answer (Attempt ${esc(it.attempt)})</div>
        ${mathBox(it.extracted_answer)}
        <div class="block-label">Last 600 Chars of SOLVE Reply</div>
        ${textBox(it.tail_reply)}
      `;
    } else {
      const attHtml = it.attempts.map(a => `
        <div class="cand-card">
          <div class="cand-title">Attempt ${esc(a.attempt)}</div>
          <div class="block-label">Extracted Answer</div>
          ${mathBox(a.extracted_answer)}
          <div class="block-label">Last 600 Chars of SOLVE Reply</div>
          ${textBox(a.tail_reply)}
        </div>
      `).join("");
      bodyHtml = `
        <div class="block-label">Problem</div>
        ${textBox(it.problem)}
        <div class="block-label">Official Answer</div>
        ${mathBox(it.official_answer, true)}
        <div class="block-label">Two SOLVE Attempts (Blinded)</div>
        <div class="cand-grid">${attHtml}</div>
      `;
    }

    html += `
      <div class="card ${isDone ? "done" : ""}">
        <div class="card-head">
          <div>
            <strong>${esc(it.item_id)}</strong>
            <span class="badge">${esc(it.comp)}</span>
          </div>
          ${doneBadge}
        </div>
        ${bodyHtml}
        <div class="radios">${renderRadios(currentTab, it.item_id, resp.verdict)}</div>
        <input type="text" class="note-input" placeholder="Optional audit note..." value="${esc(resp.note)}"
          onchange='setNote("${currentTab}", ${JSON.stringify(it.item_id)}, this.value)'>
      </div>
    `;
  }
  app.innerHTML = html;
  typeset();
}

function downloadJSON() {
  const payload = {
    exported_at: new Date().toISOString(),
    meta: AUDIT_DATA.meta,
    progress: {
      section_a_done: countSection("a", AUDIT_DATA.section_a),
      section_b_done: countSection("b", AUDIT_DATA.section_b),
      section_c_done: countSection("c", AUDIT_DATA.section_c),
    },
    responses: state.responses,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "human_audit_results.json";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function resetAll() {
  if (!confirm("Clear all recorded audit answers from local browser storage?")) return;
  state = { responses: {} };
  saveState();
  updateProgress();
  render();
}

updateProgress();
render();
</script>
</body>
</html>
"""


def main():
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    payload = load_audit_payload()
    # Escape </script> inside embedded JSON if any LaTeX or text ever contains it
    raw_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__AUDIT_DATA_JSON__", raw_json)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUT_HTML} with counts={payload['meta']['counts']}")


if __name__ == "__main__":
    main()
