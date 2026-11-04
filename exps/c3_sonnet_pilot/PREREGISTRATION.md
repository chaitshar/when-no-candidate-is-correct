# Sonnet parse-rate pilot (not a hypothesis test), written 2026-11-04T08:32:43Z before any call

Why: in C2, claude-sonnet-5-5 failed the ISO parse gate (0.896); all 10 unparsed ISO replies were plain-text imitations of tool calls (bash commands) with no verdict, although no tools were available. Change tested: append to the fixed system prompt "You have no tools and cannot run code. Reason in plain text and end with the requested final line."
Items: the first 15 problems (sorted pid) of exps/screens/s1_lineup/pools.json TA pools, which sonnet never judged and which are not in C3. Arms: ISO on the 3 wrong candidates, PICK, FORCED (75 calls). Cap 12 USD (--max-usd).
Pass rule, fixed now: parse rate >= 0.95 in each of ISO, PICK and FORCED. If it passes, a sonnet repeat of C3 may be preregistered by amendment with this system prompt; if not, sonnet is not run on C3. Results are not used in any hypothesis test.
