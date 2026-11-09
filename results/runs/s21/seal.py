"""S21 sealing (2026-11-07): split the two new datasets into an inspectable DEV slice and a sealed TEST sample, without
printing any item. Raw downloads are in data/external (hashes in data/external/SHA256SUMS.txt). After this script, nobody reads
the raw files or the test files directly; only the frozen pipeline does.
  PopQA (MIT, akariasai/PopQA test.tsv, 14,267 rows): stratified by subject popularity tercile (s_pop), seed 21:
      DEV 300 (100 per tercile), TEST 2,100 (700 per tercile) from the rest.
  Mintaka (CC BY 4.0, amazon-science/mintaka): complexityType == "generic" only, from train+dev+test (none used by this project), seed 21:
      DEV 200, TEST = all remaining generic items, capped at 2,000.
Output: results/runs/s21/{popqa,mintaka}_{dev,test}.json in the project's item format {id, question, gold, stratum, meta},
and seal_hashes.txt. Prints only counts and hashes."""
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXT = ROOT / "data" / "external"
OUT = Path(__file__).resolve().parent
SEED = 21
csv.field_size_limit(10 ** 9)


def dump(name, rows):
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return p


def popqa():
    rows = list(csv.DictReader(open(EXT / "popqa" / "test.tsv", encoding="utf-8"), delimiter="\t"))
    rows.sort(key=lambda r: float(r["s_pop"]))
    n = len(rows)
    terc = [rows[: n // 3], rows[n // 3: 2 * n // 3], rows[2 * n // 3:]]
    rng = random.Random(SEED)
    dev, test = [], []
    for t, (lab, part) in enumerate(zip(("low", "mid", "high"), terc)):
        part = part[:]
        rng.shuffle(part)
        for r, dest in [(r, dev) for r in part[:100]] + [(r, test) for r in part[100:800]]:
            dest.append({"id": f"popqa-{r['id']}", "question": r["question"], "gold": json.loads(r["possible_answers"]),
                         "stratum": f"pop_{lab}", "meta": {"prop": r["prop"], "s_wiki_title": r["s_wiki_title"], "s_pop": float(r["s_pop"])}})
    rng.shuffle(test)
    return n, dev, test


def mintaka():
    items = []
    for s in ("train", "dev", "test"):
        for r in json.load(open(EXT / "mintaka" / f"mintaka_{s}.json", encoding="utf-8")):
            if r["complexityType"] == "generic":
                items.append((s, r))
    items.sort(key=lambda x: x[1]["id"])
    rng = random.Random(SEED)
    rng.shuffle(items)
    out = []
    for s, r in items:
        a = r["answer"]
        gold = []
        if a.get("answer"):
            for x in a["answer"]:
                gold.append(x.get("label", {}).get("en") if isinstance(x, dict) else str(x))
        if a.get("mention"):
            gold.append(a["mention"])
        gold = [g for g in dict.fromkeys(gold) if g]
        out.append({"id": f"mintaka-{r['id']}", "question": r["question"], "gold": gold, "stratum": f"mintaka_{r['category']}",
                    "meta": {"split": s, "answerType": a.get("answerType"), "category": r["category"]}})
    return len(items), out[:200], out[200:2200]


if __name__ == "__main__":
    lines = []
    n, dev, test = popqa()
    for name, rows in (("popqa_dev", dev), ("popqa_test", test)):
        p = dump(name, rows)
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()} *{p.name}")
    print(f"PopQA: {n} rows -> dev {len(dev)}, test {len(test)}")
    n, dev, test = mintaka()
    for name, rows in (("mintaka_dev", dev), ("mintaka_test", test)):
        p = dump(name, rows)
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()} *{p.name}")
    print(f"Mintaka generic: {n} -> dev {len(dev)}, test {len(test)}; empty gold in test: {sum(not r['gold'] for r in test)}")
    (OUT / "seal_hashes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0)
