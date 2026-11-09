"""Polite runner for S14: waits for S13 DONE and >= 12 GB free VRAM and >= 10 GB free RAM, runs vkg.s14_run (venv_gpu, idle priority),
then judges round0, web_cautious and web_plain answers (vkg.judge_file) and unloads the Ollama models. Log: results/runs/s14/wait.log"""
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil
import requests

from .s8_wait import free_vram

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "runs" / "s14"
GPU_PY = str(ROOT / "venv_gpu" / "Scripts" / "python.exe")


def log(m):
    with open(OUT / "wait.log", "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def main():
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    OUT.mkdir(parents=True, exist_ok=True)
    while not (ROOT / "results" / "runs" / "s13" / "DONE").exists():   # run after S13 (never two GPU jobs of mine at once)
        time.sleep(120)
    said = False
    while free_vram() < 12000 or psutil.virtual_memory().available / 2**30 < 10:
        if not said:
            log(f"waiting (free VRAM {free_vram()} MiB)")
            said = True
        time.sleep(120)
    log("run: start")
    with open(OUT / "run.log", "w", encoding="utf-8") as f:
        rc = subprocess.run([GPU_PY, "-B", "-m", "vkg.s14_run"], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    log(f"run: exit {rc}")
    requests.post("http://localhost:11434/api/generate", json={"model": "qwen3-embedding:0.6b", "keep_alive": 0}, timeout=60)
    if rc:
        return
    sys.path.insert(0, str(ROOT))
    from vkg.s8_eval import non_answer
    with open(OUT / "judge_rows.jsonl", "w", encoding="utf-8") as f:
        for r in map(json.loads, open(OUT / "outputs.jsonl", encoding="utf-8")):
            for key in ("round0", "web_cautious", "web_plain"):
                if r[key] is not None and not non_answer(r[key]):
                    f.write(json.dumps({"question": r["question"], "gold": r["gold"][0], "answer": str(r[key])}, ensure_ascii=False) + "\n")
    log("judge: start")
    with open(OUT / "judge.log", "w", encoding="utf-8") as f:
        rc = subprocess.run([sys.executable, "-B", "-m", "vkg.judge_file", str(OUT / "judge_rows.jsonl")], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    log(f"judge: exit {rc}")
    (OUT / "DONE").write_text("done\n")


if __name__ == "__main__":
    main()
