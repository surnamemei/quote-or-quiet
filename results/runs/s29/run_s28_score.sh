#!/bin/bash
# S28: score the evaluation rows with the LoRA checker (GPU, one job). Check-after-write lock, idle priority, headroom gate (free RAM >= 16 GB, free VRAM >= 10 GB).
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8
LOCK=results/gpu_lock.txt
ME="vkg-main s28-score $$"
headroom_ok() {
  ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" 2>/dev/null | tr -d '\r')
  vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}')
  [ "${ram:-0}" -ge 16 ] && [ "${vram:-0}" -ge 10 ]
}
while true; do
  while [ -e $LOCK ] || ! headroom_ok; do sleep 120; done
  sleep $((RANDOM % 20 + 5))
  [ -e $LOCK ] && continue
  echo "$ME $(date +%H:%M) expected-end $(date -d '+30 min' +%H:%M)" > $LOCK
  sleep 15
  grep -q "^$ME " $LOCK && break
done
echo "lock taken $(date)"
cleanup() { grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
trap cleanup EXIT
venv_gpu/Scripts/python.exe -B results/runs/s29/s28_train.py score results/runs/s29/s28_eval_rows.jsonl results/runs/s29/s28_eval_scored.jsonl || { echo "score FAILED"; exit 1; }
echo S28_SCORE_DONE $(date)
