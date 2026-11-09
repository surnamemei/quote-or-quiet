"""Score grader 5 (judge) against the blind labels (docs/GRADER5_PROTOCOL.md, J1-J4) and regrade S6b / S8 / S9 as a sensitivity.
Run after vkg.judge_run: python -B -m vkg.grader5_eval -> results/grader5/grader5_tables.md"""
import json

import numpy as np

from .analyze_open import att, cor_rep
from .grade_v4 import correct_v4
from .probe_eval import correct
from .probe_gen import ROOT
from .s8_eval import non_answer

G = ROOT / "results" / "grader5"
R = ROOT / "results" / "runs"
J = {(r["question"], r["gold"], r["answer"]): r["grade"] for r in map(json.loads, open(G / "judge_grades.jsonl", encoding="utf-8"))}


def jg(q, g, a):
    return J[(q, g[0] if isinstance(g, list) else g, a)]


def cp(k, n):
    from scipy.stats import beta
    lo = beta.ppf(0.025, k, n - k + 1) if k else 0.0
    hi = beta.ppf(0.975, k + 1, n - k) if k < n else 1.0
    return f"{k}/{n} = {k / n:.1%} [{lo:.1%}, {hi:.1%}]"


def validate(L):
    sets = []
    b2 = [json.loads(l) for l in open(G / "v2_blind.jsonl", encoding="utf-8")]
    l2 = {int(x.split("\t")[0]): x.split("\t")[1] for x in open(G / "v2_labels.txt", encoding="utf-8")}
    key = {u["k"]: u for u in json.load(open(G / "v2_key_HIDDEN.json", encoding="utf-8"))}
    sets.append(("V2 (new, blind)", b2, l2, {r["k"]: key[r["k"]]["grader_correct"] for r in b2}))
    b1 = [json.loads(l) for l in open(ROOT / "results" / "audit" / "validation" / "sample_blind.jsonl", encoding="utf-8")]
    l1 = {int(x.split()[0]): x.split()[1] for x in open(ROOT / "results" / "audit" / "validation" / "my_labels.txt", encoding="utf-8")}
    hk = {u["k"]: u["grader"] == "correct" for u in json.load(open(ROOT / "results" / "audit" / "validation" / "sample_key_HIDDEN.json", encoding="utf-8"))}
    sets.append(("V1 (old, 27B outputs)", b1, l1, hk))
    for name, rows, lab, v3 in sets:
        L += [f"## {name}, n={len(rows)}", "", "| grader | false credit (W/N rows graded correct) | misses (C rows not graded correct) |", "|---|---|---|"]
        hw = [r for r in rows if lab[r["k"]] != "C"]
        hc = [r for r in rows if lab[r["k"]] == "C"]
        graders = {
            "v3 (frozen)": lambda r: bool(v3[r["k"]]),
            "v4": lambda r: correct_v4(r["question"], [r["gold"]], r["answer"]),
            "judge (grader 5)": lambda r: jg(r["question"], r["gold"], r["answer"]) == "CORRECT",
        }
        for gname, f in graders.items():
            try:
                fc = sum(f(r) for r in hw)
                ms = sum(not f(r) for r in hc)
                L.append(f"| {gname} | {cp(fc, len(hw))} | {cp(ms, len(hc))} |")
            except Exception as ex:            # v3 key format differs between sets
                L.append(f"| {gname} | n/a ({ex!r}) | |")
        L.append("")
        L.append("Judge disagreements with the label:")
        for r in rows:
            g = jg(r["question"], r["gold"], r["answer"])
            if (g == "CORRECT") != (lab[r["k"]] == "C"):
                L.append(f"- k={r['k']} label {lab[r['k']]} judge {g}: Q: {r['question'][:90]} | gold: {str(r['gold'])[:60]} | answer: {str(r['answer'])[:80]}")
        L.append("")
    return sets


