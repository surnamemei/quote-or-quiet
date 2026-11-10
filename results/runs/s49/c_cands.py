"""S49 part C (other corpora): rule R on web pages that are not Wikipedia. For the FRESH-5 releases of the frozen system, the pages the system fetched (cached text,
hash-pinned here), not Wikipedia or a mirror, that contain the released answer as a whole word. The naive display is the first occurrence on the first such page.
CPU only. OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s49/c_cands.py"""
import hashlib, json, os, random, re, sys
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s42"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
import e7_lib as L   # noqa: E402
D = ROOT / "results/runs/s49"
CACHE = ROOT / "results/cache/web"
MIRROR = ("wiki", "explained.today", "alchetron", "grokipedia", "dbpedia", "kiddle", "everybodywiki", "britannica")
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")


def page(url):
    f = CACHE / f"p_{hashlib.sha256(url.encode('utf-8')).hexdigest()}.json"
    return json.loads(f.read_text(encoding="utf-8")).get("text", "") if f.exists() else ""


def window(text, i, j):
    a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
    ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
    b = min(ends) if ends else len(text)
    while a < i and text[a].isspace():
        a += 1
    while b > j and text[b - 1].isspace():
        b -= 1
    if b - a > 300:
        a2 = max(a, min(i - 120, b - 300)); b2 = min(b, a2 + 300)
        if j > b2:
            b2 = j; a2 = max(a, b2 - 300)
        a, b = a2, b2
    return text[a:b]


def shape(a):
    a = str(a).strip()
    return "year" if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", a) else ("number" if re.fullmatch(r"[\d,.]+", a) else "phrase")


rel = {r["id"]: r for r in map(json.loads, open(ROOT / "results/runs/s22/fresh5_releases.jsonl", encoding="utf-8")) if r["source"] == "s19"}
outs = {r["id"]: r for r in map(json.loads, open(ROOT / "results/runs/s19/fresh5_outputs.jsonl", encoding="utf-8")) if r["id"] in rel}
pool = {}
for r in rel.values():
    pool.setdefault(shape(r["answer"]), []).append(str(r["answer"]))
rng = random.Random(4901)
n_pages = n_items = 0
with open(D / "c_cands.jsonl", "w", encoding="utf-8") as f:
    for i, r in rel.items():
        a = str(r["answer"]); cands = []
        pat = re.compile(r"(?<![\w])" + re.escape(a) + r"(?![\w])", re.I)
        for u in outs[i].get("web_kept", []):
            dom = urlparse(u).netloc.lower()
            if any(m in dom for m in MIRROR):
                continue
            text = page(u)
            if not text:
                continue
            h = hashlib.sha256(text.encode("utf-8")).hexdigest()
            for m in list(pat.finditer(text))[:10]:
                if len(cands) >= 20:
                    break
                q = window(text, m.start(), m.end())
                if len(q) < 25:
                    continue
                qt = set(L.toks(q))
                need = [w for w in L.toks(r["question"]) if re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD]
                sp = [x for x in pool[shape(a)] if x.casefold() != a.casefold() and x.casefold() not in q.casefold()]
                sw = rng.choice(sp) if sp else None
                cands.append({"url": u, "domain": dom, "doc": dom, "sha": h, "quote": q,
                              "sent": not q.lstrip().startswith(("#", "-", "*", "|", "=")) and len(q) >= 40,
                              "N": all(w in qt or re.sub(r"\D", "", w) in qt for w in need), "swap": sw,
                              "j": JP.format(t=dom, s=q, q=r["question"], a=a), "j_swap": JP.format(t=dom, s=q, q=r["question"], a=sw) if sw else None})
        n_items += bool(cands); n_pages += len({c["url"] for c in cands})
        f.write(json.dumps({"id": i, "question": r["question"], "answer": a, "cands": cands}, ensure_ascii=False) + "\n")
print("releases", len(rel), "| with a non-Wikipedia page that holds the answer", n_items, "| pages", n_pages)
