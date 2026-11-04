# S0 calibration (not a hypothesis test): difficulty of program-trace tasks per model

Written 2026-11-03 ~22:40 UTC before any call. Purpose (current rule 11): find, per model, the difficulty at which the solve rate is between 0.2 and 0.8, so later screens are off the floor.

## Bank justification (rule 13)
gen/progtrace.py (committed before this file) generates random Python functions with integer state, a loop with branching modular updates, and returns a*100+b. Fresh: instances are drawn from seeds after the generator was frozen, so no instance can be in pretraining data. Hard: mental tracing of 10 to 30 dependent modular updates without tools is error prone for current models, and difficulty is tunable by loop length. Mechanism fit: candidates are wrong integers from current models' own traces, wrongness is decided by execution, and the per-iteration trace makes intermediate claims machine-checkable (needed for critique and attribution screens). Limit: synthetic code tracing is not representative of all verification tasks; claims will be scoped to this task family, with a second source sought for replication.

## Design
Calibration seeds 100000 to 100999 only (never used in later screens; later screens use seeds from 200000 up, confirmation from 500000 up). Grid: iterations in {4, 8, 12, 18, 26}, body 3, nvars 3. haiku: 16 tasks per level (80 calls). sonnet: 10 tasks per level (50 calls). One SOLVE call per task (prompt: gen question + "Work as carefully as you need to. End your reply with exactly one line: ANSWER: <integer>"). No tools.

## Output
Solve rate per level and model with Wilson 95% intervals; parse failures counted. The level chosen for each model is the one whose rate is closest to 0.5 within [0.2, 0.8]; if none, the model is declared uncalibrated on this bank. Budget: under 2 USD.
