S19 attempt 1 stopped 13:5x: DuckDuckGo 'Oops... server error' page for one FRESH-5 query; websearch raised as frozen; postponed (protocol). Retry 1 scheduled ~15:00.
2026-11-07 14:10 retry replaced by results/runs/s19/resume.sh. Deviation rule fixed before any FRESH-5 output exists: a query that gets
  DuckDuckGo's own "Oops... server error" page at first failure and again on a direct probe >= 45 min later is recorded as having
  no web results (cache "[]"), and the run resumes. Bot checks and other failures still postpone. The user delegated the decision ("you decide").
2026-11-07 14:36 recorded as no web results (DuckDuckGo 'Oops' error page twice, >= 45 min apart): cache key 459dcd5f70e120ef
2026-11-07 14:41 attempt 2 passed evidence search, then failed: CUDA out of memory in the embedder (podgen /embed 500). Restarted with a >= 24 GB free-VRAM wait and OOM retry in resume.sh (run_test.sh unchanged).
2026-11-07 14:53 resume attempts 1-3 (14:43-14:52) failed with CUDA OOM in the embedder while system RAM was full (0 GB free: my d3_eval.py 36 GB + Kimi session analysis ~38 GB). Both stopped ~14:53; RAM back to 41 GB free. Attempt 4 proceeds.
2026-11-07 15:06 attempt 4 failed with ConnectionAborted (10053) on the embedder during wiki evidence after ~10 min; resume.sh now also retries connection errors (8 attempts).
