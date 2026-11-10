"""S43 part A (docs/S43_LONGFORM_AND_AMBIGUITY_PLAN.md): candidate witnesses for the slots of the 50 design biographies. CPU only.
Evidence is the subject's own page. Every accepted span of the value (and, for dates, of the other day-month order) in page order, at most six.
Writes s43_cands.jsonl with the two reader prompts per candidate.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s43/s43_cands.py"""
import json, os, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import l3_checks2 as C, l3_verify as V, localwiki as LW   # noqa: E402
D = ROOT / "results/runs/s43"
MON = "January February March April May June July August September October November December".split()
MAXC = 6
GP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\n'
      "Answer in a few words with only what this sentence states. If the sentence does not state the answer to this exact question, reply NONE.")


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


def variants(v):
    out = [v]
    m = re.fullmatch(r"(%s) (\d{1,2}), (\d{4})" % "|".join(MON), v)
    if m:
        out.append(f"{int(m.group(2))} {m.group(1)} {m.group(3)}")
    m = re.fullmatch(r"(\d{1,2}) (%s) (\d{4})" % "|".join(MON), v)
    if m:
        out.append(f"{m.group(2)} {int(m.group(1))}, {m.group(3)}")
    return out


slots = []
for b in map(json.loads, open(ROOT / "results/runs/s37/slots2.jsonl", encoding="utf-8")):
    for n, c in enumerate(b["claims"]):
        slots.append({"id": f"{b['name']}#{n}", "person": b["name"], "question": c["question"], "value": str(c["value"]).strip().strip("'\""), "type": c.get("type", "?")})
rng = random.Random(4301)
by = {}
for s in slots:
    by.setdefault(s["type"], []).append(s)
n_c = n_with = 0
with open(D / "s43_cands.jsonl", "w", encoding="utf-8") as f:
    for s in slots:
        text = LW.page_text(s["person"]); cands = []
        if text and s["value"]:
            h = V.doc_hash(text); found = []
            for var in variants(s["value"]):
                for i, j in V.locate(var, text):
                    found.append((i, j, var))
            for i, j, var in sorted(found)[:60]:
                if len(cands) >= MAXC:
                    break
                ok, _ = V.verify(s["question"], {"answer": var, "doc": s["person"], "doc_sha256": h, "start": i, "end": j}, LW.page_text)
                if ok:
                    ok, _ = C.extra(s["question"], text, i, j)
                if not ok:
                    continue
                q, o1, o2 = window(text, i, j)
                pool = [y for y in by[s["type"]] if y["person"] != s["person"] and y["value"].casefold() != s["value"].casefold() and y["value"].casefold() not in q.casefold()]
                sw = rng.choice(pool)["value"] if pool else None
                gp = GP.format(t=s["person"], s=q, q=s["question"])
                gps = GP.format(t=s["person"], s=q[:o1] + sw + q[o2:], q=s["question"]) if sw else None
                cands.append({"start": i, "end": j, "span": text[i:j], "quote": q, "o1": o1, "o2": o2, "swap": sw, "g_prompt": gp, "g_prompt_swap": gps})
        n_c += len(cands); n_with += bool(cands)
        f.write(json.dumps({**s, "cands": cands}, ensure_ascii=False) + "\n")
print("slots", len(slots), "| with a candidate", n_with, "| candidates", n_c)
