"""S21 scorer (docs/S21_PROTOCOL.md): transfer test of the frozen S19 H1 system on new sealed sets.
System (unchanged from S19): MS3 candidate -> l3_checks2.release2 -> Phi-4 cautious veto (vkg.s12_run.agree).
Grading: alias-aware grader 6.1 (vkg/s21_judge.g6a), cached labels only (run with OLLAMA_HOST_URL=http://127.0.0.1:9).
H1-M (single primary, one-sided 2.5%): on mintaka_test, E = ceil(k / (1 - 0.0082)); pass iff the Clopper-Pearson one-sided 97.5% upper
      bound of E/n < 0.01 and coverage >= 0.35 (n = 2000: k <= 10). Primary k after blind adjudication, secondary k gold-relative.
PopQA (descriptive): coverage, SER, strata, error classes; no hypothesis test.
usage:  python -B -m vkg.s21_eval score [--dev]   -> results/runs/s21/S21_raw.md (+ blind sheet and key for mintaka)
        python -B -m vkg.s21_eval final [--dev]   -> results/runs/s21/S21_final.md
--dev runs the identical code on popqa_dev / mintaka_dev (dry run; outputs get a _dev suffix)."""
import csv
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scipy.stats import beta

from . import l3_checks2 as C, localwiki as LW, s17_eval as S
from .s12_run import agree
from .s14_eval import ans
from .s21_judge import g6a

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results" / "runs" / "s21"
DEV = "--dev" in sys.argv
SUF = "_dev" if DEV else ""
SETS = {"mintaka": "mintaka_dev" if DEV else "mintaka_test", "popqa": "popqa_dev" if DEV else "popqa_test"}
N_EXPECT = {"mintaka_dev": 200, "popqa_dev": 300, "mintaka_test": 2000, "popqa_test": 2100}
PHI = ROOT / "results" / "shared_eval" / "readers" / "s21{}_combo_cautious_phi4.jsonl"
F_UP, FLOOR, LIMIT, CONF = 0.0082, 0.35, 0.01, 0.975
SEED = 21
RUBRIC = ("gold wrong", "answer wrong", "both acceptable", "ambiguous question", "cannot tell")
REMOVE = ("gold wrong", "both acceptable")


def upper(k, n):
    e = math.ceil(k / (1 - F_UP))
    return 1.0 if e >= n else float(beta.ppf(CONF, e + 1, n - e))


def system_rows(name):
    rows = [json.loads(l) for l in open(ROOT / "results" / "runs" / "s19" / f"{name}_outputs.jsonl", encoding="utf-8")]
    phi = {r["id"]: r for r in map(json.loads, open(str(PHI).format(name), encoding="utf-8"))}
    assert len(rows) == N_EXPECT[name] and set(phi) == {r["id"] for r in rows}, name
    out = []
    for r in rows:
        a, s = S.cand(r)
        a = a if ans(a) else None
        rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
        p = phi[r["id"]]["answer"]
        if rel and not (ans(p) and agree(str(rel), str(p))):
            rel = None
        cp = r["combo_plain"]
        out.append({"id": r["id"], "stratum": r.get("stratum"), "question": r["question"], "gold": r["gold"], "released": rel,
                    "doc": rec.get("doc") if rel else None, "graded": g6a(r["question"], r["gold"], rel) if rel else None,
                    "combo_plain": cp, "combo_plain_graded": g6a(r["question"], r["gold"], cp) if ans(cp) else None})
    return out


def strata(X):
    g = defaultdict(list)
    for x in X:
        g[x["stratum"]].append(x)
    L = ["| stratum | n | released | coverage | wrong | combo_plain answered | combo_plain wrong |", "|---|---|---|---|---|---|---|"]
    for k in sorted(g) + ["ALL"]:
        v = X if k == "ALL" else g[k]
        rel = [x for x in v if x["released"]]
        L.append(f"| {k} | {len(v)} | {len(rel)} | {len(rel) / len(v):.3f} | {sum(x['graded'] is False for x in rel)} | "
                 f"{sum(x['combo_plain_graded'] is not None for x in v)} | {sum(x['combo_plain_graded'] is False for x in v)} |")
    return L


