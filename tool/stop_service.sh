#!/bin/bash
# Stop the service and free the GPU (4B server, Ollama and every model it has loaded). Does nothing to other jobs' processes unless they use these ports.
# A caller that holds the project GPU lock itself passes --own-lock, so the models are stopped too; otherwise a held lock means another job is using them.
cd "$(dirname "$0")/.."   # the repository root
if [ -e results/gpu_lock.txt ] && [ "$1" != "--own-lock" ]; then echo "GPU lock held by $(cat results/gpu_lock.txt): leaving the 4B server and Ollama running."; ONLY_SERVICE=1; fi
k() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //T //F > /dev/null 2>&1; }   # /T: with its child runners
k 18100
if [ -z "$ONLY_SERVICE" ]; then
  for m in $(curl -s -m 10 localhost:11540/api/ps | python -c "import sys,json; print(' '.join(x['name'] for x in json.load(sys.stdin).get('models',[])))" 2>/dev/null); do
    curl -s -m 30 localhost:11540/api/generate -d "{\"model\":\"$m\",\"keep_alive\":0}" > /dev/null    # unload every loaded model, not only phi4
  done
  k 18000; k 11540
fi
echo stopped
