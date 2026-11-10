#!/bin/bash
# S53: the GPU stages of q_pipeline.py (judge with the 4B server, then the small judge) for one output directory, under the shared GPU lock. Usage: bash results/runs/s53/run_q.sh <outdir>
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf
OUTD=$1; LOCK=results/gpu_lock.txt; ME="vkg-main q53 $$"; R=results/runs/s53
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 20 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { killport 18000; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
trap cleanup EXIT
echo "--- Q53 $OUTD $(date)"
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
if [ ! -e $OUTD/q_judge.json ]; then
  VKG_MEM_FRAC=0.45 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> $OUTD/podgen.log 2>&1 &
  for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done; sleep 30
  python -B $R/q_pipeline.py judge $OUTD || { echo "Q53 judge FAILED"; exit 1; }
  killport 18000; sleep 8
fi
if [ ! -e $OUTD/q_small.json ]; then
  venv_gpu/Scripts/python.exe -B $R/q_pipeline.py small $OUTD || { echo "Q53 small FAILED"; exit 1; }
fi
cleanup; trap - EXIT
echo "Q53_DONE $(date)"
