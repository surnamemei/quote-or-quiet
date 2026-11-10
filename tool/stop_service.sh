#!/bin/bash
# Stop the service and free the GPU (4B server and Phi-4). Does nothing to other jobs' processes unless they use these ports.
cd "/f/Projects/AI hallucinations"
if [ -e results/gpu_lock.txt ]; then echo "GPU lock held by $(cat results/gpu_lock.txt): leaving the 4B server and Ollama running."; ONLY_SERVICE=1; fi
k() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
k 18100
if [ -z "$ONLY_SERVICE" ]; then curl -s -m 20 localhost:11540/api/generate -d '{"model":"phi4","keep_alive":0}' > /dev/null; k 18000; k 11540; fi
echo stopped
