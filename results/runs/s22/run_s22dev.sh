#!/bin/bash
# S22 DEV experiment, variants tok and pin: waits for the GPU lock, then 4B generation (wiki/combo), Phi-4, alias labels on mintaka_dev, popqa_dev.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt
while [ -e $LOCK ] && ! grep -q "^vkg-main s22" $LOCK; do sleep 120; done
echo "vkg-main s22-dev $(date +%H:%M) expected-end $(date -d '+150 min' +%H:%M)" > $LOCK
echo "lock taken $(date)"
cleanup() {
  PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
  for m in phi4 qwen3.8-27b; do curl -s -m 60 localhost:11535/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done
  grep -q "^vkg-main s22" $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
start_podgen() {
  if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
    VKG_MEM_FRAC=0.88 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONUNBUFFERED=1 nohup venv_gpu/Scripts/python.exe -X faulthandler vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s22/podgen.log 2>&1 &
    for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
    sleep 20
  fi
}
for V in tok pin; do export S22_VARIANT=$V; for n in mintaka_dev popqa_dev; do
  ok=0
  for attempt in 1 2 3; do
    start_podgen
    if python -B results/runs/s22/s22_run.py $n gen; then ok=1; break; fi
    PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; sleep 30
  done
  [ $ok = 1 ] || { echo "gen $V $n FAILED"; exit 1; }
done; done
PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
for V in tok pin; do export S22_VARIANT=$V; for n in mintaka_dev popqa_dev; do python -B results/runs/s22/s22_run.py $n phi4 || { echo "phi4 FAILED"; exit 1; }; done; done
for V in tok pin; do export S22_VARIANT=$V; for n in mintaka_dev popqa_dev; do python -B results/runs/s22/s22_run.py $n alias || { echo "alias FAILED"; exit 1; }; done; done
echo S22_DEV_DONE $(date)
