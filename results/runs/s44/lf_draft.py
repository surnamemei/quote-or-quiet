"""S37: draft biographies (FActScore prompt "Tell me a bio of <name>.") with Phi-4 on the CPU-only Ollama (127.0.0.1:11537), greedy, 350 tokens.
Closed book: the pilot measures decomposition, not answer quality. Writes drafts.jsonl (resumable). python -B results/runs/s37/lf_draft.py"""
import json
import requests as _rq


def _gen(payload):
    """GPU instance (11538) while it is up, otherwise the CPU-only instance (11537); same model, greedy, same options."""
    for port in (11540,):
        try:
            return _rq.post(f"http://127.0.0.1:{port}/api/generate", json=payload, timeout=3600).json()
        except Exception:
            continue
    raise RuntimeError("no Ollama instance reachable")


from pathlib import Path
D = Path(__file__).parent
people = json.load(open(D / "people.json", encoding="utf-8"))
out = D / "drafts.jsonl"
done = {json.loads(l)["name"] for l in open(out, encoding="utf-8")} if out.exists() else set()
for name in people:
    if name in done:
        continue
    r = _gen({"model": "phi4", "prompt": f"Tell me a bio of {name}.", "stream": False,
                      "options": {"temperature": 0, "seed": 0, "num_predict": 350}})
    with open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps({"name": name, "draft": r["response"]}, ensure_ascii=False) + "\n")
    print(name, r.get("eval_count"), flush=True)
print("drafts done")
