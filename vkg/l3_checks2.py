"""DRAFT (post-S18, not frozen): extra deterministic checks for the L3 gate, aimed at the failure classes seen in S18
(results/runs/s18/S18_RESULT.md). Designed AFTER seeing the S18 errors, so any score on FRESH-3/FRESH-4 is optimistic
(post hoc); only a new sealed set can test them.
  T2   question type with fixes: "year and month" in either order -> MONTH_YEAR; "version" questions -> VERSION.
  V3'  type check with T2 (VERSION grammar: digits with dots, optional letter suffix, optional leading v).
  V2'  whole numbers: a span starting or ending with a digit must not continue a longer number in the source.
  V5   unit consistency: for "how many <noun>" questions, a unit word inside the span or right after it in the source must be the
       counted noun (singular or plural); a different known unit (time, length, mass, period...) rejects.
Like V1-V4, these are deterministic functions of (question, span, document) with no learned parts and no gold."""
import re

from . import l3_verify as V

UNITS = set("""second seconds minute minutes hour hours day days week weeks month months year years decade decades century centuries
millennium millennia metre metres meter meters km kilometre kilometres kilometer kilometers mile miles foot feet ft inch inches cm mm
kg kilogram kilograms gram grams g lb lbs pound pounds ton tons tonne tonnes percent % round rounds lap laps inning innings
set sets game games match matches goal goals point points run runs episode episodes season seasons times""".split())

VERSION = re.compile(r"^v?\d+(?:\.\d+)+[a-z]?$", re.I)


def T2(question):
    q = question.casefold()
    if re.search(r"\b(?:what|which)\s+(?:[a-z]+\s+)?version\b(?!\s+of\b)", q) and not re.search(r"\bhow many\b", q):
        return "VERSION"
    if re.search(r"\byear and month\b|\bmonth and year\b", q) and not re.search(r"\bday\b", q):
        return "MONTH_YEAR"
    return V.T(question)


def counted_noun(question):
    m = re.search(r"\bhow many\s+([a-z]+)", question.casefold())
    return m.group(1) if m else None


def _canon(w):
    w = w.casefold().rstrip(".")
    return re.sub(r"(met|lit|cent)re", lambda m: m.group(1) + "er", w)


def _same(a, b):
    a, b = _canon(a), _canon(b)
    return a == b or a.rstrip("s") == b.rstrip("s") or a.replace("ies", "y") == b.replace("ies", "y")


def unit_ok(question, span, after):
    c = counted_noun(question)
    if not c:
        return True
    words = re.findall(r"[A-Za-z%]+", span)
    nxt = re.match(r"\s*([A-Za-z%]+)", after)
    cand = words[-1:] if words else ([nxt.group(1)] if nxt else [])
    for w in cand:
        if w.casefold() in UNITS and not _same(w, c):
            return False
    return True


def whole_number(doc_text, i, j):
    """V2': a span that starts or ends with a digit must not be part of a longer number in the source
    (e.g. "700" inside "5,700")."""
    s = doc_text[i:j]
    if s[:1].isdigit() and re.search(r"\d[,.   ]?$", doc_text[max(0, i - 2):i]):
        return False
    if s[-1:].isdigit() and re.match(r"^[,.   ]?\d", doc_text[j:j + 2]) and not re.match(r"^\.0+(?!\d)", doc_text[j:j + 8]):
        return False
    return True


def extra(question, doc_text, i, j):
    """(ok, reason) for the extra checks on a span that V1-V4 accepted."""
    if not whole_number(doc_text, i, j):
        return False, "V2': span is part of a longer number"
    span = doc_text[i:j].strip()
    t = T2(question)
    if t == "VERSION":
        if not VERSION.match(span):
            return False, "V3': span is not a version string"
    elif t != V.T(question) and not V.type_ok(span, t):
        return False, f"V3': span does not match type {t}"
    if not unit_ok(question, span, doc_text[j:j + 30]):
        return False, "V5: unit differs from the counted noun"
    return True, "ok"


def release2(question, answer, titles, corpus_get):
    """Gate F with V1-V4 plus T2/V5: the first span accepted by both is released."""
    if not answer:
        return None, {"reason": "no answer"}
    last = "no span found in pinned documents"
    for d in titles:
        text = corpus_get(d)
        if not text:
            continue
        for i, j in V.locate(answer, text):
            y = {"answer": answer, "doc": d, "doc_sha256": V.doc_hash(text), "start": i, "end": j}
            ok, why = V.verify(question, y, corpus_get)
            if ok:
                ok, why = extra(question, text, i, j)
            if ok:
                return answer, {**y, "span": text[i:j], "reason": why}
            last = why
    return None, {"reason": last}


# ---------------------------------------------------------------- V6 (draft): sentence support
STOP = set("""a an the of in on at to for from by with and or as is was were are be been being did does do has have had what which who
whom whose when where why how many much that this these those it its his her their there than then into over under about after before
during between up out not no year years month day date name full number first last according give tell""".split())


def _stem(w):
    return w[:5]


def content_words(question, title):
    tw = {_stem(w) for w in re.findall(r"[a-z0-9]+", title.casefold())}
    out = set()
    for w in re.findall(r"[a-z0-9]+", question.casefold()):
        if len(w) >= 3 and w not in STOP and _stem(w) not in tw:
            out.add(_stem(w))
    return out


def sentence_at(text, i, j):
    """The sentence or table row/line holding [i, j): bounded by newlines, '|' cell borders are kept (whole row),
    and sentence ends '. ' / '? ' / '! '."""
    a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
    ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
    b = min(ends) if ends else len(text)
    return text[a:b]


def sentence_support(question, title, text, i, j):
    """Number of the question's content words (5-letter stems, title words excluded) found in the span's sentence."""
    cw = content_words(question, title)
    sw = {_stem(w) for w in re.findall(r"[a-z0-9]+", sentence_at(text, i, j).casefold())}
    return len(cw & sw)


def release3(question, answer, titles, corpus_get, m=1):
    """V1-V5 draft plus V6: the span's sentence must hold at least m content words of the question."""
    if not answer:
        return None, {"reason": "no answer"}
    last = "no span found in pinned documents"
    for d in titles:
        text = corpus_get(d)
        if not text:
            continue
        for i, j in V.locate(answer, text):
            y = {"answer": answer, "doc": d, "doc_sha256": V.doc_hash(text), "start": i, "end": j}
            ok, why = V.verify(question, y, corpus_get)
            if ok:
                ok, why = extra(question, text, i, j)
            if ok and sentence_support(question, d, text, i, j) < m:
                ok, why = False, f"V6: span sentence shares < {m} content words with the question"
            if ok:
                return answer, {**y, "span": text[i:j], "reason": why}
            last = why
    return None, {"reason": last}
