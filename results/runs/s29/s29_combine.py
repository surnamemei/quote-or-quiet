"""Concatenate the four sealed chunks (wd1..wd4, consecutive slices of the 3,359 items) into wd_outputs.jsonl / wd_phi4.jsonl so s29_score.py and s29_final.py run on the whole set.
python -B s29_combine.py <fsm|ddg>   (checks the item count and that no id repeats)"""
import json, sys
from pathlib import Path
D = Path(__file__).parent / f"run_{sys.argv[1]}"
for suffix in ("outputs", "phi4"):
    rows = []
    for i in (1, 2, 3, 4):
        rows += [json.loads(l) for l in open(D / f"wd{i}_{suffix}.jsonl", encoding="utf-8")]
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == 3359, (suffix, len(ids), len(set(ids)))
    with open(D / f"wd_{suffix}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(suffix, len(rows))
