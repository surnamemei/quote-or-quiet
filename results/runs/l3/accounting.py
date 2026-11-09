"""L3 accounting table for the three Qualified variants on given sets (descriptive). Grading: alias-aware cached labels; where an
alias label is missing, gold[0]-only grader 6.1 (as S19). Silent errors shown as a range: low = Verified wrong only (every
graded-wrong Qualified output treated as an explicit miss), high = Verified wrong + Qualified wrong.
usage: OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/l3/accounting.py <set> ..."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3")); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from qualified_dev import releases                          # noqa: E402
from qualified import decide                                # noqa: E402
from abstain_dev import grade                               # noqa: E402
from vkg.s14_eval import g6                                 # noqa: E402

lines = ["| set | n | variant | releases | Verified (wrong) | Qualified (wrong) | Unresolved (correct lost) | completion | silent errors low-high |",
         "|---|---|---|---|---|---|---|---|---|"]
for name in sys.argv[1:]:
    n = sum(1 for _ in open(ROOT / f"results/runs/s19/{name}_outputs.jsonl", encoding="utf-8"))
    R = []
    for r, rel, doc, m in releases(name):
        g = grade(r["question"], r["gold"], rel)
        if g == "?":
            g = g6(r["question"], r["gold"], rel)
        R.append((r["question"], rel, doc, g))
    for v, strict in (("strict", True), ("mid", "mid"), ("lenient", False)):
        c = {"V": [0, 0], "Q": [0, 0], "U": [0, 0]}
        for q, rel, doc, g in R:
            st = decide(q, rel, doc, strict=strict)[0][0]
            c[st][0] += 1
            c[st][1] += (g is False) if st != "U" else (g is True)
        comp = sum(1 for q, rel, doc, g in R if g is True) - c["U"][1]
        lines.append(f"| {name} | {n} | {v} | {len(R)} | {c['V'][0]} ({c['V'][1]}) | {c['Q'][0]} ({c['Q'][1]}) | {c['U'][0]} ({c['U'][1]}) | "
                     f"{comp} ({comp / n:.3f}) | {c['V'][1]}-{c['V'][1] + c['Q'][1]} |")
    print(lines[-3:], flush=True)
out = ROOT / "results/runs/l3/accounting.md"
prev = out.read_text(encoding="utf-8").splitlines()[2:] if out.exists() else []
out.write_text("\n".join(lines[:2] + [l for l in prev if not any(l.startswith(f"| {s} |") for s in sys.argv[1:])] + lines[2:]), encoding="utf-8")
print("\n".join(lines))
