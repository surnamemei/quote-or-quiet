"""Build and seal FRESH-5 for the joint S19 test, before any S19 output exists: ALL remaining original SimpleQA items, i.e. the
official CSV (SHA-256 feee3f7e...) minus SimpleQA Verified (matched by original_index), minus FRESH-3 and FRESH-4. All stratum O.
Order: random.Random(7000).shuffle (file order matters only for budget rules). Writes results/runs/fresh5/items.json and prints
only counts and the SHA-256; nothing is inspected. Run: python -B -m vkg.fresh5"""
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
    used = set()
    for s in ("fresh3", "fresh4"):
        used |= {int(e["id"][4:]) for e in json.load(open(ROOT / f"results/runs/{s}/items.json", encoding="utf-8")) if e["id"].startswith("sqo-")}
    rows = list(csv.DictReader(open(ROOT / "data/simpleqa_orig/simple_qa_test_set.csv", encoding="utf-8")))
    pool = [i for i in range(len(rows)) if i not in ver and i not in used]
    random.Random(7000).shuffle(pool)
    items = [{"id": f"sqo-{i}", "stratum": "O", "question": rows[i]["problem"], "gold": [rows[i]["answer"]]} for i in pool]
    out = ROOT / "results/runs/fresh5"
    out.mkdir(parents=True, exist_ok=True)
    p = out / "items.json"
    if p.exists():
        raise SystemExit("FRESH-5 already sealed; refusing to overwrite")
    p.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    (ROOT / "results/runs/fresh5_hash.txt").write_text(f"{h}  results/runs/fresh5/items.json\n", encoding="utf-8")
    print(f"original {len(rows)} minus Verified {len(ver)} minus FRESH-3/4 O {len(used)} = FRESH-5 {len(items)}; sha256 {h}")


if __name__ == "__main__":
    main()
