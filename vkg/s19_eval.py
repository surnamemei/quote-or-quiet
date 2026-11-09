"""S19 scorer (docs/S19_PROTOCOL.md): L2 test of the frozen system on the sealed FRESH-5 (1526 items).
System: L3 gate V1-V4 (vkg/l3_verify) + draft checks V2'/V3'/V5 (vkg/l3_checks2.release2) + all 3 sources agree (support 3)
        + Phi-4 cautious veto (Phi-4's own combo answer must agree, vkg.s12_run.agree).
L2 rule (as S18): E = ceil(k / (1 - f_up)), f_up = 0.0082; pass iff the Clopper-Pearson one-sided 97.5% upper bound of E/n < 0.01
        and coverage >= 0.35. At n = 1526 this means k <= 6.
Endpoints: primary = k after blind adjudication (only "gold wrong" / "both acceptable" remove an error); secondary = k gold-relative.
usage:  python -B -m vkg.s19_eval score    -> results/runs/s19/S19_raw.md + adjudication sheet (blind) + key (sealed for the scorer)
        python -B -m vkg.s19_eval final    -> reads the filled sheet, writes results/runs/s19/S19_final.md
Cached judge labels only (run with OLLAMA_HOST_URL=http://127.0.0.1:9 to guarantee no new judging)."""
import csv
import json
import math
import random
import sys
from pathlib import Path

from scipy.stats import beta

from . import l3_checks2 as C, localwiki as LW, s17_eval as S
from .s12_run import agree
from .s14_eval import ans, g6

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results" / "runs" / "s19"
SET, N_EXPECT = "fresh5", 1526          # a dry run on design data changes only these (code check, see docs/S19_PROTOCOL.md)
PHI_FMT = str(ROOT / "results" / "shared_eval" / "readers" / "{}_combo_cautious_phi4.jsonl")
F_UP, FLOOR, LIMIT = 0.0082, 0.35, 0.01
SEED = 19
RUBRIC = ("gold wrong", "answer wrong", "both acceptable", "cannot tell")


def upper(k, n):
    e = math.ceil(k / (1 - F_UP))
    return 1.0 if e >= n else float(beta.ppf(0.975, e + 1, n - e))


def system_rows():
    rows = [json.loads(l) for l in open(R / f"{SET}_outputs.jsonl", encoding="utf-8")]
    phi = {r["id"]: r for r in map(json.loads, open(PHI_FMT.format("s19" + SET), encoding="utf-8"))}
    assert len(rows) == N_EXPECT and set(phi) == {r["id"] for r in rows}
    out = []
    for r in rows:
        a, s = S.cand(r)
        a = a if ans(a) else None
        rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
        p = phi[r["id"]]["answer"]
        if rel and not (ans(p) and agree(str(rel), str(p))):
            rel = None
        out.append({"id": r["id"], "question": r["question"], "gold": r["gold"], "released": rel, "doc": rec.get("doc") if rel else None,
                    "graded": g6(r["question"], r["gold"], rel) if rel else None,
                    "combo_plain": r["combo_plain"], "combo_plain_graded": g6(r["question"], r["gold"], r["combo_plain"]) if ans(r["combo_plain"]) else None})
    return out


