"""Polite runner for S10: train, then eval, then judge the new SimpleQA answers with grader 5 (vkg.judge_file).
Each stage waits for free VRAM / RAM, runs at idle priority, and is skipped if its output exists. Log: results/runs/s10/wait.log
Run: python -B -m vkg.s10_wait"""
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

from .s8_wait import free_vram

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "runs" / "s10"
GPU_PY = str(ROOT / "venv_gpu" / "Scripts" / "python.exe")


def log(m):
    with open(OUT / "wait.log", "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def wait_for(vram, ram, name):
    said = False
    while free_vram() < vram or psutil.virtual_memory().available / 2**30 < ram:
        if not said:
            log(f"{name}: waiting (free VRAM {free_vram()} MiB, need {vram})")
            said = True
        time.sleep(120)


def run(name, args, py=GPU_PY):
    log(f"{name}: start")
    with open(OUT / f"{name}.log", "w", encoding="utf-8") as f:
        rc = subprocess.run([py, "-B", "-m"] + args, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    log(f"{name}: exit {rc}")
    return rc


def judge_rows():
    sys.path.insert(0, str(ROOT))
    from vkg.s8_eval import non_answer
    rows = []
    for r in map(json.loads, open(OUT / "eval_outputs.jsonl", encoding="utf-8")):
        if r["suite"] not in ("fresh", "simpleqa_E"):
            continue
        for k in ("s6b", "s10"):
            if k in r and not non_answer(r[k]):
                rows.append({"question": r["question"], "gold": r["gold"][0], "answer": str(r[k])})
    with open(OUT / "judge_rows.jsonl", "w", encoding="utf-8") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")


def main():
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    OUT.mkdir(parents=True, exist_ok=True)
    if not (ROOT / "models" / "s10_lora_reading" / "adapter_config.json").exists():
        wait_for(20000, 12, "train")
        if run("train", ["vkg.s10_run", "train"]):
            return
    if not (OUT / "eval_outputs.jsonl").exists():
        wait_for(16000, 10, "eval")
        if run("eval", ["vkg.s10_run", "eval"]):
            return
    judge_rows()
    run("judge", ["vkg.judge_file", str(OUT / "judge_rows.jsonl")], py=sys.executable)
    (OUT / "DONE").write_text("done\n")


if __name__ == "__main__":
    main()
