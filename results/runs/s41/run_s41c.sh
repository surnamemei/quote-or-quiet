#!/bin/bash
# S41 third attempt (first: GPU out of memory at cap 0.45; second: localhost connection reset at 09:55 while a network tool changed socket settings).
# The reader step now checkpoints every 120 prompts and retries; this script restarts the 4B server if it is gone.
# GPU only for the evidence and readers steps (4B + embedding server, cap 0.65 as in S19), then the server is stopped and the lock released;
# Phi-4 runs on a CPU-only Ollama at idle priority. Headroom gate and check-after-write lock as before.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt; ME="vkg-main s41 $$"; L=results/runs/s41/run_s41.log
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 24 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
freegpu() { killport 18000; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
cleanup() { freegpu; curl -s -m 30 localhost:11535/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; killport 11535; }
trap cleanup EXIT
echo "--- attempt 3 $(date)"
startpod() { VKG_MEM_FRAC=0.65 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s41/podgen.log 2>&1 &
  for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done; sleep 20; }
if [ ! -e results/runs/s41/readers.json ]; then
  while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 120; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
  echo "lock taken $(date)"; startpod
fi
killport 11535; sleep 3
powershell -c "\$env:CUDA_VISIBLE_DEVICES='-1'; \$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11535'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='1'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; \$p = Start-Process -PassThru -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'; \$p.PriorityClass = 'Idle'" > /dev/null 2>&1
for t in $(seq 1 30); do curl -s -m 3 localhost:11535/api/tags > /dev/null && break; sleep 5; done
python -B results/runs/s41/lf_verify.py &
VP=$!
while kill -0 $VP 2>/dev/null && [ ! -e results/runs/s41/readers.json ]; do
  netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" || { echo "4B server gone, restarting $(date +%H:%M)"; startpod; }
  sleep 30
done
freegpu; echo "4B server stopped, GPU lock released $(date +%H:%M)"
wait $VP && echo "S41_DONE $(date)" || echo "verify FAILED $(date)"
