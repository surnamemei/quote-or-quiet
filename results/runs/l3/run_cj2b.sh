#!/bin/bash
# L3 judge v2 on DEV then held-out items. GPU lock with check-after-write (S22 convention): wait until the lock is absent,
# sleep a random 5-25 s, write our line, re-check after 15 s; if another holder's line is there, go back to waiting.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_OLLAMA_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt
ME="vkg-main l3-cj2 $$"
while true; do
  while [ -e $LOCK ]; do sleep 120; done
  sleep $((5 + RANDOM % 21))
  [ -e $LOCK ] && continue
  echo "$ME $(date +%H:%M) expected-end $(date -d '+20 min' +%H:%M)" > $LOCK
  sleep 15
  grep -q "^$ME " $LOCK 2>/dev/null && break
done
until [ "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)" -ge 22000 ]; do sleep 60; done
trap 'curl -s -m 60 127.0.0.1:11535/api/generate -d "{\"model\":\"qwen3.8-27b:latest\",\"keep_alive\":0}" > /dev/null; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK' EXIT
echo "lock taken $(date)"
python -B results/runs/l3/cj_judge2.py results/runs/l3/cj_items_dev.jsonl
python -B results/runs/l3/cj_judge2.py results/runs/l3/cj_items_heldout.jsonl
echo CJ2_DONE $(date)
