#!/bin/bash
# S66 G15: stress test of the Quote or Quiet service, after G14; under the shared GPU lock (the service is started here without its own lock check).
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 OLLAMA_HOST_URL=http://127.0.0.1:11540
LOCK=results/gpu_lock.txt; ME="vkg-main g15 $$"; R=results/runs/s66
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 24 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { killport 18000; curl -s -m 30 localhost:11540/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; curl -s -m 30 localhost:11540/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null; killport 11540; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
start_ollama() { if ! netstat -ano | grep -q "127.0.0.1:11540 .*LISTEN"; then powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11540'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='2'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1; for t in $(seq 1 30); do curl -s -m 3 localhost:11540/api/tags > /dev/null && break; sleep 5; done; fi; }

echo "--- G15 $(date)"
until grep -qE "G14_DONE|G14 FAILED" results/runs/s65/run_g14.log 2>/dev/null; do sleep 120; done
until grep -qE "S58_DONE|FAILED" results/runs/s58/run_s58e.log 2>/dev/null; do sleep 120; done   # G4 (S58) first
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
trap 'grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; bash tool/stop_service.sh > /dev/null 2>&1' EXIT   # lock first, so that stop_service also frees the 4B server and Ollama
# Start what the Quote or Quiet service needs, then the service itself (127.0.0.1:18100). Leaves headroom: refuses to start while another
# job holds the project GPU lock, and needs free RAM >= 16 GB and free VRAM >= 22 GB (4B server about 10 GB, capped at 45% of the card; Phi-4 about 9 GB plus its context).
if ! netstat -ano | grep -q "127.0.0.1:11540 .*LISTEN"; then
  powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11540'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='1'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1
fi
if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
  VKG_MEM_FRAC=0.45 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> tool/podgen.log 2>&1 &
  for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
fi
VKG_OLLAMA_URL=http://127.0.0.1:11540 nohup python -B tool/qoq_service.py 18100 >> tool/service.log 2>&1 &
for t in $(seq 1 30); do curl -s -m 2 localhost:18100/ > /dev/null && break; sleep 2; done
curl -s -m 2 localhost:18100/ && echo " service up on 127.0.0.1:18100"

python -B $R/g15_run.py run || { echo "G15 FAILED"; exit 1; }
echo "G15_DONE $(date)"
