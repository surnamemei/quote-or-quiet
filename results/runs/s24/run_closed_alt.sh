#!/bin/bash
# S23 DEV run, variant indep on mintaka_dev, popqa_dev, dev (SimpleQA). Check-after-write lock, Idle priority, one worker.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535 S24=1
LOCK=results/gpu_lock.txt
ME="vkg-main s24-alt $$"
while true; do
  while [ -e $LOCK ]; do sleep 120; done
  sleep $((RANDOM % 20 + 5))
  [ -e $LOCK ] && continue
  echo "$ME $(date +%H:%M) expected-end $(date -d '+150 min' +%H:%M)" > $LOCK
  sleep 15
  grep -q "^$ME " $LOCK && break
done
echo "lock taken $(date)"
cleanup() {
  PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
  for m in phi4 qwen3.8-27b; do curl -s -m 60 localhost:11535/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done
  grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
for SET in "$@"; do
  ok=0
  for attempt in 1 2 3; do
    if python -B results/runs/s24/closed_run_alt.py gen $SET; then ok=1; break; fi
    sleep 60
  done
  [ $ok = 1 ] || { echo "gen $SET FAILED"; exit 1; }
done
echo S24_ALT_DONE $(date)
