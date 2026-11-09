"""S8: code-only check of an ANSWER against the PASSAGE it was read from (no LLM, no gold).
Three tests; an answer is kept only if all apply and pass:
  A  span support   : every content token of the answer (words and numbers, after normalisation) occurs in the passage
                      inside one window of max(40, 3 x #tokens) passage tokens; and each number in the answer occurs in the
                      passage within 3 tokens of one of the answer's words (when the answer has words).
  T  date structure : if the answer contains a date, the passage must contain the same date with the parts next to each other
                      (day within 2 tokens of the month, year within 8 tokens of the month), in any order or format.
  Q  completeness   : if the question asks for day+month+year (or month+year) the answer must contain those parts.
Normalisation: lower case, accents stripped, digit-grouping commas removed, ordinals (2nd -> 2), number words 0-20 -> digits,
month names and abbreviations -> one token.
"""
import re
import unicodedata

MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"])}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9
NUMW = {w: str(i) for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
STOP = set("a an the of in on at to for and or by with from as is was were be been his her its their our it this that these those he she they "
           "about approximately around roughly some first last mr mrs ms dr st".split())
ORD = {"st", "nd", "rd", "th"}
FULL_DATE_Q = re.compile(r"\bday,? month,? and year\b|\bexact date\b|\b(date|day) (and|,) month,? and year\b|\bwhat (day|date),? month and year\b", re.I)
MONTH_YEAR_Q = re.compile(r"\bmonth and year\b|\bmonth,? and year\b", re.I)


def tokens(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)
    raw = re.findall(r"[a-z]+|\d+", s)
    out = []
    for i, t in enumerate(raw):
        if t in ORD and i > 0 and raw[i - 1].isdigit():
            continue
        if t in MONTHS and (t != "may" or _datey(raw, i)):
            out.append(f"@m{MONTHS[t]}")
        elif t in NUMW:
            out.append(NUMW[t])
        else:
            out.append(t)
    return out


def _datey(raw, i):
    """'may' is a month only next to a number."""
    return any(0 <= j < len(raw) and raw[j].isdigit() for j in (i - 2, i - 1, i + 1, i + 2))


def date_parts(toks):
    """Returns (day, month, year) found in a short token list (first month mention), None for missing parts; or None if no month/year date."""
    for i, t in enumerate(toks):
        if t.startswith("@m"):
            day = next((toks[j] for j in (i - 1, i + 1, i - 2, i + 2) if 0 <= j < len(toks) and toks[j].isdigit() and 1 <= int(toks[j]) <= 31 and len(toks[j]) <= 2), None)
            year = next((toks[j] for j in range(max(0, i - 3), min(len(toks), i + 4)) if toks[j].isdigit() and len(toks[j]) in (3, 4)), None)
            return day, t, year
    return None


def _window_ok(need, ptoks, minw=40):
    need = list(dict.fromkeys(need))
    if not need:
        return True
    pos = {}
    for k, t in enumerate(ptoks):
        if t in pos or t in need:
            pos.setdefault(t, []).append(k)
    if any(t not in pos for t in need):
        return False
    w = max(minw, 3 * len(need))
    anchor = min(need, key=lambda t: len(pos[t]))
    for a in pos[anchor]:
        if all(any(abs(p - a) <= w for p in pos[t]) for t in need):
            return True
    return False


def check(question, answer, passage):
    """Returns dict(ok, A, T, Q, reason)."""
    at = tokens(answer)
    pt = tokens(passage)
    content = [t for t in at if t not in STOP]
    A = _window_ok(content, pt)
    words = [t for t in content if not t.isdigit()]
    if A and words:                      # a number must sit next to (within 3 tokens of) one of the answer's words in the passage
        for t in content:
            if t.isdigit():
                if not any(pt[k] == t and any(pt[j] in words for j in range(max(0, k - 3), min(len(pt), k + 4))) for k in range(len(pt))):
                    A = False
                    break
    T = True
    dp = date_parts(at)
    if dp:
        day, mon, year = dp
        T = False
        for k, t in enumerate(pt):
            if t != mon:
                continue
            ok_day = day is None or any(0 <= j < len(pt) and pt[j] == day for j in range(k - 2, k + 3))
            ok_year = year is None or any(0 <= j < len(pt) and pt[j] == year for j in range(k - 8, k + 9))
            if ok_day and ok_year:
                T = True
                break
    Q = True
    if FULL_DATE_Q.search(question):
        Q = bool(dp and dp[0] and dp[2])
    elif MONTH_YEAR_Q.search(question):
        Q = bool(dp and dp[2])
    reason = ",".join(n for n, v in (("A", A), ("T", T), ("Q", Q)) if not v)
    return {"ok": A and T and Q, "A": A, "T": T, "Q": Q, "reason": reason}
