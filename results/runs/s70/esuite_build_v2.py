"""Track C, step C1 (v2): the evidence-sensitivity suite. v2 takes base sentences from G14 witness rows that both reviewers judged to state the answer, and every record carries its page title (v1 picked any sentence containing the gold string, many of which did not state the answer to the question) (docs/TRACK_C_CONTEXT_FAITHFUL_PLAN.md). Development data; built from the S65 PopQA questions (gate G14 is finished).
For each base item: the question, and the first sentence of the subject's own Wikipedia page (local snapshot) that holds the gold answer verbatim (sentence of 40 to 400 characters).
Versions (expected behaviour fixed by construction):
  A  original sentence                                   -> answer = original value
  B  the value replaced by another value of the same relation from another item  -> answer = replaced value
  C  the sentence removed                                -> not stated
  D  two records: the original sentence and the replaced one   -> conflict (both values)
  E  the original sentence plus the same sentence about another subject with the replaced value  -> answer = original value
Contexts: 'short' (only the record sentences) and 'long' (about 24,000 characters of sentences from unrelated pages, the records placed at a fixed random position);
question in English, and in Chinese for the short context (Chinese templates per PopQA relation).
Writes results/runs/s70/esuite.jsonl. Prints counts only. OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s70/esuite_build.py"""
import json, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20")]
import no_retrieval2  # noqa: F401
from vkg import localwiki as LW
D = ROOT / "results/runs/s70"; rng = random.Random(7001)
ZH = {"occupation": "{s}的职业是什么？", "place of birth": "{s}出生在哪里？", "genre": "{s}属于什么类型？", "father": "{s}的父亲是谁？", "country": "{s}位于哪个国家？",
      "producer": "{s}的制片人是谁？", "director": "{s}的导演是谁？", "capital of": "{s}是哪里的首都？", "screenwriter": "{s}的编剧是谁？", "composer": "{s}的作曲者是谁？",
      "color": "{s}是什么颜色？", "religion": "{s}信仰什么宗教？", "sport": "{s}从事什么运动？", "author": "{s}的作者是谁？", "mother": "{s}的母亲是谁？", "capital": "{s}的首都是哪里？"}


def sentences(text):
    out = []
    for para in text.split("\n"):
        if not para.strip() or para.lstrip().startswith(("#", "-", "*", "|", "=", ">")):
            continue
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", para.strip()) if 40 <= len(s.strip()) <= 400]
    return out


items = [json.loads(l) for l in open(ROOT / "results/runs/s65/sealed/items.jsonl", encoding="utf-8")]
IT = {e["id"]: e for e in items}
import csv as _csv
K = json.load(open(ROOT / "results/runs/s65/G14_key.json")); base = []; seen = set()
for p in ("1", "2", "3"):
    Sh = {int(r["row"]): r for r in _csv.DictReader(open(ROOT / f"results/runs/s65/G14_sheet_part{p}.csv", encoding="utf-8-sig"))}
    Vv = {}
    for rv in "AB":
        for r in _csv.DictReader(open(ROOT / f"results/runs/s65/G14_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            Vv.setdefault(int(r["row"]), []).append(r["quote_verdict"].strip().casefold())
    for k in K[p]:
        r = Sh[k["row"]]; e = IT[k["id"]]
        if k["kind"] != "witness" or Vv[k["row"]] != ["states", "states"] or e["prop"] not in ZH or k["id"] in seen:
            continue
        if r["answer"].casefold() not in r["quote"].casefold() or len(r["answer"]) < 3:
            continue
        seen.add(k["id"]); base.append({"id": e["id"], "q": e["q"], "prop": e["prop"], "page": e["page"], "value": r["answer"], "sent": r["quote"]})
by = {}
for b in base:
    by.setdefault(b["prop"], []).append(b)
pool_pages = sorted({e["page"] for e in items})
rng.shuffle(base); chosen = []
for b in base:
    others = [o for o in by[b["prop"]] if o["value"].casefold() != b["value"].casefold() and o["value"].casefold() not in b["sent"].casefold() and o["page"] != b["page"]]
    if not others:
        continue
    o = rng.choice(others); b = dict(b, alt=o["value"], alt_page=o["page"]); chosen.append(b)
    if len(chosen) >= 200:
        break
filler_src = []
for t in rng.sample(pool_pages, 300):
    filler_src += [f"[{t}] {x}" for x in sentences(LW.page_text(t) or "")[:15]]
out = []
for b in chosen:
    pat = re.compile(re.escape(b["value"]), re.I)
    s_alt = pat.sub(b["alt"], b["sent"])
    subj_words = b["page"].split(" (")[0]
    s_other = s_alt.replace(subj_words, b["alt_page"].split(" (")[0]) if subj_words in s_alt else None
    T = f"[{b['page']}] "
    versions = {"A": ([T + b["sent"]], "answer", [b["value"]]), "B": ([T + s_alt], "answer", [b["alt"]]), "C": ([], "missing", []),
                "D": ([f"Record 1 {T}{b['sent']}", f"Record 2 {T}{s_alt}"], "conflict", [b["value"], b["alt"]])}
    if s_other and s_other != s_alt:
        To = f"[{b['alt_page']}] "
        versions["E"] = ([T + b["sent"], To + s_other] if rng.random() < 0.5 else [To + s_other, T + b["sent"]], "answer", [b["value"]])
    bad = [x for x in filler_src if b["value"].casefold() not in x.casefold() and b["alt"].casefold() not in x.casefold() and subj_words.casefold() not in x.casefold()]
    rng.shuffle(bad); fill = []; n = 0
    for x in bad:
        if n > 24000:
            break
        fill.append(x); n += len(x) + 1
    pos = rng.randint(0, len(fill))
    zhq = ZH[b["prop"]].format(s=b["page"].split(" (")[0])
    for v, (recs, kind, expect) in versions.items():
        forbid = [b["alt"]] if v in ("A", "E") else ([b["value"]] if v == "B" else ([b["value"], b["alt"]] if v == "C" else []))
        common = {"base": b["id"], "version": v, "kind": kind, "expect": expect, "forbid": forbid, "prop": b["prop"], "subject": b["page"]}
        mat = "\n".join(recs) if recs else f"[{b['page']}] (The material says nothing else about this subject.)"
        out.append({**common, "id": f"{b['id']}|{v}|short|en", "context": "short", "lang": "en", "material": mat, "question": b["q"]})
        out.append({**common, "id": f"{b['id']}|{v}|short|zh", "context": "short", "lang": "zh", "material": mat, "question": zhq})
        out.append({**common, "id": f"{b['id']}|{v}|long|en", "context": "long", "lang": "en", "material": "\n".join(fill[:pos] + (recs if recs else [f"[{b['page']}] (The material says nothing else about this subject.)"]) + fill[pos:]), "question": b["q"]})
with open(D / "esuite_v2.jsonl", "w", encoding="utf-8") as f:
    for x in out:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
from collections import Counter
print("base items", len(chosen), "| prompts", len(out), Counter(x["version"] for x in out), Counter(x["context"] for x in out))
