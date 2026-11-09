"""Build and seal FRESH-3, the next confirmation set (1000 items), BEFORE any system is designed against it.
  stratum V (cleaner gold): the 200 SimpleQA Verified items never used (not in the Random(3000) 500-draw, not in FRESH-2's Random(4000) 300)
  stratum O (original SimpleQA gold, noisier): Random(5000).sample of 800 from the original SimpleQA test set (4326 items,
            official CSV, SHA-256 feee3f7e...) minus every item that is in SimpleQA Verified (matched by original_index)
Writes results/runs/fresh3/items.json (id, stratum, question, gold) and prints only counts and the file's SHA-256: no item content
is shown or inspected. Run: python -B -m vkg.fresh3"""
import ast
import csv
import hashlib
import json
import os
import random

from .probe_gen import ROOT

OUT = ROOT / "results" / "runs" / "fresh3"


def main():
    from datasets import load_dataset
    os.environ.setdefault("HF_HOME", str(ROOT / "data" / "hf"))
    d = load_dataset("google/simpleqa-verified", split="eval", cache_dir=os.environ["HF_HOME"])
    used = set(random.Random(3000).sample(range(len(d)), 500))
    rest = [i for i in range(len(d)) if i not in used]
    f2 = set(random.Random(4000).sample(rest, 300))
    v_left = [i for i in rest if i not in f2]
    ver_orig = {int(x["original_index"]) for x in d}
    rows = list(csv.DictReader(open(ROOT / "data" / "simpleqa_orig" / "simple_qa_test_set.csv", encoding="utf-8")))
    pool = [i for i in range(len(rows)) if i not in ver_orig]
    pick = random.Random(5000).sample(pool, 800)
    items = [{"id": f"sqa-{d[i]['original_index']}", "stratum": "V", "question": d[i]["problem"], "gold": [d[i]["answer"]]} for i in v_left]
    items += [{"id": f"sqo-{i}", "stratum": "O", "question": rows[i]["problem"], "gold": [rows[i]["answer"]]} for i in pick]
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "items.json"
    p.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT.parent / "fresh3_hash.txt").write_text(f"{h}  results/runs/fresh3/items.json\n", encoding="utf-8")
    print(f"Verified total {len(d)}, never used {len(v_left)}; original {len(rows)}, not in Verified {len(pool)}; "
          f"FRESH-3 = {sum(x['stratum'] == 'V' for x in items)} V + {sum(x['stratum'] == 'O' for x in items)} O; sha256 {h}")


if __name__ == "__main__":
    main()
