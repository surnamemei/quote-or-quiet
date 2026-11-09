"""S24 closed-evidence harness, configuration B (reader-role swap; docs/CLOSED_EVIDENCE_SPEC.md addendum).
Identical to closed_run.py (imported, not copied) except who plays which role: the plain and cautious readers are Phi-4 (Ollama) instead of
the 4B, and the veto is Qwen3.8-27B instead of Phi-4. Derivation specifications are still written by Phi-4. Retrieval, the gate, the entity
slot, the certificates and the scoring are the frozen ones from closed_run.py.
  gen   <set>   writes results/runs/s24/alt/<set>_run/gen.jsonl      (GPU, Ollama only; models are used one after the other)
  score <set>   uses closed_run.score on the alt directory
usage: VKG_OLLAMA_URL=http://127.0.0.1:11535 python -B results/runs/s24/closed_run_alt.py <gen|score> <set>"""
import json, os, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "results/runs/s24"))
import closed_run as B

URL = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535")
READER, VETO, SPEC = "phi4", "qwen3.8-27b", "phi4"
ALT = B.D / "alt"
MAXTOK = B.MAXTOK


def gen(name):
    os.environ["OLLAMA_HOST_URL"] = URL
    import requests
    from vkg.lite import PLAIN, CAUTIOUS
    from vkg.llm import chat
    from concurrent.futures import ThreadPoolExecutor
    items, docs = B.load(name); c = B.index(docs); text = {d["title"]: d["text"] for d in docs}; bc = B.bycore_of(docs)
    out = ALT / f"{name}_run"; out.mkdir(parents=True, exist_ok=True)
    rows = []
    for e in items:
        t = B.retrieve(c, docs, e["q"]); p = "\n\n".join(f"[{x}]\n{text[x]}" for x in t)
        rows.append({"id": e["id"], "q": e["q"], "titles": t, "passage": p, "amb": B.namesakes(e["q"], t, bc)})
    jobs = [(i, t) for i, r in enumerate(rows) for t in r["amb"]]

    def call(model, prompt, max_tokens, ctx=8192):
        return chat(model, [{"role": "user", "content": prompt}], temperature=0.0, seed=0, max_tokens=max_tokens, think=False, json_mode=False, num_ctx=ctx)

    def unload(m):
        requests.post(f"{URL}/api/generate", json={"model": m, "keep_alive": 0}, timeout=120)
    with ThreadPoolExecutor(4) as ex:
        plain = list(ex.map(lambda r: B.parse2(call(READER, PLAIN.format(p=r["passage"], q=r["q"]), MAXTOK)), rows))
        caut = list(ex.map(lambda r: B.parse2(call(READER, CAUTIOUS.format(p=r["passage"], q=r["q"]), MAXTOK)), rows))
        dp = list(ex.map(lambda ij: B.parse2(call(READER, PLAIN.format(p=f"[{ij[1]}]\n{text[ij[1]]}", q=rows[ij[0]]["q"]), MAXTOK)), jobs))
        dc = list(ex.map(lambda ij: B.parse2(call(READER, CAUTIOUS.format(p=f"[{ij[1]}]\n{text[ij[1]]}", q=rows[ij[0]]["q"]), MAXTOK)), jobs))
        specs = list(ex.map(lambda r: call(SPEC, B.SPEC_PROMPT.format(p=r["passage"], q=r["q"]), 500) if B.COMPUTE.match(r["q"]) else None, rows))
    unload(READER)
    with ThreadPoolExecutor(4) as ex:
        ph = list(ex.map(lambda r: B.parse2(call(VETO, CAUTIOUS.format(p=r["passage"], q=r["q"]), MAXTOK)), rows))
        dph = list(ex.map(lambda ij: B.parse2(call(VETO, CAUTIOUS.format(p=f"[{ij[1]}]\n{text[ij[1]]}", q=rows[ij[0]]["q"]), MAXTOK)), jobs))
    unload(VETO)
    for r, a, b, p, s in zip(rows, plain, caut, ph, specs):
        r.update({"plain": a, "cautious": b, "phi4": p, "spec": s, "per_doc": {}})
    for (i, t), a, b, p in zip(jobs, dp, dc, dph):
        rows[i]["per_doc"][t] = {"plain": a, "cautious": b, "phi4": p}
    with open(out / "gen.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("alt gen done", name, len(rows), "namesake jobs", len(jobs), flush=True)


def score(name):
    d = ALT / name; d.mkdir(parents=True, exist_ok=True)
    for fn in ("items.jsonl", "docs.jsonl"):
        shutil.copy(B.D / name / fn, d / fn)
    B.D = ALT
    B.score(name)


if __name__ == "__main__":
    {"gen": gen, "score": score}[sys.argv[1]](sys.argv[2])
