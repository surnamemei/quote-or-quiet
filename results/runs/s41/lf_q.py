"""S41 secondary (rule Q of docs/S42_CLAIM_AUDIT_AND_PLAN.md, applied unchanged): a slot that is not kept becomes Qualified if its value
passes the deductive gate (typed verbatim span in a pinned page), whatever the readers and Phi-4 said. The statement shown is the quoted
sentence with its page, not the value. CPU, idle priority. python -B results/runs/s41/lf_q.py"""
import json, os, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.stdout.reconfigure(encoding="utf-8")
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import localwiki as LW, l3_checks2 as C   # noqa: E402
from vkg.s14_eval import ans                       # noqa: E402
D = ROOT / "results/runs/s41"
X = [json.loads(l) for l in open(D / "verified.jsonl", encoding="utf-8")]
ev = json.load(open(D / "evidence.json", encoding="utf-8"))
Q = []
for x in X:
    if x["keep"] or not ans(x["value_clean"]):
        continue
    rel, rec = C.release2(x["question"], x["value_clean"], ev[x["id"]]["titles"], LW.page_text)
    if rel:
        text = LW.page_text(rec["doc"]); assert text[rec["start"]:rec["end"]] == rec["span"], "quote check failed"
        Q.append({"id": x["id"], "person": x["person"], "type": x["type"], "question": x["question"], "value_clean": x["value_clean"], "support": x["support"],
                  "phi4": x["phi4"], "page": rec["doc"], "quote": C.sentence_at(text, rec["start"], rec["end"]).strip()[:300]})
with open(D / "qualified.jsonl", "w", encoding="utf-8") as f:
    for q in Q:
        f.write(json.dumps(q, ensure_ascii=False) + "\n")
n = len(X); k = sum(x["keep"] for x in X)
print(f"slots {n}; kept {k} ({100*k/n:.1f}%); Qualified {len(Q)} ({100*len(Q)/n:.1f}%); Unresolved {n-k-len(Q)} ({100*(n-k-len(Q))/n:.1f}%)")
print("Qualified by reader support:", dict(Counter(q["support"] for q in Q)))
