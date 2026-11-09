"""CPU-only dry run requested by the S22 session: frozen qualified.decide (strict) on mintaka_test_releases.jsonl.
Reads results/runs/s22 only; writes results/runs/l3/dryrun_strict29.md"""
import json, re, sys
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3"))
from qualified import decide
S = ROOT / "results/runs/s22"
key = {k["row"]: k["id"] for k in json.load(open(S / "mintaka_test_adj_key.json", encoding="utf-8")) if k["kind"] == "system"}
kept = {}
for l in open(S / "mintaka_test_adj_result_strict.md", encoding="utf-8"):
    m = re.match(r"- r(\d+) (.*?) \| .*\*\*(.+?)\*\*", l)
    if m and m.group(3) in ("answer wrong", "ambiguous question", "cannot tell"):
        kept[key[int(m.group(1))]] = (m.group(1), m.group(3))
rels = [json.loads(l) for l in open(S / "mintaka_test_releases.jsonl", encoding="utf-8")]
out = [f"# Dry run: frozen qualified.decide (strict) on mintaka_test releases ({len(rels)}); kept strict-adjudicated errors: {len(kept)}", ""]
c = Counter(); rows = []
for r in rels:
    st, sense, info = decide(r["question"], r["answer"], r["release_doc"], strict=True)
    if r["id"] in kept:
        c[("kept", st)] += 1; rows.append((kept[r["id"]], r, st, sense))
    else:
        c[("other", st, r["grade"] is True)] += 1
out += ["## the kept errors", "", "| state | n |", "|---|---|"] + [f"| {s} | {c[('kept', s)]} |" for s in ("Verified", "Qualified", "Unresolved")]
out += ["", "| row | verdict | question | answer | state | stated sense |", "|---|---|---|---|---|---|"]
for (row, v), r, st, sense in sorted(rows, key=lambda x: int(x[0][0])):
    out.append(f"| r{row} | {v} | {r['question'][:60]} | {r['answer'][:30]} | {st} | {sense or ''} |")
n_other = sum(v for k, v in c.items() if k[0] == "other")
out += ["", f"## cost on the other {n_other} releases", "", "| state | graded correct | graded not-true |", "|---|---|---|"]
for s in ("Verified", "Qualified", "Unresolved"):
    out.append(f"| {s} | {c[('other', s, True)]} | {c[('other', s, False)]} |")
Path(ROOT / "results/runs/l3/dryrun_strict29.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
