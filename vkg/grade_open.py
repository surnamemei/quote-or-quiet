"""Two fixed graders for open-world short answers (no LLM judge).
strict  : normalized gold string appears in the answer (tasks.matches).
lenient : every gold token with >=3 chars or any digit appears as a token in the answer (order ignored).
Error bounds: wrong_hi = answered and not strict-correct; wrong_lo = answered and not lenient-correct.
Usage: python -m vkg.grade_open results/runs/<file>.jsonl
"""
import json
import random
import sys
from collections import defaultdict

from .tasks import matches, norm


def lenient(gold, answer):
    a = set(norm(answer).split())
    toks = [t for t in norm(gold).split() if len(t) >= 3 or any(c.isdigit() for c in t)]
    return bool(toks) and all(t in a for t in toks)


_NUMW = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
         "eighteen": 18, "nineteen": 19, "twenty": 20}


def _nums(s):
    s = norm(s)
    out = [float(x) for x in __import__("re").findall(r"(?<![\w.])\d+(?:\.\d+)?", s)]
    out += [float(_NUMW[w]) for w in s.split() if w in _NUMW]
    return out


def lenient2(gold, answer):
    """Third grader (added after the first results, reported as an extra column, never replacing the first two):
    (a) gold with 'acceptable range: anything between A and B' -> any number in the answer inside [A, B];
    (b) numeric gold -> its numbers all appear among the answer's numbers (digits or number words 0-20)."""
    import re
    m = re.search(r"between\s+([\d.,]+)\s*(?:%|[a-z]*)?\s*and\s+([\d.,]+)", str(gold), re.I)
    an = _nums(answer)
    if m:
        try:
            lo, hi = sorted(float(x.replace(",", "").rstrip(".")) for x in m.groups())
            return any(lo <= x <= hi for x in an)
        except ValueError:
            pass
    gtxt = re.sub(r"\(.*?\)", "", str(gold))
    months = [mo.lower() for mo in ("January February March April May June July August September October November December".split())
              if mo.lower() in norm(gtxt).split()]
    if months and not all(mo in norm(answer).split() for mo in months):     # a date with the wrong month is not a match
        return False
    gn = _nums(gtxt)
    return bool(gn) and all(any(abs(g - a) < 1e-9 for a in an) for g in gn) and len(gn) <= 3


def grade(r):
    gold = r["gold"][0] if r["gold"] else ""
    answered = r["status"] == "answer" and r["answer"].strip() != ""
    if not answered:
        return "abstain"
    if matches(r["gold"], r["answer"]):
        return "correct_strict"
    if lenient(gold, r["answer"]):
        return "correct_lenient"
    return "wrong"


# ---- repaired grader (added after an independent audit found the first graders miss correct answers; docs/AUDIT.md section 5.1)
import re as _re
import unicodedata

_UNITS = {"km", "m", "mi", "mile", "miles", "meter", "meters", "metre", "metres", "feet", "foot", "ft", "year", "years", "day", "days",
          "month", "months", "minute", "minutes", "min", "hour", "hours", "second", "seconds", "percent", "kg", "tonnes", "tons",
          "cm", "mm", "acres", "hectares", "ha", "people", "students", "times", "episodes", "members", "seats", "votes", "points",
          "district", "livres", "hp"}
_HEDGE = ("more than", "less than", "at least", "at most", "fewer than", " over ", " under ", " about ", " around ", "approximately",
          "roughly", "nearly", "almost")
_ART = {"the", "a", "an", "of"}
_MON = {"jan": "january", "feb": "february", "mar": "march", "apr": "april", "jun": "june", "jul": "july", "aug": "august",
        "sep": "september", "sept": "september", "oct": "october", "nov": "november", "dec": "december"}
_NUM = _re.compile(r"\d+(?:\.\d+)?")


