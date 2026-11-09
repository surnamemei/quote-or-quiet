"""S40: make version 2 the evaluated system (docs/S40_PLAN.md). After s40_score.py and s40_v2.py: keep the frozen releases as
w3_frozen_releases.jsonl and write w3_releases.jsonl = frozen releases + V2 (registered wording) added releases, so the sheets, L1 and L2 scripts
evaluate version 2. Idempotent. python -B results/runs/s40/s40_merge.py"""
import json, shutil
from pathlib import Path
D = Path(__file__).parent / "run_fsm"; R = Path(__file__).parent / "review" / "w3"
fro = D / "w3_frozen_releases.jsonl"
if not fro.exists():
    shutil.copy2(D / "w3_releases.jsonl", fro)
F = [json.loads(l) for l in open(fro, encoding="utf-8")]
ids = {x["id"] for x in F}
A = [x for x in map(json.loads, open(R / "V2_added.jsonl", encoding="utf-8")) if "V2" in x["rules"] and x["id"] not in ids]
with open(D / "w3_releases.jsonl", "w", encoding="utf-8") as f:
    for x in F + [{"id": a["id"], "relation": a["relation"], "question": a["question"], "gold": a["gold"], "answer": a["answer"], "doc": None, "grade": a["grade"], "rule": "cell"} for a in A]:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
print("frozen", len(F), "added", len(A), "version 2", len(F) + len(A), "gold-wrong frozen", sum(x["grade"] is False for x in F), "added", sum(a["grade"] is False for a in A))
