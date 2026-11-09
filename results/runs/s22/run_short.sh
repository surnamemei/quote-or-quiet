#!/bin/bash
# S22 DEV short-answer rewrite: waits until NO lock is held, then 4B rewrites (pin -> pinshort for Mintaka/PopQA DEV; S19 SimpleQA
# DEV -> s19short), alias/judge labels for the new strings, then frees the GPU.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt
ME="vkg-main s22-short $$"
while true; do
  while [ -e $LOCK ]; do sleep 120; done
  sleep $((RANDOM % 20 + 5))                     # another session may be waiting for the same lock
  [ -e $LOCK ] && continue
  echo "$ME $(date +%H:%M) expected-end $(date -d '+60 min' +%H:%M)" > $LOCK
  sleep 15
  grep -q "^$ME " $LOCK && break                  # still ours after 15 s: go
done
echo "lock taken $(date)"
cleanup() {
  PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
  for m in phi4 qwen3.8-27b; do curl -s -m 60 localhost:11535/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done
  grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK
}
trap cleanup EXIT
if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
  VKG_MEM_FRAC=0.88 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONUNBUFFERED=1 nohup venv_gpu/Scripts/python.exe -X faulthandler vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> results/runs/s22/podgen.log 2>&1 &
  for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
  sleep 20
  powershell -c "Get-CimInstance Win32_Process | ? { \$_.CommandLine -match 'podgen_server' } | % { (Get-Process -Id \$_.ProcessId).PriorityClass = 'Idle' }" > /dev/null 2>&1
fi
S=results/runs/s22/s22_short.py
python -B $S results/runs/s22/pin pinshort mintaka_dev || exit 1
python -B $S results/runs/s22/pin pinshort popqa_dev || exit 1
python -B $S results/runs/s19 s19short dev results/shared_eval/readers/s19dev_combo_cautious_phi4.jsonl || exit 1
PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
for V in pinshort; do for n in mintaka_dev popqa_dev; do S22_VARIANT=$V python -B results/runs/s22/s22_run.py $n alias || exit 1; done; done
S22_VARIANT=s19short python -B results/runs/s22/s22_run.py dev alias || exit 1
echo S22_SHORT_DONE $(date)
