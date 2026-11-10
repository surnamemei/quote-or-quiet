"""Score an S29 run with the FROZEN release rule (support >= 3, gate V1-V5, Phi-4 agrees), gold-relative with the cached alias-aware labels.
Writes results/runs/s40/run_<search>/<set>_score.json and a list of the wrong releases for adjudication. CPU, loads local wiki pages (one heavy job; idle priority).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s40/s40_score.py <fsm|ddg> <wdp|wd>"""
import json, os, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402  (keeps the unused 37 GB embedding table out of RAM; any use of vkg.retrieval2 raises)
from abstain_dev import grade
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW
from vkg.s12_run import agree
from vkg.s14_eval import ans

search, name = sys.argv[1], sys.argv[2]
D = ROOT / "results/runs/s40" / f"run_{search}"
rows = [json.loads(l) for l in open(D / f"{name}_outputs.jsonl", encoding="utf-8")]
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_phi4.jsonl", encoding="utf-8"))}
rel_rows = []
for r in rows:
    a, s = S.cand(r); a = a if ans(a) else None
    rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
    p = phi.get(r["id"])
    if rel and not (ans(p) and agree(str(rel), str(p))):
        rel = None
    if rel:
        rel_rows.append({"id": r["id"], "relation": r["stratum"], "question": r["question"], "gold": r["gold"], "answer": str(rel), "doc": rec.get("doc"),
                         "grade": grade(r["question"], r["gold"], rel)})
n = len(rows); k = sum(x["grade"] is False for x in rel_rows)
byrel = {}
for x in rel_rows:
    b = byrel.setdefault(x["relation"], [0, 0]); b[0] += 1; b[1] += x["grade"] is False
tot = Counter(r["stratum"] for r in rows)
summary = {"search": search, "set": name, "n": n, "released": len(rel_rows), "coverage": len(rel_rows) / n, "wrong_gold_relative": k, "unlabelled": sum(x["grade"] == "?" for x in rel_rows),
           "by_relation": {r: {"n": tot[r], "released": byrel.get(r, [0, 0])[0], "wrong": byrel.get(r, [0, 0])[1]} for r in tot}}
(D / f"{name}_score.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
with open(D / f"{name}_releases.jsonl", "w", encoding="utf-8") as f:
    for x in rel_rows:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
print(json.dumps({k_: v for k_, v in summary.items() if k_ != "by_relation"}))
for r_, v in summary["by_relation"].items():
    print(" ", r_, v)