def _rn(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace("–", " ").replace("—", " ").replace("-", " ")
    s = _re.sub(r"(?<=\d),(?=\d{3})", "", s)                 # 1,435 -> 1435
    s = _re.sub(r"(?<=\d)(st|nd|rd|th)(?![a-z])", "", s)     # 18th -> 18
    s = _re.sub(r"[^\w\s.]", " ", s)
    s = _re.sub(r"(?<!\d)\.|\.(?!\d)", " ", s)               # keep decimal points only
    toks = [str(_NUMW[t]) if t in _NUMW else _MON.get(t, t) for t in s.split()]
    return [t for t in toks if t not in _ART]


def repaired(gold, answer, hedge_check=True):
    """Token-set containment after: accent/punctuation/hyphen normalisation, ordinal and thousands-separator removal, number words,
    article/'of' removal, month abbreviations, the parenthetical dropped from the gold, 'acceptable range' parsed, unit words ignored
    for numeric golds. Hedged numbers ('more than 137') and wrong months are not credited. Single letters count ('F major' != 'G major').
    Known false negatives: omitted middle names, shorter official names ('Colombia' for 'The Republic of Colombia')."""
    gold, answer = str(gold), str(answer)
    a = _rn(answer)
    if not a:
        return False
    hedged = hedge_check and any(h in " " + norm(answer) + " " for h in _HEDGE)
    m = _re.search(r"between\s+([\d.,]+)\s*(?:%|[a-z]*)?\s*and\s+([\d.,]+)", gold, _re.I)
    if m:
        try:
            lo, hi = sorted(float(x.replace(",", "").rstrip(".")) for x in m.groups())
            return (not hedged) and any(lo <= float(t) <= hi for t in a if _NUM.fullmatch(t))
        except ValueError:
            pass
    g = _rn(_re.sub(r"\(.*?\)", "", gold))
    if not g:
        return False
    nums = [t for t in g if _NUM.fullmatch(t)]
    rest = [t for t in g if t not in nums]
    if nums and all(t in _UNITS for t in rest):               # numeric gold with units: compare the numbers only
        return (not hedged) and all(t in a for t in nums)
    return all(t in a for t in g)


def grade_v3(r):
    """abstain / correct / wrong, with correct = strict match OR repaired match."""
    gold = r["gold"][0] if r["gold"] else ""
    if not (r["status"] == "answer" and r["answer"].strip()):
        return "abstain"
    return "correct" if (matches(r["gold"], r["answer"]) or repaired(gold, r["answer"])) else "wrong"


def ci(vals, fn, n=2000, seed=0):
    rng = random.Random(seed)
    out = sorted(fn([rng.choice(vals) for _ in vals]) for _ in range(n))
    return out[int(.025 * n)], out[int(.975 * n)]


def main(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    by = defaultdict(list)
    for r in rows:
        r["g"] = grade(r)
        by[r["system"]].append(r)
    print("| system | n | attempted | correct strict | correct lenient | wrong (hi bound) | wrong (lo bound) | precision strict | precision lenient |")
    print("|---|---|---|---|---|---|---|---|---|")
    for s, x in by.items():
        n = len(x)
        att = sum(r["g"] != "abstain" for r in x)
        cs = sum(r["g"] == "correct_strict" for r in x)
        cl = cs + sum(r["g"] == "correct_lenient" for r in x)
        print(f"| {s} | {n} | {att/n:.3f} | {cs/n:.3f} | {cl/n:.3f} | {(att-cs)/n:.3f} | {(att-cl)/n:.3f} | "
              f"{(cs/att if att else float('nan')):.3f} | {(cl/att if att else float('nan')):.3f} |")
    base = {r["id"]: r for r in by.get("B0_raw", [])}
    for s, x in by.items():
        if s == "B0_raw" or not base:
            continue
        ids = sorted(base)
        cur = {r["id"]: r for r in x}
        d_hi = [((cur[i]["g"] not in ("abstain", "correct_strict")) - (base[i]["g"] not in ("abstain", "correct_strict"))) for i in ids]
        lo, hi = ci(d_hi, lambda v: sum(v) / len(v))
        print(f"{s} - B0_raw wrong_hi: {sum(d_hi)/len(d_hi):+.3f} CI [{lo:+.3f}, {hi:+.3f}]")
    if "B1_abstain" in by and "VKG_v2" in by:
        b1 = {r["id"]: r for r in by["B1_abstain"]}
        v = {r["id"]: r for r in by["VKG_v2"]}
        ids = sorted(b1)
        d = [((v[i]["g"] not in ("abstain", "correct_strict")) - (b1[i]["g"] not in ("abstain", "correct_strict"))) for i in ids]
        c = [((v[i]["g"] == "correct_strict") - (b1[i]["g"] == "correct_strict")) for i in ids]
        print(f"VKG_v2 - B1 wrong_hi: {sum(d)/len(d):+.3f} CI {tuple(round(x,3) for x in ci(d, lambda t: sum(t)/len(t)))}; "
              f"correct_strict: {sum(c)/len(c):+.3f} CI {tuple(round(x,3) for x in ci(c, lambda t: sum(t)/len(t)))}")


if __name__ == "__main__":
    main(sys.argv[1])
