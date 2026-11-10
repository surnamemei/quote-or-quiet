"""S42 exploratory (post hoc on S29): questions with a year. Does the quoted sentence hold that year or a range that covers it?
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/temporal.py"""
import json, os, re, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa
from abstain_dev import grade
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW
D = ROOT / "results/runs/s29/run_fsm"
rows = {r["id"]: r for r in map(json.loads, open(D / "wd_outputs.jsonl", encoding="utf-8"))}
REL = {r["id"]: r for r in map(json.loads, open(D / "wd_releases.jsonl", encoding="utf-8"))}
Q = {r["id"]: r for r in map(json.loads, open(ROOT / "results/runs/s42/E3_qualified.jsonl", encoding="utf-8"))}
YR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
RNG = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\s*(?:–|-|—|to|until)\s*(1[0-9]{3}|20[0-9]{2}|present|incumbent)?", re.I)
def covers(sent, y):
    if str(y) in sent: return "year"
    for a, b in RNG.findall(sent):
        hi = 9999 if (not b or not b.isdigit()) else int(b)
        if int(a) <= y <= hi: return "range"
    return None
n_y = Counter(); T = Counter(); ex = []
for i, r in rows.items():
    ys = YR.findall(r["question"])
    if not ys: continue
    n_y[r["stratum"]] += 1
    st = "Verified" if i in REL else "Qualified" if i in Q else None
    if not st: continue
    a = REL[i]["answer"] if i in REL else Q[i]["answer"]
    rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
    if not rel: T[(st, "gate differs")] += 1; continue
    text = LW.page_text(rec["doc"]); sent = C.sentence_at(text, rec["start"], rec["end"])
    c = covers(sent, int(ys[0])) or "none"
    g = grade(r["question"], r["gold"], a)
    T[(st, c, "right" if g is True else "wrong" if g is False else "?")] += 1
    if len(ex) < 14 and (g is False or c == "none"): ex.append((st, c, g, r["question"], r["gold"][:1], a, sent.strip()[:220]))
print("questions with a year by relation:", dict(n_y))
for k in sorted(T): print(k, T[k])
for e in ex: print(e)
