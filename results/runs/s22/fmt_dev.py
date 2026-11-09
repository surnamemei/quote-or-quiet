"""Effect of the format relaxation (gate_fmt) on DEV: S19 and pin outputs, Mintaka / PopQA DEV and SimpleQA DEV (s19 'dev')."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from gate_fmt import release_any                                     # noqa: E402
from vkg import localwiki as LW, l3_checks2 as C, s17_eval as S      # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402
from abstain_dev import grade                                        # noqa: E402
PHI = {("s19", "mintaka_dev"): "results/shared_eval/readers/s21mintaka_dev_combo_cautious_phi4.jsonl",
       ("s19", "popqa_dev"): "results/shared_eval/readers/s21popqa_dev_combo_cautious_phi4.jsonl",
       ("s19", "dev"): "results/shared_eval/readers/s19dev_combo_cautious_phi4.jsonl"}
for var, n in (("s19", "dev"), ("s19", "mintaka_dev"), ("pin", "mintaka_dev"), ("s19", "popqa_dev"), ("pin", "popqa_dev")):
    out = ROOT / ("results/runs/s19" if var == "s19" else "results/runs/s22/pin") / f"{n}_outputs.jsonl"
    pp = ROOT / (PHI[(var, n)] if var == "s19" else f"results/runs/s22/pin/{n}_phi4.jsonl")
    if not pp.exists():
        print(var, n, "no phi4 file", pp); continue
    rows = [json.loads(l) for l in open(out, encoding="utf-8")]
    phi = {r["id"]: r["answer"] for r in map(json.loads, open(pp, encoding="utf-8"))}
    res = {"frozen": [], "fmt": []}; new = []
    for r in rows:
        p = phi.get(r["id"])
        a, s = S.cand(r); a = a if ans(a) else None
        rel0 = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)[0] if s >= 3 else None
        rel1 = release_any(r, LW.page_text)[0]
        for k, rel in (("frozen", rel0), ("fmt", rel1)):
            if rel and ans(p) and agree(str(rel), str(p)):
                res[k].append(grade(r["question"], r["gold"], rel))
                if k == "fmt" and not (rel0 and ans(p) and agree(str(rel0), str(p))):
                    new.append((r["question"][:60], rel, r["gold"][:1], res[k][-1]))
    N = len(rows)
    print(f"{var:4s} {n:12s} frozen {len(res['frozen'])} ({len(res['frozen'])/N:.3f}) wrong {sum(x is False for x in res['frozen'])} unl {sum(x=='?' for x in res['frozen'])} | "
          f"fmt {len(res['fmt'])} ({len(res['fmt'])/N:.3f}) wrong {sum(x is False for x in res['fmt'])} unl {sum(x=='?' for x in res['fmt'])}")
    for x in new:
        if x[3] is not True: print("    new not-correct:", x)
