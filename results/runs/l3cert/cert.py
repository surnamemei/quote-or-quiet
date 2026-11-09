"""Derivation certificates (L3 beyond verbatim spans). A certificate = (facts, op): each fact is a quote that must occur
VERBATIM in a pinned local document (V.locate); the value of a fact is parsed from its quote by deterministic code (the LLM
supplies quotes and an operation name, never values); the answer is computed by a whitelisted operation. Soundness: a released
number is the output of a fixed program on parsed values of verbatim pinned spans. Not covered (as in L3): the quote answers the
relation, the source is true, time.
Ops: years_between(a,b)=year(b)-year(a) [year-or-date facts], age_at(birth,event) [needs full dates for both: else rejected],
diff(a,b)=a-b [number facts], sum(a,b,...) [number facts]. Anything else -> no certificate."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import l3_verify as V                                       # noqa: E402

MON = {m: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())}
MON.update({m[:3]: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())})
D1 = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]{3,9})\.?,?\s+(\d{3,4})\b")
D2 = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{3,4})\b")
YR = re.compile(r"(?<!\d)(\d{3,4})(?!\d)")
NUM = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\d])")


def parse_date(q):
    out = set()
    for m in D1.finditer(q):
        d, mo, y = m.groups(); mo = MON.get(mo.casefold())
        if mo: out.add((int(y), mo, int(d)))
    for m in D2.finditer(q):
        mo, d, y = m.groups(); mo = MON.get(mo.casefold())
        if mo: out.add((int(y), mo, int(d)))
    return out


def parse_fact(quote, kind):
    """-> ('date',(y,m,d)) | ('year',y) | ('number',n) | None; None unless the quote has exactly one reading."""
    if kind in ("date", "year"):
        ds = parse_date(quote)
        if len(ds) == 1:
            return ("date", next(iter(ds)))
        if kind == "year":
            ys = {int(m.group(1)) for m in YR.finditer(quote)}
            if len(ys) == 1:
                return ("year", next(iter(ys)))
        return None
    ns = {int(m.group(1).replace(",", "")) for m in NUM.finditer(quote)}
    return ("number", next(iter(ns))) if len(ns) == 1 else None


def year_of(f): return f[1][0] if f[0] == "date" else f[1] if f[0] == "year" else None


def compute(op, vals):
    if op == "years_between" and len(vals) == 2 and all(v[0] in ("date", "year") for v in vals):
        return year_of(vals[1]) - year_of(vals[0])
    if op == "age_at" and len(vals) == 2 and all(v[0] == "date" for v in vals):
        (y0, m0, d0), (y1, m1, d1) = vals[0][1], vals[1][1]
        return y1 - y0 - ((m1, d1) < (m0, d0))
    if op == "diff" and len(vals) == 2 and all(v[0] == "number" for v in vals):
        return vals[0][1] - vals[1][1]
    if op == "sum" and len(vals) >= 2 and all(v[0] == "number" for v in vals):
        return sum(v[1] for v in vals)
    return None


def certify(spec, docs):
    """spec = {"facts":[{"id","quote","kind"}], "op", "args":[ids]}; docs = {title: text}. -> (answer, certificate) or (None, reason)."""
    if not isinstance(spec, dict) or spec.get("op") in (None, "none"):
        return None, "no op"
    facts = {}
    for f in spec.get("facts", []):
        q, kind = str(f.get("quote", "")), f.get("kind")
        if len(q) < 8 or kind not in ("date", "year", "number"):
            return None, "bad fact"
        where = [t for t, txt in docs.items() if next(V.locate(q, txt), None)]
        if not where:
            return None, f"quote not verbatim in pinned docs: {q[:50]}"
        v = parse_fact(q, kind)
        if v is None:
            return None, f"unparsable: {q[:50]}"
        facts[f["id"]] = {"quote": q, "doc": where[0], "value": v}
    try:
        vals = [facts[a]["value"] for a in spec.get("args", [])]
    except KeyError:
        return None, "unknown arg"
    r = compute(spec["op"], vals)
    if r is None or r < 0:
        return None, "op not applicable"
    return str(r), {"op": spec["op"], "facts": facts, "answer": str(r)}
