"""S40 secondary analyses registered in docs/S40_PLAN.md on 2026-11-10 (before any S40 run), from docs/S42_CLAIM_AUDIT_AND_PLAN.md.
Rule Q on top of version 2: a question that version 2 does not release becomes Qualified if the max-support candidate passes the deductive
gate. Predictions: adds 4 to 10 points; the quoted answer matches gold in 78 to 92% of Qualified items.
Rule T: a release for a question that names a year moves to Qualified unless the quoted sentence holds that year or a covering range.
Prediction: at most 10 releases moved. Gold-relative with the cached labels; no new generation. CPU, idle priority.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s40/s40_q.py w3"""
import json, os, re, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from abstain_dev import grade                                      # noqa: E402
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW   # noqa: E402
from vkg.s12_run import agree                                      # noqa: E402
from vkg.s14_eval import ans                                       # noqa: E402
from vkg.s21_judge import aliases                                  # noqa: E402
name = sys.argv[1]
D = ROOT / "results/runs/s40/run_fsm"
rows = {r["id"]: r for r in map(json.loads, open(D / f"{name}_outputs.jsonl", encoding="utf-8"))}
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_phi4.jsonl", encoding="utf-8"))}
REL = {r["id"]: r for r in map(json.loads, open(D / f"{name}_releases.jsonl", encoding="utf-8"))}     # version 2 after s40_merge.py
YR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
RNG = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\s*(?:–|-|—|to|until)\s*(1[0-9]{3}|20[0-9]{2}|present|incumbent)?", re.I)


def gmatch(r, v):
    g = grade(r["question"], r["gold"], v)
    if g == "?":
        return "right*" if any(agree(str(v), a) for a in aliases(r["gold"])) else "wrong*"
    return "right" if g else "wrong"


def covers(sent, y):
    return str(y) in sent or any(int(a) <= y <= (int(b) if b and b.isdigit() else 9999) for a, b in RNG.findall(sent))


Q = {}
for i, r in rows.items():
    if i in REL:
        continue
    a, s = S.cand(r)
    if not ans(a):
        continue
    rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
    if rel:
        text = LW.page_text(rec["doc"]); assert text[rec["start"]:rec["end"]] == rec["span"], "quote check failed"
        p = phi.get(i)
        Q[i] = {"id": i, "relation": r["stratum"], "question": r["question"], "answer": str(rel), "doc": rec["doc"], "support": s,
                "quote": C.sentence_at(text, rec["start"], rec["end"]).strip()[:300], "phi4_agrees": bool(ans(p) and agree(str(rel), str(p))), "match": gmatch(r, rel)}
moved = []
for i, x in REL.items():
    r = rows[i]; ys = YR.findall(r["question"])
    if not ys:
        continue
    rel, rec = C.release2(r["question"], x["answer"], r["wiki_titles"], LW.page_text)
    sent = C.sentence_at(LW.page_text(rec["doc"]), rec["start"], rec["end"]) if rel else ""
    if not (rel and covers(sent, int(ys[0]))):
        moved.append({"id": i, "question": r["question"], "answer": x["answer"], "match": gmatch(r, x["answer"]), "quote": sent.strip()[:200]})
n = len(rows); nq = len(Q); rq = sum(x["match"].startswith("right") for x in Q.values())
ny = sum(1 for i in REL if YR.findall(rows[i]["question"]))
out = [f"# S40 secondary: rule Q and rule T on top of version 2 ({name}, n = {n})", "",
       f"Released by version 2: {len(REL)} ({100*len(REL)/n:.1f}%). Qualified by rule Q: {nq} ({100*nq/n:.1f}%; prediction 4 to 10 points: {'met' if 4 <= 100*nq/n <= 10 else 'FAILED'}). "
       f"Unresolved: {n-len(REL)-nq} ({100*(n-len(REL)-nq)/n:.1f}%).",
       f"Quoted answer matches gold: {rq} of {nq} ({100*rq/max(1,nq):.1f}%; prediction 78 to 92%: {'met' if 78 <= 100*rq/max(1,nq) <= 92 else 'FAILED'}); labels by string match only: {sum(x['match'].endswith('*') for x in Q.values())}.",
       "", "| relation | Qualified | matches gold |", "|---|---|---|"]
for rel_, c in Counter(x["relation"] for x in Q.values()).most_common():
    k = sum(x["match"].startswith("right") for x in Q.values() if x["relation"] == rel_)
    out.append(f"| {rel_} | {c} | {k} ({100*k/c:.1f}%) |")
out += ["", "| support | Phi-4 agrees | Qualified | matches gold |", "|---|---|---|---|"]
for key, c in sorted(Counter((x["support"], x["phi4_agrees"]) for x in Q.values()).items()):
    k = sum(x["match"].startswith("right") for x in Q.values() if (x["support"], x["phi4_agrees"]) == key)
    out.append(f"| {key[0]} | {key[1]} | {c} | {k} ({100*k/c:.1f}%) |")
out += ["", f"Rule T: releases for questions that name a year: {ny}; moved to Qualified: {len(moved)} (prediction at most 10: {'met' if len(moved) <= 10 else 'FAILED'}); "
        f"of the moved, gold-right {sum(m['match'].startswith('right') for m in moved)}, gold-wrong {sum(m['match'].startswith('wrong') for m in moved)}.", ""]
out += [f"- {m['question']} | {m['answer']} | {m['match']} | {m['quote']}" for m in moved]
with open(D / f"{name}_qualified.jsonl", "w", encoding="utf-8") as f:
    for x in Q.values():
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
OUT = ROOT / "results/runs/s40/review" / name; OUT.mkdir(parents=True, exist_ok=True)   # per-item listing: stays out of the release
(OUT / "QT_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out[:12]))
