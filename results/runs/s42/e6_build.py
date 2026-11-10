"""S42 E6 (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 7): re-check audit of quotes on the S29 outputs. CPU only, no generation.
For every Verified release and every Qualified item (rule Q) it recomputes the span, takes the displayed quote (the sentence or row
holding the span, at most 300 characters around it), the frame check F, and the two prompts of the quote-only reader G (original quote;
quote with the span replaced by the span of another item of the same relation). Then it draws the blind review sheet.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/e6_build.py"""
import csv, json, os, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402  (keeps the unused 37 GB embedding table out of RAM)
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW   # noqa: E402
from vkg.s12_run import agree                                      # noqa: E402
from vkg.s14_eval import ans                                       # noqa: E402
D = ROOT / "results/runs/s42"; R29 = ROOT / "results/runs/s29/run_fsm"
rows = {r["id"]: r for r in map(json.loads, open(R29 / "wd_outputs.jsonl", encoding="utf-8"))}
REL = {r["id"]: r for r in map(json.loads, open(R29 / "wd_releases.jsonl", encoding="utf-8"))}
QUA = {r["id"]: r for r in map(json.loads, open(D / "E3_qualified.jsonl", encoding="utf-8"))}
DEATH = ["died", "death", "dies", "killed", "executed", "assassinated", "murdered"]
FRAME = {"death_year": DEATH, "birth_place": ["born", "birth", "native"], "birth_year": ["born", "birth"], "director": ["direct"],
         "author": ["writ", "wrote", "author", "novel", "book", "play", "poem", "story", " by "], "capital": ["capital"]}   # as in e4_run.py
YR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
RNG = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\s*(?:–|-|—|to|until)\s*(1[0-9]{3}|20[0-9]{2}|present|incumbent)?", re.I)
GP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\n'
      "Answer in a few words with only what this sentence states. If the sentence does not state the answer to this exact question, reply NONE.")


def bounds(text, i, j):                      # same rule as C.sentence_at
    a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
    ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
    return a, (min(ends) if ends else len(text))


def window(text, i, j):
    """Displayed quote and the span's offsets in it: the sentence, cut to at most 300 characters around the span."""
    a, b = bounds(text, i, j)
    assert text[a:b] == C.sentence_at(text, i, j)
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


def frame_ok(rel, question, text, i, j):
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


items = []
for state, src in (("Verified", REL), ("Qualified", QUA)):
    for i in src:
        r = rows[i]; a, s = S.cand(r)
        rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
        assert rel, (i, "gate no longer passes")
        text = LW.page_text(rec["doc"]); assert text[rec["start"]:rec["end"]] == rec["span"], "quote check failed"
        q, o1, o2 = window(text, rec["start"], rec["end"]); assert q[o1:o2] == rec["span"]
        items.append({"id": i, "state": state, "relation": r["stratum"], "question": r["question"], "answer": str(rel), "doc": rec["doc"],
                      "span": rec["span"], "quote": q, "o1": o1, "o2": o2, "frame_ok": frame_ok(r["stratum"], r["question"], text, rec["start"], rec["end"]),
                      "gold_match": bool(src[i]["grade"]) if state == "Verified" else src[i]["match"].startswith("right")})
    print(state, sum(x["state"] == state for x in items), flush=True)
rng = random.Random(4206)
by = {}
for x in items:
    by.setdefault(x["relation"], []).append(x)
for x in items:                              # replacement span for the swap step of G
    pool = [y for y in by[x["relation"]] if not agree(y["span"], x["span"]) and not agree(y["span"], x["answer"]) and y["span"] not in x["quote"]]
    y = rng.choice(pool)
    x["swap"] = y["span"]; x["swap_quote"] = x["quote"][:x["o1"]] + y["span"] + x["quote"][x["o2"]:]
    x["g_prompt"] = GP.format(t=x["doc"], s=x["quote"], q=x["question"]); x["g_prompt_swap"] = GP.format(t=x["doc"], s=x["swap_quote"], q=x["question"])
with open(D / "e6_items.jsonl", "w", encoding="utf-8") as f:
    for x in items:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
V = [x for x in items if x["state"] == "Verified"]; Q = [x for x in items if x["state"] == "Qualified"]
sv = rng.sample(V, 600); sq = rng.sample(Q, 100); got = {x["id"] for x in sv}
tg = [x for x in V if not x["gold_match"] and x["id"] not in got]
sheet = [dict(kind="verified", **x) for x in sv] + [dict(kind="qualified", **x) for x in sq] + [dict(kind="targeted", **x) for x in tg]
for k in range(60):
    x = rng.choice(V)
    if k < 30:                               # answer of another question of the same relation
        y = rng.choice([y for y in by[x["relation"]] if not agree(y["answer"], x["answer"]) and y["answer"].casefold() not in x["quote"].casefold()])
        sheet.append(dict(x, kind="decoy_answer", answer=y["answer"]))
    else:                                    # question about another subject of the same relation
        y = rng.choice([y for y in by[x["relation"]] if y["doc"] != x["doc"] and not agree(y["answer"], x["answer"])])
        sheet.append(dict(x, kind="decoy_question", question=y["question"]))
rng.shuffle(sheet)
P = 4; key = {}
for p in range(P):
    part = sheet[p::P]
    with open(D / f"E6_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "page_title", "quote"])
        for n, x in enumerate(part, 1):
            w.writerow([n, x["question"], x["answer"], x["doc"], x["quote"]])
    key[str(p + 1)] = [{"row": n, "id": x["id"], "kind": x["kind"]} for n, x in enumerate(part, 1)]
json.dump(key, open(D / "E6_key.json", "w", encoding="utf-8"))
print("items", len(items), "| frame_ok Verified", sum(x["frame_ok"] for x in V), "of", len(V), "| Qualified", sum(x["frame_ok"] for x in Q), "of", len(Q))
print("sheet rows", len(sheet), "| targeted", len(tg), "| parts", [len(sheet[p::P]) for p in range(P)])
