#!/bin/bash
# S23 DEV run, variant indep on mintaka_dev, popqa_dev, dev (SimpleQA). Check-after-write lock, Idle priority, one worker.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535 S23_VARIANT=indep
LOCK=results/gpu_lock.txt
ME="vkg-main s23-dev $$"
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
  PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
  for m in phi4 qwen3.8-27b; do curl -s -m 60 localhost:11535/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done
  grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
start_podgen() {
  if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
    VKG_MEM_FRAC=0.88 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONUNBUFFERED=1 nohup venv_gpu/Scripts/python.exe -X faulthandler vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s23/podgen.log 2>&1 &
    for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
    sleep 20
    powershell -c "Get-CimInstance Win32_Process | ? { \$_.CommandLine -match 'podgen_server|s23_run' } | % { (Get-Process -Id \$_.ProcessId).PriorityClass = 'Idle' }" > /dev/null 2>&1
  fi
}
for n in mintaka_dev popqa_dev dev; do
  ok=0
  for attempt in 1 2 3; do
    start_podgen
    if python -B results/runs/s23/s23_run.py $n gen; then ok=1; break; fi
    PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; sleep 30
  done
  [ $ok = 1 ] || { echo "gen $n FAILED"; exit 1; }
done
PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
for n in mintaka_dev popqa_dev dev; do python -B results/runs/s23/s23_run.py $n phi4 || { echo "phi4 FAILED"; exit 1; }; done
for n in mintaka_dev popqa_dev dev; do python -B results/runs/s23/s23_run.py $n alias || { echo "alias FAILED"; exit 1; }; done
echo S23_DEV_DONE $(date)
