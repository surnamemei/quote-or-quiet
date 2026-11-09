"""S28 training data (docs/S28_PLAN.md): (question, sentence, span, label) from the SimpleQA design pool only (S18 sets fresh3 and fresh4, dev, fresh).
Positive: a gold alias occurring verbatim in a sentence of a retrieved page. Hard negatives: other typed spans (years, numbers, capitalised names) from that sentence,
and typed spans of the same kind from other sentences of the page that share words with the question. No FRESH-5, Mintaka or PopQA item is read.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s29/s28_data.py   (idle priority; loads local wiki pages)"""
import json, os, random, re, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
from vkg import localwiki as LW, l3_verify as V, l3_checks2 as C

OUT = ROOT / "results/runs/s29/s28_train.jsonl"
SRC = [("s17", "fresh3"), ("s17", "fresh4"), ("s19", "dev"), ("s19", "fresh")]
YEAR = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)")
NUM = re.compile(r"(?<![\d.,])\d{1,3}(?:,\d{3})*(?:\.\d+)?(?![\d])")
NAME = re.compile(r"\b[A-Z][a-zA-Z'\-]+(?:\s+(?:of|de|van|von|the)?\s*[A-Z][a-zA-Z'\-]+)*")
STOP = set("the a an of in on at to for and or is was were are who what when where which how many much did does do has have had".split())


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.casefold()) if w not in STOP and len(w) > 2}


def spans_of(sentence, kind):
    if kind == "year":
        return [m.group(0) for m in YEAR.finditer(sentence)]
    if kind == "number":
        return [m.group(0) for m in NUM.finditer(sentence)]
    return [m.group(0) for m in NAME.finditer(sentence) if len(m.group(0)) > 2]


def kind_of(gold):
    g = gold.strip()
    if re.fullmatch(r"(1[0-9]{3}|20[0-9]{2})", g):
        return "year"
    if re.fullmatch(r"[\d,\.]+", g):
        return "number"
    return "name"


rng = random.Random(28)
rows = []
for pre, name in SRC:
    p = ROOT / "results/runs" / pre / f"{name}_outputs.jsonl"
    for r in map(json.loads, open(p, encoding="utf-8")):
        q, golds = r["question"], [str(g) for g in r["gold"]][:9]
        qw = words(q)
        for t in r["wiki_titles"][:5]:
            text = LW.page_text(t) or ""
            found = None
            for g in golds:
                hit = next(V.locate(g, text), None)
                if hit:
                    found = (g, hit); break
            if not found:
                continue
            g, (i, j) = found
            sent = C.sentence_at(text, i, j).strip()
            if not (20 <= len(sent) <= 600):
                continue
            kind = kind_of(g)
            rows.append({"id": r["id"], "set": name, "question": q, "sentence": sent, "span": text[i:j], "label": 1, "kind": kind})
            neg = [s for s in spans_of(sent, kind) if s.casefold() != g.casefold() and g.casefold() not in s.casefold() and s.casefold() not in g.casefold()]
            others = []
            for s2 in re.split(r"(?<=[.!?])\s+", text[:60000]):
                if 20 <= len(s2) <= 600 and s2.strip() != sent and len(words(s2) & qw) >= 2:
                    for sp in spans_of(s2, kind):
                        if sp.casefold() != g.casefold():
                            others.append((s2.strip(), sp))
            rng.shuffle(others)
            for sp in neg[:2]:
                rows.append({"id": r["id"], "set": name, "question": q, "sentence": sent, "span": sp, "label": 0, "kind": kind})
            for s2, sp in others[:2]:
                rows.append({"id": r["id"], "set": name, "question": q, "sentence": s2, "span": sp, "label": 0, "kind": kind})
            break
with open(OUT, "w", encoding="utf-8") as f:
    for x in rows:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
print("examples", len(rows), dict(Counter(x["label"] for x in rows)), dict(Counter(x["kind"] for x in rows)), "questions", len({x["id"] for x in rows}))
