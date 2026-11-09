#!/bin/bash
# S19 step 3 (docs/S19_PROTOCOL.md): after run_test.sh printed S19_TEST_GENERATED.
# Hash check after the run, then H1 raw scoring with the judge unreachable (cached labels only). No GPU.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 VKG_EMB=hf VKG_WEB=ddg OLLAMA_HOST_URL=http://127.0.0.1:9
grep -q S19_TEST_GENERATED results/runs/s19/run_test.log || { echo "run not finished"; exit 1; }
bad=$(grep -vc ': OK$' results/runs/s19/hashes_check_after.txt)
echo "hash check after run: $(grep -c ': OK$' results/runs/s19/hashes_check_after.txt) OK, $bad not OK"
[ "$bad" = "0" ] || { echo "FROZEN FILE CHANGED - stop, do not score"; exit 1; }
python -B -m vkg.s19_eval score
