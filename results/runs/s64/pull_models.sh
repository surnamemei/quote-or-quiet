#!/bin/bash
# G14: pull three open models of other families into the project's Ollama store (user permission 2026-11-11). Network only.
export OLLAMA_HOST=127.0.0.1:11540
for m in llama3.1:8b gemma3:12b mistral-nemo:12b; do
  /c/Users/mei/AppData/Local/Programs/Ollama/ollama pull $m > /dev/null 2>&1 && echo "pulled $m $(date +%H:%M)" || echo "FAILED $m"
done
echo PULL_DONE