def score():
    lines = [f"# S21 raw result{' (DEV dry run)' if DEV else ''} (vkg/s21_eval.py score; alias-aware gold-relative, before adjudication)", ""]
    sheet = []
    for key in ("mintaka", "popqa"):
        name = SETS[key]
        X = system_rows(name)
        n = len(X)
        rel = [x for x in X if x["released"]]
        wrong = [x for x in rel if x["graded"] is False]
        cov, k = len(rel) / n, len(wrong)
        lines += [f"## {name}" + (" (H1-M, primary)" if key == "mintaka" else " (descriptive)"),
                  f"n = {n}; released {len(rel)} (coverage {cov:.3f}, floor {FLOOR}); correct {sum(x['graded'] is True for x in rel)}; "
                  f"graded-wrong k = {k}; raw SER {k / n:.4f}; corrected upper ({CONF * 100:.2f}% CP) {upper(k, n):.4f}"]
        if key == "mintaka":
            lines += [f"Secondary endpoint (gold-relative): **{'PASS' if cov >= FLOOR and upper(k, n) < LIMIT else 'FAIL'}**",
                      "Primary endpoint (adjudicated): pending the blind adjudication sheet."]
            rng = random.Random(SEED)
            others = [x for x in X if not x["released"] and x["combo_plain_graded"] is False]
            right = [x for x in rel if x["graded"] is True]
            dw, dc = rng.sample(others, min(k, len(others))), rng.sample(right, min(k, len(right)))
            sheet = [("system", x, x["released"]) for x in wrong] + [("decoy_baseline_wrong", x, x["combo_plain"]) for x in dw] + \
                    [("decoy_system_correct", x, x["released"]) for x in dc]
            rng.shuffle(sheet)
        lines += [""] + strata(X) + [""]
        lines += ["Graded-wrong releases (" + name + "):", ""] + \
                 [f"- {x['question']} | gold {' / '.join(x['gold'][:4])} | released {x['released']} | page {x['doc']}" for x in wrong] + [""] \
            if key == "popqa" else []
    with open(R / f"S21_adjudication_sheet{SUF}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["row", "question", "gold", "answer", "verdict (" + " / ".join(RUBRIC) + ")", "note"])
        for i, (_, x, a) in enumerate(sheet, 1):
            w.writerow([i, x["question"], " | ".join(x["gold"]), a, "", ""])
    json.dump([{"row": i, "kind": kd, "id": x["id"]} for i, (kd, x, _) in enumerate(sheet, 1)],
              open(R / f"S21_adjudication_key{SUF}.json", "w", encoding="utf-8"))
    lines.append(f"Adjudication sheet (mintaka only): {len(sheet)} rows, results/runs/s21/S21_adjudication_sheet{SUF}.csv; "
                 f"key in S21_adjudication_key{SUF}.json (not shown to the adjudicator).")
    (R / f"S21_raw{SUF}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def final():
    X = system_rows(SETS["mintaka"])
    n = len(X)
    rel = [x for x in X if x["released"]]
    cov, k = len(rel) / n, sum(x["graded"] is False for x in rel)
    key = {d["row"]: d for d in json.load(open(R / f"S21_adjudication_key{SUF}.json", encoding="utf-8"))}
    sheet = list(csv.DictReader(open(R / f"S21_adjudication_sheet{SUF}.csv", encoding="utf-8")))
    verdict = {}
    if sheet:
        col = [c for c in sheet[0] if c.startswith("verdict")][0]
        verdict = {int(s["row"]): s[col].strip().casefold() or "cannot tell" for s in sheet}   # blank = not adjudicated = keep
    bad = [r for r, v in verdict.items() if v not in RUBRIC]
    if bad:
        sys.exit(f"rows without a valid verdict: {bad[:20]} (allowed: {RUBRIC})")
    sysr = [r for r, d in key.items() if d["kind"] == "system"]
    removed = sum(verdict[r] in REMOVE for r in sysr)
    ka = k - removed
    by = {kd: Counter(verdict[r] for r, d in key.items() if d["kind"] == kd) for kd in ("system", "decoy_baseline_wrong", "decoy_system_correct")}
    v = lambda kk: "PASS" if cov >= FLOOR and upper(kk, n) < LIMIT else "FAIL"
    lines = [f"# S21 final result, H1-M{' (DEV dry run)' if DEV else ''} (vkg/s21_eval.py final)", "",
             f"n = {n}; coverage {cov:.3f} (floor {FLOOR})",
             f"**Primary (adjudicated): k = {ka} (removed {removed} of {k}); upper {upper(ka, n):.4f} -> {v(ka)}**",
             f"Secondary (gold-relative, alias-aware): k = {k}; upper {upper(k, n):.4f} -> {v(k)}", "",
             "| kind | " + " | ".join(RUBRIC) + " |", "|---|" + "---|" * len(RUBRIC)]
    lines += [f"| {kd} | " + " | ".join(str(c[x]) for x in RUBRIC) + " |" for kd, c in by.items()]
    (R / f"S21_final{SUF}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    {"score": score, "final": final}[sys.argv[1]]()
