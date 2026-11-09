"""Phi-4 cautious reader on the combo passages that vkg.s17_run built for a set (same settings as the S19 run_test.sh call:
CAUTIOUS template, greedy, 40 tokens, num_ctx 24576, via vkg.llm.chat on Ollama 11435). usage: python -B phi4_dev.py <set>"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations")
sys.path.insert(0, str(ROOT))
os.environ["OLLAMA_HOST_URL"] = "http://127.0.0.1:11435"
from vkg.lite import CAUTIOUS, parse  # noqa: E402
from vkg.llm import chat  # noqa: E402
name = sys.argv[1]
items = json.load(open(ROOT / f"results/runs/s21/{name}.json", encoding="utf-8"))
ev = json.load(open(ROOT / f"results/runs/s19/{name}_ev_combo.json", encoding="utf-8"))
out_f = ROOT / f"results/shared_eval/readers/s21{name}_combo_cautious_phi4.jsonl"


def one(e):
    p = ev.get(e["id"], {}).get("passage")
    rec = {"id": e["id"], "question": e["question"], "gold": e["gold"], "answer": None}
    if p:
        raw = chat("phi4", [{"role": "user", "content": CAUTIOUS.format(p=p, q=e["question"])}], temperature=0.0, seed=0, max_tokens=40,
                   think=False, json_mode=False, num_ctx=24576)
        rec["answer"], rec["raw"] = parse(raw), raw
    return rec


with ThreadPoolExecutor(4) as ex:
    rows = list(ex.map(one, items))
with open(out_f, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("phi4 rows", len(rows), "->", out_f.name)
