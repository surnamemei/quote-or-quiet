"""S65 (gate G14): seal 2,001 PopQA questions never used: positions 1000-1667 of each popularity tercile in the S21 seeded shuffle (S21 used 0-800, S39 800-1000).
Writes results/runs/s65/sealed/items.jsonl and seal_hashes.txt. Prints counts and the hash only, never an item. python -B results/runs/s65/seal65.py"""
import csv, hashlib, json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "results/runs/s21"))
import seal
csv.field_size_limit(10 ** 9)
rows = list(csv.DictReader(open(seal.EXT / "popqa" / "test.tsv", encoding="utf-8"), delimiter="\t"))
rows.sort(key=lambda r: float(r["s_pop"])); n = len(rows)
terc = [rows[: n // 3], rows[n // 3: 2 * n // 3], rows[2 * n // 3:]]
rng = random.Random(seal.SEED); out = []
for lab, part in zip(("low", "mid", "high"), terc):
    part = part[:]; rng.shuffle(part)
    for r in part[1000:1667]:
        out.append({"id": f"popqa-{r['id']}", "q": r["question"], "gold": json.loads(r["possible_answers"]), "stratum": f"pop_{lab}", "page": r["s_wiki_title"], "prop": r["prop"]})
used = {e["id"] for f in ("popqa_dev", "popqa_test") for e in json.load(open(ROOT / f"results/runs/s21/{f}.json", encoding="utf-8"))}
used |= {json.loads(l)["id"] for l in open(ROOT / "results/runs/s39/design/items.jsonl", encoding="utf-8")}
assert len(out) == 2001 and not used & {e["id"] for e in out}, "overlap"
(ROOT / "results/runs/s65/sealed").mkdir(parents=True, exist_ok=True)
p = ROOT / "results/runs/s65/sealed/items.jsonl"
with open(p, "w", encoding="utf-8") as f:
    for e in out:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
h = hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT / "results/runs/s65/seal_hashes.txt").write_text(f"items.jsonl {h}\n", encoding="utf-8")
print("sealed", len(out), "sha256", h)
