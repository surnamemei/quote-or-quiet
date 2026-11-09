"""S22 design (DEV only): counterfactual release rules on top of the frozen S19 H1 system.
  base  : S19 H1 (support>=3 -> release2 -> Phi-4 agree)
  +fmt  : if the gate finds no span, retry with (i) date surface variants (Month D, YYYY <-> D Month YYYY) and (ii) the longest
          n-gram of a sentence answer (>4 tokens) that the gate accepts, with question words stripped from its ends; the released
          string must still agree with Phi-4.
  +ms2  : also admit support-2 candidates (same gate and veto).
Grading of new strings: no judge labels yet, so 'str' = normalised containment match against any gold alias; for unchanged
strings the cached alias-aware label is used."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S      # noqa: E402
from vkg.s12_run import agree, tokens                                # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402
sys.path.insert(0, str(ROOT / "results/runs/s22"))
from abstain_dev import grade                                        # noqa: E402

MON = "January February March April May June July August September October November December".split()
def date_variants(a):
    out = []
    m = re.fullmatch(r"\s*(%s)\s+(\d{1,2}),?\s+(\d{3,4})\s*" % "|".join(MON), a, re.I)
    if m: out.append(f"{int(m.group(2))} {m.group(1)} {m.group(3)}")
    m = re.fullmatch(r"\s*(\d{1,2})\s+(%s),?\s+(\d{3,4})\s*" % "|".join(MON), a, re.I)
    if m: out.append(f"{m.group(2)} {int(m.group(1))}, {m.group(3)}")
    return out

def spans(q, a):
    t = re.findall(r"[^\s]+", a.strip().rstrip("."))
    if len(t) <= 4: return []
    qt = set(tokens(q))
    out = []
    for n in range(min(8, len(t)), 0, -1):
        for i in range(len(t) - n + 1):
            g = [w.strip(",.;:()") for w in t[i:i + n]]
            if not g[0] or not g[-1] or tokens(g[0])[:1] and set(tokens(g[0])) <= qt or set(tokens(g[-1])) <= qt: continue
            if g[0].casefold() in ("the", "a", "an", "is", "was", "in", "by", "of") or g[-1].casefold() in ("the", "a", "an", "of", "and"): continue
            out.append(" ".join(g))
    return out

def strmatch(gold, a):
    ta = " " + " ".join(tokens(a)) + " "
    return any(len(tokens(g)) and (" " + " ".join(tokens(g)) + " ") in ta for g in gold[:9])

def run(name):
    rows = [json.loads(l) for l in open(ROOT / "results/runs/s19" / f"{name}_outputs.jsonl", encoding="utf-8")]
    phi = {r["id"]: r["answer"] for r in map(json.loads, open(ROOT / "results/shared_eval/readers" / f"s21{name}_combo_cautious_phi4.jsonl", encoding="utf-8"))}
    res = {k: [] for k in ("base", "+fmt", "+fmt+ms2")}
    new = []
    for r in rows:
        q, gold = r["question"], r["gold"]
        a, s = S.cand(r); a = a if ans(a) else None
        p = phi[r["id"]]
        def rel_of(min_s, fmt):
            if not a or s < min_s: return None, None
            rel, _ = C.release2(q, a, r["wiki_titles"], LW.page_text)
            how = "orig"
            if not rel and fmt:
                for alt in date_variants(a) + spans(q, a):
                    rel, _ = C.release2(q, alt, r["wiki_titles"], LW.page_text)
                    if rel: how = "alt"; break
            if rel and not (ans(p) and agree(str(rel), str(p))): return None, None
            return rel, how
        for key, ms, fmt in (("base", 3, False), ("+fmt", 3, True), ("+fmt+ms2", 2, True)):
            rel, how = rel_of(ms, fmt)
            if not rel: continue
            g = grade(q, gold, rel) if how == "orig" else strmatch(gold, rel)
            res[key].append(g)
            if how == "alt" and key == "+fmt": new.append((q, a, rel, gold[:2], g))
    n = len(rows)
    print(f"## {name} (n={n})")
    for k, v in res.items():
        print(f"{k:10s} released {len(v):4d} cov {len(v)/n:.3f}  wrong {sum(x is False for x in v)}  unlabelled {sum(x == '?' for x in v)}")
    for x in new: print("  new:", x)

for nm in sys.argv[1:] or ["mintaka_dev", "popqa_dev"]:
    run(nm)
