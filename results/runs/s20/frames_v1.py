"""S20 draft D3 v1 (docs/S20_PLAN.md section 6). Changes over v0 (frames.py), designed from DEV blocked-correct cases only:
- extra sentence synonyms per relation;
- lifespan parentheses "(date – date)": born = first part, died = second part;
- table-aware reading: the relation may be named in the span's column header or the table's heading;
- one-sentence look-back when the span's sentence continues the previous subject (starts with a pronoun);
- ordinals are required only when they sit in the question's wh-phrase (first six words: "Who was the first president ...");
- role check: the span must not be the tail of a larger name ("Philip of <span>") or one side of a score ("2–2")."""
import re

from frames import CQ, REL, YEAR, question_relation, sentence_of  # noqa: F401  (question parser unchanged)

EXTRA = {
    "died": r"\bdying\b|\bdeath\b|\bkilled\b",
    "award": r"\bwinners?\b|\brecipients?\b|\bhonou?rees?\b|\blaureates?\b",
    "height": r"\belevation\b|\belev\.",
    "joined": r"\bbecame\b",
    "educated": r"\bwent to\b|\battended\b|\breceived (his|her|a) (B|M|Ph|doctor|degree)",
    "released": r"\brelease date\b",
    "opened": r"\bopened\b|\binaugurat\w*",
    "elected": r"\belected\b|\bre-elected\b|\bmember of\b",
}
CS = {k: re.compile(v[1] + ("|" + EXTRA[k] if k in EXTRA else ""), re.I) for k, v in REL.items()}
ORD = re.compile(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last|final|\d+(?:st|nd|rd|th)|inaugural)\b", re.I)
PRON = re.compile(r"^\s*(he|she|it|they|his|her|its|their|the (company|band|album|film|team|party|club|building|museum))\b", re.I)
LIFESPAN = re.compile(r"\(([^()]{4,60}?)\s[–-]\s([^()]{4,60}?)\)")


def _confirms_in(s, mid, r):
    def dist(rel):
        d = [min(abs(m.start() - mid), abs(m.end() - mid)) for m in CS[rel].finditer(s)]
        return min(d) if d else None
    dr = dist(r)
    if dr is None:
        return False
    return all(dist(c) is None or dist(c) >= dr for c in REL[r][2])


def _table_header(text, i):
    """If position i is inside a markdown table row, return (header cell of i's column, table heading text); else None."""
    ls = text.rfind("\n", 0, i) + 1
    le = text.find("\n", i)
    le = len(text) if le < 0 else le
    row = text[ls:le]
    if row.count("|") < 2:
        return None
    col = row[:i - ls].count("|") - 1
    k = ls
    header = None
    while k > 0:
        ps = text.rfind("\n", 0, k - 1) + 1
        line = text[ps:k - 1]
        if line.count("|") < 2:
            break
        if not re.fullmatch(r"[\s|:\-]+", line):
            header = line
        k = ps
    cells = [c.strip() for c in (header or "").strip().strip("|").split("|")]
    hs = text.rfind("\n#", 0, k)
    heading = text[hs:text.find("\n", hs + 1)] if hs >= 0 else ""
    return (cells[col] if 0 <= col < len(cells) else ""), heading


def sentence_confirms(r, text, i, j):
    a, b = sentence_of(text, i, j)
    s = text[a:b]
    mid = (i + j) / 2 - a
    if r in ("born", "died"):
        for m in LIFESPAN.finditer(s):
            if m.start(1) <= mid - 0 <= m.end(1) and r == "born":
                return True
            if m.start(2) <= mid <= m.end(2) and r == "died":
                return True
    if _confirms_in(s, mid, r):
        return True
    t = _table_header(text, i)
    if t and (CS[r].search(t[0]) or CS[r].search(t[1])):
        return True
    if PRON.match(s):                                   # subject continues from the previous sentence
        pa, _ = sentence_of(text, max(0, a - 2), max(0, a - 2))
        prev = text[pa:a]
        if CS[r].search(prev) and not any(CS[c].search(s) for c in REL[r][2]):
            return True
    return False


def qualifiers_ok(q, answer, text, i, j, window=400):
    a, b = sentence_of(text, i, j)
    sent = text[a:b].lower()
    head = " ".join(q.split()[:6])
    for m in ORD.finditer(head):                         # only ordinals in the wh-phrase are required qualifiers
        w = m.group(0).lower()
        if w not in sent and not (w == "first" and re.search(r"\b(1st|inaugural|founding)\b", sent)):
            t = _table_header(text, i)
            if not (t and w in (t[1] + t[0]).lower()):
                return False
    ls = text.rfind("\n", 0, i) + 1
    near = text[max(0, i - window):j + window]
    for y in set(YEAR.findall(q)):
        if y not in str(answer) and y not in near and y not in text[ls:text.find("\n", j) if text.find("\n", j) > 0 else len(text)]:
            return False
    return True


def role_ok(q, text, i, j):
    """Role check: the span fills its own slot, not part of another name or one side of a score."""
    before, after = text[max(0, i - 40):i], text[j:j + 12]
    if re.search(r"\b[A-Z][\w'’.-]+ (of|de|von|van) $", before) and text[i:i + 1].isupper():
        return False
    if re.fullmatch(r"\d{1,3}", text[i:j].strip()) and (re.search(r"\d\s*[–-]\s*$", before) or re.match(r"\s*[–-]\s*\d", after)):
        if not re.search(r"\bscore\b|\bresult\b", q, re.I):
            return False
    return True
