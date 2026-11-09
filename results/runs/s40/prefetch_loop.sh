#!/bin/bash
# Resume the S40 prefetch (cached queries are skipped) until a pass ends without the repeated-failure stop; 30 min cool-down between passes,
# never bypasses bot checks. Writes PREFETCH_COMPLETE to prefetch.log when done, or PREFETCH_GAVE_UP after 16 passes.
cd "/f/Projects/AI hallucinations"
for i in $(seq 1 16); do
  out=$(F:/Projects/tools/fsm_venv/Scripts/python.exe -B results/runs/s40/fsm_prefetch40.py sealed 2>&1)
  echo "$out" >> results/runs/s40/prefetch.log
  echo "pass $i $(date +%H:%M): $(echo "$out" | tail -n 1)" >> results/runs/s40/prefetch.log
  if ! echo "$out" | grep -q 'stopped after'; then echo "PREFETCH_COMPLETE $(date)" >> results/runs/s40/prefetch.log; exit 0; fi
  sleep 1800
done
echo "PREFETCH_GAVE_UP $(date)" >> results/runs/s40/prefetch.log
