"""Build and seal FRESH-4 (1000 items) for the S18 L2 test, before any S18 output exists.
Random(6000).sample of 1000 from the original SimpleQA test set (official CSV, SHA-256 feee3f7e...), excluding every item in
SimpleQA Verified (matched by original_index) and every item already in FRESH-3. All stratum O (original gold).
Writes results/runs/fresh4/items.json; prints only counts and the SHA-256. Run: python -B -m vkg.fresh4"""
import csv
import hashlib
import json
import os
import random

from .probe_gen import ROOT


def main():
    from datasets import load_dataset
    os.environ.setdefault("HF_HOME", str(ROOT / "data" / "hf"))
    d = load_dataset("google/simpleqa-verified", split="eval", cache_dir=os.environ["HF_HOME"])
    ver = {int(x["original_index"]) for x in d}
    f3 = {int(e["id"][4:]) for e in json.load(open(ROOT / "results/runs/fresh3/items.json", encoding="utf-8")) if e["id"].startswith("sqo-")}
    rows = list(csv.DictReader(open(ROOT / "data/simpleqa_orig/simple_qa_test_set.csv", encoding="utf-8")))
    pool = [i for i in range(len(rows)) if i not in ver and i not in f3]
    pick = random.Random(6000).sample(pool, 1000)
    items = [{"id": f"sqo-{i}", "stratum": "O", "question": rows[i]["problem"], "gold": [rows[i]["answer"]]} for i in pick]
    out = ROOT / "results/runs/fresh4"
    out.mkdir(parents=True, exist_ok=True)
    p = out / "items.json"
    p.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    (ROOT / "results/runs/fresh4_hash.txt").write_text(f"{h}  results/runs/fresh4/items.json\n", encoding="utf-8")
    print(f"pool {len(pool)} (original {len(rows)} minus Verified {len(ver)} minus FRESH-3 O {len(f3)}); FRESH-4 = {len(items)}; "
          f"left untouched afterwards {len(pool) - len(items)}; sha256 {h}")


if __name__ == "__main__":
    main()