def score():
    X = system_rows()
    n = len(X)
    rel = [x for x in X if x["released"]]
    wrong = [x for x in rel if x["graded"] is False]
    cov = len(rel) / n
    k = len(wrong)
    lines = ["# S19 raw result (vkg/s19_eval.py score; gold-relative, before adjudication)", "",
             f"n = {n}; released {len(rel)} (coverage {cov:.3f}, floor {FLOOR}); correct {sum(x['graded'] is True for x in rel)}; "
             f"graded-wrong k = {k}; raw SER {k / n:.4f}; corrected upper (97.5% CP) {upper(k, n):.4f}",
             f"Secondary endpoint (gold-relative): **{'PASS' if cov >= FLOOR and upper(k, n) < LIMIT else 'FAIL'}**",
             "Primary endpoint (adjudicated): pending the blind adjudication sheet."]
    # blind sheet: every graded-wrong release + k graded-wrong combo_plain answers on other items + k graded-correct releases
    rng = random.Random(SEED)
    others = [x for x in X if not x["released"] and x["combo_plain_graded"] is False]
    right = [x for x in rel if x["graded"] is True]
    dec_w = rng.sample(others, min(k, len(others)))
    dec_c = rng.sample(right, min(k, len(right)))
    items = [("system", x, x["released"]) for x in wrong] + [("decoy_baseline_wrong", x, x["combo_plain"]) for x in dec_w] + \
            [("decoy_system_correct", x, x["released"]) for x in dec_c]
    rng.shuffle(items)
    with open(R / "S19_adjudication_sheet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["row", "question", "gold", "answer", "verdict (" + " / ".join(RUBRIC) + ")", "note"])
        for i, (_, x, a) in enumerate(items, 1):
            w.writerow([i, x["question"], " | ".join(x["gold"]), a, "", ""])
    with open(R / "S19_adjudication_key.json", "w", encoding="utf-8") as f:
        json.dump([{"row": i, "kind": kind, "id": x["id"]} for i, (kind, x, _) in enumerate(items, 1)], f)
    lines.append(f"Adjudication sheet: {len(items)} rows ({k} system errors + {len(dec_w)} + {len(dec_c)} decoys), "
                 "results/runs/s19/S19_adjudication_sheet.csv; key kept separately (S19_adjudication_key.json, not shown to the adjudicator).")
    (R / "S19_raw.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def final():
    X = system_rows()
    n = len(X)
    rel = [x for x in X if x["released"]]
    cov = len(rel) / n
    k = sum(x["graded"] is False for x in rel)
    key = {d["row"]: d for d in json.load(open(R / "S19_adjudication_key.json", encoding="utf-8"))}
    sheet = list(csv.DictReader(open(R / "S19_adjudication_sheet.csv", encoding="utf-8")))
    col = [c for c in sheet[0] if c.startswith("verdict")][0]
    verdict = {int(s["row"]): s[col].strip().casefold() for s in sheet}
    bad = [r for r, v in verdict.items() if v not in RUBRIC]
    if bad:
        sys.exit(f"rows without a valid verdict: {bad[:20]} (allowed: {RUBRIC})")
    sys_rows = [r for r, d in key.items() if d["kind"] == "system"]
    removed = sum(verdict[r] in ("gold wrong", "both acceptable") for r in sys_rows)
    k_adj = k - removed
    by = {kind: {v: sum(1 for r, d in key.items() if d["kind"] == kind and verdict[r] == v) for v in RUBRIC}
          for kind in ("system", "decoy_baseline_wrong", "decoy_system_correct")}
    lines = ["# S19 final result (vkg/s19_eval.py final)", "",
             f"n = {n}; coverage {cov:.3f} (floor {FLOOR})",
             f"**Primary (adjudicated): k = {k_adj} (removed {removed} of {k}); upper {upper(k_adj, n):.4f} -> "
             f"{'PASS' if cov >= FLOOR and upper(k_adj, n) < LIMIT else 'FAIL'}**",
             f"Secondary (gold-relative): k = {k}; upper {upper(k, n):.4f} -> {'PASS' if cov >= FLOOR and upper(k, n) < LIMIT else 'FAIL'}",
             "", "Verdicts by row kind (decoys check that the adjudicator was not lenient only on system rows):",
             "| kind | " + " | ".join(RUBRIC) + " |", "|---|" + "---|" * len(RUBRIC)]
    lines += [f"| {kind} | " + " | ".join(str(c[v]) for v in RUBRIC) + " |" for kind, c in by.items()]
    (R / "S19_final.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    {"score": score, "final": final}[sys.argv[1]]()
