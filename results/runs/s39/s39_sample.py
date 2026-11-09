"""S39 design questions (plan docs/S39_PLAN.md): the next slices of the S21 seeded shuffles, so no overlap with S21 dev/test:
PopQA 200 per popularity tercile from positions 800-1000 (S21 used 0-800), Mintaka generic items 2200-2800 (S21 used 0-2200).
Writes results/runs/s39/design/items.jsonl in the S29 item format. python -B results/runs/s39/s39_sample.py"""
import json, random, csv, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "results/runs/s21"))
import seal                                   # S21 sampling code (same seed, same order)
csv.field_size_limit(10 ** 9)
rows = list(csv.DictReader(open(seal.EXT / "popqa" / "test.tsv", encoding="utf-8"), delimiter="\t"))
rows.sort(key=lambda r: float(r["s_pop"])); n = len(rows)
terc = [rows[: n // 3], rows[n // 3: 2 * n // 3], rows[2 * n // 3:]]
rng = random.Random(seal.SEED)
out = []
for lab, part in zip(("low", "mid", "high"), terc):
    part = part[:]; rng.shuffle(part)
    for r in part[800:1000]:
        out.append({"id": f"popqa-{r['id']}", "q": r["question"], "gold": json.loads(r["possible_answers"]), "relation": f"pop_{lab}", "stratum": f"pop_{lab}", "qid": r["s_wiki_title"]})
_, allm = None, None
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
out += mint[2200:2800]
used = {e["id"] for f in ("popqa_dev", "popqa_test", "mintaka_dev", "mintaka_test") for e in json.load(open(ROOT / f"results/runs/s21/{f}.json", encoding="utf-8"))}
assert not used & {e["id"] for e in out}, "overlap with S21"
with open(ROOT / "results/runs/s39/design/items.jsonl", "w", encoding="utf-8") as f:
    for e in out:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
print(len(out), "design items, no overlap with S21")
