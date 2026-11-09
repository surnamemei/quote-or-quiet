"""Independent check of the synthetic benchmark's gold: re-derive every gold answer from the document text alone (fresh regexes, no code from
gen_closed.py), compare with items.jsonl, and test the answerability labels. python -I -B results/runs/s24/verify_gold.py closed_test [closed_test2 ...]"""
import json, re, sys
from pathlib import Path
D = Path(__file__).resolve().parent
MON = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}
DATE = r"(?:(?P<m1>[A-Z][a-z]+) (?P<d1>\d{1,2}), (?P<y1>\d{4})|(?P<d2>\d{1,2}) (?P<m2>[A-Z][a-z]+) (?P<y2>\d{4}))"


def parse_dates(text):
    out = []
    for m in re.finditer(DATE, text):
        g = m.groupdict()
        if g["m1"]:
            out.append((int(g["y1"]), MON[g["m1"]], int(g["d1"])))
        else:
            out.append((int(g["y2"]), MON[g["m2"]], int(g["d2"])))
    return out


def check(name):
    items = [json.loads(l) for l in open(D / name / "items.jsonl", encoding="utf-8")]
    docs = {json.loads(l)["id"]: json.loads(l) for l in open(D / name / "docs.jsonl", encoding="utf-8")}
    bad = []; n = 0
    for e in items:
        q = e["q"]; ds = [docs[i] for i in e["docs"]]; n += 1
        if q.startswith("In which city was"):
            for k, d in enumerate(ds):
                m = re.search(r"born in ([A-Z][a-z]+)(?= on )|born on [^.]*? in ([A-Z][a-z]+)\.", d["text"])
                city = (m.group(1) or m.group(2)) if m else None
                want = e["gold"][k] if k < len(e["gold"]) else None
                if want is None:
                    continue                       # the second document of a qualified question is the namesake distractor
                if city != want:
                    bad.append((e["id"], "city", city, want))
        elif q.startswith("How old was"):
            d = ds[0]; t = d["text"]
            dates = parse_dates(t)
            if len(dates) != 2:
                bad.append((e["id"], "dates", dates, e["gold"])); continue
            (by, bm, bd), (jy, jm, jd) = dates
            age = jy - by - ((jm, jd) < (bm, bd))
            if [str(age)] != e["gold"]:
                bad.append((e["id"], "age", age, e["gold"]))
        elif q.startswith("What is the name of") and "doctoral supervisor" in q:
            if e["gold"] != [] or any(re.search(r"supervis|advis|doctoral|PhD", d["text"], re.I) for d in ds):
                bad.append((e["id"], "unanswerable-not", None, e["gold"]))
        elif q.startswith("Who directed"):
            m = re.match(r"Who directed (.+) in (\d{4})\?", q)
            org, y = m.group(1), int(m.group(2)); t = ds[0]["text"]
            spans = re.findall(r"([A-Z][a-z]+ [A-Z][a-z]+) led it from (\d{4}) to (\d{4})", t)
            hit = [n_ for n_, a, b in spans if int(a) <= y < int(b) or (int(a) <= y <= int(b) and b == "2020" and y < 2020)]
            if len(hit) != 1 or [hit[0]] != e["gold"]:
                bad.append((e["id"], "tenure", hit, e["gold"]))
        else:
            bad.append((e["id"], "unrecognised question", q, None))
    print(name, "items", n, "mismatches", len(bad), bad[:3])
    return len(bad)


if __name__ == "__main__":
    tot = sum(check(n) for n in sys.argv[1:])
    print("total mismatches", tot)
