"""S55: the 27B (Ollama 11540) labels the silver rows with the YES/NO prompt of rule R. python -B results/runs/s55/silver_label.py"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
from vkg.llm import chat
D = ROOT / "results/runs/s55"
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
rows = [json.loads(l) for l in open(D / "silver_rows.jsonl", encoding="utf-8")]
PF = D / "silver_labels.json"
done = json.load(open(PF)) if PF.exists() else []
t0 = time.time()
while len(done) < len(rows):
    r = rows[len(done)]
    for t in range(20):
        try:
            o = chat("qwen3.8-27b", [{"role": "user", "content": JP.format(t=r["title"], s=r["quote"], q=r["question"], a=r["answer"])}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=600)
            break
        except Exception as e:
            print("retry", t, repr(e)[:100], flush=True); time.sleep(30)
    else:
        raise SystemExit("gave up")
    done.append(str(o).strip().upper().startswith("YES"))
    if len(done) % 200 == 0:
        json.dump(done, open(PF, "w")); print(len(done), "of", len(rows), f"{time.time()-t0:.0f}s", flush=True)
json.dump(done, open(PF, "w"))
print("labelled", len(done), "YES", sum(done), flush=True)
