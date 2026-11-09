#!/bin/bash
# S19 sealed run on FRESH-5 (docs/S19_PROTOCOL.md). Same pipeline and settings as the S19 design re-check (run_design.sh):
# 4B + HF embedder via vkg/podgen_server.py (venv_gpu, 127.0.0.1:18000, 65% cap), judge + Phi-4 via the project Ollama
# (127.0.0.1:11435). GPU lock results/gpu_lock.txt (rule agreed with the Kimi session). Scoring is a separate step.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local OLLAMA_HOST_URL=http://localhost:11435
sha256sum -c results/runs/s19/hashes_freeze.txt > results/runs/s19/hashes_check_before.txt 2>&1 || { echo "FROZEN FILE CHANGED - not running"; exit 1; }
until [ -s results/runs/fresh5/prefetch_ddg_fresh5.json ]; do sleep 120; done
echo "prefetch FRESH-5 present $(date)"
LOCK=results/gpu_lock.txt
while [ -e $LOCK ] && ! grep -q "^vkg-main " $LOCK; do sleep 120; done
echo "vkg-main s19-test $(date +%H:%M) expected-end $(date -d '+3 hours' +%H:%M)" > $LOCK
if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
  VKG_MEM_FRAC=0.65 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py \
    models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b > results/runs/s19/podgen_local_test.log 2>&1 &
  sleep 60
fi
python -B -m vkg.s17_run fresh5 || { echo "s17_run fresh5 FAILED (lock kept)"; exit 1; }
f=results/shared_eval/readers/s19fresh5_combo_cautious_phi4.jsonl
[ -s $f ] || python -B -m vkg.reader_run --reader phi4 --evidence combo --prompt cautious --set fresh5 --out $f --workers 4 --num-ctx 24576 \
  || { echo "phi4 FAILED (lock kept)"; exit 1; }
curl -s -m 60 $OLLAMA_HOST_URL/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null
curl -s -m 60 $OLLAMA_HOST_URL/api/generate -d '{"model":"qwen3.8-27b","keep_alive":0}' > /dev/null
curl -s -m 60 localhost:18000/unload -X POST -d '{}' > /dev/null || true
PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1)
[ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
rm -f $LOCK
sha256sum -c results/runs/s19/hashes_freeze.txt > results/runs/s19/hashes_check_after.txt 2>&1 || echo "WARNING: a frozen file changed during the run"
echo S19_TEST_GENERATED $(date)
