# Failure taxonomy for subject calls (v1)

Every subject call ends in exactly one class. Counts per class, arm and model go in each experiment's results.

1. OK: parsed verdict, choice, winner or answer.
2. PARSE_MISSING: reply complete but the required final line is absent.
3. PARSE_INVALID: final line present but out of range (CHOICE 4 in a pool of 3) or malformed.
4. TRUNCATED: reply cut by a token limit (open models: finish_reason length).
5. REFUSAL: the subject declines the task.
6. TIMEOUT: the runner hit its time limit; no output file is written and the job is retried on the next run (retries counted from run logs).
7. API_ERROR: nonzero exit or an error result from the CLI; retried like TIMEOUT.
8. MULTI_TURN_BREAK: a sequential conversation that stopped before all turns.

Rules: no class is silently dropped. Primary analyses treat 2 to 5 as missing for that unit and report a sensitivity analysis in which they count against the hypothesis.
