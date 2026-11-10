#!/bin/bash
# S41 stage 4: gate + Phi-4 only (evidence.json and readers.json exist from attempt 3).
# Why a separate stage: lf_verify.py held 36 GB of RAM (an unused embedding table loaded by an import), so a CPU Phi-4 on top of it
# would have left no free memory. The process is restarted without that table, and Phi-4 runs on the GPU under the lock
# (as in S29; about 15 GiB, minutes instead of many hours on CPU). The method is unchanged (same prompts, greedy decoding, cached calls).
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt; ME="vkg-main s41d $$"
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 24 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { curl -s -m 30 localhost:11535/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; killport 11535; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
trap cleanup EXIT
echo "--- stage 4 $(date)"
[ -e results/runs/s41/readers.json ] || { echo "verify FAILED: readers.json missing"; exit 1; }
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
killport 11535; sleep 3
powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11535'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='1'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; \$p = Start-Process -PassThru -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'; \$p.PriorityClass = 'Idle'" > /dev/null 2>&1
for t in $(seq 1 30); do curl -s -m 3 localhost:11535/api/tags > /dev/null && break; sleep 5; done
python -B results/runs/s41/lf_verify.py && echo "S41_DONE $(date)" || echo "verify FAILED $(date)"
