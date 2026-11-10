"""S51: the 4B prompt judge (YES/NO, as in rule R without the swap control) on the test rows of d_pred.json. 4B server on 18000. python -B results/runs/s51/d_judge.py"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
import no_retrieval2  # noqa: F401,E402
from vkg import pod  # noqa: E402
D = ROOT / "results/runs/s51"
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
rows = json.load(open(D / "d_pred.json", encoding="utf-8"))
out = []
for i in range(0, len(rows), 8):
    for t in range(40):
        try:
            out += [o[0] for o in pod.gen([JP.format(t=r["title"], s=r["quote"], q=r["question"], a=r["answer"]) for r in rows[i:i + 8]], 4)]
            break
        except Exception as e:
            print("retry", t, repr(e)[:100], flush=True); time.sleep(30)
    else:
        raise SystemExit("gave up")
    if (i // 8) % 20 == 0:
        print(len(out), "of", len(rows), flush=True)
json.dump(out, open(D / "d_judge.json", "w", encoding="utf-8"))
print("judge done", flush=True)
