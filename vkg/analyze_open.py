"""Regenerates every open-world (SimpleQA Verified) table from the raw jsonl files and writes results/open_world_tables.md.
Two gradings, always side by side:
  strict   = vkg.tasks.matches  (upper bound on wrong answers; misses punctuation/range/number-word variants)
  repaired = strict OR vkg.grade_open.repaired (best estimate; validated by eye on 25 new credits and 34 remaining wrong B1 rows, see docs/AUDIT.md)
"""
import json
import random
from pathlib import Path

from . import tasks
from .grade_open import repaired
from .tasks import matches

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "runs"
EXCLUDE = {"sqa-3343", "sqa-323"}      # two test questions whose pages were used while debugging the page cleaner (FREEZE 6d, AUDIT 3)
FILES = {"closed-book (n=500)": "openworld_simpleqa_qwen3.8-27b_s3000_n500",
         "search retrieval (n=300)": "openworld_simpleqa_rag_qwen3.8-27b_s3000_n300",
         "ORACLE gold source pages, upper bound, not deployable (n=251)": "openworld_simpleqa_oracle_qwen3.8-27b_s3000_n251",
         "S2 variant E hybrid retrieval (n=300)": "openworld_simpleqa_hybrid_qwen3.8-27b_s3000_n300"}


def load(name):
    return [json.loads(l) for l in open(RUNS / f"{name}.jsonl", encoding="utf-8")]


def att(r):
    return r["status"] == "answer" and r["answer"].strip() != ""


def cor_strict(r):
    return att(r) and matches(r["gold"], r["answer"])


def cor_rep(r):
    return att(r) and (matches(r["gold"], r["answer"]) or repaired(r["gold"][0], r["answer"]))


def boot(rows, a, b, f, ids, n=2000):
    A = {r["id"]: r for r in rows if r["system"] == a}
    B = {r["id"]: r for r in rows if r["system"] == b}
    d = [f(B[i]) - f(A[i]) for i in sorted(ids)]
    rng = random.Random(0)
    bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(n))
    return sum(d) / len(d), bs[int(.025 * n)], bs[int(.975 * n) - 1]


def table(rows, ids=None):
    out = ["| system | n | attempted | correct strict | correct repaired | wrong strict (hi) | wrong repaired | precision repaired |", "|---|---|---|---|---|---|---|---|"]
    for s in ("B0_raw", "B1_abstain", "B2_strict", "VKG_v2"):
        x = [r for r in rows if r["system"] == s and (ids is None or r["id"] in ids)]
        if not x:
            continue
        n = len(x)
        a = sum(map(att, x))
        cs, cr = sum(map(cor_strict, x)), sum(map(cor_rep, x))
        out.append(f"| {s} | {n} | {a/n:.3f} | {cs/n:.3f} | {cr/n:.3f} | {(a-cs)/n:.3f} | {(a-cr)/n:.3f} | {(cr/a if a else float('nan')):.3f} |")
    return "\n".join(out)


