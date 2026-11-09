#!/bin/bash
# S25: Qwen3.8-27B veto on the pre-veto releases (Ollama only). Check-after-write lock, Idle priority.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_OLLAMA_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt
ME="vkg-main s25-veto $$"
while true; do
  while [ -e $LOCK ]; do sleep 120; done
  sleep $((RANDOM % 20 + 5))
  [ -e $LOCK ] && continue
  echo "$ME $(date +%H:%M) expected-end $(date -d '+120 min' +%H:%M)" > $LOCK
  sleep 15
  grep -q "^$ME " $LOCK && break
done
echo "lock taken $(date)"
cleanup() {
  for m in phi4 qwen3.8-27b; do curl -s -m 60 localhost:11535/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done
  grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
python -B results/runs/s25/veto27.py ask || { echo "ask FAILED"; exit 1; }
echo S25_ASK_DONE $(date)
