"""S22 format relaxation of the gate (accepted by the user 2026-11-08): the claim stays a verbatim, typed span of a pinned page.
F1 surface choice: among the reader outputs that agree with the max-support candidate (same support group), try every surface
   form at the gate, longest first (sentences fail the gate; the most specific short form wins), plus date surface variants ("November 23, 2004" <-> "23 November 2004").
F2 type grammar: YEAR also accepts years with an era ("218 BC", "AD 79"); a "when ..." question typed YEAR also accepts a full
   date or month-year span (more specific than asked, still verbatim and typed).
Everything else is vkg.l3_checks2.release2 unchanged (V1-V5)."""
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from vkg import l3_checks2 as C, l3_verify as V, s17_eval as S       # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402

KEYS = [f"{s}_{k}" for s in ("web", "wiki", "combo") for k in ("plain", "cautious")]
MON = "January February March April May June July August September October November December".split()
ERA_YEAR = re.compile(r"^(?:c\.\s*)?(?:\d{1,4}\s*(?:BC|BCE|AD|CE)|(?:AD|CE)\s*\d{1,4})$", re.I)


def date_variants(a):
    out = []
    m = re.fullmatch(r"\s*(%s)\s+(\d{1,2}),?\s+(\d{3,4})\s*" % "|".join(MON), a, re.I)
    if m: out.append(f"{int(m.group(2))} {m.group(1)} {m.group(3)}")
    m = re.fullmatch(r"\s*(\d{1,2})\s+(%s),?\s+(\d{3,4})\s*" % "|".join(MON), a, re.I)
    if m: out.append(f"{m.group(2)} {int(m.group(1))}, {m.group(3)}")
    return out


_orig_extra_T = C.T2


def _type_ok(question, span):
    t = C.T2(question)
    if t == "YEAR":
        if V.G["YEAR"].match(span) or ERA_YEAR.match(span):
            return True
        if question.strip().casefold().startswith("when") and (V.G["DATE_DMY"].match(span) or V.G["MONTH_YEAR"].match(span)):
            return True
        return False
    return None            # not decided here: fall back to the frozen check


def release_fmt(question, answer, titles, corpus_get):
    """release2 with F2 (type) relaxation for one surface form."""
    rel, rec = C.release2(question, answer, titles, corpus_get)
    if rel or "V3" not in str(rec.get("reason", "")):
        return rel, rec
    # V3 failed: re-run the span search accepting the F2 grammar, keeping V1, V2, V4, V5
    for d in titles:
        text = corpus_get(d)
        if not text:
            continue
        for i, j in V.locate(answer, text):
            if _type_ok(question, text[i:j]) is not True:
                continue
            y = {"answer": answer, "doc": d, "doc_sha256": V.doc_hash(text), "start": i, "end": j}
            saved = V.T
            try:
                V.T = lambda q: "ANY"          # V3 replaced by _type_ok above; V1, V2, V4 unchanged
                ok, why = V.verify(question, y, corpus_get)
            finally:
                V.T = saved
            if ok:
                ok, why = C.extra(question, text, i, j) if C.T2(question) != "YEAR" else (True, "F2")
            if ok:
                return answer, {**y, "span": text[i:j], "reason": "F2 " + str(why)}
    return None, rec


def candidate_forms(r):
    a, s = S.cand(r)
    if not ans(a):
        return [], s
    group = [str(r[k]) for k in KEYS if ans(r[k]) and agree(str(r[k]), str(a))]
    forms = []
    for x in sorted(set(group), key=len, reverse=True):   # longest first: sentences fail the gate, then the most specific short form
        for f in [x] + date_variants(x):
            if f not in forms:
                forms.append(f)
    return forms, s


def release_any(r, corpus_get, min_support=3):
    forms, s = candidate_forms(r)
    if s < min_support:
        return None, {}
    last = {}
    for f in forms:
        rel, rec = release_fmt(r["question"], f, r["wiki_titles"], corpus_get)
        if rel:
            return rel, rec
        last = rec
    return None, last
