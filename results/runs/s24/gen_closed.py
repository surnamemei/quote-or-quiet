"""S24 closed-evidence benchmark generator (fictional entities, exact gold, no benchmark noise).
Each item has: question, gold (list of acceptable strings), expected state (Verified / Derived / Qualified / Unresolved) and the ids of
the documents that contain the evidence. Documents are short encyclopedic paragraphs about invented people and organisations; namesake
pairs make some questions ambiguous by design; some questions ask for facts that no document states.
A definite answer to a question whose expected state is Qualified or Unresolved is a silent error by construction.
usage: python -I -B results/runs/s24/gen_closed.py <name> <seed> <n_items>   -> results/runs/s24/<name>/{items,docs}.jsonl + hashes"""
import hashlib, json, random, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
MON = "January February March April May June July August September October November December".split()
SYL1 = "Mar Vel Tor Ka Lin Sor Del Bren Qui Zan Hol Pel Dru Fen Gal Ost Rav Tam Wyn Yor".split()
SYL2 = "ek den vik ra lo mi ta sen dor nal pen shu ric bel gar".split()
SYL3 = "ov son berg stein ley ford wick hart man field ton by".split()
CITY1 = ("Alder Brook Cedar Dun Elm Fair Glen Hollow Iron Kings Lake Marsh North Oak Pine Quarry Ridge Stone Thorn West "
         "Ash Bay Crow Dove East Fox Grey Hart Ivy Jay Kirk Lark Moss Nether Over Pike Rook South Tarn Upper Vale Wolf Yew Birch Clay").split()
CITY2 = "ford ton field bury wick port ham mouth dale gate vale haven by combe worth stead mere".split()
OCC = ["architect", "botanist", "cartographer", "composer", "economist", "geologist", "historian", "linguist", "painter", "surgeon"]
ORG1 = ("Apex Borealis Corvid Delta Ember Fathom Garnet Helix Ivory Juniper Keystone Lumen Meridian Nimbus Onyx Pioneer "
        "Quartz Radian Sable Talon Umber Vertex Willow Xenon Yarrow Zephyr Argent Basalt Cobalt Dusk Ether Flint Granite Harbor "
        "Indigo Jasper Kestrel Lantern Mosaic Nova Orchid Prism Quill Raven Summit Tundra Union Valor Wren Zenith Anchor Beacon "
        "Cinder Drift Echo Forge Glacier Horizon Isle Journey Kite Loom Marble Nectar Opal Pearl Quest Reef Spire Terrace").split()
ORG2 = ["Institute", "Laboratories", "Press", "Works", "Society", "Foundation", "Council", "Studio"]


class World:
    def __init__(self, seed):
        self.r = random.Random(seed); self.docs = {}; self.used = set()

    def uniq(self, f):
        while True:
            x = f()
            if x not in self.used:
                self.used.add(x); return x

    def person_name(self):
        r = self.r
        return self.uniq(lambda: f"{r.choice(SYL1)}{r.choice(SYL2)} {r.choice(SYL1)}{r.choice(SYL3)}")

    def city(self, avoid=()):
        r = self.r
        while True:
            c = f"{r.choice(CITY1)}{r.choice(CITY2)}"
            if c not in avoid:
                return c

    def org(self):
        r = self.r
        return self.uniq(lambda: f"{r.choice(ORG1)} {r.choice(ORG2)}")

    def org_any(self):
        r = self.r
        return f"{r.choice(ORG1)} {r.choice(ORG2)}"

    def add(self, title, text):
        did = f"d{len(self.docs):06d}"; self.docs[did] = {"id": did, "title": title, "text": text}; return did

    def date(self, y0, y1):
        r = self.r; y = r.randint(y0, y1); m = r.randint(1, 12); d = r.randint(1, 28)
        return y, m, d

    def person(self, name=None, occ=None, org=None, avoid_city=()):
        r = self.r
        name = name or self.person_name(); occ = occ or r.choice(OCC)
        by, bm, bd = self.date(1930, 1985); city = self.city(avoid_city)
        jy = by + r.randint(22, 40); jm = r.randint(1, 12); jd = r.randint(1, 28); org = org or self.org_any()
        bdate = f"{MON[bm-1]} {bd}, {by}" if r.random() < 0.5 else f"{bd} {MON[bm-1]} {by}"
        jdate = f"{MON[jm-1]} {jd}, {jy}" if r.random() < 0.5 else f"{jd} {MON[jm-1]} {jy}"
        age = jy - by - ((jm, jd) < (bm, bd))
        t = r.choice([f"{name} was born on {bdate} in {city}. A {occ} by training, {name} joined {org} on {jdate}.",
                      f"{name} ({occ}) was born in {city} on {bdate}. On {jdate}, {name} took a post at {org}."])
        return {"name": name, "occ": occ, "by": by, "city": city, "jy": jy, "age": age, "org": org, "text": t, "bdate": bdate}


