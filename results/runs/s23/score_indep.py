"""S23 DEV scoring: combination rule R = S19 releases (format gate) U (variant releases that are not time-sensitive and not subject-ambiguous),
for variant = independent retrieval (s23/indep) and, for comparison, web-pinning (s22/pin). A = releases added beyond the frozen S19 system
(frozen gate), w = graded-wrong among them. Decision rule in docs/S23_DEV_PLAN.md: continue only if pooled A >= 40 and w / A <= 3%.
Heavy (loads local wiki pages): idle priority, one process.  python -I -B results/runs/s23/score_indep.py"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
from entity_dev import ambiguous                                     # noqa: E402
from temporal import time_sensitive                                  # noqa: E402
from abstain_dev import grade                                        # noqa: E402
from gate_fmt import release_any                                     # noqa: E402
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW      # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402


def releases(out, phi, fmt):
    rows = [json.loads(l) for l in open(out, encoding="utf-8")]
    ph = {r["id"]: r["answer"] for r in map(json.loads, open(phi, encoding="utf-8"))}
    res = {}
    for r in rows:
        if fmt:
            rel, rec = release_any(r, LW.page_text)
        else:
            a, s = S.cand(r); a = a if ans(a) else None
            rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
        p = ph.get(r["id"])
        if rel and not (ans(p) and agree(str(rel), str(p))):
            rel = None
        res[r["id"]] = (r, rel, rec.get("doc"))
    return res


def combo(s19f, var):
    final = {}
    for i, (r, rel, doc) in s19f.items():
        if rel:
            final[i] = (r, rel, "s19")
    for i, (r, rel, doc) in var.items():
        if i in final or not rel:
            continue
        if time_sensitive(r["question"]) or ambiguous(r["question"], r["wiki_titles"], doc)[0]:
            continue
        final[i] = (r, rel, "var")
    return final


lines = ["# S23 DEV scoring (design data)", "", "| set | variant | n | released (cov) | wrong | added vs frozen S19 | wrong among added | added from variant |", "|---|---|---|---|---|---|---|---|"]
pool = {"indep": [0, 0], "pin": [0, 0]}
wl = []
for N in ("mintaka_dev", "popqa_dev", "dev"):
    PRE = "s19" if N in ("dev", "fresh", "fresh5") else "s21"
    phi19 = ROOT / f"results/shared_eval/readers/{PRE}{N}_combo_cautious_phi4.jsonl"
    frozen = releases(ROOT / f"results/runs/s19/{N}_outputs.jsonl", phi19, False)
    froz_ids = {i for i, v in frozen.items() if v[1]}
    s19f = releases(ROOT / f"results/runs/s19/{N}_outputs.jsonl", phi19, True)
    n = len(frozen)
    for name, d in (("indep", ROOT / "results/runs/s23/indep"), ("pin", ROOT / "results/runs/s22/pin")):
        if not (d / f"{N}_outputs.jsonl").exists():
            continue
        var = releases(d / f"{N}_outputs.jsonl", d / f"{N}_phi4.jsonl", True)
        fin = combo(s19f, var)
        g = {i: grade(r["question"], r["gold"], rel) for i, (r, rel, src) in fin.items()}
        wrong = sum(x is False for x in g.values())
        added = [i for i in fin if i not in froz_ids]
        aw = sum(g[i] is False for i in added); fv = sum(fin[i][2] == "var" for i in added)
        unl = sum(x == "?" for x in g.values())
        pool[name][0] += len(added); pool[name][1] += aw
        for i in added:
            if g[i] is False:
                wl.append(f"- {N} {name}: {fin[i][0]['question']} | gold {fin[i][0]['gold'][:2]} | answer {fin[i][1]} | from {fin[i][2]}")
        lines.append(f"| {N} | {name} | {n} | {len(fin)} ({len(fin)/n:.3f}) | {wrong} | {len(added)} | {aw} | {fv} |" + (f" unlabelled {unl}" if unl else ""))
        print(lines[-1], flush=True)
lines += ["", "Pooled over the three DEV sets (added beyond the frozen S19 system):"]
for k, (a, w) in pool.items():
    lines.append(f"- {k}: A = {a}, w = {w}, w / A = {(w / a if a else float('nan')):.3f}")
ok = pool["indep"][0] >= 40 and pool["indep"][0] and pool["indep"][1] / pool["indep"][0] <= 0.03
lines.append(f"Decision rule (A >= 40 and w / A <= 3%) for indep: {'CONTINUE to the FRESH-5 design run' if ok else 'STOP the independent-retrieval line'}")
lines += ["", "Wrong among added releases:"] + wl
(ROOT / "results/runs/s23/score_indep.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[-4:]))
