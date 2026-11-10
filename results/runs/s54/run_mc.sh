#!/bin/bash
# S51: train the small quote-sufficiency judge under the shared GPU lock (no 4B server needed).
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8
LOCK=results/gpu_lock.txt; ME="vkg-main mc54 $$"; R=results/runs/s54
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 20 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }

cleanup() { grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
trap cleanup EXIT
echo "--- MC54 $(date)"
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
venv_gpu/Scripts/python.exe -I -B $R/minicheck_eval.py || { echo "MC54 FAILED"; exit 1; }
cleanup; trap - EXIT
echo "MC54_DONE $(date)"
