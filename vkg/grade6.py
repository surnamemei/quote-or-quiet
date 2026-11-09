"""Grader 6 = grader 5 (LLM judge, SimpleQA Verified prompt) with a code veto on completeness and date agreement.
An answer is correct only if the judge says CORRECT and no veto fires. The vetoes target the judge's validated failure
mode (crediting incomplete answers and wrong dates; results/grader5/GRADER5_RESULT.md). They were designed on V1/V2, so
grader 6 is validated on a new blind set (docs/GRADER6_PROTOCOL.md).
  R1 date agreement : gold and answer both contain a date -> every part present in both (day, month, year) must agree.
  R2 date completeness: question asks day+month+year (any order) -> answer has all three; asks month+year -> has both.
  R3 two-part place  : question asks "<city|town|...> and <country|state|...>" and the gold has a comma -> the answer contains the last part.
  R4 full name       : question asks for a "full name" -> every gold name token is in the answer (one-edit tolerance for tokens of 5+ letters).
  R5 qualifier       : the gold contains a kinship/rank qualifier (maternal, vice, deputy, ...) that is neither in the answer nor in the question.
"""
import re

from .grade_judge import judge
from .support_check import date_parts, tokens

QUAL = set("maternal paternal elder older younger eldest youngest step half great grand vice deputy assistant associate acting co".split())
PLACE2 = re.compile(r"\b(city|town|village|municipality|place|state|province|county|region)\s*(,|and|&)\s*(the\s+)?(country|state|province|county|region|nation)\b", re.I)


def _asks_full_date(q):
    w = set(re.findall(r"[a-z]+", q.lower()))
    return {"day", "month", "year"} <= w or bool(re.search(r"\bexact date\b|\bfull date\b", q, re.I))


def _asks_month_year(q):
    w = set(re.findall(r"[a-z]+", q.lower()))
    return {"month", "year"} <= w and "day" not in w


def _lev1(a, b):
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    if len(a) > len(b):
        a, b = b, a
    return any(b[:i] + b[i + 1:] == a for i in range(len(b)))


def _has(tok, toks):
    return any(t == tok or (len(tok) >= 5 and _lev1(tok, t)) for t in toks)


def veto(question, gold, answer):
    """Returns the name of the first rule that fires, or None."""
    gt, at, qt = tokens(gold), tokens(answer), set(tokens(question))
    gp, ap = date_parts(gt), date_parts(at)
    num = lambda x: str(int(x)) if x is not None and x.isdigit() else x   # amendment 6.1 (2026-11-06): "09" == "9"
    if gp and ap and any(g is not None and a is not None and num(g) != num(a) for g, a in zip(gp, ap)):
        return "R1"
    if _asks_full_date(question) and not (ap and ap[0] and ap[2]):
        return "R2"
    if _asks_month_year(question) and not (ap and ap[2]):
        return "R2"
    if PLACE2.search(question) and "," in gold:
        last = [t for t in tokens(gold.split(",")[-1]) if t not in ("the",)]
        if last and not all(_has(t, at) for t in last):
            return "R3"
    if re.search(r"\bfull name\b", question, re.I):
        g = re.sub(r"\([^)]*\)|\"[^\"]*\"|“[^”]*”", " ", gold)
        need = [t for t in tokens(g) if t.isalpha() and len(t) > 1 and t not in ("the", "of", "de", "von", "van", "da", "and")]
        if need and not all(_has(t, at) for t in need):
            return "R4"
    miss = [t for t in gt if t in QUAL and t not in at and t not in qt]
    if miss:
        return "R5"
    return None


def grade6(question, gold, answer):
    """Returns CORRECT / INCORRECT / NOT_ATTEMPTED."""
    g = judge(question, gold, str(answer))
    if g == "CORRECT" and veto(question, gold, str(answer)):
        return "INCORRECT"
    return g


def correct6(question, gold_list, answer):
    gold = gold_list[0] if isinstance(gold_list, (list, tuple)) else gold_list
    return grade6(question, gold, answer) == "CORRECT"
