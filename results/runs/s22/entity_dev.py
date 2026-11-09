"""S22 design (DEV only): subject-ambiguity rule on top of the pin variant.
E-subj: among the pinned/retrieved titles and the release page, take the longest title core that occurs in the question (the
question's subject as the wiki names it). The question is entity-ambiguous if the local wiki has more than one page with that
core ("X", "X (film)", "X (novel)" ...) and the question does not name the release page's qualifier. Ambiguous -> no Verified
answer (Qualified / Unresolved). Falls back to the release page's own core when no title core occurs in the question.
Uses the sqlite title index only (no page loading beyond the gate)."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s21"))
from ent_eval import norm, split, n_same_core                        # noqa: E402
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW      # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402
from abstain_dev import grade                                        # noqa: E402
from temporal import time_sensitive                                  # noqa: E402


def ambiguous(q, titles, doc):
    nq = norm(q)
    cores = sorted({split(t)[0] for t in list(titles) + [doc]}, key=len, reverse=True)
    subj = next((c for c in cores if len(c) >= 3 and norm(c) in nq), None) or split(doc)[0]
    qual = split(doc)[1]
    named = bool(qual) and all(norm(w) in nq for w in re.findall(r"\w+", qual) if len(w) > 2)
    return n_same_core(subj) > 1 and not named, subj


def run(var, n):
    base = ROOT / ("results/runs/s19" if var == "s19" else f"results/runs/s22/{var}")
    rows = [json.loads(l) for l in open(base / f"{n}_outputs.jsonl", encoding="utf-8")]
    pp = (ROOT / f"results/shared_eval/readers/s21{n}_combo_cautious_phi4.jsonl") if var == "s19" else base / f"{n}_phi4.jsonl"
    phi = {r["id"]: r["answer"] for r in map(json.loads, open(pp, encoding="utf-8"))}
    X = []
    for r in rows:
        a, s = S.cand(r); a = a if ans(a) else None
        rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
        p = phi.get(r["id"])
        if rel and not (ans(p) and agree(str(rel), str(p))): rel = None
        if not rel: continue
        amb, subj = ambiguous(r["question"], r["wiki_titles"], rec["doc"])
        X.append({"q": r["question"], "rel": rel, "g": grade(r["question"], r["gold"], rel), "amb": amb, "subj": subj,
                  "ts": time_sensitive(r["question"]), "doc": rec["doc"], "gold": r["gold"][:2]})
    return len(rows), X


if __name__ == "__main__":
    lines = ["| set | variant | rule | released | coverage | wrong (gold-relative) |", "|---|---|---|---|---|---|"]
    dump = {}
    for n in ("mintaka_dev", "popqa_dev"):
        for var in ("s19", "pin"):
            N, X = run(var, n)
            dump[f"{n}/{var}"] = X
            for lab, f in (("none", lambda x: True), ("time", lambda x: not x["ts"]), ("subj", lambda x: not x["amb"]),
                           ("time + subj", lambda x: not x["ts"] and not x["amb"])):
                v = [x for x in X if f(x)]
                lines.append(f"| {n} | {var} | {lab} | {len(v)} | {len(v)/N:.3f} | {sum(x['g'] is False for x in v)} |")
    (ROOT / "results/runs/s22/entity_dev.md").write_text("\n".join(lines), encoding="utf-8")
    json.dump(dump, open(ROOT / "results/runs/s22/entity_dev.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("\n".join(lines))
