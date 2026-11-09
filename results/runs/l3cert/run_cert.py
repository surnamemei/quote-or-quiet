"""Certificate generation + check on numerical Mintaka questions (closed S21 sets, design data).
Phi-4 (Ollama) proposes quotes + an operation from the S22-pin evidence passage; cert.py checks quotes against pinned local pages and
computes the answer. usage: OLLAMA_HOST_URL=... python -B run_cert.py <set> gen|score"""
import json, os, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(Path(__file__).parent))
N, MODE = sys.argv[1], sys.argv[2]
D = Path(__file__).parent
PROMPT = """You answer a question by a calculation from facts that are written in the passage. Do not use outside knowledge.
Output ONLY a JSON object:
{{"facts":[{{"id":"a","quote":"<words copied exactly from the passage, containing the date, year or number>","kind":"date|year|number"}}, ...],
 "op":"age_at|years_between|diff|sum","args":["a","b"]}}
Rules: each quote must be copied character for character from the passage and contain exactly one date/year/number.
age_at(a,b): a = full birth date, b = full later date (both with day, month, year). years_between(a,b): year(b) - year(a).
diff(a,b): number a minus number b. sum(a,b,...): add numbers.
If the answer is already stated in the passage as a single number, or cannot be computed from facts in the passage, output {{"op":"none"}}.

Passage:
{p}

Question: {q}
JSON:"""


def qtype(q):          # copy of ceiling_dev.qtype (that module has no main guard)
    ql = q.casefold()
    if re.match(r"^(is|are|was|were|did|does|do|has|have|can|will)\b", ql): return "yes/no"
    if re.search(r"\bhow (old|long|far|tall|many years)\b|\bage\b", ql): return "compute"
    if re.search(r"\bhow many\b|\bnumber of\b", ql): return "count"
    return "lookup"


def gen():
    os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535")
    from vkg.llm import chat
    from concurrent.futures import ThreadPoolExecutor
    items = [e for e in json.load(open(ROOT / f"results/runs/s21/{N}.json", encoding="utf-8")) if e["meta"].get("answerType") == "numerical"]
    items = [e for e in items if qtype(e["question"]) in ("compute", "count")]
    ev = json.load(open(ROOT / f"results/runs/s22/pin/{N}_ev_wiki.json", encoding="utf-8"))

    def one(e):
        p = ev.get(e["id"], {}).get("passage")
        if not p:
            return {"id": e["id"], "raw": None}
        raw = chat("phi4", [{"role": "user", "content": PROMPT.format(p=p, q=e["question"])}], temperature=0.0, seed=0,
                   max_tokens=500, think=False, json_mode=False, num_ctx=24576)
        return {"id": e["id"], "raw": raw}
    with ThreadPoolExecutor(2) as ex:
        rows = list(ex.map(one, items))
    with open(D / f"spec_{N}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("gen", N, len(rows), flush=True)


def score():
    import cert
    from vkg import localwiki as LW
    from temporal import time_sensitive
    items = {e["id"]: e for e in json.load(open(ROOT / f"results/runs/s21/{N}.json", encoding="utf-8"))}
    pin = {r["id"]: r for r in map(json.loads, open(ROOT / f"results/runs/s22/pin/{N}_outputs.jsonl", encoding="utf-8"))}
    rp = ROOT / f"results/runs/s22/{N}_releases.jsonl"
    rel = {r["id"]: r for r in map(json.loads, open(rp, encoding="utf-8"))} if rp.exists() else {}
    out = []
    for r in map(json.loads, open(D / f"spec_{N}.jsonl", encoding="utf-8")):
        e = items[r["id"]]; spec = None
        m = re.search(r"\{.*\}", r["raw"] or "", re.S)
        if m:
            try: spec = json.loads(m.group(0))
            except Exception: spec = None
        docs = {t: (LW.page_text(t) or "") for t in pin[r["id"]]["wiki_titles"]}
        ans, c = cert.certify(spec, docs)
        gnum = {re.sub(r"[^\d]", "", g) for g in e["gold"] if re.sub(r"[^\d]", "", g)}
        out.append({"id": r["id"], "q": e["question"], "gold": e["gold"], "certified": ans is not None, "answer": ans,
                    "correct": (ans in gnum) if ans is not None else None, "why": None if ans else c,
                    "time": time_sensitive(e["question"]), "released_already": r["id"] in rel,
                    "released_answer": rel[r["id"]]["answer"] if r["id"] in rel else None,
                    "cert": c if ans else None})
    json.dump(out, open(D / f"cert_{N}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    cs = [o for o in out if o["certified"]]
    print(f"{N}: candidates {len(out)}; certified {len(cs)}; correct {sum(o['correct'] for o in cs)}; wrong {sum(not o['correct'] for o in cs)}; "
          f"new (not released) {sum(not o['released_already'] for o in cs)}; time-sensitive among certified {sum(o['time'] for o in cs)}")
    for o in cs:
        print(" ", "OK " if o["correct"] else "BAD", o["q"][:80], "| gold", o["gold"][:2], "| cert", o["answer"], "| released", o["released_answer"])


{"gen": gen, "score": score}[MODE]()
