#!/bin/bash
cd "$(dirname "$0")"
until grep -q FINISHED run_h.log; do sleep 20; done
cd ../s3_tournament && python3 ../../../harness/run_jobs.py jobs.jsonl raw --par 24 > run.log 2>&1
