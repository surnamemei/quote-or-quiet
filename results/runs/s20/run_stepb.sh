#!/bin/bash
# Step B runner: GPU lock, podgen (4B) gen, Phi-4 gen, Phi-4 parsers, unload, release lock, score.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 OLLAMA_HOST_URL=http://127.0.0.1:9
LOCK=results/gpu_lock.txt
[ -e $LOCK ] && ! grep -q "^vkg-main " $LOCK && { echo "lock held by someone else: $(cat $LOCK)"; exit 1; }
echo "vkg-main s20-stepb $(date +%H:%M) expected-end $(date -d '+60 min' +%H:%M)" > $LOCK
cleanup() {
  PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
  curl -s -m 60 localhost:11435/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null
  grep -q "^vkg-main s20-stepb" $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
  VKG_MEM_FRAC=0.65 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py \
    models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b > results/runs/s20/podgen_stepb.log 2>&1 &
  for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
fi
nice -n 19 python -B results/runs/s20/synth.py gen || { echo "gen failed"; exit 1; }
nice -n 19 python -B results/runs/s20/synth.py parse || { echo "parse failed"; exit 1; }
cleanup; trap - EXIT
echo "lock after: $(cat $LOCK 2>/dev/null)"
nice -n 19 python -B results/runs/s20/synth.py score
