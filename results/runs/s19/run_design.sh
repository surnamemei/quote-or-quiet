#!/bin/bash
# S19 design re-measurement on DEV + FRESH with DuckDuckGo evidence (docs/S19_DESIGN.md, Decisions 2 and 7), on the user's
# local RTX 5090: 4B + HF embedder via vkg/podgen_server.py on 127.0.0.1:18000 (venv_gpu), judge and Phi-4 via the project
# Ollama on 127.0.0.1:11435. Waits for the DuckDuckGo prefetch of DEV and FRESH so only one process ever queries DuckDuckGo.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local OLLAMA_HOST_URL=http://localhost:11435
until [ -s results/runs/s19design/prefetch_ddg_fresh.json ]; do sleep 120; done
echo "prefetch DEV+FRESH present $(date)"
# GPU sharing rule agreed with the Kimi session (2026-11-07): one holder at a time, lock file, delete after unloading
LOCK=results/gpu_lock.txt
while [ -e $LOCK ] && ! grep -q "^vkg-main " $LOCK; do sleep 120; done
echo "vkg-main s19-design $(date +%H:%M) expected-end $(date -d '+2 hours' +%H:%M)" > $LOCK
# generation/embedding server (stdlib HTTP, local only); cap at 45% of the card so the desktop and any user job keep room
if ! curl -s -m 5 localhost:18000/health >/dev/null 2>&1 && ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
  VKG_MEM_FRAC=0.65 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py \
    models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b > results/runs/s19/podgen_local.log 2>&1 &
  sleep 60
fi
for s in dev fresh; do
  python -B -m vkg.s17_run $s || { echo "s17_run $s FAILED"; exit 1; }
done
for s in dev fresh; do
  for p in cautious plain; do
    f=results/shared_eval/readers/s19${s}_combo_${p}_phi4.jsonl
    [ -s $f ] || python -B -m vkg.reader_run --reader phi4 --evidence combo --prompt $p --set s19$s --out $f --workers 4 --num-ctx 24576
  done
done
curl -s -m 60 $OLLAMA_HOST_URL/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null
curl -s -m 60 localhost:18000/unload -X POST -d '{}' > /dev/null || true
PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1)
[ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
rm -f $LOCK
echo S19_DESIGN_DONE $(date)
