"""S52 (rule R on Mintaka releases): candidates for rule R on the 601 Mintaka test releases of the frozen system. CPU only.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s52/m_cands.py"""
import json, os, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s42"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import l3_checks2 as C, l3_verify as V, localwiki as LW   # noqa: E402
import e7_lib as L   # noqa: E402
D = ROOT / "results/runs/s52"
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")


def bounds(text, i, j):
    a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
    ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
    return a, (min(ends) if ends else len(text))


def window(text, i, j):
    a, b = bounds(text, i, j)
    while a < i and text[a].isspace():
        a += 1
    while b > j and text[b - 1].isspace():
        b -= 1
    if b - a > 300:
        a2 = max(a, min(i - 120, b - 300)); b2 = min(b, a2 + 300)
        if j > b2:
            b2 = j; a2 = max(a, b2 - 300)
        a, b = a2, b2
    return text[a:b], i - a, j - a


def shape(a):
    a = str(a).strip()
    if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", a):
        return "year"
    if re.fullmatch(r"[\d,.]+", a):
        return "number"
    return "phrase"


rel = [json.loads(l) for l in open(ROOT / "results/runs/s22/mintaka_test_releases.jsonl", encoding="utf-8")]
rel = [r for r in rel if r["source"] == "s19"]
pool = {}
for r in rel:
    pool.setdefault(shape(r["answer"]), []).append(str(r["answer"]))
rng = random.Random(5201)
n_first = 0
with open(D / "m_cands.jsonl", "w", encoding="utf-8") as f:
    for r in rel:
        cands, tried = [], 0
        for d in r["wiki_titles"]:
            text = LW.page_text(d)
            if not text:
                continue
            h = V.doc_hash(text)
            for i, j in V.locate(str(r["answer"]), text):
                if len(cands) >= 30 or tried >= 600:
                    break
                tried += 1
                ok, _ = V.verify(r["question"], {"answer": str(r["answer"]), "doc": d, "doc_sha256": h, "start": i, "end": j}, LW.page_text)
                if ok:
                    ok, _ = C.extra(r["question"], text, i, j)
                if not ok:
                    continue
                q, o1, o2 = window(text, i, j)
                qt = set(L.toks(q))
                need = [w for w in L.toks(r["question"]) if re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD]
                sp = [a for a in pool[shape(r["answer"])] if a.casefold() != str(r["answer"]).casefold() and a.casefold() not in q.casefold()]
                sw = rng.choice(sp) if sp else None
                cands.append({"doc": d, "quote": q, "span": text[i:j], "sent": not q.lstrip().startswith(("#", "-", "*", "|", "=")) and len(q) >= 40,
                              "N": all(w in qt or re.sub(r"\D", "", w) in qt for w in need), "swap": sw,
                              "j": JP.format(t=d, s=q, q=r["question"], a=r["answer"]), "j_swap": JP.format(t=d, s=q, q=r["question"], a=sw) if sw else None})
        n_first += bool(cands) and cands[0]["doc"] == r["release_doc"]
        f.write(json.dumps({"id": r["id"], "question": r["question"], "answer": str(r["answer"]), "grade": r["grade"], "cands": cands}, ensure_ascii=False) + "\n")
print("releases", len(rel), "| first accepted span is in the release doc", n_first, "| with candidates", sum(1 for l in open(D / "m_cands.jsonl", encoding="utf-8") if json.loads(l)["cands"]))
