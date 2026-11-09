#!/bin/bash
# Lean GPU use for the running S41 verify: Phi-4 on a CPU-only Ollama (same port 11535, idle priority); the 4B server is stopped and the GPU lock
# released as soon as the readers are done; the CPU Ollama is stopped when verification ends. Replaces run_s41.sh's cleanup (that shell is killed).
cd "/f/Projects/AI hallucinations"
L=results/runs/s41/run_s41.log
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
killport 11535; sleep 3
powershell -c "\$env:CUDA_VISIBLE_DEVICES='-1'; \$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11535'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='1'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; \$p = Start-Process -PassThru -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'; \$p.PriorityClass = 'Idle'" > /dev/null 2>&1
for t in $(seq 1 30); do curl -s -m 3 localhost:11535/api/tags > /dev/null && break; sleep 5; done
echo "cpu ollama up $(date +%H:%M)" >> $L
until grep -qE '^readers|Traceback' $L; do sleep 30; done
killport 18000; grep -q '^vkg-main s41 ' results/gpu_lock.txt 2>/dev/null && rm -f results/gpu_lock.txt
echo "4B server stopped, GPU lock released $(date +%H:%M)" >> $L
until grep -qE '^kept|Traceback' $L && ! pgrep -f lf_verify > /dev/null 2>&1 && ! powershell -c "Get-CimInstance Win32_Process | ? { \$_.CommandLine -match 'lf_verify.py' -and \$_.CommandLine -notmatch 'CimInstance' }" | grep -q lf_verify; do sleep 60; done
curl -s -m 30 localhost:11535/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; killport 11535
grep -q '^kept' $L && echo "S41_DONE $(date)" >> $L || echo "verify FAILED $(date)" >> $L
