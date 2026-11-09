"""Standalone scorer for the shared evaluation format (evaluation session, F:\\Projects\\AI hallucinations).

INPUT: one JSON object per line:
  id            str   item id (DEV/FRESH ids as in the item files, e.g. "sqa-1234")
  question      str
  gold          list[str]   (gold[0] is graded; same as the item files)
  answer        str | null  the system's final answer; abstain with "I don't know" / "unknown" / null
  evidence_urls list[str]   optional
  prompt_tokens int, gen_tokens int   optional (cost)
GRADING: grader 6.1 = qwen3.8-27b judge (Ollama, model e0a7cdbef002) + code vetoes (vkg/grade6.py). Non-answers are
  detected by code (vkg/s8_eval.non_answer) and count as abstentions, not errors. Judge labels are cached in
  results/grader5/judge_grades.jsonl (prompt-keyed, so re-scoring is free); missing labels are computed via
  OLLAMA_HOST_URL (default http://localhost:11434).
OUTPUT: coverage, correct (yield), SER (wrong / all items), selective risk (wrong / answered), Clopper-Pearson one-sided
  95% upper bound on SER, cost; per-row grades written next to the input as <input>.graded.jsonl.
  With --baseline B.jsonl (same ids): paired differences with one-sided 95% bootstrap bounds (10000 draws, seed 0) and the
  programme's L1 criteria: (a) upper bound of mean(e - 0.5 e_base) < 0, (b) correct diff >= 0 and lower bound > -0.03,
  (c) coverage diff >= -0.03.
SEALED SETS: ids of FRESH-3 (results/runs/fresh3/items.json) are refused unless --sealed-ok is given; that flag is for
  pre-registered confirmations only.
USAGE:  python -B -m vkg.score_jsonl RUN.jsonl [--baseline BASE.jsonl] [--sealed-ok]"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta

ROOT = Path(__file__).resolve().parent.parent
JFILE = ROOT / "results" / "grader5" / "judge_grades.jsonl"


def load(path):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    for i, r in enumerate(rows):
        for k in ("id", "question", "gold"):
            if k not in r:
                sys.exit(f"{path}: row {i} lacks '{k}'")
        if isinstance(r["gold"], str):
            r["gold"] = [r["gold"]]
        r.setdefault("answer", None)
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        sys.exit(f"{path}: duplicate ids")
    return rows


def sealed_ids():
    p = ROOT / "results" / "runs" / "fresh3" / "items.json"
    return {e["id"] for e in json.load(open(p, encoding="utf-8"))} if p.exists() else set()


def grade(rows):
    from . import s14_eval as S
    from .grade_judge import judge
    from .s8_eval import non_answer
    todo = []
    for r in rows:
        a = r["answer"]
        if a is not None and not non_answer(str(a)):
            t = (r["question"], r["gold"][0], str(a))
            if t not in S.J and t not in todo:
                todo.append(t)
    if todo:
        print(f"judging {len(todo)} new answers ...", flush=True)
        with open(JFILE, "a", encoding="utf-8") as f:
            for q, g, a in todo:
                lab = judge(q, g, a)
                S.J[(q, g, a)] = lab
                f.write(json.dumps({"question": q, "gold": g, "answer": a, "grade": lab}, ensure_ascii=False) + "\n")
                f.flush()
    out = []
    for r in rows:
        g = S.g6(r["question"], r["gold"], r["answer"])
        out.append("abstain" if g is None else "correct" if g else "wrong")
    return out


def cp_upper(k, n):
    return 1.0 if k >= n else float(beta.ppf(0.95, k + 1, n - k))


def summary(rows, labels, name):
    n = len(rows)
    a = sum(l != "abstain" for l in labels)
    c = labels.count("correct")
    w = labels.count("wrong")
    pt = [r["prompt_tokens"] for r in rows if "prompt_tokens" in r]
    gt = [r["gen_tokens"] for r in rows if "gen_tokens" in r]
    s = (f"{name}: n={n}  coverage {a / n:.3f}  correct {c / n:.3f}  SER {w / n:.4f}  selective risk {w / max(1, a):.4f}  "
         f"SER 95% upper (CP) {cp_upper(w, n):.4f}")
    if pt:
        s += f"  | prompt tokens/item {np.mean(pt):.0f}"
    if gt:
        s += f", gen tokens/item {np.mean(gt):.0f}"
    return s


def lo_hi(d, rng):
    d = np.asarray(d, float)
    bs = np.sort(d[rng.integers(0, len(d), (10000, len(d)))].mean(1))
    return d.mean(), bs[500], bs[9499]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run")
    ap.add_argument("--baseline")
    ap.add_argument("--sealed-ok", action="store_true")
    a = ap.parse_args()
    runs = {"run": load(a.run)}
    if a.baseline:
        runs["baseline"] = load(a.baseline)
    sealed = sealed_ids()
    for k, rows in runs.items():
        hit = sum(r["id"] in sealed for r in rows)
        if hit and not a.sealed_ok:
            sys.exit(f"{k}: {hit} ids belong to the SEALED FRESH-3 set; scoring refused (pre-registered confirmations only: --sealed-ok)")
    labs = {}
    for k, rows in runs.items():
        labs[k] = grade(rows)
        p = Path(getattr(a, k) if k == "run" else a.baseline)
        with open(p.with_suffix(".graded.jsonl"), "w", encoding="utf-8") as f:
            for r, l in zip(rows, labs[k]):
                f.write(json.dumps({"id": r["id"], "answer": r["answer"], "grade": l}, ensure_ascii=False) + "\n")
        print(summary(rows, labs[k], k))
    if a.baseline:
        bmap = dict(zip([r["id"] for r in runs["baseline"]], labs["baseline"]))
        ids = [r["id"] for r in runs["run"]]
        if set(ids) != set(bmap):
            sys.exit("run and baseline must contain the same ids")
        L = dict(zip(ids, labs["run"]))
        e = np.array([L[i] == "wrong" for i in ids], float)
        eb = np.array([bmap[i] == "wrong" for i in ids], float)
        c = np.array([L[i] == "correct" for i in ids], float)
        cb = np.array([bmap[i] == "correct" for i in ids], float)
        cov = np.mean([L[i] != "abstain" for i in ids]) - np.mean([bmap[i] != "abstain" for i in ids])
        rng = np.random.default_rng(0)
        s = lo_hi(e - 0.5 * eb, rng)
        y = lo_hi(c - cb, rng)
        d = lo_hi(e - eb, rng)
        ok = (s[2] < 0, y[0] >= 0 and y[1] > -0.03, cov >= -0.03)
        print(f"paired (n={len(ids)}): SER diff {d[0]:+.4f} [one-sided 95%: {d[1]:+.4f}, {d[2]:+.4f}]; correct diff {y[0]:+.4f} (lower {y[1]:+.4f}); "
              f"coverage diff {cov:+.4f}")
        print(f"L1 criteria: (a) SER at most half the baseline's: upper {s[2]:+.4f} -> {'pass' if ok[0] else 'fail'}; "
              f"(b) yield not lower -> {'pass' if ok[1] else 'fail'}; (c) coverage within 3 points -> {'pass' if ok[2] else 'fail'}; "
              f"L1 {'MET' if all(ok) else 'NOT MET'}")


if __name__ == "__main__":
    main()
