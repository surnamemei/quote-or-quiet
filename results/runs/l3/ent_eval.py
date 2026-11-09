"""Goal B step 1 evaluation on DEV (criteria fixed in docs/L3_QUALIFIED_DESIGN.md section 11, before the output was read).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/l3/ent_eval.py"""
import json, re, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3")); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from qualified_dev import releases
from qualified import decide, norm, core_of, senses, contains, TDB
from vkg import localwiki as LW
from vkg.s12_run import agree
from abstain_dev import grade

raw = {(r["set"], r["id"]): r for r in map(json.loads, open(ROOT / "results/runs/l3/ent_raw.jsonl", encoding="utf-8"))}

def parse(s):
    e = re.search(r'"entity"\s*:\s*"((?:[^"\\]|\\.)*)"', s); a = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', s)
    return (e.group(1).strip() if e else ""), (a.group(1).strip() if a else "")

def qual_of(t):
    m = re.search(r"\(([^)]*)\)\s*$", t); return m.group(1) if m else ""

def resolve(e):
    """titles the stated entity names: exact title, else senses of its core whose qualifier words occur in e."""
    if not e: return []
    ex = TDB.execute("SELECT title FROM t WHERE title = ?", (e,)).fetchall()
    if ex: return [ex[0][0]]
    core = core_of(re.sub(r"\s*\([^)]*\)\s*$", "", e)); q = qual_of(e)
    ss = senses(norm(core), core)
    if q:
        w = set(norm(q).split()); return [t for t, ql, _ in ss if ql and w & set(norm(ql).split())]
    return [t for t, ql, _ in ss if not ql] or ([ss[0][0]] if len(ss) == 1 else [])

def matches_intended(e, intended):
    if not e or not intended: return None
    if norm(e) == norm(intended): return True
    if norm(core_of(re.sub(r"\s*\([^)]*\)\s*$", "", e))) != norm(core_of(intended)): return False
    qi, qe = qual_of(intended), qual_of(e)
    return (not qi) or bool(qe and set(norm(qi).split()) & set(norm(qe).split()))

lines = ["# Goal B step 1 on DEV: stated entity vs rule-based layer", ""]
tot = Counter(); rec = []; q1 = Counter()
for name in ("popqa_dev", "mintaka_dev", "dev", "fresh"):
    for r, rel, doc, m in releases(name):
        st, sense, info = decide(r["question"], rel, doc, strict=True)
        g = grade(r["question"], r["gold"], rel)
        e, a = parse(raw[(name, r["id"])]["raw"]) if (name, r["id"]) in raw else ("", "")
        tot[(name, "n")] += 1; tot[(name, "no_entity")] += (not e)
        tot[(name, "ans_agrees")] += bool(a) and a.lower() != "unknown" and bool(agree(str(rel), a))
        intended = m.get("s_wiki_title")
        if intended:
            q1["items"] += 1
            q1["4B_entity_matches"] += bool(matches_intended(e, intended))
            if st == "Qualified": q1["rule_qualified"] += 1; q1["rule_sense_matches"] += bool(norm(sense) == norm(intended))
            q1["rule_verified_doc_matches"] += (st == "Verified" and norm(core_of(doc)) == norm(core_of(intended)))
        if st == "Unresolved":
            ts = resolve(e); hold = [t for t in ts if contains(LW.page_text(t), rel)]
            rec.append((name, r["question"], rel, g, e, ts[:3], hold[:2]))
lines += ["| set | releases | no entity parsed | 4B answer agrees with release |", "|---|---|---|---|"]
for name in ("popqa_dev", "mintaka_dev", "dev", "fresh"):
    lines.append(f"| {name} | {tot[(name,'n')]} | {tot[(name,'no_entity')]} | {tot[(name,'ans_agrees')]} |")
lines += ["", "## Q1 PopQA DEV, intended subject known", "", f"- releases with intended sense: {q1['items']}",
          f"- 4B stated entity matches intended: {q1['4B_entity_matches']}",
          f"- rule-based: Qualified {q1['rule_qualified']}, of which sense = intended {q1['rule_sense_matches']}; Verified with release page core = intended core {q1['rule_verified_doc_matches']}",
          "", "## Q3 Unresolved releases on DEV (entity resolves to a sense page holding the answer?)", "",
          "| set | question | release | graded | stated entity | resolved titles | holding the answer |", "|---|---|---|---|---|---|---|"]
for n, q, rel, g, e, ts, hold in rec:
    lines.append(f"| {n} | {q[:60]} | {rel[:25]} | {g} | {e[:35]} | {'; '.join(ts)[:60]} | {'; '.join(hold)} |")
Path(ROOT / "results/runs/l3/ent_eval.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
