"""Closed-book baselines B0/B1 for the revised L1-a (prompts fixed in docs/CRITERIA_REVISION_L1.md before any sealed result).
Qwen3-4B-Instruct-2507 through the generation server (127.0.0.1:18000), greedy, 40 tokens, original parser. Writes run_fsm/wd_closed.jsonl.
python -B results/runs/s29/s29_closed.py"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import pod                     # noqa: E402
from vkg.lite import parse              # noqa: E402
B0 = "Answer the question with a short answer only.\nQuestion: {q}\nAnswer:"
B1 = "Answer the question with a short answer only. If you are not sure of the answer, reply exactly: I don't know.\nQuestion: {q}\nAnswer:"
rows = [json.loads(l) for l in open(ROOT / "results/runs/s29/sealed/items.jsonl", encoding="utf-8")]
rows = [r for r in rows if r["relation"] != "founded"]
assert len(rows) == 3359
o0 = pod.gen([B0.format(q=r["q"]) for r in rows], 40)
o1 = pod.gen([B1.format(q=r["q"]) for r in rows], 40)
with open(ROOT / "results/runs/s29/run_fsm/wd_closed.jsonl", "w", encoding="utf-8") as f:
    for r, a, b in zip(rows, o0, o1):
        f.write(json.dumps({"id": r["id"], "b0": parse(a[0]), "b1": parse(b[0]), "b0_raw": a[0], "b1_raw": b[0]}, ensure_ascii=False) + "\n")
print("closed-book done", len(rows))
