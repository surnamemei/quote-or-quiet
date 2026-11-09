#!/bin/bash
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_OLLAMA_URL=http://127.0.0.1:11535 OLLAMA_HOST_URL=http://127.0.0.1:11535
LOCK=results/gpu_lock.txt
ME="vkg-main l3cert $$"
while true; do
  while [ -e $LOCK ]; do sleep 120; done
  sleep $((RANDOM % 20 + 5))
  [ -e $LOCK ] && continue
  echo "$ME $(date +%H:%M) expected-end $(date -d '+40 min' +%H:%M)" > $LOCK
  sleep 15
  grep -q "^$ME " $LOCK && break
done
cleanup() { for m in phi4 qwen3.8-27b; do curl -s -m 60 localhost:11535/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK; }
trap cleanup EXIT
for n in mintaka_dev mintaka_test; do python -B results/runs/l3cert/run_cert.py $n gen || exit 1; done
echo L3CERT_GEN_DONE $(date)
