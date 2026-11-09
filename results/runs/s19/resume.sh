#!/bin/bash
# S19 resume after a postponement (docs/S19_PROTOCOL.md: stop, postpone, resume from caches, never skip).
# Deviation rule, fixed 2026-11-07 ~14:05 before any FRESH-5 output exists (the user delegated the decision):
#   DuckDuckGo sometimes answers one specific query with its own error page ("Oops... The server encountered an error").
#   The frozen vkg/websearch.py treats it as a failure and raises. If run_test.sh stops on a query, and a direct probe of that
#   same query at least 45 min after the first failure still returns the "Oops" error page, then the query is recorded as
#   having no web results (cache file "[]", exactly what websearch writes for a "No results" page) and the run resumes.
#   Any other failure (bot check, anomaly page, network) is NOT handled: the run stays postponed.
#   No frozen file changes; each recorded query is logged in results/runs/s19/INCIDENTS.md.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8
LOG=results/runs/s19/run_test.log
for attempt in 1 2 3 4 5 6 7 8; do
  # wait until >= 24 GB VRAM is free (resource etiquette; attempt 2 hit a CUDA OOM in the embedder while VRAM was taken elsewhere)
  until [ "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)" -ge 24000 ]; do sleep 60; done
  bash results/runs/s19/run_test.sh > $LOG 2>&1
  grep -q S19_TEST_GENERATED $LOG && { echo "S19 generated on resume attempt $attempt"; exit 0; }
  q=$(grep -a "RuntimeError: web search failed repeatedly" $LOG | tail -1)
  if [ -z "$q" ]; then
    if grep -q "out of memory\|500 Server Error\|Connection aborted\|ConnectionError" $LOG && [ $attempt -lt 8 ]; then   # transient GPU OOM: clean up my own podgen and lock, retry
      echo "attempt $attempt: GPU out of memory; retrying" ; cp $LOG results/runs/s19/run_test_oom_$attempt.log
      if grep -q "^vkg-main " results/gpu_lock.txt 2>/dev/null; then
        PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
        for m in phi4 qwen3.8-27b; do curl -s -m 60 localhost:11435/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null; done
        rm -f results/gpu_lock.txt; fi
      sleep 120; continue
    fi
    echo "stopped for another reason (see $LOG); postponed"; exit 1
  fi
  # run_test.sh keeps its lock on failure; it fails in the evidence stage, before any model loads. Clean up only my own lock and podgen.
  if grep -q "^vkg-main " results/gpu_lock.txt 2>/dev/null; then
    PID=$(netstat -ano | grep "127.0.0.1:18000 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1
    rm -f results/gpu_lock.txt
  fi
  python -B - "$LOG" <<'EOF' || { echo "query not recorded; postponed"; exit 1; }
import ast, datetime, re, sys, time, requests
from vkg import websearch as W
line = [l for l in open(sys.argv[1], encoding="utf-8", errors="replace") if "web search failed repeatedly" in l and "RuntimeError" in l][-1]
q = ast.literal_eval(line.split("web search failed repeatedly: ", 1)[1].strip())
f = W.CACHE / f"s_{W._key(q)}.json"
import json, pathlib
seen_f = pathlib.Path("results/runs/s19/search_failures.json")
seen = json.loads(seen_f.read_text()) if seen_f.exists() else {}
k = W._key(q)
seen.setdefault(k, time.time())
seen_f.write_text(json.dumps(seen))
wait = seen[k] + 45 * 60 - time.time()
if wait > 0:
    print(f"waiting {wait / 60:.0f} min before the probe", flush=True)
    time.sleep(wait)
time.sleep(10)
r = requests.post("https://html.duckduckgo.com/html/", data={"q": q}, headers=W.HDR, timeout=30)
oops = r.status_code == 200 and "Oops" in r.text and "server encountered an error" in r.text and "result__a" not in r.text
if not oops:
    sys.exit(f"probe did not return the Oops page (status {r.status_code}); not recorded")
f.write_text("[]", encoding="utf-8")
with open("results/runs/s19/INCIDENTS.md", "a", encoding="utf-8") as g:
    g.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M} recorded as no web results (DuckDuckGo 'Oops' error page twice, >= 45 min apart): "
            f"cache key {W._key(q)[:16]}\n")
print("recorded as empty:", W._key(q)[:16])
EOF
done
echo "too many recorded queries; postponed"; exit 1
