#!/bin/bash
# S69: cross-family reviewers (Gemma 3 12B, Mistral Nemo 12B) after S68; under the shared GPU lock.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 OLLAMA_HOST_URL=http://127.0.0.1:11540
LOCK=results/gpu_lock.txt; ME="vkg-main xfam $$"; R=results/runs/s69
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 24 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { killport 18000; curl -s -m 30 localhost:11540/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; curl -s -m 30 localhost:11540/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null; killport 11540; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
start_ollama() { if ! netstat -ano | grep -q "127.0.0.1:11540 .*LISTEN"; then powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11540'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='2'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1; for t in $(seq 1 30); do curl -s -m 3 localhost:11540/api/tags > /dev/null && break; sleep 5; done; fi; }

echo "--- XFAM $(date)"
until grep -qE "S68_DONE|FAILED" results/runs/s68/run_s68.log 2>/dev/null; do sleep 120; done
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
trap cleanup EXIT   # only after the lock is ours
start_ollama
for m in gemma3:12b mistral-nemo:12b; do python -B $R/xfam.py review $m || { echo "XFAM FAILED $m"; exit 1; }; curl -s -m 30 localhost:11540/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done
python -B $R/xfam.py score || { echo "XFAM FAILED score"; exit 1; }
cleanup; trap - EXIT
echo "XFAM_DONE $(date)"
