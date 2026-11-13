"""Track C C1: finer scoring of versions B (value changed) and C (fact removed), English, short context, stored answers (no model).
B: material only = the material's value and not the original; material + note = both values (the answer follows the material and mentions the original value);
   original only = the original value without the material's (answered from memory); abstained; other.
C: abstained only = says the material does not state it and names no candidate; abstained + names = says so and also gives the original value;
   original, no abstention = gives the original value as the answer; other, no abstention.
python -B results/runs/s70/rescore_bc.py"""
import json, re, sys, unicodedata
from collections import Counter
from pathlib import Path
D = Path(__file__).resolve().parent; sys.stdout.reconfigure(encoding="utf-8")
fold = lambda t: "".join(c for c in unicodedata.normalize("NFKD", str(t or "")) if not unicodedata.combining(c)).casefold()
ABST = re.compile(r"does not (state|say|mention|specify|provide|contain|include|identify|name|explicitly)|doesn't (state|say|mention|specify)|not (stated|mentioned|specified|provided|given|included|explicitly)|no (information|mention|indication)|cannot (be )?determin|can't determine|unable to determine|not possible to determine|is unknown|unclear from", re.I)
S = {x["id"]: x for x in map(json.loads, open(D / "esuite_v2.jsonl", encoding="utf-8")) if x["lang"] == "en" and x["context"] == "short" and x["version"] in "BC"}
out = ["# C1 versions B and C rescored (English, short context)", ""]
for F in sorted(D.glob("out_esuite_v2_*.jsonl")):
    cb, cc = Counter(), Counter()
    for r in map(json.loads, open(F, encoding="utf-8")):
        x = S.get(r["id"]); a = r["answer"]
        if not x or a is None: continue
        t = fold(a); has = lambda v: fold(v) in t; ab = bool(ABST.search(a)); orig = any(has(v) for v in x["forbid"])
        if x["version"] == "B":
            mat = has(x["expect"][0])
            cb["material + note" if mat and orig else "material only" if mat else "original only" if orig else "abstained" if ab else "other"] += 1
        else:
            cc["abstained + names" if ab and orig else "abstained only" if ab else "original, no abstention" if orig else "other, no abstention"] += 1
    out += [f"## {F.stem.replace('out_esuite_v2_', '')}", "B: " + ", ".join(f"{k} {v}" for k, v in cb.most_common()), "C: " + ", ".join(f"{k} {v}" for k, v in cc.most_common()), ""]
(D / "ESUITE_rescore_bc_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
