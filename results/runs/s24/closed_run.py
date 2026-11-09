"""S24 closed-evidence harness v2 (docs/CLOSED_EVIDENCE_SPEC.md). Stages:
  gen   <set>   BM25 (sqlite FTS5) over the synthetic corpus, top 3 documents as the passage; Qwen3-4B plain + cautious (128 tokens);
                Phi-4 cautious veto. Extra generations: (a) namesake questions (two or more retrieved documents share the name in the
                question and the question names no qualifier): the same three readers on each candidate document alone;
                (b) computed questions ("How old/long/many"): the Phi-4 derivation specification of results/runs/l3cert.
                Writes results/runs/s24/<set>_run/gen.jsonl                                              (GPU; run_closed_dev.sh)
  score <set>   release rule. Ordinary question: plain and cautious agree, Phi-4 agrees, verbatim typed span in a retrieved document
                (V1-V5 via vkg.l3_checks2.release2) -> Verified. Namesake question: every candidate document passes the same rule on its
                own document -> Qualified list "A (E1); B (E2)", otherwise Unresolved. No span and a certifying derivation -> Derived.
                Outcomes against the expected state and exact gold; writes <set>_score.md                 (CPU)
usage: VKG_POD_HOST=local VKG_OLLAMA_URL=http://127.0.0.1:11535 python -B results/runs/s24/closed_run.py <gen|score> <set>"""
import json, os, re, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3cert"))
D = ROOT / "results/runs/s24"
MAXTOK = 128
SPEC_PROMPT = """You answer a question by a calculation from facts that are written in the passage. Do not use outside knowledge.
Output ONLY a JSON object:
{{"facts":[{{"id":"a","quote":"<words copied exactly from the passage, containing the date, year or number>","kind":"date|year|number"}}, ...],
 "op":"age_at|years_between|diff|sum","args":["a","b"]}}
Rules: each quote must be copied character for character from the passage and contain exactly one date/year/number; the date alone (for example "July 21, 1976") is a valid quote.
age_at(a,b): a = full birth date, b = full later date (both with day, month, year). years_between(a,b): year(b) - year(a).
diff(a,b): number a minus number b. sum(a,b,...): add numbers.
If the answer is already stated in the passage as a single number, or cannot be computed from facts in the passage, output {{"op":"none"}}.

Passage:
{p}

Question: {q}"""
COMPUTE = re.compile(r"^\s*how\s+(old|long|many|far|tall)\b", re.I)


def load(name):
    d = D / name
    items = [json.loads(l) for l in open(d / "items.jsonl", encoding="utf-8")]
    docs = [json.loads(l) for l in open(d / "docs.jsonl", encoding="utf-8")]
    return items, docs


def parse2(raw):
    from vkg.lite import parse
    m = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    if m:
        return m.group(1)[:200]
    body = re.sub(r"^\s*```(?:json)?\s*", "", raw).strip()
    if body.startswith("{"):
        return ""
    return parse(body) if body else parse(raw)


def index(docs):
    c = sqlite3.connect(":memory:")
    c.execute("CREATE VIRTUAL TABLE f USING fts5(title, text, tokenize='unicode61')")
    c.executemany("INSERT INTO f(rowid, title, text) VALUES (?,?,?)", [(i, d["title"], d["text"]) for i, d in enumerate(docs)])
    return c


def retrieve(c, docs, q, k=3):
    words = list(dict.fromkeys(w for w in re.findall(r"\w+", q.lower()) if len(w) > 2))
    if not words:
        return []
    m = " OR ".join(f'"{w}"' for w in words)
    return [docs[r[0]]["title"] for r in c.execute("SELECT rowid FROM f WHERE f MATCH ? ORDER BY bm25(f, 5.0, 1.0) LIMIT ?", (m, k))]


def core(t):
    return re.sub(r"\s*\([^()]*\)$", "", t)


def qual(t):
    m = re.search(r"\(([^()]*)\)$", t)
    return m.group(1) if m else ""


def namesakes(q, titles, bycore):
    """Retrieved titles whose name occurs in the question, is shared by another document, and whose qualifier the question does not name."""
    out = []
    for t in titles:
        named = qual(t) and all(w.lower() in q.lower() for w in re.findall(r"\w+", qual(t)) if len(w) > 2)
        if core(t) in q and len(bycore[core(t)]) > 1 and not named:
            out.append(t)
    return out if len({core(t) for t in out}) == 1 and len(out) >= 2 else []


def bycore_of(docs):
    b = defaultdict(set)
    for d in docs:
        b[core(d["title"])].add(d["title"])
    return b


