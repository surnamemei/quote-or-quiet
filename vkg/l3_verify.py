"""L3: constrained, verified extraction from a pinned corpus (docs/L2_L3_ANALYSIS.md, section 2).

Release object  y = (answer a, document title d, character span [i, j) of D[d]).
Verifier V(x, y) accepts iff
  V1  d is in the pinned corpus D (local FineWiki index) and sha256(D[d]) equals the hash recorded in y   (document identity)
  V2  N(D[d][i:j]) == N(a)                                                                                (verbatim grounding)
  V3  D[d][i:j] matches the answer-type grammar G[T(x)] of the question's type T(x)                       (type conformity)
  V4  every year named in the title d (incl. season ranges such as 2018-19) is named in the question x   (period consistency)
N, T and G are small deterministic functions defined here, with no learned parts and no gold.
Gate F: release a only with an accepted y; otherwise "Unresolved" (target state 3) with the failed check as the reason.

THEOREM (soundness of release). For every x: if F(x) = a != Unresolved, there is a title d in D and a span [i, j) with
N(D[d][i:j]) = N(a), sha256(D[d]) equal to the recorded hash, D[d][i:j] in the language of G[T(x)], and
years(d) a subset of years(x).
Proof: release happens only on the branch where V returned accept, and V accepts only if V1-V4 hold (they are
evaluated directly on the inputs). QED.
Not covered (assumptions, measured statistically): A1 the source text is wrong; A2 the span does not answer x (wrong
entity, year, ...); A3 T(x) misparses the question. End-to-end: P(false release) <= eps_A1 + eps_A2 + eps_A3 (union bound).

The span finder `locate` is heuristic and outside the theorem: it only proposes candidate spans; V decides."""
import hashlib
import re
import unicodedata

MONTHS = ("january february march april may june july august september october november december".split())
_MON = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
_YEAR = r"(?:1[0-9]{3}|20[0-9]{2})"
_DAY = r"(?:[0-3]?[0-9])(?:st|nd|rd|th)?"


# ---------------------------------------------------------------- N: normaliser
def N(s):
    """Deterministic normaliser: Unicode NFKC, casefold, unify dashes/quotes, drop thousands separators in numbers,
    strip surrounding punctuation, collapse whitespace."""
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = re.sub(r"[‐-―−]", "-", s)
    s = re.sub(r"[‘’‚‛]", "'", s)
    s = re.sub(r"[“”„‟]", '"', s)
    s = re.sub(r"(?<=\d)[,   ](?=\d{3}\b)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.strip(" .,;:!?\"'()[]")


# ---------------------------------------------------------------- T: question answer type
def T(question):
    q = question.casefold()
    if re.search(r"\b(day, month,? and year|month, day,? and year|exact date|what date|which date|on what day)\b", q) or \
       re.search(r"\b(day|date)\b.*\byear\b", q):
        return "DATE_DMY"
    if re.search(r"\bmonth and year\b|\bwhich month\b.*\byear\b|\bwhat month\b.*\byear\b", q):
        return "MONTH_YEAR"
    if re.search(r"\b(what|which|in what|in which) year\b|\byear (was|did|were)\b|^when (was|did)\b.*\b(born|founded|established|published|released)\b", q):
        return "YEAR"
    if re.search(r"\bexact (number|count|amount|figure)\b|\bprecise (number|count)\b", q):
        return "NUMBER_EXACT"
    if re.search(r"\bhow (many|much|old|long|tall|high|far|deep|wide)\b|\bwhat (number|percentage|amount|score|rank)\b", q):
        return "NUMBER"
    if re.search(r"^\s*(who|whom)\b|\bwhat (is|was) the (full |first |last )?name of\b|\bwhich (person|artist|player|author|scientist)\b", q):
        return "NAME"
    return "ANY"


