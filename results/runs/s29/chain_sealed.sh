#!/bin/bash
# Wait for the sealed-set search prefetch to finish, check that it did not stop on repeated failures, then start the sealed run (headroom gate and lock are inside run_s29.sh).
cd "/f/Projects/AI hallucinations"
LOG=results/runs/s29/prefetch_sealed.log
until grep -qE '^done sealed|^stopped after repeated failures' $LOG; do sleep 300; done
if grep -q '^stopped after repeated failures' $LOG; then echo "prefetch stopped early; not starting the run"; exit 1; fi
echo "prefetch finished: $(grep '^done sealed' $LOG)"
bash results/runs/s29/run_s29.sh fsm wd
