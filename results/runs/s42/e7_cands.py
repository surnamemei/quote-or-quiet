"""S42 E7 step 1 (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 8): candidate witnesses. CPU only, no generation.
The frozen gate quotes the FIRST span it accepts. Here every accepted span of the same answer in the pinned pages is listed
(at most 30 per item), each with its displayed quote, the frame check F and three structure flags. Nothing is selected yet.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/e7_cands.py"""
import json, os, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402  (keeps the unused 37 GB embedding table out of RAM)
from vkg import l3_checks2 as C, l3_verify as V, localwiki as LW   # noqa: E402
D = ROOT / "results/runs/s42"; R29 = ROOT / "results/runs/s29/run_fsm"
rows = {r["id"]: r for r in map(json.loads, open(R29 / "wd_outputs.jsonl", encoding="utf-8"))}
items = [json.loads(l) for l in open(D / "e6_items.jsonl", encoding="utf-8")]
DEATH = ["died", "death", "dies", "killed", "executed", "assassinated", "murdered"]
FRAME = {"death_year": DEATH, "birth_place": ["born", "birth", "native"], "birth_year": ["born", "birth"], "director": ["direct"],
         "author": ["writ", "wrote", "author", "novel", "book", "play", "poem", "story", " by "], "capital": ["capital"]}   # as in e6_build.py
YR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
RNG = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\s*(?:–|-|—|to|until)\s*(1[0-9]{3}|20[0-9]{2}|present|incumbent)?", re.I)
MAXC, MAXTRY = 30, 600


def bounds(text, i, j):                      # same rule as C.sentence_at
    a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
    ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
    return a, (min(ends) if ends else len(text))


def window(text, i, j):                      # as in e6_build.py
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


def frame_ok(rel, question, text, i, j):     # as in e6_build.py
    sent = C.sentence_at(text, i, j); low = sent.lower()
    if rel == "office":
        y = int(YR.findall(question)[-1])
        return str(y) in sent or any(int(a) <= y <= (int(b) if b and b.isdigit() else 9999) for a, b in RNG.findall(sent))
    if any(w in low for w in FRAME[rel]):
        return True
    if rel == "death_year":
        return bool(re.search(r"[–—-]\s*[\w ,.]{0,20}$", text[max(0, i - 25):i]))
    if rel == "birth_year":
        return bool(re.match(r"^[\w ,.]{0,20}\s*[–—-]", text[j:j + 25]))
    return False


def norm(s):
    return " ".join(re.findall(r"[a-z0-9]+", s.casefold()))


def title_in_q(title, question):
    t = norm(re.sub(r"\s*\([^)]*\)\s*$", "", title))
    return bool(t) and f" {t} " in f" {norm(question)} "


n_c = n_try = 0
with open(D / "e7_cands.jsonl", "w", encoding="utf-8") as f:
    for n, x in enumerate(items):
        r = rows[x["id"]]; cands = []; tried = 0
        for d in r["wiki_titles"]:
            text = LW.page_text(d)
            if not text:
                continue
            h = V.doc_hash(text); tq = title_in_q(d, x["question"])
            for i, j in V.locate(x["answer"], text):
                if len(cands) >= MAXC or tried >= MAXTRY:
                    break
                tried += 1
                ok, _ = V.verify(x["question"], {"answer": x["answer"], "doc": d, "doc_sha256": h, "start": i, "end": j}, LW.page_text)
                if ok:
                    ok, _ = C.extra(x["question"], text, i, j)
                if not ok:
                    continue
                q, o1, o2 = window(text, i, j)
                cands.append({"doc": d, "start": i, "end": j, "span": text[i:j], "quote": q, "o1": o1, "o2": o2,
                              "F": frame_ok(x["relation"], x["question"], text, i, j), "title_in_q": tq,
                              "sentence": not q.lstrip().startswith(("#", "-", "*", "|", "=")) and len(q) >= 40,
                              "first": d == x["doc"] and q == x["quote"]})
        assert cands and cands[0]["first"], (x["id"], "first accepted span differs from the E6 quote")
        f.write(json.dumps({"id": x["id"], "tried": tried, "cands": cands}, ensure_ascii=False) + "\n")
        n_c += len(cands); n_try += tried
        if n % 300 == 0:
            print(n, "items", n_c, "candidates", flush=True)
print("items", len(items), "| candidates", n_c, "| spans tried", n_try)
