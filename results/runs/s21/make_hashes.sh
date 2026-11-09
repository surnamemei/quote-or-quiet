#!/bin/bash
# Writes results/runs/s21/hashes_freeze.txt at the S21 freeze (docs/S21_PROTOCOL.md, "Frozen files").
# KIMI_FILES: the Kimi session's scorer + wrapper + section (set at the freeze; empty if H2-M is dropped).
cd "/f/Projects/AI hallucinations"
F="results/runs/s21/seal.py results/runs/s21/popqa_dev.json results/runs/s21/popqa_test.json results/runs/s21/mintaka_dev.json
results/runs/s21/mintaka_test.json results/runs/s21/prefetch_s21.py results/runs/s21/phi4_dev.py results/runs/s21/run_test.sh
docs/S21_PROTOCOL.md models/qwen3-embedding-0.6b/model.safetensors $KIMI_FILES"
for f in $F; do [ -e "$f" ] || { echo "MISSING $f"; exit 1; }; done
sha256sum vkg/*.py $F > results/runs/s21/hashes_freeze.txt
# the item files must still match the hashes written at sealing
for n in popqa_dev popqa_test mintaka_dev mintaka_test; do
  a=$(grep " \*$n.json" results/runs/s21/seal_hashes.txt | cut -c1-64); b=$(sha256sum results/runs/s21/$n.json | cut -c1-64)
  [ "$a" = "$b" ] || { echo "SEAL MISMATCH $n"; exit 1; }
done
wc -l < results/runs/s21/hashes_freeze.txt
