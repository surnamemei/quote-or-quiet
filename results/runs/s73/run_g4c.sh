#!/bin/bash
# S73: rule Q3 design run on spent S68 data: 27B witness judgements, then decisions with gold grading (27B). Shared GPU lock, desktop headroom (RAM >= 16, VRAM >= 22 GB free).
cd "$(dirname "$0")/../../.."
export PYTHONIOENCODING=utf-8 OLLAMA_HOST_URL=http://127.0.0.1:11540 G4C_JUDGE=${G4C_JUDGE:-}
LOCK=results/gpu_lock.txt; ME="vkg-main g4c $$"; R=results/runs/s73
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 22 ]; }
echo "--- G4C $(date)"
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 60; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
trap 'bash tool/stop_service.sh --own-lock > /dev/null 2>&1; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK' EXIT
if ! netstat -ano | grep -q "127.0.0.1:11540 .*LISTEN"; then
  powershell -c "\$env:OLLAMA_MODELS='$(cygpath -w "$PWD/models/ollama_store")'; \$env:OLLAMA_HOST='127.0.0.1:11540'; \$env:OLLAMA_CONTEXT_LENGTH='8192'; \$env:OLLAMA_NUM_PARALLEL='1'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath '$(cygpath -w "$LOCALAPPDATA")\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1
  for t in $(seq 1 30); do curl -s -m 3 localhost:11540/api/tags > /dev/null && break; sleep 5; done
fi
nice python -B $R/g4c_design.py ${G4C_STEPS:-judge} && nice python -B $R/g4c_design.py decide || echo "G4C FAILED"
echo "G4C_DONE $(date)"
