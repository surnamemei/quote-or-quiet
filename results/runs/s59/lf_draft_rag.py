"""S59 G8 (copy of results/runs/s47/lf_draft_rag.py; topic pages instead of people: 'tell me about' instead of 'tell me a bio of'). S45: grounded drafts. Phi-4 on Ollama (11540), greedy, 350 tokens. The model sees the first 14,000 characters of the subject's own local Wikipedia page
and is told to use only that text. Everything after the draft (decomposition, rule W4) is unchanged. Writes drafts_rag.jsonl (resumable).
python -B results/runs/s45/lf_draft_rag.py"""
import json, sys
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401
from vkg import localwiki as LW
D = Path(__file__).parent
people = json.load(open(D / "people.json", encoding="utf-8"))
out = D / "drafts_rag.jsonl"
done = {json.loads(l)["name"] for l in open(out, encoding="utf-8")} if out.exists() else set()
P = ("Wikipedia article text:\n\"\"\"\n{t}\n\"\"\"\n\nUsing only facts stated in the article text above, tell me about {n}. "
     "Write 6 to 10 plain sentences and do not add anything that is not in the text.")
for name in people:
    if name in done:
        continue
    text = (LW.page_text(name) or "")[:14000]
    r = requests.post("http://127.0.0.1:11540/api/generate", json={"model": "phi4", "prompt": P.format(t=text, n=name), "stream": False,
                      "options": {"temperature": 0, "seed": 0, "num_predict": 350, "num_ctx": 8192}}, timeout=3600).json()
    with open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps({"name": name, "draft": r["response"]}, ensure_ascii=False) + "\n")
    print(name, r.get("eval_count"), flush=True)
print("drafts done")
