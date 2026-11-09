#!/bin/bash
# S39 GPU jobs, queued after the S29 sealed chunks and the closed-book baselines: frozen pipeline, then the independent-retrieval variant,
# on the 1,200 S39 design questions. Headroom gate and check-after-write lock as in run_s29.sh; idle priority.
cd "/f/Projects/AI hallucinations"
until grep -qE 'CLOSED_DONE|FAILED|not run' results/runs/s29/run_closed.log 2>/dev/null && grep -q '^done design' results/runs/s39/prefetch.log; do sleep 300; done
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535 S29_SEARCH=fsm
LOCK=results/gpu_lock.txt; ME="vkg-main s39 $$"
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 10 ]; }
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 120; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { killport 18000; curl -s -m 30 localhost:11535/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; curl -s -m 30 localhost:11535/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null; killport 11535; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
trap cleanup EXIT
start_ollama() { if ! netstat -ano | grep -q "127.0.0.1:11535 .*LISTEN"; then powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11535'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='2'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1; for t in $(seq 1 30); do curl -s -m 3 localhost:11535/api/tags > /dev/null && break; sleep 5; done; fi; }
start_podgen() { if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then VKG_MEM_FRAC=0.68 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s39/podgen.log 2>&1 & for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done; sleep 20; fi; }
start_ollama
start_podgen; python -B results/runs/s39/s39_run.py s39d gen || { echo "frozen gen FAILED"; exit 1; }
killport 18000
python -B results/runs/s39/s39_run.py s39d phi4 || { echo "frozen phi4 FAILED"; exit 1; }
python -B results/runs/s39/s39_run.py s39d alias || { echo "frozen alias FAILED"; exit 1; }
curl -s -m 30 localhost:11535/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null
start_podgen; python -B results/runs/s39/s39_indep.py s39d gen || { echo "indep gen FAILED"; exit 1; }
killport 18000
python -B results/runs/s39/s39_indep.py s39d phi4 || { echo "indep phi4 FAILED"; exit 1; }
python -B results/runs/s39/s39_indep.py s39d alias || { echo "indep alias FAILED"; exit 1; }
echo S39_DONE $(date)
