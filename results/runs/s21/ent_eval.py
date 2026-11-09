"""S21 exploratory (post hoc, design data only): entity-slot checks for the frozen S19 H1 system (D3 entity slot, docs/S20_PLAN.md).
Motivation: on popqa_dev most H1 errors were releases from a page about a different entity of the same name (Dobra (Kupa) vs the
Romanian Dobra, "Index of Jordan-related articles", "List of Legion ... publications").
  core(t)  = title without a trailing "(...)" qualifier
  E-match  : core(release page) occurs in the question (the page is about the question's subject)
  E-unique : no other page in the local wiki has the same core (title == core or "core (...)"), unless every word of the release
             page's own qualifier occurs in the question (the question names the disambiguator)
Sets: dev, fresh, s18, fresh5 (all used) + popqa_dev, mintaka_dev (S21 DEV). Cached judge labels only.
usage: OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s21/ent_eval.py"""
import json
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "results" / "runs" / "s20"))
import no_retrieval2  # noqa: E402,F401
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S, s18_eval as E  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans, g6  # noqa: E402

RD = ROOT / "results" / "shared_eval" / "readers"
DB = sqlite3.connect(f"file:{LW.DB}?mode=ro", uri=True)


def load(name):
    if name == "s18":
        return E.load(["fresh3", "fresh4"]), {r["id"]: r["answer"] for r in map(json.loads, open(RD / "s18_combo_cautious_phi4.jsonl", encoding="utf-8"))}
    rows = [json.loads(l) for l in open(ROOT / f"results/runs/s19/{name}_outputs.jsonl", encoding="utf-8")]
    pre = "s21" if name.endswith("_dev") and name != "dev" else "s19"
    return rows, {r["id"]: r["answer"] for r in map(json.loads, open(RD / f"{pre}{name}_combo_cautious_phi4.jsonl", encoding="utf-8"))}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().casefold()
    return " " + " ".join(re.sub(r"[^a-z0-9]", " ", s).split()) + " "


def split(t):
    m = re.match(r"^(.*?)\s*\(([^()]*)\)$", t)
    return (m.group(1), m.group(2)) if m else (t, "")


_amb = {}


def n_same_core(core):
    if core not in _amb:
        _amb[core] = DB.execute("SELECT count(DISTINCT title) FROM articles WHERE title = ? OR (title >= ? AND title < ?)",
                                (core, core + " (", core + " )")).fetchone()[0]
    return _amb[core]


def checks(q, doc):
    core, qual = split(doc)
    nq = norm(q)
    match = norm(core) in nq
    named = bool(qual) and all(norm(w) in nq for w in re.findall(r"\w+", qual) if len(w) > 2)
    unique = n_same_core(core) <= 1 or named
    return match, unique


def main():
    out = ["# Entity-slot checks on the S19 H1 system (exploratory, post hoc; results/runs/s21/ent_eval.py)", "",
           "| set | n | system | released | coverage | wrong | correct |", "|---|---|---|---|---|---|---|"]
    blocked = []
    for name in ("dev", "fresh", "s18", "fresh5", "popqa_dev", "mintaka_dev"):
        rows, phi = load(name)
        n = len(rows)
        R = []
        for r in rows:
            a, s = S.cand(r)
            if s < 3 or not ans(a):
                continue
            rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
            p = phi.get(r["id"])
            if not rel or not (p is not None and ans(p) and agree(str(rel), str(p))):
                continue
            m, u = checks(r["question"], rec["doc"])
            R.append({"set": name, "id": r["id"], "q": r["question"], "gold": r["gold"][:3], "rel": rel, "doc": rec["doc"],
                      "graded": g6(r["question"], r["gold"], rel), "match": m, "unique": u})
        for lab, f in (("H1", lambda x: True), ("H1 + E-match", lambda x: x["match"]), ("H1 + E-unique", lambda x: x["unique"]),
                       ("H1 + E-match + E-unique", lambda x: x["match"] and x["unique"])):
            L = [x for x in R if f(x)]
            out.append(f"| {name} | {n} | {lab} | {len(L)} | {len(L) / n:.3f} | {sum(x['graded'] is False for x in L)} | {sum(x['graded'] is True for x in L)} |")
        blocked += [x for x in R if not (x["match"] and x["unique"])]
    (ROOT / "results" / "runs" / "s21" / "ent_eval.md").write_text("\n".join(out), encoding="utf-8")
    json.dump(blocked, open(ROOT / "results" / "runs" / "s21" / "ent_blocked.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(out))


if __name__ == "__main__":
    main()
