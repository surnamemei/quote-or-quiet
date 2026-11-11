#!/bin/bash
# S65 G14: drafts of three models, candidates, 27B judge, grading, sheets; after S58 finishes; under the shared GPU lock.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 OLLAMA_HOST_URL=http://127.0.0.1:11540
LOCK=results/gpu_lock.txt; ME="vkg-main g14 $$"; R=results/runs/s65
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 24 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { killport 18000; curl -s -m 30 localhost:11540/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; curl -s -m 30 localhost:11540/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null; killport 11540; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
start_ollama() { if ! netstat -ano | grep -q "127.0.0.1:11540 .*LISTEN"; then powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11540'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='2'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1; for t in $(seq 1 30); do curl -s -m 3 localhost:11540/api/tags > /dev/null && break; sleep 5; done; fi; }

trap cleanup EXIT
echo "--- G14 $(date)"
until grep -qE "S58_DONE|FAILED|gave up" results/runs/s58/run_s58.log 2>/dev/null; do sleep 120; done
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
start_ollama
for m in llama3.1:8b gemma3:12b mistral-nemo:12b; do python -B $R/g14.py draft $m || { echo "G14 FAILED draft $m"; exit 1; }; done
curl -s -m 30 localhost:11540/api/generate -d '{"model":"llama3.1:8b","keep_alive":0}' > /dev/null; curl -s -m 30 localhost:11540/api/generate -d '{"model":"gemma3:12b","keep_alive":0}' > /dev/null; curl -s -m 30 localhost:11540/api/generate -d '{"model":"mistral-nemo:12b","keep_alive":0}' > /dev/null
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B $R/g14.py cands || { echo "G14 FAILED cands"; exit 1; }
for m in judge decide sheet; do python -B $R/g14.py $m || { echo "G14 FAILED $m"; exit 1; }; done
cleanup; trap - EXIT
echo "G14_DONE $(date)"
