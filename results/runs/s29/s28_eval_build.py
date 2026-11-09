"""S28 evaluation rows (docs/S28_PLAN.md): releases of (a) the Mintaka test combination system (1,005), (b) the FRESH-5 combination system (727), (c) the DEV releases added by
the pinned and title-retrieval variants beyond the frozen S19 system (S25 pooling). Each row: question, sentence containing the released span in its release page, the span, the gold-relative
grade, and for Mintaka whether the row is one of the 8 clear relation errors of docs/S27_RESOLUTION_ANALYSIS.md. CPU, loads local wiki pages (one heavy job; idle priority).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s29/s28_eval_build.py"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s25"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import veto27 as V27
from vkg import localwiki as LW, l3_verify as V, l3_checks2 as C, s17_eval as S
from vkg.s12_run import agree
from vkg.s14_eval import ans
from entity_dev import ambiguous
from temporal import time_sensitive
from abstain_dev import grade
from gate_fmt import release_any

CLEAR = {"What is another name for an instrument called Harp by blues musicians?", "What is Japan's Senate called?", "Between what years was the Franco-Dutch war fought?",
         "When did Pizarro reach the Inca territory?", "What is it called when you walk or run while bouncing the ball?", "What position did the creator of the Game Boy have at Nintendo?",
         "Number of movies in the Thor franchise?", "What is the population of Parma, Ohio?"}
out = []


def row(pool, id_, q, answer, doc, g, extra=None):
    text = LW.page_text(doc) or ""
    hit = next(V.locate(str(answer), text), None)
    if not hit:
        return
    i, j = hit
    sent = C.sentence_at(text, i, j).strip()
    out.append({"pool": pool, "id": id_, "question": q, "sentence": sent[:700], "span": text[i:j], "grade": g, "clear": q in CLEAR, **(extra or {})})


for pool, fn in (("mintaka_test", "mintaka_test_releases.jsonl"), ("fresh5", "fresh5_releases.jsonl")):
    for r in map(json.loads, open(ROOT / "results/runs/s22" / fn, encoding="utf-8")):
        row(pool, r["id"], r["question"], r["answer"], r["release_doc"], r["grade"], {"source": r["source"]})
n_main = len(out)
# DEV added releases (pin and indep), Phi-4 veto policy, as in S25/S26
for N in V27.SETS:
    base = V27.outputs("s19", N)
    phi19 = {r["id"]: r["answer"] for r in map(json.loads, open(V27.phi_file("s19", N), encoding="utf-8"))}
    froz = set()
    for r in base:
        a, s = S.cand(r); a = a if ans(a) else None
        rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
        p = phi19.get(r["id"])
        if rel and ans(p) and agree(str(rel), str(p)):
            froz.add(r["id"])
    pre = {}
    for var in V27.VARS:
        rows = V27.outputs(var, N)
        if rows is None:
            continue
        ph = {r["id"]: r["answer"] for r in map(json.loads, open(V27.phi_file(var, N), encoding="utf-8"))}
        d = {}
        for r in rows:
            rel, rec = release_any(r, LW.page_text)
            d[r["id"]] = (r, rel, rec.get("doc"), ph.get(r["id"]))
        pre[var] = d
    for var in ("pin", "indep"):
        if var not in pre:
            continue
        final = {}
        for i, (r, rel, doc, p) in pre["s19"].items():
            if rel and ans(p) and agree(str(rel), str(p)):
                final[i] = (r, rel, doc, "s19")
        for i, (r, rel, doc, p) in pre[var].items():
            if i in final or not rel or not (ans(p) and agree(str(rel), str(p))):
                continue
            if time_sensitive(r["question"]) or ambiguous(r["question"], r["wiki_titles"], doc)[0]:
                continue
            final[i] = (r, rel, doc, var)
        for i, (r, rel, doc, src) in final.items():
            if i not in froz:
                row("dev_added", f"{N}:{var}:{i}", r["question"], rel, doc, grade(r["question"], r["gold"], rel), {"source": src})
with open(ROOT / "results/runs/s29/s28_eval_rows.jsonl", "w", encoding="utf-8") as f:
    for x in out:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
from collections import Counter
print("rows", len(out), "main", n_main, dict(Counter((x["pool"], str(x["grade"])) for x in out)), "clear rows", sum(x["clear"] for x in out))