def main():
    L = ["# Open-world tables regenerated from raw jsonl (vkg/analyze_open.py)", "",
         "Wrong = attempted and not correct. B0_raw abstention is detected by regex, so refusals written as text ('None', 'not in the passage') count as attempts: B0 rows are reference only.", ""]
    data = {k: load(v) for k, v in FILES.items()}
    for k, rows in data.items():
        L += [f"## {k}", table(rows), ""]
    L += ["## Sensitivity: search retrieval without the two test questions used while debugging the page cleaner (sqa-3343, sqa-323)"]
    rag = data["search retrieval (n=300)"]
    keep = {r["id"] for r in rag} - EXCLUDE
    L += [table(rag, keep), ""]
    L += ["## Paired differences, search retrieval (n=300), repaired grader", ""]
    ids = {r["id"] for r in rag}
    for a, b in (("B1_abstain", "B2_strict"), ("B2_strict", "VKG_v2"), ("B1_abstain", "VKG_v2")):
        w = lambda r: att(r) and not cor_rep(r)
        c = lambda r: cor_rep(r)
        dw, dc = boot(rag, a, b, w, ids), boot(rag, a, b, c, ids)
        L.append(f"- {b} minus {a}: wrong {dw[0]:+.3f} [{dw[1]:+.3f}, {dw[2]:+.3f}]; correct {dc[0]:+.3f} [{dc[1]:+.3f}, {dc[2]:+.3f}]")
    # evidence coverage with the repaired matcher (no hedge guard when searching a passage)
    L += ["", "## Evidence coverage (gold present in passage) and B1 outcome split", ""]
    for mode, key in (("search", "search retrieval (n=300)"), ("oracle", "ORACLE gold source pages, upper bound, not deployable (n=251)")):
        items = tasks.simpleqa_rag(300, 3000, mode)
        cov = {it.id: (matches(it.gold, it.passage) or repaired(it.gold[0], it.passage, hedge_check=False)) for it in items}
        L.append(f"- {mode}: coverage {sum(cov.values())}/{len(cov)} = {sum(cov.values())/len(cov):.3f}")
        for s in ("B1_abstain", "VKG_v2"):
            x = [r for r in data[key] if r["system"] == s]
            for has in (True, False):
                sub = [r for r in x if cov.get(r["id"]) == has]
                L.append(f"    - {s}, evidence {'has' if has else 'lacks'} the answer (n={len(sub)}): correct {sum(map(cor_rep, sub))}, abstain {sum(not att(r) for r in sub)}, wrong {sum(att(r) and not cor_rep(r) for r in sub)}")
    hyb_key = "S2 variant E hybrid retrieval (n=300)"
    if hyb_key in data:
        hyb = data[hyb_key]
        L += ["", "## Variant E vs baseline search retrieval, same 300 questions, repaired grader (paired)", ""]
        for s_ in ("B1_abstain", "B2_strict", "VKG_v2"):
            A = {r["id"]: r for r in rag if r["system"] == s_}
            B = {r["id"]: r for r in hyb if r["system"] == s_}
            idsb = sorted(set(A) & set(B))
            for lab, f in (("correct", cor_rep), ("wrong", lambda r: att(r) and not cor_rep(r))):
                d = [f(B[i]) - f(A[i]) for i in idsb]
                rng = random.Random(0)
                bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(2000))
                L.append(f"- {s_}, E minus baseline: {lab} {sum(d)/len(d):+.3f} [{bs[50]:+.3f}, {bs[1949]:+.3f}]")
        items = tasks.simpleqa_rag(300, 3000, "hybrid")
        cov = {it.id: (matches(it.gold, it.passage) or repaired(it.gold[0], it.passage, hedge_check=False)) for it in items}
        L.append(f"- variant E evidence coverage: {sum(cov.values())}/{len(cov)} = {sum(cov.values())/len(cov):.3f}")
        for s_ in ("B1_abstain", "B2_strict", "VKG_v2"):
            x = [r for r in hyb if r["system"] == s_]
            for has in (True, False):
                sub = [r for r in x if cov.get(r["id"]) == has]
                L.append(f"    - {s_}, evidence {'has' if has else 'lacks'} the answer (n={len(sub)}): correct {sum(map(cor_rep, sub))}, abstain {sum(not att(r) for r in sub)}, wrong {sum(att(r) and not cor_rep(r) for r in sub)}")
        L += ["", "### Variant E: paired differences between systems (repaired)"]
        for a, b in (("B1_abstain", "B2_strict"), ("B2_strict", "VKG_v2")):
            w = lambda r: att(r) and not cor_rep(r)
            dw, dc = boot(hyb, a, b, w, ids), boot(hyb, a, b, cor_rep, ids)
            L.append(f"- {b} minus {a}: wrong {dw[0]:+.3f} [{dw[1]:+.3f}, {dw[2]:+.3f}]; correct {dc[0]:+.3f} [{dc[1]:+.3f}, {dc[2]:+.3f}]")
    (ROOT / "results" / "open_world_tables.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
