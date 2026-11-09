#!/bin/bash
# S21 DEV feasibility: frozen S19 pipeline (vkg.s17_run, VKG_WEB=ddg) + Phi-4 veto reader on popqa_dev and mintaka_dev.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local   # judge gate checks the local GPU (as in S19); missing in the first DEV run, which waited on the dead pod
until [ -s results/runs/s21/prefetch_ddg_popqa_dev.json ] && [ -s results/runs/s21/prefetch_ddg_mintaka_dev.json ]; do sleep 120; done
echo "dev prefetch present $(date)"
LOCK=results/gpu_lock.txt
while [ -e $LOCK ] && ! grep -q "^vkg-main " $LOCK; do sleep 120; done
echo "vkg-main s21-dev $(date +%H:%M) expected-end $(date -d '+120 min' +%H:%M)" > $LOCK
cleanup() {
  PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
  for m in phi4 qwen3.8-27b; do curl -s -m 60 localhost:11435/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done
  grep -q "^vkg-main s21-dev" $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
start_podgen() {
  if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
    VKG_MEM_FRAC=0.65 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONUNBUFFERED=1 nohup venv_gpu/Scripts/python.exe -X faulthandler vkg/podgen_server.py       models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s21/podgen_dev.log 2>&1 &
    for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
    sleep 20
  fi
}
for n in popqa_dev mintaka_dev; do
  ok=0
  for attempt in 1 2 3 4; do      # stages are cached, so a retry resumes; transient embedder resets were seen in S19 too
    start_podgen
    if python -B -m vkg.s17_run $n; then ok=1; break; fi
    echo "s17_run $n attempt $attempt failed; restarting podgen" ; PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; sleep 30
  done
  [ $ok = 1 ] || { echo "s17_run $n FAILED"; exit 1; }
done
for n in popqa_dev mintaka_dev; do python -B results/runs/s21/phi4_dev.py $n || { echo "phi4 $n FAILED"; exit 1; }; done
echo S21_DEV_GENERATED $(date)