def gen(name):
    os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535")   # before vkg.llm is imported
    from vkg.lite import PLAIN, CAUTIOUS
    from vkg import pod
    from vkg.llm import chat
    from concurrent.futures import ThreadPoolExecutor
    items, docs = load(name); c = index(docs); text = {d["title"]: d["text"] for d in docs}; bc = bycore_of(docs)
    out = D / f"{name}_run"; out.mkdir(exist_ok=True)
    rows = []
    for e in items:
        t = retrieve(c, docs, e["q"]); p = "\n\n".join(f"[{x}]\n{text[x]}" for x in t)
        rows.append({"id": e["id"], "q": e["q"], "titles": t, "passage": p, "amb": namesakes(e["q"], t, bc)})
    # per-document jobs for namesake questions
    jobs = [(i, t) for i, r in enumerate(rows) for t in r["amb"]]
    jp = [f"[{t}]\n{text[t]}" for i, t in jobs]
    base_plain = pod.gen([PLAIN.format(p=r["passage"], q=r["q"]) for r in rows], MAXTOK)
    base_caut = pod.gen([CAUTIOUS.format(p=r["passage"], q=r["q"]) for r in rows], MAXTOK)
    doc_plain = pod.gen([PLAIN.format(p=p, q=rows[i]["q"]) for (i, t), p in zip(jobs, jp)], MAXTOK) if jobs else []
    doc_caut = pod.gen([CAUTIOUS.format(p=p, q=rows[i]["q"]) for (i, t), p in zip(jobs, jp)], MAXTOK) if jobs else []
    pod.unload_gen()

    def phi(prompt, max_tokens):
        return chat("phi4", [{"role": "user", "content": prompt}], temperature=0.0, seed=0, max_tokens=max_tokens,
                    think=False, json_mode=False, num_ctx=8192)
    with ThreadPoolExecutor(4) as ex:
        ph = list(ex.map(lambda r: parse2(phi(CAUTIOUS.format(p=r["passage"], q=r["q"]), MAXTOK)), rows))
        doc_ph = list(ex.map(lambda ij: parse2(phi(CAUTIOUS.format(p=f"[{ij[1]}]\n{text[ij[1]]}", q=rows[ij[0]]["q"]), MAXTOK)), jobs))
        specs = list(ex.map(lambda r: phi(SPEC_PROMPT.format(p=r["passage"], q=r["q"]), 500) if COMPUTE.match(r["q"]) else None, rows))
    for r, a, b, p, s in zip(rows, base_plain, base_caut, ph, specs):
        r.update({"plain": parse2(a[0]), "cautious": parse2(b[0]), "phi4": p, "spec": s, "per_doc": {}})
    for (i, t), a, b, p in zip(jobs, doc_plain, doc_caut, doc_ph):
        rows[i]["per_doc"][t] = {"plain": parse2(a[0]), "cautious": parse2(b[0]), "phi4": p}
    with open(out / "gen.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("gen done", name, len(rows), "namesake jobs", len(jobs), "specs", sum(1 for s in specs if s), flush=True)


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(s).casefold()).split())


def matches(ans, golds):
    a = norm(ans)
    return bool(a) and any(norm(g) and (norm(g) == a or f" {norm(g)} " in f" {a} ") for g in golds)


def score(name):
    from vkg import l3_checks2 as C
    from vkg.s12_run import agree
    from vkg.s14_eval import ans
    import cert
    items, docs = load(name); text = {d["title"]: d["text"] for d in docs}; bc = bycore_of(docs)
    did = {d["id"]: d["title"] for d in docs}
    runs = {r["id"]: r for r in map(json.loads, open(D / f"{name}_run/gen.jsonl", encoding="utf-8"))}
    cnt = Counter(); bytype = defaultdict(Counter); errs = []
    get = lambda t: text.get(t, "")

    def span_release(q, trip, titles):
        a, b, p = trip["plain"], trip["cautious"], trip["phi4"]
        if ans(a) and ans(b) and ans(p) and agree(str(a), str(b)) and agree(str(a), str(p)):
            rel, rec = C.release2(q, a, titles, get)
            if rel:
                return rel, rec["doc"]
        return None, None

    for e in items:
        r = runs[e["id"]]; q = e["q"]; exp = e["state"]; golds = e["gold"]
        state, out = "Unresolved", None
        if r["amb"]:
            ents = []
            for t in r["amb"]:
                rel, doc = span_release(q, r["per_doc"][t], [t])
                if not rel:
                    ents = None; break
                ents.append((rel, doc))
            if ents:
                state, out = "Qualified", ents
        else:
            rel, doc = span_release(q, r, r["titles"])
            if rel:
                state, out = "Verified", (rel, doc)
            elif r.get("spec"):
                m = re.search(r"\{.*\}", r["spec"], re.S)
                try:
                    spec = json.loads(m.group(0)) if m else None
                except Exception:
                    spec = None
                val, cert_ = cert.certify(spec, {t: text.get(t, "") for t in r["titles"]}) if spec else (None, "bad json")
                if val is not None:
                    state, out = "Derived", (val, None)
        if state == "Unresolved":
            res = "unresolved_ok" if exp == "Unresolved" else "lost"
        elif state in ("Verified", "Derived"):
            res = "verified_correct" if exp in ("Verified", "Derived") and matches(out[0], golds) else "SILENT_ERROR"
        else:
            if exp == "Qualified":
                good = True
                for rel, doc in out:
                    i = next((k for k, dd in enumerate(e["docs"]) if did[dd] == doc), None)
                    good &= i is not None and i < len(golds) and matches(rel, [golds[i]])
                res = "qualified_ok" if good else "SILENT_ERROR"
            else:
                res = "SILENT_ERROR"
        cnt[res] += 1; bytype[(exp, " ".join(q.split()[:2]), state)][res] += 1
        if res == "SILENT_ERROR":
            errs.append(f"- [{exp}] {q} | gold {golds[:2]} | state {state} {out}")
    n = len(items)
    L = [f"# S24 closed-evidence score on {name} (n = {n}; harness v2)", "", "| outcome | count |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(cnt.items())]
    ok = cnt["verified_correct"] + cnt["qualified_ok"]
    L += ["", f"silent errors {cnt['SILENT_ERROR']} of {n} ({100*cnt['SILENT_ERROR']/n:.1f}%); completion (correct Verified/Derived + Qualified-ok) {ok} of {n} ({100*ok/n:.1f}%)",
          "", "By expected state, question opening and output state:", "", "| expected | question | state | outcomes |", "|---|---|---|---|"]
    for (exp, qs, st), c in sorted(bytype.items()):
        L.append(f"| {exp} | {qs} | {st} | " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) + " |")
    L += ["", "Silent errors:"] + errs
    (D / f"{name}_score.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:30]))


if __name__ == "__main__":
    {"gen": gen, "score": score}[sys.argv[1]](sys.argv[2])
