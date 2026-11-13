#!/bin/bash
# Self-test of the Quote or Quiet service: waits for headroom (the GPU lock free, free RAM >= 16 GB, free VRAM >= 22 GB), starts the servers, runs one call of each
# kind, writes tool/selftest.log, stops everything it started. Leaves other jobs and the desktop alone.
cd "$(dirname "$0")/.."   # the repository root
LOG=tool/selftest.log; : > $LOG
until bash tool/start_service.sh > tool/selftest_start.log 2>&1; do sleep 120; done
for t in $(seq 1 40); do python -c "import sys,os; sys.path.insert(0,'.'); os.environ['VKG_EMB']='hf'; from vkg import pod; pod.gen(['Say hi'],2)" > /dev/null 2>&1 && break; sleep 15; done
echo "service up and 4B answering $(date)" >> $LOG
call() { echo "--- $1 $2 $(date +%H:%M:%S)" >> $LOG; curl -s -m 1500 -X POST localhost:18100/$1 -H 'Content-Type: application/json' -d "$2" | python -c "import sys,json; r=json.load(sys.stdin); print(json.dumps(r,ensure_ascii=False)[:2500])" >> $LOG 2>&1; }
call readings '{"name":"Heat","relation":"director"}'
call readings '{"name":"John Smith","relation":"birth_year"}'
call bio '{"name":"Tina Fey"}'
call answer '{"question":"In what year was Tina Fey born?"}'
call answer '{"question":"Who was the head of government of Saudi Arabia in 1933?"}'
call answer '{"question":"In what year did Albert Einstein die?"}'
call answer '{"question":"Who was the doctoral advisor of Andreas Speiser?"}'
call answer '{"question":"What year was the first MBTI manual published?"}'
bash tool/stop_service.sh >> $LOG 2>&1
echo "SELFTEST_DONE $(date)" >> $LOG
