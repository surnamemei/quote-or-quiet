#!/bin/bash
# L3 conditional-truth judge on DEV items: waits for the GPU lock to be free and 22 GiB VRAM, takes the lock, judges, unloads.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_OLLAMA_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt
while [ -e $LOCK ]; do sleep 120; done
until [ "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)" -ge 22000 ]; do sleep 120; done
echo "vkg-main l3-cj2 $(date +%H:%M) expected-end $(date -d '+30 min' +%H:%M)" > $LOCK
trap 'curl -s -m 60 127.0.0.1:11535/api/generate -d "{\"model\":\"qwen3.8-27b:latest\",\"keep_alive\":0}" > /dev/null; grep -q "^vkg-main l3-cj2" $LOCK 2>/dev/null && rm -f $LOCK' EXIT
echo "lock taken $(date)"
python -B results/runs/l3/cj_judge2.py "$1"
echo CJ_DONE $(date)
