#!/bin/bash
# S59 G8 (docs/S59_G8_LONGFORM_TOPICS_PLAN.md): drafts and slots (Phi-4), candidates (CPU), 4B judge (W4), then the blind sheet.
cd "/f/Projects/AI hallucinations"
R=results/runs/s59
bash $R/run_g8a.sh || { echo "G8 FAILED (drafts)"; exit 1; }
OLLAMA_HOST_URL=http://127.0.0.1:9 PYTHONIOENCODING=utf-8 python -B $R/f5_cands.py || { echo "G8 FAILED (cands)"; exit 1; }
bash $R/run_f5.sh || { echo "G8 FAILED (judge)"; exit 1; }
OLLAMA_HOST_URL=http://127.0.0.1:9 PYTHONIOENCODING=utf-8 python -B $R/f5_sheet.py || { echo "G8 FAILED (sheet)"; exit 1; }
echo "G8_DONE $(date)"
