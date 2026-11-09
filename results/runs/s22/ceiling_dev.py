"""Certifiable ceiling on DEV: share of items whose gold (any alias, with date surface variants) occurs verbatim in the pinned
pages, for the S19 titles and the pin titles; plus a question-type census (count / compute / compare / yes-no)."""
import json, re, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from vkg import localwiki as LW, l3_verify as V                      # noqa: E402
from cf_dev import date_variants                                     # noqa: E402

ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
MON = "January February March April May June July August September October November December".split()


def forms(g):
    g = str(g).strip(); out = {g}
    m = ISO.match(g)
    if m:
        y, mo, d = m.groups(); M = MON[int(mo) - 1]
        out |= {f"{int(d)} {M} {y}", f"{M} {int(d)}, {y}"}
    out |= set(date_variants(g))
    return [x for x in out if x]


def present(gold, titles):
    for t in titles:
        txt = LW.page_text(t) or ""
        for g in gold[:9]:
            for f in forms(g):
                if next(V.locate(f, txt), None):
                    return True
    return False


def qtype(q):
    ql = q.casefold()
    if re.match(r"^(is|are|was|were|did|does|do|has|have|can|will)\b", ql): return "yes/no"
    if re.search(r"\bhow (old|long|far|tall|many years)\b|\bage\b", ql): return "compute"
    if re.search(r"\bhow many\b|\bnumber of\b", ql): return "count"
    if re.search(r"\b(more|less|older|younger|bigger|larger|smaller|first|last|longest|highest|most|least)\b.*\b(or|than)\b", ql): return "compare"
    return "lookup"


for n in ("mintaka_dev", "popqa_dev", "dev"):
    rows = [json.loads(l) for l in open(ROOT / f"results/runs/s19/{n}_outputs.jsonl", encoding="utf-8")]
    pinp = ROOT / f"results/runs/s22/pin/{n}_outputs.jsonl"
    pin = {json.loads(l)["id"]: json.loads(l)["wiki_titles"] for l in open(pinp, encoding="utf-8")} if pinp.exists() else {}
    c = Counter(); qt = Counter(); qtp = Counter()
    for r in rows:
        a = present(r["gold"], r["wiki_titles"]); b = present(r["gold"], pin[r["id"]]) if pin else None
        t = qtype(r["question"]); qt[t] += 1
        c["s19 titles"] += a
        if pin: c["pin titles"] += b; c["either"] += a or b; qtp[t] += b
    print(n, len(rows), {k: f"{v} ({v/len(rows):.2f})" for k, v in c.items()}, "| qtypes", dict(qt), "| gold on pinned page by type", dict(qtp))
