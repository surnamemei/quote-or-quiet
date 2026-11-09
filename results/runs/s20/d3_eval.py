"""S20 Step A (exploratory, post hoc; docs/S20_PLAN.md): the D3 frame-match check on used sets.
Base system: G3 (all 3 sources agree) + L3 gate V1-V5 (vkg.l3_checks2.release2), with and without the Phi-4 cautious veto.
D3-soft: block a release only if the question parser gives a relation and the sentence check or the qualifier check fails.
D3-strict: release only if the parser gives a relation and both checks pass (the T* form; uncovered questions -> Unresolved).
Sets: S19 DEV and FRESH (DuckDuckGo design data) and S18 (FRESH-3 + FRESH-4). Cached judge labels only.
usage: OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s20/d3_eval.py"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
sys.path.insert(0, str(Path(__file__).parent))
import no_retrieval2  # noqa: E402,F401  (must precede vkg imports)
import importlib  # noqa: E402
VER = sys.argv[1] if len(sys.argv) > 1 else "frames"
F = importlib.import_module(VER)
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S, s18_eval as E  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans, g6  # noqa: E402

ROOT = Path(os.getcwd())
RD = ROOT / "results" / "shared_eval" / "readers"


def load(name):
    if name == "s18":
        rows = E.load(["fresh3", "fresh4"])
        phi = {}
        phi.update({r["id"]: r["answer"] for r in map(json.loads, open(RD / "s18_combo_cautious_phi4.jsonl", encoding="utf-8"))})
        return rows, phi
    rows = [json.loads(l) for l in open(ROOT / f"results/runs/s19/{name}_outputs.jsonl", encoding="utf-8")]
    phi = {r["id"]: r["answer"] for r in map(json.loads, open(RD / f"s19{name}_combo_cautious_phi4.jsonl", encoding="utf-8"))}
    return rows, phi


def main():
    out = ["# D3 frame-match check on used sets (exploratory, post hoc; results/runs/s20/d3_eval.py)", "",
           "| set | system | released | coverage | wrong | correct | wrong blocked | correct blocked |", "|---|---|---|---|---|---|---|---|"]
    detail = []
    for name in ("dev", "fresh", "s18"):
        rows, phi = load(name)
        n = len(rows)
        R = []
        for r in rows:
            a, s = S.cand(r)
            if s < 3 or not ans(a):
                continue
            rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
            if not rel:
                continue
            t = LW.page_text(rec["doc"])
            i, j = rec["start"], rec["end"]
            fr = F.question_relation(r["question"])
            sc = F.sentence_confirms(fr, t, i, j) if fr else None
            qo = F.qualifiers_ok(r["question"], rel, t, i, j) and (F.role_ok(r["question"], t, i, j) if hasattr(F, "role_ok") else True)
            p = phi.get(r["id"])
            R.append({"id": r["id"], "q": r["question"], "gold": r["gold"], "rel": rel, "graded": g6(r["question"], r["gold"], rel),
                      "veto_ok": bool(p is not None and ans(p) and agree(str(rel), str(p))), "frame": fr, "sent_ok": sc, "qual_ok": qo,
                      "sentence": t[slice(*F.sentence_of(t, i, j))][:300]})
        for veto in (False, True):
            base = [x for x in R if x["veto_ok"] or not veto]
            soft = [x for x in base if x["qual_ok"] and (x["frame"] is None or x["sent_ok"])]
            strict = [x for x in base if x["frame"] and x["sent_ok"] and x["qual_ok"]]
            w0 = sum(x["graded"] is False for x in base)
            c0 = sum(x["graded"] is True for x in base)
            for lab, L in (("", base), (" + D3-soft", soft), (" + D3-strict", strict)):
                w = sum(x["graded"] is False for x in L)
                c = sum(x["graded"] is True for x in L)
                sysname = "G3 V1-V5" + (" + Phi-4 veto" if veto else "") + lab
                out.append(f"| {name} (n={n}) | {sysname} | {len(L)} | {len(L) / n:.3f} | {w} ({w / n:.4f}) | {c} | "
                           f"{w0 - w if lab else ''} | {c0 - c if lab else ''} |")
        cor = [x for x in R if x["graded"] is True]
        why = {"no frame": sum(x["frame"] is None for x in cor), "sentence check fails": sum(bool(x["frame"]) and not x["sent_ok"] for x in cor),
               "qualifier check fails": sum(not x["qual_ok"] for x in cor)}
        out.append(f"| {name} | correct releases by D3 outcome (of {len(cor)}) | " + "; ".join(f"{k} {v}" for k, v in why.items()) + " | | | | | |")
        cov = sum(x["frame"] is not None for x in R) / max(1, len(R))
        out.append(f"| {name} | parser coverage among G3 releases | {cov:.2f} | | | | | |")
        detail += [{"set": name, **x} for x in R if x["graded"] is False]
        json.dump([x for x in cor if x["frame"] and not (x["sent_ok"] and x["qual_ok"])][:80],
                  open(Path(__file__).parent / f"d3_blocked_correct_{VER}_{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    txt = "\n".join(out)
    (Path(__file__).parent / f"d3_eval_{VER}.md").write_text(txt, encoding="utf-8")
    json.dump(detail, open(Path(__file__).parent / f"d3_errors_{VER}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(txt)


if __name__ == "__main__":
    main()
