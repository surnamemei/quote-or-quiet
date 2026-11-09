"""S26: corroboration across distinct pages for the added releases (docs/S26_PLAN.md). CPU only (loads local wiki pages: idle priority, one process).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s25/corroborate.py"""
import json, os, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s25"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import veto27 as V27
from entity_dev import ambiguous
from temporal import time_sensitive
from abstain_dev import grade
from gate_fmt import release_any
from vkg import localwiki as LW, s17_eval as S, l3_checks2 as C, l3_verify as V
from vkg.s12_run import agree
from vkg.s14_eval import ans


def core(t):
    return re.sub(r"\s*\([^()]*\)$", "", t).casefold()


def corroborated(answer, release_doc, titles):
    for t in titles:
        if t == release_doc or core(t) == core(release_doc):
            continue
        txt = LW.page_text(t) or ""
        if next(V.locate(str(answer), txt), None):
            return t
    return None


rows_out = ["# S26 corroboration (design data)", "", "| variant | set | added | corroborated: wrong / correct | not corroborated: wrong / correct |", "|---|---|---|---|---|"]
tot = {}
for N in V27.SETS:
    base = V27.outputs("s19", N)
    phi19 = {r["id"]: r["answer"] for r in map(json.loads, open(V27.phi_file("s19", N), encoding="utf-8"))}
    froz = set()
    for r in base:
        a, s = S.cand(r); a = a if ans(a) else None
        rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
        p = phi19.get(r["id"])
        if rel and ans(p) and agree(str(rel), str(p)):
            froz.add(r["id"])
    pre = {}
    for var in V27.VARS:
        rows = V27.outputs(var, N)
        if rows is None:
            continue
        ph = {r["id"]: r["answer"] for r in map(json.loads, open(V27.phi_file(var, N), encoding="utf-8"))}
        d = {}
        for r in rows:
            rel, rec = release_any(r, LW.page_text)
            d[r["id"]] = (r, rel, rec.get("doc"), ph.get(r["id"]))
        pre[var] = d
    for var in ("pin", "indep"):
        if var not in pre:
            continue
        final = {}
        for i, (r, rel, doc, p) in pre["s19"].items():
            if rel and ans(p) and agree(str(rel), str(p)):
                final[i] = (r, rel, doc, "s19")
        for i, (r, rel, doc, p) in pre[var].items():
            if i in final or not rel or not (ans(p) and agree(str(rel), str(p))):
                continue
            if time_sensitive(r["question"]) or ambiguous(r["question"], r["wiki_titles"], doc)[0]:
                continue
            final[i] = (r, rel, doc, var)
        cnt = {True: [0, 0], False: [0, 0]}
        added = [i for i in final if i not in froz]
        for i in added:
            r, rel, doc, src = final[i]
            g = grade(r["question"], r["gold"], rel)
            c_ = corroborated(rel, doc, r["wiki_titles"]) is not None
            if g is False:
                cnt[c_][0] += 1
            elif g is True:
                cnt[c_][1] += 1
        rows_out.append(f"| {var} | {N} | {len(added)} | {cnt[True][0]} / {cnt[True][1]} | {cnt[False][0]} / {cnt[False][1]} |")
        print(rows_out[-1], flush=True)
        t = tot.setdefault(var, {True: [0, 0], False: [0, 0]})
        for k in (True, False):
            t[k][0] += cnt[k][0]; t[k][1] += cnt[k][1]
cw = sum(tot[v][True][0] for v in tot); cc = sum(tot[v][True][1] for v in tot)
uw = sum(tot[v][False][0] for v in tot); uc = sum(tot[v][False][1] for v in tot)
rows_out += ["", f"Pooled over pin and indep: corroborated {cw} wrong / {cc} correct; not corroborated {uw} wrong / {uc} correct."]
n_c = cw + cc
ok = n_c >= 40 and cw <= 0.03 * n_c and uw >= (cw + uw) / 2
rows_out.append(f"Decision rule (corroborated >= 40 releases, <= 3% wrong, uncorroborated carry at least half of the wrong): {'USEFUL' if ok else 'not useful; line stops'}")
(ROOT / "results/runs/s25/corroborate.md").write_text("\n".join(rows_out) + "\n", encoding="utf-8")
print("\n".join(rows_out[-3:]))
