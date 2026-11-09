"""Judge every row of a blind file with grader 5 (vkg/grade_judge.py), politely (idle priority, waits for >= 22 GB free VRAM
and >= 10 GB free RAM, unloads the judge after). Appends to results/grader5/judge_grades.jsonl (rows already judged are skipped).
Run: python -B -m vkg.judge_file <blind.jsonl>"""
import json
import sys
import time

import psutil
import requests

from .grade_judge import JUDGE, judge
from .probe_gen import ROOT
from .s8_wait import free_vram

OUT = ROOT / "results" / "grader5" / "judge_grades.jsonl"


def main():
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    done = {(r["question"], r["gold"], r["answer"]) for r in map(json.loads, open(OUT, encoding="utf-8"))}
    todo = []
    for r in map(json.loads, open(sys.argv[1], encoding="utf-8")):
        t = (r["question"], r["gold"], r["answer"])
        if t not in done and t not in todo:
            todo.append(t)
    while free_vram() < 22000 or psutil.virtual_memory().available / 2**30 < 10:
        time.sleep(120)
    with open(OUT, "a", encoding="utf-8") as f:
        for q, g, a in todo:
            f.write(json.dumps({"question": q, "gold": g, "answer": a, "grade": judge(q, g, a)}, ensure_ascii=False) + "\n")
    requests.post("http://localhost:11434/api/generate", json={"model": JUDGE, "keep_alive": 0}, timeout=60)
    print("judged", len(todo))


if __name__ == "__main__":
    main()
