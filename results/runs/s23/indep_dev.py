"""S23 DEV diagnostic: can a question-only retrieval path (no web results) put the gold answer on a local Wikipedia page as often
as web-named pinning does? Design data only (DEV sets), CPU only, read-only on the wiki DB and the title index.
Variants (all independent of web search):
  s19 : frozen top-5 from localwiki.search
  T1  : s19 + pages whose normalised title core equals the longest question n-gram found in the title index
        (up to 3 senses, longest page first)
  T2  : BM25 top-30 re-ranked so that pages whose title core occurs in the question come first, take 5
  T12 : T2 + T1 pages (at most 8)
Reference (not independent of web): pin titles from results/runs/s22/pin.
Run: python -I -B results/runs/s23/indep_dev.py   (idle priority, one process)"""
import json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
from vkg import localwiki as LW, l3_verify as V                           # noqa: E402
from build_titles import norm                                             # noqa: E402

MON = "January February March April May June July August September October November December".split()
ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
import threading
_TL = threading.local()


class _Titles:
    """Per-thread read-only connection to the title index (sqlite connections cannot cross threads)."""
    def execute(self, *a):
        c = getattr(_TL, "c", None)
        if c is None:
            c = _TL.c = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
        return c.execute(*a)


T = _Titles()


def date_variants(a):
    out = []
    m = re.fullmatch(r"\s*(%s)\s+(\d{1,2}),?\s+(\d{3,4})\s*" % "|".join(MON), a, re.I)
    if m: out.append(f"{int(m.group(2))} {m.group(1)} {m.group(3)}")
    m = re.fullmatch(r"\s*(\d{1,2})\s+(%s),?\s+(\d{3,4})\s*" % "|".join(MON), a, re.I)
    if m: out.append(f"{m.group(2)} {int(m.group(1))}, {m.group(3)}")
    return out


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


STOPN = set("the a an of in on at to for and or is was were are who what when where which how many much did does do has have had".split())


def ngrams(q):
    toks = norm(q).split()
    for n in range(min(6, len(toks)), 0, -1):
        for i in range(len(toks) - n + 1):
            g = toks[i:i + n]
            if n == 1 and (g[0] in STOPN or len(g[0]) < 3):
                continue
            if g[0] in STOPN and n > 1 and g[-1] in STOPN:
                continue
            yield " ".join(g)


def title_pages(q, limit=3):
    """Pages whose title core equals the longest matching question n-gram (longest page first among senses)."""
    for g in ngrams(q):
        rows = T.execute("SELECT title, len FROM t WHERE ncore = ? ORDER BY len DESC LIMIT ?", (g, limit)).fetchall()
        if rows:
            return [r[0] for r in rows], g
    return [], None


def title_in_question(title, nq):
    core = norm(re.sub(r"\s*\([^()]*\)$", "", title))
    return len(core) >= 4 and f" {core} " in f" {nq} "


def t2(q):
    nq = norm(q)
    hits = LW.search(q, 30)
    first = [t for t in hits if title_in_question(t, nq)]
    rest = [t for t in hits if t not in first]
    return (first + rest)[:5]


REL = set("author composer producer genre screenwriter director capital country occupation record most all first last largest biggest award awards winner won year born died population name called".split())
QW = set("who what when where which whose whom how why is are was were did does do has have had".split())
CONN = {"of", "the", "and", "de", "von", "van", "la", "le", "in", "on", "for", "a", "an"}


def mentions(q):
    """Quoted strings, then maximal capitalised runs (inner connectors allowed), then boundary-clean n-grams."""
    out = [m for m in re.findall(r'"([^"]{2,60})"', q)]
    toks = re.findall(r"[\w'\.&-]+", q)
    i = 0
    while i < len(toks):
        t = toks[i]
        if t[:1].isupper() and t.casefold() not in QW:
            j = i + 1
            while j < len(toks) and (toks[j][:1].isupper() or (toks[j].casefold() in CONN and j + 1 < len(toks) and toks[j + 1][:1].isupper())):
                j += 1
            out.append(" ".join(toks[i:j])); i = j
        else:
            i += 1
    for g in ngrams(q):
        w = g.split()
        if w[0] in STOPN or w[-1] in STOPN or w[0] in REL or w[-1] in REL:
            continue
        out.append(g)
    return list(dict.fromkeys(out))


def title_pages2(q, limit=3, maxm=2):
    pages, used = [], []
    for m in mentions(q):
        nm = norm(m)
        bare = re.sub(r"^the ", "", nm)
        cands = [c for c in dict.fromkeys((nm, bare, "the " + bare)) if c]
        if cands:
            q = ",".join("?" * len(cands))
            rows = T.execute(f"SELECT title, len FROM t WHERE ncore IN ({q}) ORDER BY len DESC LIMIT ?", (*cands, limit)).fetchall()
            if rows:
                pages += [r[0] for r in rows]; used.append(bare)
        if len(used) >= maxm:
            break
    return uniq(pages), used


def uniq(xs):
    return list(dict.fromkeys(xs))


if __name__ == "__main__":
    out = []
    for n in ("mintaka_dev", "popqa_dev", "dev"):
        rows = [json.loads(l) for l in open(ROOT / f"results/runs/s19/{n}_outputs.jsonl", encoding="utf-8")]
        pinp = ROOT / f"results/runs/s22/pin/{n}_outputs.jsonl"
        pin = {json.loads(l)["id"]: json.loads(l)["wiki_titles"] for l in open(pinp, encoding="utf-8")} if pinp.exists() else {}
        c = Counter(); size = Counter(); miss = []
        for r in rows:
            q, gold = r["question"], r["gold"]
            s19 = r["wiki_titles"]
            tp, g = title_pages(q)
            tp2, g2 = title_pages2(q)
            v = {"s19": s19, "T1": uniq(s19 + tp), "T2": t2(q), "T3a": uniq(s19 + tp2)}
            v["T12"] = uniq(v["T2"] + tp)[:8]
            v["T3"] = uniq(v["T2"] + tp2)[:8]
            if pin: v["pin(ref)"] = pin[r["id"]]
            hit = {k: present(gold, ts) for k, ts in v.items()}
            for k in v:
                c[k] += hit[k]; size[k] += len(v[k])
            c["T12 or s19"] += hit["T12"] or hit["s19"]
            if pin and hit["pin(ref)"] and not hit["T3"]:
                miss.append((q, gold[:2], g2))
        N = len(rows)
        line = f"{n} n={N} | " + " | ".join(f"{k} {c[k]} ({c[k]/N:.2f}, pages {size[k]/N:.1f})" for k in ("s19", "T1", "T2", "T12", "T3a", "T3", "pin(ref)") if k in c)
        out.append(line); print(line)
        for m in miss[:8]:
            print("   pin hits, T3 misses:", m)
    (ROOT / "results/runs/s23/indep_dev2.md").write_text("# S23 DEV: independent retrieval diagnostic (gold verbatim on retrieved pages)\n\n" + "\n".join("- " + l for l in out) + "\n", encoding="utf-8")
