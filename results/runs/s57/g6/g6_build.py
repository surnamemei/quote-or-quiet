"""S57 G6: draw 600 person pages (no qualifier in the title, 6,000 to 60,000 characters, seed 5706), excluding the people of results/runs/s42/e6_items.jsonl;
one reading each, question 'Where was X born?'. Writes e9_items.jsonl for the hop-1 pipeline. CPU only.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s57/g6/g6_build.py"""
import json, os, random, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s37"))
import no_retrieval2  # noqa: F401
from lf_people import is_person   # noqa: E402
D = ROOT / "results/runs/s57/g6"
old = {x["doc"] for x in map(json.loads, open(ROOT / "results/runs/s42/e6_items.jsonl", encoding="utf-8"))}
db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
rows = sorted(t for (t,) in db.execute("select title from t where qual = '' and len >= 6000 and len <= 60000").fetchall() if t not in old and "," not in t and not t.startswith("List of"))
rng = random.Random(5706); rng.shuffle(rows)
pers = []
for t in rows:
    if len(t.split()) >= 2 and is_person(t):
        pers.append(t)
    if len(pers) >= 600:
        break
with open(D / "e9_items.jsonl", "w", encoding="utf-8") as f:
    for i, t in enumerate(pers):
        f.write(json.dumps({"id": f"g{i}", "base": t, "relation": "birth_place", "question": f"Where was {t} born?", "readings": [t]}, ensure_ascii=False) + "\n")
print("persons", len(pers))
