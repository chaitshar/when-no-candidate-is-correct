# C3 pool lock

- Date (UTC): Wed Nov  4 08:28:55 UTC 2026
- Commit of banks/matharena_pools.py: 412f29761f17919f5d878299acc6c075311bdba9
- pools.json sha256: c471650bbe5fea9078f6d892ef2672280f54ba231bbafca87d133383e18c544b

## Code run

```python
import json, os, sys
sys.path.insert(0, "banks"); os.environ["MA_ALL_MODELS"] = "1"
import matharena_pools as M
used = set(p["pid"] for p in json.load(open("exps/screens/s1_lineup/pools.json"))) | set(p["pid"] for p in json.load(open("exps/c2_confirm/pools.json")))
comps = ["smt_2025","cmimc_2025","brumo_2025","apex_2025","hmmt_nov_2025","arxivmath-0626","arxivmath-1225","arxivmath-0126","arxivmath-0226","arxivmath-0326","arxivmath-0426","arxivmath-0526","apex-shortlist"]
P = [p for p in M.build(comps) if p["pid"] not in used]
json.dump(P, open("banks/locked_c3/pools.json", "w"))
from collections import Counter
print(Counter((p["comp"], p["kind"]) for p in P)); print("TA", sum(p["kind"]=="TA" for p in P), "excluded_used", len(used))
```

## Printed counts

```
Counter({('arxivmath-0426', 'TA'): 38, ('arxivmath-0526', 'TA'): 37, ('arxivmath-0526', 'TP'): 36, ('arxivmath-0426', 'TP'): 34, ('apex-shortlist', 'TA'): 33, ('apex-shortlist', 'TP'): 33, ('arxivmath-0226', 'TA'): 28, ('smt_2025', 'TA'): 26, ('arxivmath-0226', 'TP'): 26, ('smt_2025', 'TP'): 25, ('arxivmath-0326', 'TA'): 25, ('arxivmath-0326', 'TP'): 22, ('arxivmath-0126', 'TA'): 20, ('arxivmath-0126', 'TP'): 19, ('arxivmath-0626', 'TA'): 18, ('brumo_2025', 'TA'): 17, ('brumo_2025', 'TP'): 17, ('arxivmath-0626', 'TP'): 17, ('cmimc_2025', 'TA'): 16, ('cmimc_2025', 'TP'): 16, ('arxivmath-1225', 'TA'): 14, ('arxivmath-1225', 'TP'): 14, ('hmmt_nov_2025', 'TA'): 5, ('hmmt_nov_2025', 'TP'): 5, ('apex_2025', 'TA'): 1, ('apex_2025', 'TP'): 1})
TA 278 excluded_used 163
```

Built by an independent agent; contents not shown to the PI. Excludes every problem used in screens S1 to S9 or C2.
