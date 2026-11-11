"""S59 G8: draw 50 non-person topic pages (17 organisations, 17 events, 16 science topics) from the pinned title index, seed 5901.
Page: no qualifier in the title, 8,000 to 60,000 characters, not a list, not a person (S37 test), not an S56 contested page; class from the first sentence:
organisation ('is/was a/an/the ... company|corporation|organisation|organization|university|college|band|club|party|agency|charity|foundation|airline|bank|newspaper|publisher|record label|team'),
event ('was/is a/an/the ... battle|war|election|earthquake|treaty|revolution|disaster|tournament|championship|siege|massacre|riot|expedition|flood|hurricane|conference|festival|referendum|crisis|campaign'),
science ('is/was a/an/the ... disease|disorder|species|genus|chemical|element|compound|theory|process|protein|enzyme|hormone|mineral|phenomenon|particle|galaxy|star|planet|algorithm|syndrome|virus|bacterium|drug|molecule|reaction').
Writes people.json (the list of titles; the name is kept for the copied pipeline). Prints counts only. OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s59/g8_topics.py"""
import json, random, re, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20"), str(ROOT / "results/runs/s37")]
import no_retrieval2  # noqa: F401
from vkg import localwiki as LW
from lf_people import is_person
D = ROOT / "results/runs/s59"
CL = {"org": r"company|corporation|organisation|organization|university|college|band|club|party|agency|charity|foundation|airline|bank|newspaper|publisher|record label|team",
      "event": r"battle|war|election|earthquake|treaty|revolution|disaster|tournament|championship|siege|massacre|riot|expedition|flood|hurricane|conference|festival|referendum|crisis|campaign",
      "sci": r"disease|disorder|species|genus|chemical|element|compound|theory|process|protein|enzyme|hormone|mineral|phenomenon|particle|galaxy|star|planet|algorithm|syndrome|virus|bacterium|drug|molecule|reaction"}
NEED = {"org": 17, "event": 17, "sci": 16}
excl = {json.loads(l)["topic"] for l in open(ROOT / "results/runs/s56/e12_stmts.jsonl", encoding="utf-8")}
db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
rows = sorted(t for (t,) in db.execute("select title from t where qual = '' and len >= 8000 and len <= 60000").fetchall() if not t.startswith("List") and "," not in t and t not in excl)
rng = random.Random(5901); rng.shuffle(rows)
got = {k: [] for k in CL}
for t in rows:
    if all(len(got[k]) >= NEED[k] for k in CL):
        break
    lines = (LW.page_text(t) or "").split("\n")
    first = next((l for l in lines[1:6] if len(l) > 40), "")[:300]
    for k, pat in CL.items():
        if len(got[k]) < NEED[k] and re.search(r"\b(is|was|are|were)\s+(a|an|the)\s+[^.]{0,80}?\b(" + pat + r")\b", first, re.I) and not is_person(t):
            got[k].append(t); break
topics = [t for k in CL for t in got[k]]
json.dump(topics, open(D / "people.json", "w", encoding="utf-8"), ensure_ascii=False)
print({k: len(v) for k, v in got.items()}, "total", len(topics))
