"""S29: build the new sealed real-question set from Wikidata (docs/SEALED_SET_DESIGN.md). Read-only queries to the public QLever Wikidata endpoint.
  fetch : one randomised query per relation -> raw/<rel>.json  (candidates with English labels and sitelink counts)
  build : filter (subject name unique in the local Wikipedia title index, value usable), stratify by sitelinks, sample, write
          sealed/items.jsonl (4,000 questions) and pilot/items.jsonl (150, disjoint, different seed), hashes in seal_hashes.txt.
The sealed file is never printed or opened by later code except by the run that is pre-registered; this script prints counts only.
python -I -B results/runs/s29/wd_build.py fetch|build"""
import hashlib, json, random, re, sqlite3, sys, time, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "results/runs/s29"
UA = {"User-Agent": "quote-or-quiet-research/0.1 (research script, read-only)", "Accept": "application/sparql-results+json"}
EP = "https://qlever.cs.uni-freiburg.de/api/wikidata"
PRE = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
"""
# relation -> (class, property, value kind, question template, target count)
REL = {
    "birth_place": ("Q5", "P19", "label", "Where was {x} born?", 800),
    "birth_year": ("Q5", "P569", "year", "In what year was {x} born?", 600),
    "death_year": ("Q5", "P570", "year", "In what year did {x} die?", 400),
    "founded": ("Q4830453", "P571", "year", "In what year was {x} founded?", 600),
    "capital": ("Q6256", "P36", "label", "What is the capital of {x}?", 150),
    "author": ("Q7725634", "P50", "label", "Who wrote {x}?", 500),
    "director": ("Q11424", "P57", "label", "Who directed the film {x}?", 600),
}
LIMIT = 9000


def q_simple(cls, prop, kind):
    val = "?valLabel" if kind == "label" else "?val"
    vlab = "?val rdfs:label ?valLabel . FILTER(LANG(?valLabel)=\"en\")" if kind == "label" else "BIND(YEAR(?val) AS ?y) FILTER(?y >= 1200)"
    sel = "?item ?itemLabel ?valLabel ?links" if kind == "label" else "?item ?itemLabel ?y ?links"
    return PRE + f"""SELECT {sel} WHERE {{
  ?item wdt:P31 wd:{cls} . ?item wdt:{prop} ?val . ?item wikibase:sitelinks ?links .
  FILTER(?links >= 10)
  FILTER NOT EXISTS {{ ?item wdt:{prop} ?v2 . FILTER(?v2 != ?val) }}
  ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel)="en")
  {vlab}
  BIND(RAND() AS ?r)
}} ORDER BY ?r LIMIT {LIMIT}"""


Q_OFFICE = PRE + """SELECT ?country ?countryLabel ?personLabel ?start ?end ?links WHERE {
  ?country wdt:P31 wd:Q6256 . ?country wikibase:sitelinks ?links .
  ?country p:P6 ?st . ?st ps:P6 ?person . ?st pq:P580 ?start . ?st pq:P582 ?end .
  ?country rdfs:label ?countryLabel . FILTER(LANG(?countryLabel)="en")
  ?person rdfs:label ?personLabel . FILTER(LANG(?personLabel)="en")
}"""


def get(query, tries=3):
    for k in range(tries):
        try:
            r = requests.get(EP, params={"query": query}, headers=UA, timeout=300)
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
            print("status", r.status_code, re.sub(r"\s+", " ", r.text)[:200], flush=True)
        except Exception as e:
            print("error", str(e)[:120], flush=True)
        time.sleep(20)
    return None


def fetch():
    (D / "raw").mkdir(exist_ok=True)
    for rel, (cls, prop, kind, tmpl, n) in REL.items():
        if (D / "raw" / f"{rel}.json").exists():
            continue
        t = time.time()
        b = get(q_simple(cls, prop, kind))
        if b is None:
            print("FAILED", rel); continue
        (D / "raw" / f"{rel}.json").write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
        print(rel, len(b), f"{time.time()-t:.0f}s", flush=True)
        time.sleep(5)
    if not (D / "raw" / "office.json").exists():
        b = get(Q_OFFICE)
        if b is not None:
            (D / "raw" / "office.json").write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8"); print("office", len(b))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().casefold()
    return " ".join(re.sub(r"[^a-z0-9]", " ", s).split())


def stratum(links):
    return "low" if links < 25 else "mid" if links < 60 else "high"


def build():
    T = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
    uniq_cache = {}

    def unique_title(label):
        k = norm(label)
        if k not in uniq_cache:
            uniq_cache[k] = T.execute("SELECT count(*) FROM t WHERE ncore = ?", (k,)).fetchone()[0]
        return uniq_cache[k] == 1
    pool = defaultdict(list)
    for rel, (cls, prop, kind, tmpl, n) in REL.items():
        p = D / "raw" / f"{rel}.json"
        if not p.exists():
            continue
        seen = set()
        for b in json.loads(p.read_text(encoding="utf-8")):
            qid = b["item"]["value"].rsplit("/", 1)[-1]
            x = b["itemLabel"]["value"]
            if qid in seen or not re.search(r"[A-Za-z]", x) or not unique_title(x):
                continue
            seen.add(qid)
            gold = b["valLabel"]["value"] if kind == "label" else b["y"]["value"]
            if kind == "label" and re.fullmatch(r"Q\d+", gold):
                continue
            pool[rel].append({"qid": qid, "q": tmpl.format(x=x), "gold": [str(gold)], "relation": rel, "links": int(float(b["links"]["value"])),
                              "stratum": stratum(int(float(b["links"]["value"])))})
    # head of government in a year covered by exactly one holder for the whole year
    po = D / "raw" / "office.json"
    if po.exists():
        iv = defaultdict(list)
        for b in json.loads(po.read_text(encoding="utf-8")):
            try:
                s = int(b["start"]["value"][:4]); e = int(b["end"]["value"][:4])
            except Exception:
                continue
            iv[(b["country"]["value"].rsplit("/", 1)[-1], b["countryLabel"]["value"], int(float(b["links"]["value"])))].append((s, e, b["personLabel"]["value"]))
        for (qid, name, links), lst in iv.items():
            if not unique_title(name):
                continue
            for y in range(1900, 2021):
                hold = [pn for s, e, pn in lst if s < y and e > y]
                other = [1 for s, e, pn in lst if s <= y <= e and not (s < y and e > y)]
                if len(set(hold)) == 1 and not other:
                    pool["office"].append({"qid": qid, "q": f"Who was the head of government of {name} in {y}?", "gold": [hold[0]], "relation": "office",
                                           "links": links, "stratum": stratum(links)})
    rng = random.Random(2909)
    sealed, pilot = [], []
    targets = {**{k: v[4] for k, v in REL.items()}, "office": 400}
    for rel, items in pool.items():
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
        used = {id(it) for it in take}
        left = [it for it in items if id(it) not in used]
        rng.shuffle(left)
        sealed += take
        pilot += left[:max(1, 150 * want // 4000)]
    rng.shuffle(sealed); rng.shuffle(pilot)
    for i, it in enumerate(sealed):
        it["id"] = f"wd-{i:05d}"
    for i, it in enumerate(pilot):
        it["id"] = f"wdp-{i:04d}"
    for name, rows in (("sealed", sealed), ("pilot", pilot)):
        (D / name).mkdir(exist_ok=True)
        with open(D / name / "items.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    hs = [f"{hashlib.sha256((D / n / 'items.jsonl').read_bytes()).hexdigest()}  {n}/items.jsonl" for n in ("sealed", "pilot")]
    hs.append(f"{hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}  wd_build.py")
    (D / "seal_hashes.txt").write_text("\n".join(hs) + "\n", encoding="utf-8")
    print("pool sizes", {k: len(v) for k, v in pool.items()})
    print("sealed", len(sealed), dict(Counter(i["relation"] for i in sealed)), dict(Counter(i["stratum"] for i in sealed)))
    print("pilot", len(pilot), dict(Counter(i["relation"] for i in pilot)))


if __name__ == "__main__":
    {"fetch": fetch, "build": build}[sys.argv[1]]()
