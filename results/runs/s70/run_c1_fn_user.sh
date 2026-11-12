#!/bin/bash
# Track C C1 on Flash Next through the user's own running infernix-serve (port 12689, their settings: DFlash2 drafter, n-gram volume, int8 KV, max concurrency 2),
# thinking off, one request at a time, so one of the two slots stays free for the user. No model of mine is loaded. Short contexts for both prompts, then long
# contexts for the first 100 base items (material_only); long prompts take 15 to 60 s each on this server. Stops if the server goes away.
cd "/f/Projects/AI hallucinations"; export PYTHONIOENCODING=utf-8 INFX_NOTHINK=1; R=results/runs/s70
echo "--- C1FN $(date)"
for s in material_only direct; do CONTEXTS=short python -B $R/esuite_run.py run infernix:12689 $s || { echo "C1FN STOPPED $s short"; exit 1; }; done
CONTEXTS=long LONG_BASES=100 python -B $R/esuite_run.py run infernix:12689 material_only || { echo "C1FN STOPPED long"; exit 1; }
echo "C1FN_DONE $(date)"
