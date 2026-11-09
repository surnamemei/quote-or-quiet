"""Run grader 5 (vkg/grade_judge.py) on the validation sets and on every answered SimpleQA row we report, politely:
waits for >= 22 GB free VRAM and >= 10 GB free RAM, idle priority, one request at a time, unloads the judge at the end.
Writes results/grader5/judge_grades.jsonl: {question, gold, answer, grade}. Run: python -B -m vkg.judge_run"""
import json
import time

import psutil
import requests

from .analyze_open import att
from .grade_judge import JUDGE, judge
from .probe_gen import ROOT
from .s8_eval import non_answer
from .s8_wait import free_vram

G = ROOT / "results" / "grader5"
R = ROOT / "results" / "runs"


def rows():
    out = []
    for f in (ROOT / "results" / "audit" / "validation" / "sample_blind.jsonl", G / "v2_blind.jsonl"):
        out += [(r["question"], r["gold"], r["answer"]) for r in map(json.loads, open(f, encoding="utf-8"))]
    fresh = {e["id"]: e for e in json.load(open(R / "s8" / "fresh_items.json", encoding="utf-8"))}
    dev = {e["id"]: e for e in json.load(open(R / "s6b" / "eval_items.json", encoding="utf-8")) if e["suite"] == "simpleqa_E"}
    for o in map(json.loads, open(R / "s6b" / "eval_outputs.jsonl", encoding="utf-8")):
        if o["suite"] == "simpleqa_E":
            out += [(o["question"], o["gold"][0], str(o[s])) for s in ("plain", "cautious", "trained") if not non_answer(o[s])]
    for o in map(json.loads, open(R / "s8" / "fresh_4b.jsonl", encoding="utf-8")):
        out += [(fresh[o["id"]]["question"], fresh[o["id"]]["gold"][0], str(o[s])) for s in ("plain", "cautious") if not non_answer(o[s])]
    for suite, it in (("fresh", fresh), ("simpleqa_E", dev)):
        for r in map(json.loads, open(R / "cert" / f"{suite}.jsonl", encoding="utf-8")):
            if r["mode"] != "unknown":
                out.append((it[r["id"]]["question"], it[r["id"]]["gold"][0], r["answer"]))
    big = [json.loads(l) for l in open(R / "openworld_simpleqa_hybrid_qwen3.8-27b_s3000_n300.jsonl", encoding="utf-8")]
    big += [json.loads(l) for l in open(R / "s8" / "fresh_27b.jsonl", encoding="utf-8")]
    out += [(r["question"], r["gold"][0] if isinstance(r["gold"], list) else r["gold"], r["answer"]) for r in big if att(r)]
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def main():
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    todo = rows()
    while free_vram() < 22000 or psutil.virtual_memory().available / 2**30 < 10:
        time.sleep(120)
    G.mkdir(parents=True, exist_ok=True)
    with open(G / "judge_grades.jsonl", "w", encoding="utf-8") as f:
        for k, (q, g, a) in enumerate(todo, 1):
            f.write(json.dumps({"question": q, "gold": g, "answer": a, "grade": judge(q, g, a)}, ensure_ascii=False) + "\n")
            if k % 100 == 0:
                print(f"  {k}/{len(todo)}", flush=True)
    requests.post("http://localhost:11434/api/generate", json={"model": JUDGE, "keep_alive": 0}, timeout=60)
    print("done", len(todo))


if __name__ == "__main__":
    main()
