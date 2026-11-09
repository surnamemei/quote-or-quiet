"""python -m vkg.run --model qwen3.8-27b [--limit N] [--seed S] [--workers W]"""
import argparse
import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import tasks
from .metrics import classify, summarize, paired_bootstrap_delta, ser, yld
from .systems import SYSTEMS

ROOT = Path(__file__).resolve().parent.parent


def evaluate(model, systems, items, workers):
    rows = []

    def one(args):
        sysname, item = args
        t = time.time()
        try:
            out = SYSTEMS[sysname](item, model)
        except Exception as e:  # keep failures visible; count as abstain-with-error
            out = {"status": "unknown", "answer": "", "raw": f"ERROR {e!r}", "trace": ["error"]}
        return {"system": sysname, "id": item.id, "family": item.family, "kind": item.kind,
                "question": item.question, "gold": item.gold, "status": out["status"], "answer": out["answer"],
                "outcome": classify(item, out), "trace": out.get("trace"), "sec": round(time.time() - t, 2)}

    jobs = [(s, it) for s in systems for it in items]
    with ThreadPoolExecutor(workers) as ex:
        for i, r in enumerate(ex.map(one, jobs), 1):
            rows.append(r)
            if i % 25 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)
    return rows


def report(rows, systems, model, seed):
    L = [f"# Pilot results — {model} (task seed {seed})\n",
         "SER = silent error rate over all items; yield = correct share of answerable items; "
         "safe = abstain/qualify share of non-answerable items.\n"]
    fams = sorted({r["family"] for r in rows})
    L.append("| system | family | n | SER | SER strict (+false conflict) | SER 95% UB | selective risk | yield | over-abstain | safe handling |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for s in systems:
        for f in ["ALL"] + fams:
            sub = [r for r in rows if r["system"] == s and (f == "ALL" or r["family"] == f)]
            m = summarize(sub)
            L.append(f"| {s} | {f} | {m['n']} | {m['SER']:.3f} | {m['SER_strict']:.3f} | {m['SER_ub95']:.3f} | {m['selective_risk']:.3f} | "
                     f"{m['answer_yield']:.3f} | {m['over_abstain']:.3f} | {m['safe_handling']:.3f} |")
    def ser_strict(x):
        return sum(r["outcome"] in ("silent_error", "false_conflict") for r in x) / len(x)

    for bname in ("B0_raw", "B1_abstain"):
        L.append(f"\n## Paired bootstrap vs {bname} (95% CI over questions; negative ΔSER = fewer errors)\n")
        L.append("| system | ΔSER | CI | ΔSER strict | CI | Δyield | CI |")
        L.append("|---|---|---|---|---|---|---|")
        base = {r["id"]: r for r in rows if r["system"] == bname}
        for s in systems:
            if s == bname or not base:
                continue
            cur = {r["id"]: r for r in rows if r["system"] == s}
            d1 = paired_bootstrap_delta(base, cur, ser)
            d3 = paired_bootstrap_delta(base, cur, ser_strict)
            d2 = paired_bootstrap_delta(base, cur, yld)
            L.append(f"| {s} | {d1[0]:+.3f} | [{d1[1]:+.3f}, {d1[2]:+.3f}] | {d3[0]:+.3f} | [{d3[1]:+.3f}, {d3[2]:+.3f}] | "
                     f"{d2[0]:+.3f} | [{d2[1]:+.3f}, {d2[2]:+.3f}] |")
    L.append("\n## Outcome counts by system and family\n")
    for s in systems:
        for f in fams:
            c = defaultdict(int)
            for r in rows:
                if r["system"] == s and r["family"] == f:
                    c[r["outcome"]] += 1
            L.append(f"- {s} / {f}: {dict(c)}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--systems", default=",".join(SYSTEMS))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="items per family (0 = full pilot)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--suite", default="synthetic", choices=["synthetic", "faitheval", "squad2", "simpleqa", "simpleqa_rag", "simpleqa_oracle", "simpleqa_hybrid"])
    ap.add_argument("--faith-n", dest="faith_n", type=int, default=150)
    ap.add_argument("--tag", default="")
    ap.add_argument("--exclude-seed", dest="exclude_seed", type=int, default=None)
    ap.add_argument("--meta", default="", help="free text recorded in the report: quant/runtime/arch")
    a = ap.parse_args()
    items = {"faitheval": lambda: tasks.faitheval(a.faith_n, a.seed, a.exclude_seed),
             "squad2": lambda: tasks.squad2(a.faith_n, a.seed, a.exclude_seed),
             "simpleqa": lambda: tasks.simpleqa(a.faith_n, a.seed),
             "simpleqa_rag": lambda: tasks.simpleqa_rag(a.faith_n, a.seed, "search"),
             "simpleqa_oracle": lambda: tasks.simpleqa_rag(a.faith_n, a.seed, "oracle"),
             "simpleqa_hybrid": lambda: tasks.simpleqa_rag(a.faith_n, a.seed, "hybrid"),
             "synthetic": lambda: tasks.build(a.seed)}[a.suite]()
    if a.limit:
        per = defaultdict(int)
        keep = []
        for it in items:
            if per[it.family] < a.limit:
                per[it.family] += 1
                keep.append(it)
        items = keep
    systems = a.systems.split(",")
    print(f"{len(items)} items x {len(systems)} systems on {a.model}")
    rows = evaluate(a.model, systems, items, a.workers)
    tag = f"{a.tag}{a.suite}_{a.model.replace(':', '_').replace('/', '_')}_s{a.seed}_n{len(items)}"
    out = ROOT / "results" / "runs"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{tag}.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    header = (f"> suite={a.suite} model={a.model} seed={a.seed} date={time.strftime('%Y-%m-%d')} "
              f"meta=[{a.meta}]\n> LIMITS: single seed; dev-tuned systems; not a frozen held-out test unless stated.\n\n")
    md = header + report(rows, systems, a.model, a.seed)
    (out / f"{tag}.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
