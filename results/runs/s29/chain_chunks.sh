#!/bin/bash
# Sealed run in 4 chunks of 840 (file order, founded dropped), each started as soon as the search prefetch has covered its items; one heavy job at a time (run_s29.sh holds the lock and the headroom gate).
cd "/f/Projects/AI hallucinations"
LOG=results/runs/s29/prefetch_sealed.log
ready() { python -B - "$1" <<'PY'
import json, hashlib, sys, os
i = int(sys.argv[1])
rows = [json.loads(l) for l in open("results/runs/s29/sealed/items.jsonl", encoding="utf-8")]
rows = [r for r in rows if r["relation"] != "founded"][(i - 1) * 840:i * 840]
miss = sum(not os.path.exists("results/cache/web_fsm/s_" + hashlib.sha256(r["q"].encode()).hexdigest() + ".json") for r in rows)
sys.exit(0 if miss == 0 else 1)
PY
}
for i in 1 2 3 4; do
  until ready $i; do
    if grep -q '^stopped after repeated failures' $LOG; then echo "prefetch stopped early; chunk $i not started"; exit 1; fi
    if grep -q '^done sealed' $LOG; then break; fi    # prefetch finished: remaining misses are search failures, run anyway (live fallback is logged by the pipeline)
    sleep 120
  done
  echo "chunk $i start $(date +%T)"
  bash results/runs/s29/run_s29.sh fsm wd$i || { echo "chunk $i FAILED"; exit 1; }
done
echo S29_ALL_CHUNKS_DONE $(date)
