# Locked MathArena pools

- Date (UTC): Tue Nov  3 23:05:42 UTC 2026
- Command 1: python3 banks/matharena_pools.py hmmt_feb_2026,aime_2026 banks/locked_ma/confirm_pools.json
- Command 2: python3 banks/matharena_pools.py arxivmath-0826,arxivmath-0926 banks/locked_ma/replication_pools.json
- Confirm pools (printed Counter): hmmt_feb_2026 TA=18 TP=18; aime_2026 TA=6 TP=6 (48 entries total)
- Replication pools (printed Counter): empty, TA=0 TP=0 (0 entries; file is "[]")
- Note: replication set is empty. Not locked for use until the builder's candidate filter is revisited.
- builder commit (banks/matharena_pools.py): 24e40df8d3c1ac0d1f62a44de14edf21c533ce7c
- sha256 of confirm_pools.json and replication_pools.json: see LOCK.sha256

Built by an independent agent; contents not shown to the PI.

## Replication rebuild

- Date (UTC): Tue Nov  3 23:16:01 UTC 2026
- Command: MA_ALL_MODELS=1 python3 banks/matharena_pools.py arxivmath-0826,arxivmath-0926 banks/locked_ma/replication_pools.json
- Note: MA_ALL_MODELS=1 set, so generators are all models MathArena ran on those monthly sets.
- builder commit (banks/matharena_pools.py): 412f29761f17919f5d878299acc6c075311bdba9
- Replication pools (printed Counter): arxivmath-0826 TA=47 TP=46; arxivmath-0926 TA=32 TP=30 (TA=79 TP=76 total, 155 entries)
- sha256 of replication_pools.json: c6fc1ef9c3a08452ddb71616b2c6c429eb9fc30d43897c8909e8d9d517f17519
