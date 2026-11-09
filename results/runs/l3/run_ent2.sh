#!/bin/bash
# Goal B step 1 on DEV: lock (check-after-write), 4B server, ent_gen2.py, cleanup.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_POD_HOST=local VKG_EMB=hf
LOCK=results/gpu_lock.txt
ME="vkg-main l3-ent2 $$"
while true; do
  while [ -e $LOCK ]; do sleep 120; done
  sleep $((5 + RANDOM % 21))
  [ -e $LOCK ] && continue
  echo "$ME $(date +%H:%M) expected-end $(date -d '+40 min' +%H:%M)" > $LOCK
  sleep 15
  grep -q "^$ME " $LOCK 2>/dev/null && break
done
cleanup() {
  PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
  grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
until [ "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)" -ge 12000 ]; do sleep 60; done
VKG_MEM_FRAC=0.5 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONUNBUFFERED=1 nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/l3/podgen.log 2>&1 &
for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
sleep 20
python -B results/runs/l3/ent_gen2.py && echo ENT2_DONE $(date)
