#!/bin/bash
# Start what the Quote or Quiet service needs, then the service itself (127.0.0.1:18100). Leaves headroom: refuses to start while another
# job holds the project GPU lock, and needs free RAM >= 16 GB and free VRAM >= 22 GB (4B server about 10 GB, capped at 45% of the card; Phi-4 about 9 GB plus its context).
cd "/f/Projects/AI hallucinations"
if [ -e results/gpu_lock.txt ]; then echo "GPU lock held: $(cat results/gpu_lock.txt). Try again when it is free."; exit 1; fi
ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r')
vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}')
if [ "$ram" -lt 16 ] || [ "$vram" -lt 22 ]; then echo "Not enough headroom (free RAM $ram GB, free VRAM $vram GB)."; exit 1; fi
if ! netstat -ano | grep -q "127.0.0.1:11535 .*LISTEN"; then
  powershell -c "\$env:OLLAMA_MODELS='F:\Projects\AI hallucinations\models\ollama_store'; \$env:OLLAMA_HOST='127.0.0.1:11535'; \$env:OLLAMA_CONTEXT_LENGTH='32768'; \$env:OLLAMA_NUM_PARALLEL='1'; \$env:OLLAMA_MAX_LOADED_MODELS='1'; Start-Process -WindowStyle Hidden -FilePath 'C:\Users\mei\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve'" > /dev/null 2>&1
fi
if ! netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN"; then
  VKG_MEM_FRAC=0.45 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup venv_gpu/Scripts/python.exe vkg/podgen_server.py models/qwen3-4b-instruct-2507 models/qwen3-embedding-0.6b >> tool/podgen.log 2>&1 &
  for t in $(seq 1 30); do netstat -ano | grep -q "127.0.0.1:18000 .*LISTEN" && break; sleep 10; done
fi
VKG_OLLAMA_URL=http://127.0.0.1:11535 nohup python -B tool/qoq_service.py 18100 >> tool/service.log 2>&1 &
for t in $(seq 1 30); do curl -s -m 2 localhost:18100/ > /dev/null && break; sleep 2; done
curl -s -m 2 localhost:18100/ && echo " service up on 127.0.0.1:18100"
