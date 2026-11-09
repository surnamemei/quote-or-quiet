# S21 deviations from the frozen protocol (docs/S21_PROTOCOL.md, frozen 2026-11-08 07:08)

## D1 (2026-11-08 09:10): 4B server memory cap raised from 0.65 to 0.88 of the GPU
- What happened: run_test.sh built all mintaka_test evidence (web, wiki, combo), then the first generation stage (web_plain) failed
  4 times with CUDA out of memory at the 0.65 cap (20.68 GiB; "tried to allocate 1.52 GiB"), once as a server crash.
  Cause, from passage-length statistics only (no item content read): one mintaka_test web passage is 201,455 characters
  (the next longest 37,001; FRESH-5 maximum was 46,422). The passage builder caps passages by whitespace words, so a page
  with few spaces gives a very long prompt; at batch size 1 it does not fit under the cap.
- Change: run_test_resume.sh = run_test.sh with VKG_MEM_FRAC=0.88 instead of 0.65 (diff: that one line and the comment).
  run_test.sh and every hashed file stay unchanged; run_test_resume.sh still checks results/runs/s21/hashes_freeze.txt before
  running. Greedy generation does not depend on the memory cap (batches are formed by TOKENS_PER_BATCH, not by memory), so
  outputs are what the frozen code produces given enough memory. No item, output or label was inspected; nothing was scored.
- If the long prompt still does not fit, the next step is to report it here before any further change.
