"""S21 alias-aware grading (added 2026-11-08; leaves the frozen grader untouched).
PopQA and Mintaka list several acceptable answers (aliases); grader 6.1 (vkg/s14_eval.g6) sees only gold[0]. Rule:
    g6a(q, gold, a) = True  iff  g6 is CORRECT against at least one usable alias (gold[0] first, then up to MAX_ALIAS more),
                      None  iff  a is a non-answer (as g6).
The judge prompt, model and veto are unchanged; each alias is judged as its own gold string. Extra labels are only needed when
the gold[0] label is not CORRECT, so for single-gold items (SimpleQA) g6a == g6 exactly.
Usable alias: at least 2 letters or digits and at least 2 characters (drops emoji flags and one-letter codes); duplicates
(case-folded) removed.
usage: python -B -m vkg.s21_judge <set> [<set> ...]   (labels missing alias triples for released and combo_plain answers of
       results/runs/s19/<set>_outputs.jsonl and appends them to results/grader5/judge_grades.jsonl; needs the judge on Ollama)"""
import json
import re
import sys

from . import pod
from .grade6 import veto
from .s14_eval import J, ans

MAX_ALIAS = 8


def aliases(gold):
    out, seen = [], set()
    for g in gold:
        g = str(g).strip()
        if len(g) < 2 or len(re.findall(r"[^\W_]", g)) < 2 or g.casefold() in seen:
            continue
        seen.add(g.casefold())
        out.append(g)
    return out[:1 + MAX_ALIAS] if out else [str(gold[0])]


def needed(q, gold, a):
    """Triples that must be labelled to compute g6a (empty if decided)."""
    if not ans(a):
        return []
    a = str(a)
    todo = []
    for g in aliases(gold):
        lab = J.get((q, g, a))
        if lab is None:
            todo.append((q, g, a))
            continue
        if lab == "CORRECT" and not veto(q, g, a):
            return []
    return todo


def g6a(q, gold, a):
    if not ans(a):
        return None
    a = str(a)
    for g in aliases(gold):
        lab = J[(q, g, a)]
        if lab == "CORRECT" and not veto(q, g, a):
            return True
    return False


def main(sets):
    from .probe_gen import ROOT
    keys = [k for s in ("web", "wiki", "combo") for k in (f"{s}_plain", f"{s}_cautious")]
    todo = []
    for name in sets:
        for r in map(json.loads, open(ROOT / "results" / "runs" / "s19" / f"{name}_outputs.jsonl", encoding="utf-8")):
            for k in keys:
                for t in needed(r["question"], r["gold"], r.get(k)):
                    if t not in todo:
                        todo.append(t)
    print(f"alias labels to add: {len(todo)}", flush=True)
    path = ROOT / "results" / "grader5" / "judge_grades.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        for s in range(0, len(todo), 64):
            part = todo[s:s + 64]
            for (q, g, a), gr in zip(part, pod.judge_many(part, 4)):
                f.write(json.dumps({"question": q, "gold": g, "answer": a, "grade": gr}, ensure_ascii=False) + "\n")
                J[(q, g, a)] = gr
            f.flush()
    pod.unload_judge()
    print("done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
