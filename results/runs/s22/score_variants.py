"""Score S22 DEV variants with the frozen S19 H1 decision logic (MS3 -> release2 -> Phi-4 agree), cached labels only.
Rows: S19 baseline (results/runs/s19 + s21 Phi-4 files), variant tok, variant pin; each with and without the time rule.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s22/score_variants.py"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S      # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402
from abstain_dev import grade                                        # noqa: E402
from temporal import time_sensitive                                  # noqa: E402

SRC = {"s19": (ROOT / "results/runs/s19/{n}_outputs.jsonl", ROOT / "results/shared_eval/readers/s21{n}_combo_cautious_phi4.jsonl"),
       "tok": (ROOT / "results/runs/s22/tok/{n}_outputs.jsonl", ROOT / "results/runs/s22/tok/{n}_phi4.jsonl"),
       "pin": (ROOT / "results/runs/s22/pin/{n}_outputs.jsonl", ROOT / "results/runs/s22/pin/{n}_phi4.jsonl")}


def score(var, n):
    po, pp = (str(p).format(n=n) for p in SRC[var])
    if not Path(po).exists() or not Path(pp).exists():
        return None
    rows = [json.loads(l) for l in open(po, encoding="utf-8")]
    phi = {r["id"]: r["answer"] for r in map(json.loads, open(pp, encoding="utf-8"))}
    out = []
    for r in rows:
        a, s = S.cand(r)
        a = a if ans(a) else None
        rel = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)[0] if s >= 3 else None
        p = phi.get(r["id"])
        if rel and not (ans(p) and agree(str(rel), str(p))):
            rel = None
        out.append((r["question"], rel, grade(r["question"], r["gold"], rel) if rel else None))
    return out


lines = ["# S22 DEV variants (frozen S19 decision logic; alias-aware cached labels)", "",
         "| set | variant | n | released | coverage | wrong | unlabelled | +time rule: released / coverage / wrong |", "|---|---|---|---|---|---|---|---|"]
for n in ("mintaka_dev", "popqa_dev"):
    for v in SRC:
        X = score(v, n)
        if X is None:
            lines.append(f"| {n} | {v} | missing |"); continue
        rel = [x for x in X if x[1]]
        relt = [x for x in rel if not time_sensitive(x[0])]
        lines.append(f"| {n} | {v} | {len(X)} | {len(rel)} | {len(rel)/len(X):.3f} | {sum(x[2] is False for x in rel)} | {sum(x[2] == '?' for x in rel)} | "
                     f"{len(relt)} / {len(relt)/len(X):.3f} / {sum(x[2] is False for x in relt)} |")
(ROOT / "results/runs/s22/variants_dev.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
