"""Independent re-scoring of Tables 4 and 5 from the raw generations, with a simpler release rule written separately from closed_run.py (no V1-V5, no
release2, no cert.py): an ordinary answer is released when the reader outputs agree (normalised equality of plain, cautious and veto) and the string occurs verbatim
in a retrieved document; a namesake question needs that rule on each candidate document; a computed answer is the age computed here from the dates quoted in the
Phi-4 specification, when each quote occurs verbatim in a retrieved document and parses to exactly one date. python -I -B results/runs/s24/verify_scores.py"""
import json, re, sys
from collections import Counter
from pathlib import Path
D = Path(__file__).resolve().parent
MON = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}
DATE = r"(?:(?P<m1>[A-Z][a-z]+) (?P<d1>\d{1,2}), (?P<y1>\d{4})|(?P<d2>\d{1,2}) (?P<m2>[A-Z][a-z]+) (?P<y2>\d{4}))"


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(s).casefold()).split())


def dates(text):
    out = []
    for m in re.finditer(DATE, text):
        g = m.groupdict()
        out.append((int(g["y1"]), MON[g["m1"]], int(g["d1"])) if g["m1"] else (int(g["y2"]), MON[g["m2"]], int(g["d2"])))
    return out


def run(name, gen_path):
    items = {json.loads(l)["id"]: json.loads(l) for l in open(D / name / "items.jsonl", encoding="utf-8")}
    docs = {json.loads(l)["id"]: json.loads(l) for l in open(D / name / "docs.jsonl", encoding="utf-8")}
    title_text = {d["title"]: d["text"] for d in docs.values()}
    id_title = {i: d["title"] for i, d in docs.items()}
    rows = [json.loads(l) for l in open(gen_path, encoding="utf-8")]
    c = Counter(); wrong = []
    for r in rows:
        e = items[r["id"]]; q = e["q"]
        def agree(t):
            a, b, p = norm(t["plain"]), norm(t["cautious"]), norm(t["phi4"])
            return bool(a) and a == b == p and a not in ("unknown", "") and not a.startswith("unknown")
        def verbatim(ans, titles):
            return any(norm(ans) and f" {norm(ans)} " in f" {norm(title_text[t])} " for t in titles)
        kind = ("namesake" if e["state"] == "Qualified" else "unanswerable" if e["state"] == "Unresolved" else
                "computed" if e["state"] == "Derived" else "tenure" if q.startswith("Who directed") else "lookup")
        state = "none"; ok = None
        if r["amb"]:
            res = []
            for t in r["amb"]:
                pd = r["per_doc"][t]
                res.append(pd["plain"] if agree(pd) and verbatim(pd["plain"], [t]) else None)
            if all(x is not None for x in res):
                state = "list"
                ok = e["state"] == "Qualified" and all(
                    norm(res[i]) == norm(e["gold"][next(k for k, dd in enumerate(e["docs"]) if id_title[dd] == t)]) for i, t in enumerate(r["amb"]))
        else:
            if agree(r) and verbatim(r["plain"], r["titles"]):
                state = "span"; ok = any(norm(g) == norm(r["plain"]) for g in e["gold"]) and e["state"] in ("Verified", "Derived")
            elif kind == "computed" and r.get("spec"):
                m = re.search(r"\{.*\}", r["spec"], re.S)
                try:
                    sp = json.loads(m.group(0)) if m else {}
                    qs = [f["quote"] for f in sp.get("facts", [])]
                    ds = []
                    for qq in qs:
                        found = [t for t in r["titles"] if qq in title_text[t]]
                        pd_ = dates(qq)
                        if found and len(pd_) == 1:
                            ds.append(pd_[0])
                    if sp.get("op") == "age_at" and len(ds) == 2:
                        (by, bm, bd), (jy, jm, jd) = ds
                        age = jy - by - ((jm, jd) < (bm, bd))
                        state = "derived"; ok = [str(age)] == e["gold"]
                except Exception:
                    pass
        c[(kind, state, ok)] += 1
        if state != "none" and ok is False:
            wrong.append((e["id"], kind, state))
    definite = sum(v for (k, s, o), v in c.items() if s != "none")
    right = sum(v for (k, s, o), v in c.items() if s != "none" and o)
    print(f"{name}: items {len(rows)}, definite answers {definite} ({definite/len(rows):.3f}), correct {right}, wrong definite {len(wrong)}")
    bykind = Counter()
    for (k, s, o), v in c.items():
        bykind[(k, "correct" if (s != "none" and o) else "wrong" if (s != "none") else "unresolved")] += v
    for k in ("lookup", "tenure", "computed", "namesake", "unanswerable"):
        print("  ", k, {x: bykind[(k, x)] for x in ("correct", "wrong", "unresolved")})
    print("   wrong examples:", wrong[:3])


if __name__ == "__main__":
    run("closed_test", D / "closed_test_run" / "gen.jsonl")
    run("closed_test2", D / "alt" / "closed_test2_run" / "gen.jsonl")
