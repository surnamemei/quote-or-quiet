"""S58 (gate G4): seal the 1,200 Mintaka 'generic' items never used before: positions 2800-4000 of the S21 seeded shuffle (S21 used 0-2200, S39 used 2200-2800).
Writes results/runs/s58/sealed/items.jsonl (S29 item format) and seal_hashes.txt. Prints counts only, never an item. python -B results/runs/s58/seal58.py"""
import json, random, csv, sys, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "results/runs/s21"))
import seal
items = []
for s in ("train", "dev", "test"):
    for r in json.load(open(seal.EXT / "mintaka" / f"mintaka_{s}.json", encoding="utf-8")):
        if r["complexityType"] == "generic":
            items.append((s, r))
items.sort(key=lambda x: x[1]["id"]); random.Random(seal.SEED).shuffle(items)
mint = []
for s, r in items:
    a = r["answer"]; gold = []
    if a.get("answer"):
        for x in a["answer"]:
            gold.append(x.get("label", {}).get("en") if isinstance(x, dict) else str(x))
    if a.get("mention"):
        gold.append(a["mention"])
    gold = [g for g in dict.fromkeys(gold) if g]
    mint.append({"id": f"mintaka-{r['id']}", "q": r["question"], "gold": gold, "relation": f"mintaka_{r['category']}", "stratum": f"mintaka_{r['category']}", "qid": ""})
out = mint[2800:4000]
used = {e["id"] for f in ("popqa_dev", "popqa_test", "mintaka_dev", "mintaka_test") for e in json.load(open(ROOT / f"results/runs/s21/{f}.json", encoding="utf-8"))}
used |= {json.loads(l)["id"] for l in open(ROOT / "results/runs/s39/design/items.jsonl", encoding="utf-8")}
assert len(out) == 1200 and not used & {e["id"] for e in out}, "overlap"
p = ROOT / "results/runs/s58/sealed/items.jsonl"
with open(p, "w", encoding="utf-8") as f:
    for e in out:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
h = hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT / "results/runs/s58/seal_hashes.txt").write_text(f"items.jsonl {h}\n", encoding="utf-8")
print("sealed", len(out), "sha256", h)
