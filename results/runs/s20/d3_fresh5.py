"""Apply D3 v0/v1 (frames.py / frames_v1.py, unchanged since 15:14, before any FRESH-5 output existed at 17:07) to FRESH-5.
Not pre-registered, so exploratory; but out of sample for D3. Same logic as d3_eval.py, set fresh5 only. Cached labels only."""
import json, os, sys, importlib
from pathlib import Path
sys.path.insert(0, os.getcwd()); sys.path.insert(0, str(Path(__file__).parent))
import no_retrieval2  # noqa
import d3_eval as D
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S
from vkg.s12_run import agree
from vkg.s14_eval import ans, g6
out = ["# D3 on FRESH-5 (exploratory; D3 code frozen in effect at 15:14, FRESH-5 outputs from 17:07)", "",
       "| D3 version | system | released | coverage | wrong | correct |", "|---|---|---|---|---|---|"]
rows, phi = D.load("fresh5"); n = len(rows)
base = []
for r in rows:
    a, s = S.cand(r)
    if s < 3 or not ans(a):
        continue
    rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
    if not rel:
        continue
    base.append((r, rel, rec))
errs = []
for VER in ("frames", "frames_v1"):
    F = importlib.import_module(VER)
    R = []
    for r, rel, rec in base:
        t = LW.page_text(rec["doc"]); i, j = rec["start"], rec["end"]
        fr = F.question_relation(r["question"])
        sc = F.sentence_confirms(fr, t, i, j) if fr else None
        qo = F.qualifiers_ok(r["question"], rel, t, i, j) and (F.role_ok(r["question"], t, i, j) if hasattr(F, "role_ok") else True)
        p = phi.get(r["id"])
        R.append({"id": r["id"], "q": r["question"], "gold": r["gold"], "rel": rel, "graded": g6(r["question"], r["gold"], rel),
                  "veto_ok": bool(p is not None and ans(p) and agree(str(rel), str(p))), "frame": fr, "sent_ok": sc, "qual_ok": qo,
                  "doc": rec["doc"], "sentence": t[slice(*F.sentence_of(t, i, j))][:400]})
    for veto in (False, True):
        b = [x for x in R if x["veto_ok"] or not veto]
        soft = [x for x in b if x["qual_ok"] and (x["frame"] is None or x["sent_ok"])]
        strict = [x for x in b if x["frame"] and x["sent_ok"] and x["qual_ok"]]
        for lab, L in (("", b), (" + D3-soft", soft), (" + D3-strict", strict)):
            w = sum(x["graded"] is False for x in L); c = sum(x["graded"] is True for x in L)
            out.append(f"| {VER} | G3 V1-V5{' + Phi-4 veto' if veto else ''}{lab} | {len(L)} | {len(L)/n:.3f} | {w} | {c} |")
    errs += [{"ver": VER, **x} for x in R if x["graded"] is False and x["veto_ok"]]
txt = "\n".join(out)
(Path(__file__).parent / "d3_fresh5.md").write_text(txt, encoding="utf-8")
json.dump(errs, open(Path(__file__).parent / "d3_fresh5_errors.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(txt)