def build(seed, n):
    w = World(seed); r = w.r; items = []
    mix = [("lookup_unique", .28), ("lookup_qualified", .14), ("lookup_ambiguous", .10), ("compute_age", .16), ("unanswerable", .16), ("tenure", .16)]
    kinds = []
    for k, p in mix:
        kinds += [k] * round(n * p)
    while len(kinds) < n: kinds.append("lookup_unique")
    r.shuffle(kinds); kinds = kinds[:n]
    for i, k in enumerate(kinds):
        if k == "lookup_unique":
            p = w.person(); d = w.add(p["name"], p["text"])
            items.append(dict(q=f"In which city was {p['name']} born?", gold=[p["city"]], state="Verified", docs=[d]))
        elif k in ("lookup_qualified", "lookup_ambiguous"):
            a = w.person(); b = w.person(name=a["name"], occ=r.choice([o for o in OCC if o != a["occ"]]), avoid_city=(a["city"],))
            da = w.add(a["name"] + " (" + a["occ"] + ")", a["text"]); db = w.add(b["name"] + " (" + b["occ"] + ")", b["text"])
            if k == "lookup_qualified":
                items.append(dict(q=f"In which city was the {a['occ']} {a['name']} born?", gold=[a["city"]], state="Verified", docs=[da, db]))
            else:
                items.append(dict(q=f"In which city was {a['name']} born?", gold=[a["city"], b["city"]], state="Qualified", docs=[da, db]))
        elif k == "compute_age":
            p = w.person(); d = w.add(p["name"], p["text"])
            items.append(dict(q=f"How old was {p['name']} when they joined {p['org']}?", gold=[str(p["age"])],
                              state="Derived", docs=[d], note="age in whole years on the stated joining date"))
        elif k == "unanswerable":
            p = w.person(); d = w.add(p["name"], p["text"])
            items.append(dict(q=f"What is the name of {p['name']}'s doctoral supervisor?", gold=[], state="Unresolved", docs=[d]))
        elif k == "tenure":
            org = w.org(); ys = sorted(r.sample(range(1950, 2020), 3)); names = [w.person_name() for _ in range(3)]
            text = f"{org} has had three directors. " + " ".join(
                f"{n} led it from {y} to {ys[j+1] if j < 2 else 2020}." for j, (n, y) in enumerate(zip(names, ys)))
            d = w.add(org, text); j = r.randint(0, 2); y = r.randint(ys[j], (ys[j + 1] if j < 2 else 2020) - 1)
            items.append(dict(q=f"Who directed {org} in {y}?", gold=[names[j]], state="Verified", docs=[d]))
    for i, it in enumerate(items):
        it["id"] = f"closed-{seed}-{i:05d}"
    return items, list(w.docs.values())


if __name__ == "__main__":
    name, seed, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    items, docs = build(seed, n)
    d = OUT / name; d.mkdir(parents=True, exist_ok=True)
    for fn, rows in (("items.jsonl", items), ("docs.jsonl", docs)):
        with open(d / fn, "w", encoding="utf-8") as f:
            for r_ in rows:
                f.write(json.dumps(r_, ensure_ascii=False) + "\n")
    h = {fn: hashlib.sha256((d / fn).read_bytes()).hexdigest() for fn in ("items.jsonl", "docs.jsonl")}
    h["generator"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (d / "hashes.json").write_text(json.dumps(h, indent=1), encoding="utf-8")
    from collections import Counter
    print(name, seed, len(items), "items", len(docs), "docs", dict(Counter(i["state"] for i in items)))
