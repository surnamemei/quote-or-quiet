"""Grader v4 = the repaired grader plus rules 1, 2 and 3(a) of docs/GRADER_VALIDATION.md section 6 (prototype
results/audit/validation/v3_extra.py `proposed`, ported unchanged without the optional fuzzy rule P4).
The rules were designed on the 240 hand-labelled rows of the earlier SimpleQA runs; on any later set they are out of sample.
Used ONLY as a labelled sensitivity grader; the frozen graders in grade_open.py are unchanged.
"""
import re

from .grade_open import _rn, repaired
from .tasks import matches

_SCALE = {"thousand": 1e3, "million": 1e6, "billion": 1e9}
_OFFICIAL = {"republic", "kingdom", "commonwealth", "federation", "state", "democratic", "islamic", "peoples", "people", "s"}


def clean_gold(g):
    g = re.sub(r"https?://\S*", "", g)
    g = re.sub(r"\[\d+\]", "", g)
    return g.strip()


def scale_numbers(a):
    return re.sub(r"(\d+(?:[.,]\d+)?)\s*(thousand|million|billion)\b",
                  lambda m: str(int(float(m.group(1).replace(",", "")) * _SCALE[m.group(2).lower()])), a, flags=re.I)


def alt_golds(q, g):
    alts = []
    m = re.search(r"\(.*?[\"“']([^\"”']+)[\"”'].*?\)", g)
    if m:
        alts.append(m.group(1))
    if ":" in g:
        sub = g.split(":", 1)[1].strip()
        if len(sub.split()) >= 3 and re.search(r"\b(title|titled|publication|book|album|called|name of)\b", q, re.I):
            alts.append(sub)
    if "," in g and not re.search(r"\b(city|town|state|province|country|district|region|county)\s+and\b|\band\s+(country|state|province)\b", q, re.I) \
            and re.search(r"(?i)\b(county|parish|province|state|district|region|oblast|prefecture)\s*$", g.split(",", 1)[1].strip()):
        alts.append(g.split(",")[0])
    toks = _rn(re.sub(r"\(.*?\)", "", g))
    core = [t for t in toks if t not in _OFFICIAL]
    if core and len(core) < len(toks):
        alts.append(" ".join(core))
    if not re.search(r"\d", g) and re.search(r"(?i)\bwhom?\b|\b(scientist|person|woman|man|player|singer|author|actor|artist|politician|coach|chemist|botanist|engineer|mathematician|disc jockey)\b", q):
        t = re.sub(r"\(.*?\)", "", g).split()
        t = [x for x in t if x.strip(".").lower() not in ("jr", "sr", "ii", "iii")]
        if len(t) >= 3:
            alts.append(t[0] + " " + t[-1])
    return alts


def correct_v4(question, gold_list, answer):
    a = str(answer)
    if not a.strip():
        return False
    if matches(gold_list, a) or repaired(gold_list[0], a):
        return True
    g1 = clean_gold(gold_list[0])
    a1 = scale_numbers(a)
    return any(c and (repaired(c, a) or repaired(c, a1)) for c in [g1] + alt_golds(question, g1))
