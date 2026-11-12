#!/bin/bash
# Track C1 on the user's Infernix builds (docs/TRACK_C_CONTEXT_FAITHFUL_PLAN.md): Flash Next Uncensored-NVFP4 with the DFlash2 drafter, then the 27B Uncensored-NVFP4;
# each with --reproducible, one request at a time, both prompts (material_only, direct). Alone on the GPU under the shared lock; after the Ollama C1 run.
cd "/f/Projects/AI hallucinations"
export PYTHONIOENCODING=utf-8 INFX_NOTHINK=1
R=results/runs/s70; LOCK=results/gpu_lock.txt; ME="vkg-main c1inf $$"
BIN="/c/Users/mei/Documents/Codex/2026-10-25/ai-ollma-x20/work/infernix-test/release/infernix-2026.11.01-windows-x64/infernix-serve.exe"
FN="E:/InfernixTest/Qwen3.8-Flash-Next-Uncensored-NVFP4-Infernix/Qwen3.8-Flash-Next-Uncensored-NVFP4-Infernix-00001-of-00003.infernix"
DR="E:/InfernixTest/Qwen3.8-Flash-Next-DFlash2-Infernix/Qwen3.8-Flash-Next-DFlash2-Infernix.infernix"
NG="E:/InfernixTest/Qwen3.8-Flash-Next-NVIDIA-NVFP4-Infernix/Qwen3.8-Flash-Next-NVIDIA-NVFP4-Infernix.ngram"
M27="E:/InfernixTest/Qwen3.8-27B-Uncensored-NVFP4-NInferV3/qwen3_8_27b_nvfp4-uncensored.ninfer"
headroom_ok() { ram=$(powershell -c "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r'); vram=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{printf "%d", ($2-$1)/1024}'); [ "${ram:-0}" -ge 24 ] && [ "${vram:-0}" -ge 22 ]; }
killport() { PID=$(netstat -ano | grep "127.0.0.1:$1 .*LISTENING" | awk '{print $NF}' | head -1); [ -n "$PID" ] && taskkill //PID $PID //F > /dev/null 2>&1; }
echo "--- C1INF $(date)"
while true; do while [ -e $LOCK ] || ! headroom_ok; do sleep 120; done; echo "$ME $(date +%H:%M)" > $LOCK; sleep 15; grep -q "^$ME " $LOCK && break; done
echo "lock taken $(date)"
trap 'killport 11951; grep -q "^$ME " $LOCK 2>/dev/null && rm -f $LOCK' EXIT
serve() { nohup "$BIN" "$@" --port 11951 --reproducible --max-context 16384 --vram-headroom-mib 6144 --ram-free-mib 16384 --host-context-mib 2048 > $R/infernix_serve_${tag}_$(date +%H%M).log 2>&1 &
  for t in $(seq 1 90); do curl -s -m 3 localhost:11951/v1/models > /dev/null && return 0; sleep 10; done; return 1; }
run_model() { tag=$1; shift
  serve "$@" || { echo "C1INF FAILED start $tag"; exit 1; }
  nvidia-smi --query-gpu=memory.used --format=csv,noheader > $R/infernix_${tag}_vram.txt
  curl -s -m 60 localhost:11951/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"default","messages":[{"role":"user","content":"Say OK."}],"max_tokens":5,"temperature":0,"logprobs":true,"top_logprobs":3}' > $R/infernix_${tag}_logprobs_probe.json
  for s in material_only direct; do python -B $R/esuite_run.py run infernix:11951 $s || { echo "C1INF FAILED $tag $s"; exit 1; }
    f=$R/out_esuite_v2_infernix_11951_$s.jsonl; [ -e $f ] && mv $f $R/out_esuite_v2_infernix_${tag}_$s.jsonl; done
  killport 11951; sleep 20; }
# Flash Next was run through the user's own server (run_c1_fn_user.sh); only the 27B here.
run_model q27nvfp4 "$M27"
python -B $R/esuite_run.py score > /dev/null
echo "C1INF_DONE $(date)"
