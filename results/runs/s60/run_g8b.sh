#!/bin/bash
# S60 (docs/S60_G8B_PLAN.md): 50 fresh topics, grounded drafts and slots (Phi-4), candidates (CPU), rule W4-27 (27B judge), blind sheet.
cd "/f/Projects/AI hallucinations"
R=results/runs/s60
bash $R/run_g8a.sh || { echo "G8B FAILED (drafts)"; exit 1; }
OLLAMA_HOST_URL=http://127.0.0.1:9 PYTHONIOENCODING=utf-8 python -B $R/f5_cands.py || { echo "G8B FAILED (cands)"; exit 1; }
bash $R/run_w27.sh || { echo "G8B FAILED (judge)"; exit 1; }
OLLAMA_HOST_URL=http://127.0.0.1:9 PYTHONIOENCODING=utf-8 python -B $R/f5_sheet.py || { echo "G8B FAILED (sheet)"; exit 1; }
echo "G8B_DONE $(date)"
