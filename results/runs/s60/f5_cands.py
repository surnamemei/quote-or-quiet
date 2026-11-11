"""S43 part C (W4 sealed test, S44): sentence-level candidate witnesses. CPU only.
For each slot: the three sentences of the subject's page with the highest content-word overlap with the draft sentence of the slot
(sentences only: no table rows, headings, list lines; at least 40 characters), the number/year/ordinal check N, and two judge prompts per
candidate (value, and the same sentence with a value of the same type from another subject).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s43/f5_cands.py"""
import json, os, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s42"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import localwiki as LW   # noqa: E402
import e7_lib as L                # noqa: E402
D = ROOT / "results/runs/s60"
STOP = set("""a an the of in on at to for from by with and or but is are was were be been being he she it they his her their its this that these those as
has have had not no also which who whom whose when where what how into than then there here after before during over under about between""".split())
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")


def words(s):
    return {w for w in L.toks(s) if w not in STOP and len(w) > 2}


def sentences(text):
    out = []
    for para in text.split("\n"):
        if para.lstrip().startswith(("#", "-", "*", "|", "=", ">")) or not para.strip():
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", para.strip()):
            if len(s) >= 40:
                out.append(s[:400])
    return out


slots = []
for b in map(json.loads, open(ROOT / "results/runs/s60/slots2_rag.jsonl", encoding="utf-8")):
    for n, c in enumerate(b["claims"]):
        slots.append({"id": f"{b['name']}#{n}", "person": b["name"], "question": c["question"], "value": str(c["value"]).strip().strip("'\""),
                      "type": c.get("type", "?"), "draft": b["sentences"][c["sentence"] - 1]})
rng = random.Random(6004); by = {}
for s in slots:
    by.setdefault(s["type"], []).append(s)
cache = {}
n_c = 0
with open(D / "f5_cands.jsonl", "w", encoding="utf-8") as f:
    for s in slots:
        if s["person"] not in cache:
            cache[s["person"]] = sentences(LW.page_text(s["person"]) or "")
        dw = words(s["draft"]) | words(s["value"])
        name = set(L.toks(s["person"]))
        need = [w for w in L.toks(s["question"]) if (re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD) and w not in name]
        sc = sorted(((len(dw & words(x)), i) for i, x in enumerate(cache[s["person"]])), key=lambda t: (-t[0], t[1]))[:3]
        cands = []
        for ov, i in sc:
            if ov < 2:
                continue
            q = cache[s["person"]][i]; qt = set(L.toks(q))
            pool = [y for y in by[s["type"]] if y["person"] != s["person"] and y["value"].casefold() != s["value"].casefold() and y["value"].casefold() not in q.casefold()]
            sw = rng.choice(pool)["value"] if pool else None
            cands.append({"quote": q, "overlap": ov, "N": all(w in qt or re.sub(r"\D", "", w) in qt for w in need), "swap": sw,
                          "j": JP.format(t=s["person"], s=q, q=s["question"], a=s["value"]),
                          "j_swap": JP.format(t=s["person"], s=q, q=s["question"], a=sw) if sw else None})
        n_c += len(cands)
        f.write(json.dumps({**s, "cands": cands}, ensure_ascii=False) + "\n")
print("slots", len(slots), "| candidates", n_c)
