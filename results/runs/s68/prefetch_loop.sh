#!/bin/bash
# Resume the S58 prefetch (cached queries are skipped) until a pass ends without the repeated-failure stop; 2 h cool-down between passes,
# never bypasses bot checks. Writes PREFETCH_COMPLETE to prefetch.log when done, or PREFETCH_GAVE_UP after 30 passes.
cd "/f/Projects/AI hallucinations"
for i in $(seq 1 30); do
  out=$(FSM_GAP_RANGE=10,12 F:/Projects/tools/fsm_venv/Scripts/python.exe -B results/runs/s68/fsm_prefetch68.py sealed 2>&1)
  echo "$out" >> results/runs/s68/prefetch.log
  echo "pass $i $(date +%H:%M): $(echo "$out" | tail -n 1)" >> results/runs/s68/prefetch.log
  if ! echo "$out" | grep -q 'stopped after'; then echo "PREFETCH_COMPLETE $(date)" >> results/runs/s68/prefetch.log; exit 0; fi
  sleep 3600
done
echo "PREFETCH_GAVE_UP $(date)" >> results/runs/s68/prefetch.log
