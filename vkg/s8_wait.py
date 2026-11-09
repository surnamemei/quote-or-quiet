"""Polite runner for the S8 fresh stages: idle CPU priority, one worker, and each GPU stage starts only when enough GPU memory
and RAM are free (i.e. the user's own GPU jobs are not using them). Ollama models are unloaded after every stage.
Run: python -B -m vkg.s8_wait   (writes results/runs/s8/wait.log and results/runs/s8/DONE)
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
S8 = ROOT / "results" / "runs" / "s8"
LOG = S8 / "wait.log"
# (stage, interpreter, free VRAM MiB needed, free RAM GB needed)
STAGES = [("build", sys.executable, 25000, 10), ("big", sys.executable, 21000, 10),
          ("small", str(ROOT / "venv_gpu" / "Scripts" / "python.exe"), 11000, 10)]


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def free_vram():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total,memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    tot, used = map(int, out.strip().split(","))
    return tot - used


def unload():
    for m in ("qwen3.8-27b:latest", "qwen3-embedding:0.6b"):
        try:
            req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps({"model": m, "keep_alive": 0}).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:
            log(f"unload {m}: {e!r}")


def main():
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    env = dict(os.environ, S8_WORKERS="1", PYTHONIOENCODING="utf-8")
    done_marker = {"build": S8 / "fresh_items.json", "big": S8 / "fresh_27b.jsonl", "small": S8 / "fresh_4b.jsonl"}
    for stage, py, vram, ram in STAGES:
        if done_marker[stage].exists():
            log(f"{stage}: output exists, skipping")
            continue
        waited = False
        while True:
            fv, fr = free_vram(), psutil.virtual_memory().available / 2**30
            if fv >= vram and fr >= ram:
                break
            if not waited:
                log(f"{stage}: waiting (free VRAM {fv} MiB, need {vram}; free RAM {fr:.1f} GB, need {ram})")
                waited = True
            time.sleep(120)
        log(f"{stage}: start (free VRAM {fv} MiB, free RAM {fr:.1f} GB)")
        with open(S8 / f"{stage}.log", "w", encoding="utf-8") as f:
            rc = subprocess.run([py, "-B", "-m", f"vkg.s8_fresh", stage], cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
        unload()
        log(f"{stage}: exit {rc}")
        if rc != 0:
            (S8 / "DONE").write_text(f"failed at {stage} exit {rc}\n")
            return
    (S8 / "DONE").write_text("exit 0\n")


if __name__ == "__main__":
    main()
