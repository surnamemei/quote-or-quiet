"""S57 G5 (copy of results/runs/s46/e9_build.py: seed 5703, 75 films and 75 persons, E9 bases excluded). S46 part B (docs/S43_LONGFORM_AND_AMBIGUITY_PLAN.md): ambiguous names. Bases that name several pages of the same kind
(films of different years; people with different occupations), from the pinned FineWiki title index. CPU only.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s57/g5/e9_build.py"""
import json, os, random, re, sqlite3, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s37"))
import no_retrieval2  # noqa: F401
from lf_people import is_person   # noqa: E402
D = ROOT / "results/runs/s57/g5"
db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
rows = db.execute("select title, qual, len from t where qual != '' and len >= 4000").fetchall()
by = defaultdict(list)
for t, q, ln in rows:
    by[re.sub(r"\s*\([^)]*\)$", "", t)].append((t, q, ln))
PERS = re.compile(r"footballer|politician|actor|actress|singer|musician|writer|author|poet|painter|cricketer|boxer|wrestler|director|journalist|"
                  r"basketball|baseball|general|physician|composer|rapper|swimmer|footballer|lawyer|judge|bishop|priest|businessman|athlete")
rng = random.Random(5703)
film, pers = [], []
OLD = {json.loads(l)["base"] for l in open(ROOT / "results/runs/s46/e9_items.jsonl", encoding="utf-8")}   # S57 G5: exclude the E9 bases
names = [b for b in by if b not in OLD]; rng.shuffle(names)
for b in names:
    v = by[b]
    if "," in b or len(b.split()) > 4:
        continue
    f = [x for x in v if re.fullmatch(r"\d{4} (?:\w+ )?film", x[1])]
    if len(f) >= 2 and len(film) < 75:
        film.append((b, sorted(f, key=lambda x: -x[2])[:4]))
    p = [x for x in v if PERS.search(x[1])]
    if len(p) >= 2 and len(pers) < 75 and len(b.split()) >= 2:
        p = [x for x in sorted(p, key=lambda x: -x[2]) if is_person(x[0])][:4]
        if len(p) >= 2:
            pers.append((b, p))
    if len(film) >= 75 and len(pers) >= 75:
        break
items = [{"id": f"f{i}", "base": b, "relation": "director", "question": f"Who directed the film {b}?", "readings": [x[0] for x in rs]} for i, (b, rs) in enumerate(film)]
items += [{"id": f"p{i}", "base": b, "relation": "birth_year", "question": f"In what year was {b} born?", "readings": [x[0] for x in rs]} for i, (b, rs) in enumerate(pers)]
with open(D / "e9_items.jsonl", "w", encoding="utf-8") as f:
    for x in items:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
print("films", len(film), "persons", len(pers), "readings", sum(len(x["readings"]) for x in items))
