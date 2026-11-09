"""S40: a third sealed real-question set for testing version 2 (plan docs/S40_PLAN.md). Built offline from the S29 Wikidata candidate pools
(results/runs/s29/raw, same filters as wd_build.py), excluding every subject (relation, Wikidata id) used in the S29 sealed or pilot sets and every
S29 question string. "founded" is not used (dropped in S29). New seed. Prints counts only; the sealed file is not opened by later code except
the pre-registered run. python -I -B results/runs/s40/s40_build.py"""
import hashlib, importlib.util, json, random, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("wd", ROOT / "results/runs/s29/wd_build.py")
W = importlib.util.module_from_spec(spec); spec.loader.exec_module(W)
D = ROOT / "results/runs/s40"
used_subj, used_q = set(), set()
for f in ("sealed", "pilot"):
    for r in map(json.loads, open(ROOT / f"results/runs/s29/{f}/items.jsonl", encoding="utf-8")):
        used_q.add(r["q"])
        if r["relation"] != "office":
            used_subj.add((r["relation"], r["qid"]))
# rebuild the candidate pools exactly as wd_build.build() does, without writing anything
src =Path(W.__file__).read_text(encoding="utf-8")
body = src.split("def build():")[1].split("    rng = random.Random(2909)")[0]
ns = {**W.__dict__}
exec("def _pool():" + body + "    return pool\n", ns)
pool = ns["_pool"]()
targets = {**{k: v[4] for k, v in W.REL.items() if k != "founded"}, "office": 400}
rng = random.Random(4040)
sealed = []
avail = {}
for rel in targets:
    items = [it for it in pool.get(rel, []) if it["q"] not in used_q and (rel == "office" or (rel, it["qid"]) not in used_subj)]
    avail[rel] = len(items)
    by = defaultdict(list)
    for it in items:
        by[it["stratum"]].append(it)
    for s in by:
        rng.shuffle(by[s])
    want = targets[rel]; per = want // 3
    take = []
    for s in ("low", "mid", "high"):
        take += by[s][:per]
    rest = [it for s in by for it in by[s][per:]]
    rng.shuffle(rest)
    take += rest[:max(0, want - len(take))]
    sealed += take
rng.shuffle(sealed)
for i, it in enumerate(sealed):
    it["id"] = f"w3-{i:05d}"
(D / "sealed").mkdir(parents=True, exist_ok=True)
with open(D / "sealed" / "items.jsonl", "w", encoding="utf-8") as f:
    for r in sealed:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
assert not ({r["q"] for r in sealed} & used_q)
hs = [f"{hashlib.sha256((D / 'sealed/items.jsonl').read_bytes()).hexdigest()}  sealed/items.jsonl",
      f"{hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}  s40_build.py",
      f"{hashlib.sha256(sorted_ids.encode()).hexdigest()}  sorted ids" if (sorted_ids := "\n".join(sorted(r['id'] for r in sealed))) else ""]
(D / "seal_hashes.txt").write_text("\n".join(hs) + "\n", encoding="utf-8")
print("available after exclusion", avail)
print("sealed", len(sealed), dict(Counter(i["relation"] for i in sealed)), dict(Counter(i["stratum"] for i in sealed)))
