#!/bin/bash
# S42 E7 (reader checks on candidate quotes; argument: dev or test): one GPU job at a time under the shared lock. Stage A: 4B + embedding server (cap 0.65) for evidence and readers.
# No Phi-4 stage. Headroom gate and check-after-write lock.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt; ME="vkg-main s43 $$"; MODE=${1:-dev}; R=results/runs/s43
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 24 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { killport 18000; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
HAVE=0; trap '[ $HAVE = 1 ] && cleanup' EXIT
echo "--- S43 $(date)"
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
HAVE=1; echo "lock taken $(date)"
startpod() { VKG_MEM_FRAC=0.65 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> $R/podgen.log 2>&1 &
  for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done; sleep 20; }
if [ ! -e $R/s43_out.json ]; then
  startpod
  python -B $R/s43_run.py &
  VP=$!
  while kill -0 $VP 2>/dev/null; do
    netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" || { echo "4B server gone, restarting $(date +%H:%M)"; startpod; }
    sleep 30
  done
  wait $VP || { echo "S43 FAILED $(date)"; exit 1; }
  killport 18000; sleep 10
fi
echo "S43_DONE $(date)"
