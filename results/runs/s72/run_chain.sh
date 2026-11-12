#!/bin/bash
# After S68: S69 (cross-family reviewers, its own wrapper and lock), then the v2 self-test for S72 under the shared GPU lock. The registered S72 run is started separately after the self-test is read.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 OLLAMA_HOST_URL=http://127.0.0.1:11540
echo "--- CHAIN $(date)"
bash results/runs/s69/run_xfam.sh >> results/runs/s69/run_xfam.log 2>&1
LOCK=results/gpu_lock.txt; ME="vkg-main selftest $$"
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 24 ]; }
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "selftest lock taken $(date)"
trap 'grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; bash tool/stop_service.sh > /dev/null 2>&1' EXIT
if ! netstat -ano | grep -q "127.0.0.1:11540 .*LISTEN"; then
  powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11540'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='1'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1
  for t in $(seq 1 30); do curl -s -m 3 localhost:11540/api/tags > /dev/null && break; sleep 5; done
fi
if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
  VKG_MEM_FRAC=0.45 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> tool/podgen.log 2>&1 &
  for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done; sleep 20
fi
VKG_OLLAMA_URL=http://127.0.0.1:11540 nohup python -B tool/qoq_service.py 18100 >> tool/service.log 2>&1 &
for t in $(seq 1 30); do curl -s -m 2 localhost:18100/ > /dev/null && break; sleep 2; done
python -B results/runs/s72/selftest.py || echo "SELFTEST FAILED"
echo "CHAIN_DONE $(date)"
