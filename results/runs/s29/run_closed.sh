#!/bin/bash
# After the sealed chunks: closed-book B0/B1 generation (headroom gate + lock, like run_s29.sh).
cd "/f/Projects/AI hallucinations"
until grep -qE 'S29_ALL_CHUNKS_DONE|FAILED|stopped early' results/runs/s29/chain_chunks.log; do sleep 300; done
grep -q S29_ALL_CHUNKS_DONE results/runs/s29/chain_chunks.log || { echo "chain did not finish; closed-book not run"; exit 1; }
LOCK=results/gpu_lock.txt; ME="vkg-main s29-closed $$"
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 10 ]; }
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 120; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
trap 'killport 18000; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK' EXIT
VKG_MEM_FRAC=0.68 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s29/podgen.log 2>&1 &
for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done; sleep 20
python -B results/runs/s29/s29_closed.py && echo CLOSED_DONE
