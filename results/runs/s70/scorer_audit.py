"""Track C C1: audit of the mechanical scorer on the stored answers (no model). Counts, per run and version (English, short):
  both   : answer items scored 'wrong value from material' whose answer also contains the expected value (e.g. 'X, not Y')
  long   : answers scored 'correct' that are longer than 25 words (room for unsupported additions; not checked by the scorer)
  denial : conflict items scored 'correct' whose answer denies a conflict or picks one ('no conflict', 'is correct', 'ignore', 'incorrect', 'outdated')
python -B results/runs/s70/scorer_audit.py"""
import json, re, sys, unicodedata
from collections import defaultdict
from pathlib import Path
D = Path(__file__).resolve().parent; sys.stdout.reconfigure(encoding="utf-8")
fold = lambda t: "".join(c for c in unicodedata.normalize("NFKD", str(t or "")) if not unicodedata.combining(c)).casefold()
ABST = re.compile(r"does not (state|say|mention|specify|provide|contain|include)|doesn't (state|say|mention|specify)|not (stated|mentioned|specified|provided|given|included)|no (information|mention|indication)|cannot (be )?determin|can't determine|unable to determine|not possible to determine|is unknown|unclear from", re.I)
DEN = re.compile(r"no conflict|not conflict|is correct|is incorrect|ignore|outdated|more reliable|more likely", re.I)
S = {x["id"]: x for x in map(json.loads, open(D / "esuite_v2.jsonl", encoding="utf-8")) if x["lang"] == "en" and x["context"] == "short" and x["version"] in "ABCDF"}
out = ["# C1 scorer audit (English, short context; stored answers)", "", "| run | version | n | scored own/forbidden value | of these also contain the expected value | scored correct | correct and over 25 words | conflict correct with a denial phrase |", "|---|---|---|---|---|---|---|---|"]
for F in sorted(D.glob("out_esuite_v2_*.jsonl")):
    c = defaultdict(lambda: [0] * 6)
    for r in map(json.loads, open(F, encoding="utf-8")):
        x = S.get(r["id"]); a = r["answer"]
        if not x or a is None: continue
        t = fold(a); has = lambda v: fold(v) in t; ab = bool(ABST.search(a)); k = c[x["version"]]; k[0] += 1
        if x["kind"] == "answer":
            fb = any(has(v) for v in x["forbid"]); ok = (not fb) and has(x["expect"][0]) and not ab
            k[1] += fb; k[2] += fb and has(x["expect"][0])
        elif x["kind"] == "missing":
            ok = not (any(has(v) for v in x["forbid"]) or not ab)
        else:
            ok = all(has(v) for v in x["expect"]); k[5] += ok and bool(DEN.search(a))
        k[3] += ok; k[4] += ok and len(a.split()) > 25
    for v in sorted(c):
        k = c[v]; out.append(f"| {F.stem.replace('out_esuite_v2_', '')} | {v} | {k[0]} | {k[1]} | {k[2]} | {k[3]} | {k[4]} | {k[5]} |")
(D / "ESUITE_scorer_audit_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
