"""S57 G6 hop 1 (copy of results/runs/s46/e9_run.py; birth_place frame added, seed 5707). S46 part B: one answer per reading. For every reading page of an ambiguous name: the 4B reader answers the question from the first 3,000
characters of that page (plain and cautious prompts, both must answer and agree), the answer is located as a typed verbatim span, and the E7 rule W1
(frame check, subject link, quote-only reader) chooses the witness among up to four accepted spans. Stage A reader answers, stage B quote-only reader.
4B server on 18000. python -B results/runs/s57/g6b/e9_run.py"""
import json, os, random, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s42"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import pod, l3_checks2 as C, l3_verify as V, localwiki as LW   # noqa: E402
from vkg.lite import parse, PLAIN, CAUTIOUS                            # noqa: E402
from vkg.s12_run import agree                                          # noqa: E402
from vkg.s14_eval import ans                                           # noqa: E402
import e7_lib as L                                                     # noqa: E402
D = ROOT / "results/runs/s57/g6b"
items = [json.loads(l) for l in open(D / "e9_items.jsonl", encoding="utf-8")]
FRAME = {"director": ["direct"], "birth_year": ["born", "birth"], "birth_place": ["born", "birth", "native"]}   # S57 G6: birth_place frame as in S40 W1
YR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")


def gpu_used():
    import subprocess
    try:
        return int(subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits".split(), capture_output=True, text=True).stdout.strip()) / 1024
    except Exception:
        return 0.0


def gen_resilient(batch, n=40, tries=40):
    import requests
    for t in range(tries):
        try:
            if gpu_used() > 27:
                pod.unload_gen(); print("gpu busy elsewhere: 4B unloaded, waiting", time.strftime("%H:%M"), flush=True)
                while gpu_used() > 10:
                    time.sleep(120)
            return pod.gen(batch, n)
        except (requests.exceptions.RequestException, RuntimeError) as e:
            print("chunk retry", t, repr(e)[:160], flush=True); time.sleep(45)
    raise SystemExit("e9 gave up")


def run(prompts, name, n, step=100):
    PF = D / f"e9_{name}_part.json"
    part = json.load(open(PF, encoding="utf-8")) if PF.exists() else []
    while len(part) < len(prompts):
        part += [o[0] for o in gen_resilient(prompts[len(part):len(part) + step], n)]
        json.dump(part, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
        print(name, len(part), "of", len(prompts), flush=True)
    return part


def frame_ok(rel, text, i, j):
    sent = C.sentence_at(text, i, j); low = sent.lower()
    if any(w in low for w in FRAME[rel]):
        return True
    if rel == "birth_year":
        return bool(re.match(r"^[\w ,.]{0,20}\s*[–—-]", text[j:j + 25]))
    return False


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
    return text[a:b], i - a, j - a


def reading_q(x, t):
    """The question as it is asked of one reading: for films the title with its qualifier (so that the year in the title is in the question, as gate check V4 requires)."""
    return f"Who directed the film {t}?" if x["relation"] == "director" else x["question"]


R = [(dict(x, question=reading_q(x, t)), t) for x in items for t in x["readings"]]
t0 = time.time()
# stage A: reader answers from the reading page
pa = []
for x, t in R:
    p = f"[{t}] " + (LW.page_text(t) or "")[:3000]
    pa += [PLAIN.format(p=p, q=x["question"]), CAUTIOUS.format(p=p, q=x["question"])]
oa = run(pa, "a", 40, 8)
res = []
for n, (x, t) in enumerate(R):
    a1, a2 = parse(oa[2 * n]), parse(oa[2 * n + 1])
    a = a1 if (ans(a1) and ans(a2) and agree(a1, a2)) else None
    res.append({"id": x["id"], "reading": t, "question": x["question"], "answer": a and str(a1).strip()})
print("answered readings", sum(bool(r["answer"]) for r in res), "of", len(res), f"{time.time()-t0:.0f}s", flush=True)
# stage B: candidates (accepted spans) and the quote-only reader checks
rng = random.Random(5711)
pool = {rel: [r["answer"] for r, (x, _) in zip(res, R) if r["answer"] and x["relation"] == rel] for rel in FRAME}
keys, pb = [], []
for r, (x, t) in zip(res, R):
    r["cands"] = []
    if not r["answer"]:
        continue
    text = LW.page_text(t) or ""; h = V.doc_hash(text) if text else None
    for i, j in list(V.locate(r["answer"], text) if text else [])[:40]:
        if len(r["cands"]) >= 4:
            break
        ok, _ = V.verify(x["question"], {"answer": r["answer"], "doc": t, "doc_sha256": h, "start": i, "end": j}, LW.page_text)
        if ok:
            ok, _ = C.extra(x["question"], text, i, j)
        if not ok:
            continue
        q, o1, o2 = window(text, i, j)
        sw = rng.choice([a for a in pool[x["relation"]] if not agree(a, r["answer"]) and a not in q] or ["1900"])
        c = {"doc": t, "quote": q, "o1": o1, "o2": o2, "span": text[i:j], "F": frame_ok(x["relation"], text, i, j),
             "S": L.subject_link(x["question"], t, q)}
        xx = {"relation": x["relation"], "question": x["question"], "answer": r["answer"], "swap": sw}
        c["swap"] = sw
        r["cands"].append(c)
        keys.append((len(res), len(r["cands"]) - 1)); pb += L.prompts(xx, c)
# index fix: keys must point at the reading's position
keys = []; pb = []
for n, (r, (x, t)) in enumerate(zip(res, R)):
    for k, c in enumerate(r["cands"]):
        xx = {"relation": x["relation"], "question": x["question"], "answer": r["answer"], "swap": c["swap"]}
        keys.append((n, k)); pb += L.prompts(xx, c)
ob = run(pb, "b", 24)
for m, (n, k) in enumerate(keys):
    res[n]["cands"][k]["out"] = [parse(o) for o in ob[4 * m:4 * m + 4]]
json.dump(res, open(D / "e9_out.json", "w", encoding="utf-8"), ensure_ascii=False)
print("e9 done", f"{time.time()-t0:.0f}s", flush=True)
