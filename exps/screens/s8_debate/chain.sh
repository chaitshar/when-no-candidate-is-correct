#!/bin/bash
cd "$(dirname "$0")"
until grep -q FINISHED run1.log; do sleep 15; done
python3 stages.py 2 && python3 ../../../harness/run_jobs.py jobs_2.jsonl raw --par 8 > run2.log 2>&1
python3 stages.py 3 && python3 ../../../harness/run_jobs.py jobs_3.jsonl raw --par 8 > run3.log 2>&1
echo CHAIN_DONE >> run3.log
