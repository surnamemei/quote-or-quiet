"""Polite queue for the certificate runs: waits until the S8 runner has finished (results/runs/s8/DONE) and the GPU is free of the
user's jobs (>= 20 GB free VRAM, >= 10 GB free RAM), then runs vkg.cert_gen on fresh, simpleqa_E, squad2, faitheval at idle priority.
Re-checks the free memory before each suite. Run: python -B -m vkg.cert_wait  (log: results/runs/cert/wait.log)"""
import subprocess
import time
from pathlib import Path

import psutil

from .s8_wait import free_vram

ROOT = Path(__file__).resolve().parent.parent      # no heavy imports: the waiter must stay small

C = ROOT / "results" / "runs" / "cert"
LOG = C / "wait.log"
PY = str(ROOT / "venv_gpu" / "Scripts" / "python.exe")


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def main():
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    C.mkdir(parents=True, exist_ok=True)
    s8done = ROOT / "results" / "runs" / "s8" / "DONE"
    log("waiting for the S8 runner to finish")
    while not s8done.exists():
        time.sleep(120)
    for suite in ("fresh", "simpleqa_E", "squad2", "faitheval"):
        if (C / f"{suite}.jsonl").exists():
            log(f"{suite}: exists, skipping")
            continue
        if suite == "fresh" and not (ROOT / "results" / "runs" / "s8" / "fresh_items.json").exists():
            log("fresh: no fresh items (S8 build failed?), skipping")
            continue
        w = False
        while free_vram() < 20000 or psutil.virtual_memory().available / 2**30 < 10:
            if not w:
                log(f"{suite}: waiting for free GPU (free {free_vram()} MiB)")
                w = True
            time.sleep(120)
        log(f"{suite}: start")
        with open(C / f"{suite}.log", "w", encoding="utf-8") as f:
            rc = subprocess.run([PY, "-B", "-m", "vkg.cert_gen", suite], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
        log(f"{suite}: exit {rc}")
    (C / "DONE").write_text("done\n")


if __name__ == "__main__":
    main()
