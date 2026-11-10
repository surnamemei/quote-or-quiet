#!/bin/bash
# S47 (docs/S43_LONGFORM_AND_AMBIGUITY_PLAN.md, part C): drafts and slots for 50 new subjects with Phi-4 on Ollama (11540), under the shared GPU lock.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8
LOCK=results/gpu_lock.txt; ME="vkg-main s47 $$"; R=results/runs/s47
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 10 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { killport 18000; curl -s -m 30 localhost:11540/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; curl -s -m 30 localhost:11540/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null; killport 11540; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
start_ollama() { if ! netstat -ano | grep -q "127.0.0.1:11540 .*LISTEN"; then powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11540'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='2'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1; for t in $(seq 1 30); do curl -s -m 3 localhost:11540/api/tags > /dev/null && break; sleep 5; done; fi; }

trap cleanup EXIT
echo "--- S47 $(date)"
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
start_ollama
python -B $R/lf_draft_rag.py || { echo "S47 draft FAILED"; exit 1; }
python -B $R/lf_decompose2_rag.py || { echo "S47 decompose FAILED"; exit 1; }
cleanup; trap - EXIT
echo "S47_DONE $(date)"
