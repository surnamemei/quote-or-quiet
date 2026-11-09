"""Judge labels (alias-aware, same judge and procedure as the S29 alias stage) for the closed-book answers B0/B1. Needs Ollama with the judge on VKG_OLLAMA_URL.
python -B results/runs/s40/s40_closed_judge.py"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535")
from vkg import pod                       # noqa: E402
from vkg.s21_judge import needed, J       # noqa: E402
gold = {r["id"]: (r["q"], r["gold"]) for r in map(json.loads, open(ROOT / "results/runs/s40/sealed/items.jsonl", encoding="utf-8"))}
todo = []
for r in map(json.loads, open(ROOT / "results/runs/s40/run_fsm/w3_closed.jsonl", encoding="utf-8")):
    q, g = gold[r["id"]]
    for k in ("b0", "b1"):
        for t in needed(q, g, r.get(k)):
            if t not in todo:
                todo.append(t)
print("closed-book judge labels", len(todo), flush=True)
with open(ROOT / "results/grader5/judge_grades.jsonl", "a", encoding="utf-8") as f:
    for s in range(0, len(todo), 32):
        part = todo[s:s + 32]
        for (q, g, a), gr in zip(part, pod.judge_many(part, 2)):
            f.write(json.dumps({"question": q, "gold": g, "answer": a, "grade": gr}, ensure_ascii=False) + "\n")
            J[(q, g, a)] = gr
        f.flush()
pod.unload_judge()
print("closed-book judge done")
