#!/bin/bash
# Writes results/runs/s19/hashes_freeze.txt at the freeze: the whole vkg package (every module the run and both scorers can
# import), the sealed items, the run script, the protocol, the embedder weights and the Kimi session's scorer + section.
cd "/f/Projects/AI hallucinations"
F="results/runs/fresh5/items.json results/shared_eval/two_reader.py results/runs/s19/run_test.sh docs/S19_PROTOCOL.md
models/qwen3-embedding-0.6b/model.safetensors E:/Models/halluc_runs/tiered.py E:/Models/halluc_runs/PREREG_TIERED.md"
for f in $F; do [ -e "$f" ] || { echo "MISSING $f"; exit 1; }; done
sha256sum vkg/*.py $F > results/runs/s19/hashes_freeze.txt
wc -l < results/runs/s19/hashes_freeze.txt
