"""S44 sealed long-form test: 50 new people (seed 4444, not among the S37 design people) from the pinned FineWiki title index (seed 3737).
A page counts as a person if its first sentence has a life-date parenthesis followed by "is/was a(n) ... <occupation word>".
25 long pages (>= 30,000 chars) and 25 medium (8,000-30,000). Every subject and value label in the S29 candidate lists is excluded
(so no sealed subject can be drawn). Writes people.json. python -B results/runs/s37/lf_people.py"""
import json, random, re, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import localwiki as LW

OCC = ("politician|actor|actress|writer|player|singer|musician|scientist|philosopher|director|author|novelist|footballer|cricketer|"
       "officer|businessman|businesswoman|artist|poet|composer|lawyer|journalist|activist|economist|historian|engineer|driver|wrestler|"
       "rapper|producer|athlete|statesman|orator|painter|photographer|coach|judge|bishop|priest|physician|grandmaster|general|psychologist|"
       "linguist|mathematician|physicist|chemist|biologist|boxer|fighter|guitarist|comedian|screenwriter|filmmaker|designer|architect")
LIFE = re.compile(r"\((?:[^)]*\bborn\b[^)]*\d{4}|[^)]*\d{3,4}\s*[–-]\s*[^)]*\d{3,4})[^)]*\)")
PERSON = re.compile(r"\)\s+(?:was|is)\s+an?\s+[^.]{0,120}?\b(?:" + OCC + r")s?\b", re.I)


def is_person(title):
    lines = (LW.page_text(title) or "").split("\n")
    first = next((l for l in lines[1:6] if len(l) > 40), "")
    m = LIFE.search(first[:300])
    return bool(m and PERSON.search(first[m.start():m.start() + 400]))


if __name__ == "__main__":
    excl = set(json.load(open(ROOT / "results/runs/s37/people.json", encoding="utf-8")))   # the 50 design subjects of S37
    excl2 = set()
    for f in (ROOT / "results/runs/s29/raw").glob("*.json"):
        for b in json.load(open(f, encoding="utf-8")):
            excl.add(str(b.get("itemLabel", ""))); excl.add(str(b.get("valLabel", "")))
    db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
    rows = db.execute("select title, len from t where qual='' and len >= 8000 and title not like '%,%' and title not like 'List of%'").fetchall()
    rng = random.Random(4444); rng.shuffle(rows)
    out = {"long": [], "medium": []}; seen = 0
    for t, ln in rows:
        b = "long" if ln >= 30000 else "medium"
        if len(out[b]) >= 25 or t in excl:
            continue
        seen += 1
        if is_person(t):
            out[b].append(t)
        if len(out["long"]) >= 25 and len(out["medium"]) >= 25:
            break
    json.dump(out["long"] + out["medium"], open(ROOT / "results/runs/s44/people.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(excl), "excluded labels; pages checked", seen, out)
