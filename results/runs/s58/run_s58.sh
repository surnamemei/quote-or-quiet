#!/bin/bash
# S58 (docs/S58_G4_PLAN.md): after the S58 prefetch: frozen pipeline gen (six readers), then rule Q2 (candidates, 27B witness judge, decisions and grading).
# Headroom gate and check-after-write lock as before; idle priority.
cd "/f/Projects/AI hallucinations"
until grep -q '^PREFETCH_COMPLETE' results/runs/s58/prefetch.log 2>/dev/null; do if grep -q '^PREFETCH_GAVE_UP' results/runs/s58/prefetch.log 2>/dev/null; then echo 'prefetch gave up'; exit 1; fi; sleep 300; done
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11540 S29_SEARCH=fsm
LOCK=results/gpu_lock.txt; ME="vkg-main s58 $$"
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 10 ]; }
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 120; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() { killport 18000; curl -s -m 30 localhost:11540/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; curl -s -m 30 localhost:11540/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null; killport 11540; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
trap cleanup EXIT
start_ollama() { if ! netstat -ano | grep -q "127.0.0.1:11540 .*LISTEN"; then powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11540'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='2'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1; for t in $(seq 1 30); do curl -s -m 3 localhost:11540/api/tags > /dev/null && break; sleep 5; done; fi; }
start_podgen() { if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then VKG_MEM_FRAC=0.68 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s58/podgen.log 2>&1 & for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done; sleep 20; fi; }
start_ollama
vram_free() { nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'; }
ok=0
for att in 1 2 3 4 5; do
  until [ "$(vram_free)" -ge 24 ] || netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; do sleep 60; done
  start_podgen
  if python -B results/runs/s58/s58_run.py m58 gen; then ok=1; break; fi
  echo "gen attempt $att failed $(date +%H:%M); waiting for 24 GB free VRAM"; killport 18000; sleep 120
  until [ "$(vram_free)" -ge 24 ]; do sleep 60; done
done
[ $ok = 1 ] || { echo "gen FAILED"; exit 1; }
killport 18000; sleep 10
OLLAMA_HOST_URL=http://127.0.0.1:9 G4SET=s58 python -B results/runs/s57/g4/g4_design.py cands || { echo "cands FAILED"; exit 1; }
start_ollama; OLLAMA_HOST_URL=http://127.0.0.1:11540 G4SET=s58 python -B results/runs/s57/g4/g4_design.py judge || { echo "judge FAILED"; exit 1; }
OLLAMA_HOST_URL=http://127.0.0.1:11540 python -B results/runs/s58/s58_q2.py decide || { echo "decide FAILED"; exit 1; }
python -B results/runs/s58/s58_q2.py sheet || { echo "sheet FAILED"; exit 1; }
cleanup; trap - EXIT
echo "S58_DONE $(date)"