def regrade(L):
    fresh = {e["id"]: e for e in json.load(open(R / "s8" / "fresh_items.json", encoding="utf-8"))}
    dev = {e["id"]: e for e in json.load(open(R / "s6b" / "eval_items.json", encoding="utf-8")) if e["suite"] == "simpleqa_E"}
    L += ["## Regrade (sensitivity only; predictions stay scored on frozen graders)", "",
          "SER = answered and not graded correct / all; correct = graded correct / all. 4B non-answers: code detector; certificate: mode unknown; 27B: att().", "",
          "| set | system | n | coverage | correct frozen | correct judge | SER frozen | SER judge | judge NOT_ATTEMPTED among answered |", "|---|---|---|---|---|---|---|---|---|"]
    def line(setname, sysname, recs):
        n = len(recs)
        a = np.array([x[0] for x in recs])
        cf = np.array([x[1] for x in recs]) & a
        g = [x[2] for x in recs]
        cj = np.array([gg == "CORRECT" for gg in g]) & a
        na = sum(1 for aa, gg in zip(a, g) if aa and gg == "NOT_ATTEMPTED")
        L.append(f"| {setname} | {sysname} | {n} | {a.mean():.3f} | {cf.mean():.3f} | {cj.mean():.3f} | {(a & ~cf).mean():.3f} | {(a & ~cj).mean():.3f} | {na} |")
    s6b = [o for o in map(json.loads, open(R / "s6b" / "eval_outputs.jsonl", encoding="utf-8")) if o["suite"] == "simpleqa_E"]
    for s in ("plain", "cautious", "trained"):
        line("DEV SimpleQA-E", f"4B {s}", [(not non_answer(o[s]), bool(correct({"dataset": "simpleqa", "gold": o["gold"]}, str(o[s]))),
                                           jg(o["question"], o["gold"], str(o[s])) if not non_answer(o[s]) else "-") for o in s6b])
    f4 = [json.loads(l) for l in open(R / "s8" / "fresh_4b.jsonl", encoding="utf-8")]
    for s in ("plain", "cautious"):
        line("FRESH", f"4B {s}", [(not non_answer(o[s]), bool(correct({"dataset": "simpleqa", "gold": fresh[o["id"]]["gold"]}, str(o[s]))),
                                   jg(fresh[o["id"]]["question"], fresh[o["id"]]["gold"], str(o[s])) if not non_answer(o[s]) else "-") for o in f4])
    for suite, it, nm in (("simpleqa_E", dev, "DEV SimpleQA-E"), ("fresh", fresh, "FRESH")):
        recs = []
        for r in map(json.loads, open(R / "cert" / f"{suite}.jsonl", encoding="utf-8")):
            a = r["mode"] != "unknown"
            e = it[r["id"]]
            recs.append((a, a and bool(correct({"dataset": "simpleqa", "gold": e["gold"]}, r["answer"])), jg(e["question"], e["gold"], r["answer"]) if a else "-"))
        line(nm, "4B certificate", recs)
    big = [json.loads(l) for l in open(R / "openworld_simpleqa_hybrid_qwen3.8-27b_s3000_n300.jsonl", encoding="utf-8")]
    fb = [json.loads(l) for l in open(R / "s8" / "fresh_27b.jsonl", encoding="utf-8")]
    for nm, src, systems in (("DEV SimpleQA-E", big, ("B1_abstain", "B2_strict", "VKG_v2")), ("FRESH", fb, ("B1_abstain", "B2_strict"))):
        for s in systems:
            rs = [r for r in src if r["system"] == s]
            line(nm, f"27B {s}", [(bool(att(r)), bool(cor_rep(r)), jg(r["question"], r["gold"], r["answer"]) if att(r) else "-") for r in rs])
    L.append("")


def main():
    L = ["# Grader 5 (LLM judge, SimpleQA Verified prompt) — generated by vkg/grader5_eval.py", ""]
    validate(L)
    regrade(L)
    txt = "\n".join(L)
    (G / "grader5_tables.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