# ---------------------------------------------------------------- G: grammar per type (on the raw span)
G = {
    "DATE_DMY": re.compile(rf"^(?:{_DAY}\s+{_MON},?\s+{_YEAR}|{_MON}\s+{_DAY},?\s+{_YEAR}|{_YEAR}-[01][0-9]-[0-3][0-9])$", re.I),
    "MONTH_YEAR": re.compile(rf"^(?:{_MON},?\s+{_YEAR}|{_DAY}\s+{_MON},?\s+{_YEAR}|{_MON}\s+{_DAY},?\s+{_YEAR})$", re.I),
    "YEAR": re.compile(rf"^(?:c\.\s*)?{_YEAR}$", re.I),
    "NUMBER": re.compile(r"^[~≈]?[-+]?(?:\d{1,3}(?:[,   ]\d{3})+|\d+)(?:\.\d+)?(?:\s*(?:%|percent|[a-zA-Z°µ²³/]+(?:\s[a-zA-Z]+)?))?$"),
    "NUMBER_EXACT": re.compile(r"^[-+]?(?:\d{1,3}(?:[,   ]\d{3})+|\d+)(?:\s*(?:%|percent|[a-zA-Z°µ²³/]+))?$"),
    "NAME": re.compile(r"^[^\W\d_][\w.'\-]*(?:\s+(?:[^\W\d_][\w.'\-]*|de|da|van|von|der|del|la|le|bin|al|y|of|the))*$"),
    "ANY": re.compile(r"^\S(?:.{0,198}\S)?$", re.S),
}
NAME_MAX_TOKENS = 8


_SCALE = re.compile(r"(thousand|million|billion|trillion|about|approximately|around|over|nearly|roughly)", re.I)


def type_ok(span, t):
    if not G[t].match(span):
        return False
    if t == "NUMBER_EXACT" and _SCALE.search(span):
        return False
    if t == "NAME":
        toks = span.split()
        return len(toks) <= NAME_MAX_TOKENS and toks[0][:1].isupper()
    return True


def years(s):
    """Four-digit years named in s, with season ranges expanded: '2018-19' / '2018–19' -> {2018, 2019}."""
    out = set()
    for m in re.finditer(r"(?<!\d)(1[0-9]{3}|20[0-9]{2})(?:\s*[-‐-―/]\s*(\d{2,4}))?(?!\d)", s):
        y = int(m.group(1))
        out.add(y)
        if m.group(2):
            e = m.group(2)
            e = int(str(y)[: 4 - len(e)] + e) if len(e) < 4 else int(e)
            if y < e <= y + 10:
                out.update(range(y + 1, e + 1))
    return out


def doc_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- V: verifier
def verify(question, y, corpus_get):
    """y = {"answer", "doc", "doc_sha256", "start", "end"}; corpus_get(title) -> text or "".
    Returns (accepted: bool, reason: str). Pure function of its inputs and the pinned corpus."""
    try:
        a, d, h, i, j = y["answer"], y["doc"], y["doc_sha256"], int(y["start"]), int(y["end"])
    except (KeyError, TypeError, ValueError):
        return False, "malformed"
    text = corpus_get(d)
    if not text:
        return False, "V1: document not in corpus"
    if doc_hash(text) != h:
        return False, "V1: document hash mismatch"
    if not (0 <= i < j <= len(text)):
        return False, "V2: span out of range"
    span = text[i:j]
    if not N(a) or N(span) != N(a):
        return False, "V2: answer is not the span"
    t = T(question)
    if not type_ok(span.strip(), t):
        return False, f"V3: span does not match type {t}"
    if not years(d) <= years(question):
        return False, "V4: document title names a year not in the question"
    return True, f"accepted ({t})"


# ---------------------------------------------------------------- heuristic span finder (outside the theorem)
def locate(answer, text):
    """Candidate spans [i, j) in text whose normalised form equals N(answer) (flexible whitespace, optional thousands
    separators, case-insensitive). Yields spans in document order."""
    na = N(answer)
    if not na:
        return
    parts = []
    for tok in na.split(" "):
        if re.fullmatch(r"\d+", tok) and len(tok) > 3:          # allow 1,234 / 1 234 in the source for 1234
            head = len(tok) % 3 or 3
            groups = [tok[:head]] + [tok[k:k + 3] for k in range(head, len(tok), 3)]
            parts.append(r"[,   ]?".join(groups))
        else:
            parts.append(re.escape(tok).replace("\\-", "[-‐-―−]").replace("'", "['‘’]"))
    pat = re.compile(r"(?<!\w)" + r"\s+".join(parts) + r"(?!\w)", re.I)
    for m in pat.finditer(text):
        yield m.start(), m.end()


def release(question, answer, titles, corpus_get):
    """Gate F: try the candidate answer against the evidence documents (titles, in order); release the first span that V
    accepts. Returns (answer or None, record)."""
    if not answer:
        return None, {"reason": "no answer"}
    last = "no span found in pinned documents"
    for d in titles:
        text = corpus_get(d)
        if not text:
            continue
        for i, j in locate(answer, text):
            y = {"answer": answer, "doc": d, "doc_sha256": doc_hash(text), "start": i, "end": j}
            ok, why = verify(question, y, corpus_get)
            if ok:
                return answer, {**y, "span": text[i:j], "reason": why}
            last = why
    return None, {"reason": last}
