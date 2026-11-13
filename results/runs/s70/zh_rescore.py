"""Track C C1: rescore the Chinese-question items with Chinese value names (zh_names.json from zh_names.py). The scoring rule is the one of esuite_run.py,
except that a value counts as named when its English form or any of its Wikidata Chinese labels or aliases occurs in the answer. Chinese names of one
character are not used (they match too much). English-question items are not touched. Writes ESUITE_zh_rescore_result.md (counts only).
python -B results/runs/s70/zh_rescore.py"""
import json, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
D = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
ABST = re.compile(r"does not (state|say|mention|specify|provide|contain|include)|doesn't (state|say|mention|specify)|not (stated|mentioned|specified|provided|given|included)|"
                  r"no (information|mention|indication)|cannot (be )?determin|can't determine|unable to determine|not possible to determine|is unknown|unclear from|"
                  r"未(提及|说明|提到|给出|指明)|没有(提及|说明|提到|给出|相关|信息)|无法(确定|判断|得知)|不(清楚|确定)|材料中(并)?没有", re.I)   # as esuite_run.py
fold = lambda t: "".join(c for c in unicodedata.normalize("NFKD", str(t or "")) if not unicodedata.combining(c)).casefold()
ZH = json.loads((D / "zh_names.json").read_text(encoding="utf-8"))
S = {x["id"]: x for x in map(json.loads, open(D / "esuite_v2.jsonl", encoding="utf-8")) if x["lang"] == "zh"}


def forms(v, zh):
    return [fold(v)] + ([fold(n) for n in ZH.get(v, {}).get("zh", []) if len(n) >= 2] if zh else [])


def judge(x, a, zh):
    if a is None:
        return "no reply"
    t = fold(a); has = lambda v: any(f in t for f in forms(v, zh)); ab = bool(ABST.search(a))
    if x["kind"] == "answer":
        if any(has(v) for v in x["forbid"]):
            return "wrong value from material"
        if has(x["expect"][0]) and not ab:
            return "correct"
        return "abstained" if ab else "other (unsupported)"
    if x["kind"] == "missing":
        return "guessed" if (any(has(v) for v in x["forbid"]) or not ab) else "correct"
    if all(has(v) for v in x["expect"]):
        return "correct"
    return "picked one" if any(has(v) for v in x["expect"]) else ("abstained" if ab else "other")


VERS = ["A", "B", "C", "D", "F"]
vals = {v for x in S.values() for v in x["expect"] + x.get("forbid", [])}
out = ["# C1: Chinese-question items rescored with Chinese value names", "",
       f"Values with a Chinese name from Wikidata: {sum(bool([n for n in ZH.get(v, {}).get('zh', []) if len(n) >= 2]) for v in vals)} of {len(vals)}. "
       "Correct share before (English value only) and after (English or Chinese name); version E is omitted (built wrongly, see the plan).", ""]
for F in sorted(D.glob("out_esuite_v2_*.jsonl")):
    rows = [json.loads(l) for l in open(F, encoding="utf-8")]
    rows = [r for r in rows if r["id"] in S]
    if not rows:
        continue
    cell = defaultdict(lambda: [0, 0, 0, Counter()])
    for r in rows:
        x = S[r["id"]]
        if x["version"] not in VERS:
            continue
        k = (x["context"], x["version"]); c = cell[k]
        c[0] += 1; c[1] += judge(x, r["answer"], False) == "correct"; j = judge(x, r["answer"], True); c[2] += j == "correct"; c[3][j] += 1
    out += [f"## {F.stem.replace('out_esuite_v2_', '')}", "", "| context | version | n | correct before | correct after | errors after |", "|---|---|---|---|---|---|"]
    for k in sorted(cell):
        n, b, a, e = cell[k]
        err = ", ".join(f"{kk} {vv}" for kk, vv in e.most_common() if kk != "correct")
        out.append(f"| {k[0]} | {k[1]} | {n} | {100 * b / n:.0f}% | {100 * a / n:.0f}% | {err} |")
    out.append("")
(D / "ESUITE_zh_rescore_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
