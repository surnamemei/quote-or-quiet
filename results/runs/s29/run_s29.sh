#!/bin/bash
# S29: frozen pipeline on a new Wikidata question set, one search pool. Stages run one after another (never two heavy jobs at once):
#   4B generation server (about 68% of VRAM) -> Phi-4 veto and alias judge through the project Ollama (parallel 2) -> release the lock.
# usage: bash run_s29.sh <fsm|ddg> <wdp|wd>
# Gate: free RAM >= 16 GB and free VRAM >= 10 GB before taking the lock. Check-after-write lock. Idle priority for python.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535 S29_SEARCH=$1
SET=$2
LOCK=results/gpu_lock.txt
ME="vkg-main s29-$1-$SET $$"
headroom_ok() {
  ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" 2>/dev/null | tr -d '\r')
  vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}')
  [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 10 ]
}
while true; do
  while [ -e $LOCK ] || ! headroom_ok; do sleep 120; done
  sleep $((RANDOM % 20 + 5))
  [ -e $LOCK ] && continue
  echo "$ME $(date +%H:%M) expected-end $(date -d '+120 min' +%H:%M)" > $LOCK
  sleep 15
  grep -q "^$ME " $LOCK && break
done
echo "lock taken $(date)"
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
cleanup() {
  killport 18000
  curl -s -m 30 localhost:11535/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null
  curl -s -m 30 localhost:11535/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null
  killport 11535
  grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
# 0. Ollama (parallel 2), up before generation because the S17 runner labels outputs with the judge at the end of its run
if ! netstat -ano | grep -q "127.0.0.1:11535 .*LISTEN"; then
  powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11535'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='2'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1
  for t in $(seq 1 30); do curl -s -m 3 localhost:11535/api/tags > /dev/null && break; sleep 5; done
fi
# 1. generation
ok=0
for attempt in 1 2 3; do
  if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
    VKG_MEM_FRAC=0.68 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONUNBUFFERED=1 nohup venv_gpu/Scripts/python.exe -X faulthandler vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s29/podgen.log 2>&1 &
    for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
    sleep 20
    powershell -c "Get-CimInstance Win32_Process | ? { \$_.CommandLine -match 'podgen_server|s29_run' } | % { (Get-Process -Id \$_.ProcessId).PriorityClass = 'Idle' }" > /dev/null 2>&1
  fi
  if python -B results/runs/s29/s29_run.py $SET gen; then ok=1; break; fi
  killport 18000; sleep 30
done
[ $ok = 1 ] || { echo "gen FAILED"; exit 1; }
killport 18000
python -B results/runs/s29/s29_run.py $SET phi4 || { echo "phi4 FAILED"; exit 1; }
curl -s -m 30 localhost:11535/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null
python -B results/runs/s29/s29_run.py $SET alias || { echo "alias FAILED"; exit 1; }
echo S29_DONE $1 $SET $(date)
