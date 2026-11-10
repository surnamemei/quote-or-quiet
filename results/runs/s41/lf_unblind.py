"""Unblind S41 (docs/S41_LONGFORM_E2E_PLAN.md): retention, false-kept rate (both reviewers), cluster bootstrap by biography. python -B results/runs/s41/lf_unblind.py"""
import csv, json, random
from collections import Counter, defaultdict
from pathlib import Path
D = Path(__file__).parent
K = json.load(open(D / "S41_key.json", encoding="utf-8"))
X = [json.loads(l) for l in open(D / "verified.jsonl", encoding="utf-8")]
rows = []
for p in ("1", "2"):
    V = {}
    for rv in ("A", "B"):
        for x in csv.DictReader(open(D / f"S41_verdict_part{p}_{rv}.csv", encoding="utf-8")):
            V.setdefault(int(x["row"]), []).append(x["verdict"].strip().strip("'\"").casefold())
    for k in K[p]:
        v = V[k["row"]]
        rows.append({**k, "v": v, "err": v == ["wrong", "wrong"], "either": "wrong" in v})
dec = [r for r in rows if r["kind"] == "decoy"]; nd = sum(r["err"] for r in dec)
kept = [r for r in rows if r["kind"] == "kept"]; dr = [r for r in rows if r["kind"] == "dropped"]
k = sum(r["err"] for r in kept); n = len(kept)
by = defaultdict(lambda: [0, 0])
for r in kept:
    by[r["person"]][0] += 1; by[r["person"]][1] += r["err"]
people = sorted({x["person"] for x in X}); rng = random.Random(41); bs = []
for _ in range(10000):
    s = [rng.choice(people) for _ in people]
    a = sum(by[q][0] for q in s); b = sum(by[q][1] for q in s)
    bs.append(b / a if a else 0)
bs.sort()
tk = Counter(x["type"] for x in X if x["keep"]); ta = Counter(x["type"] for x in X)
out = ["# S41: long-form end-to-end on the design biographies", "",
       f"Slots {len(X)}; kept {n} (retention {100*n/len(X):.1f}%); biographies with at least one kept slot {sum(1 for q in people if by[q][0])}/50.",
       f"Funnel: reader support {sum(x['support'] for x in X)}, gate {sum(x['gate'] for x in X)}, Phi-4 agrees (kept) {n}.",
       f"Decoys called wrong by both: {nd}/{len(dec)} ({'VALID' if nd >= 18 else 'INVALID'}). Random dropped slots called wrong by both: {sum(r['err'] for r in dr)}/{len(dr)}, by either {sum(r['either'] for r in dr)}.",
       f"False kept (both reviewers): {k}/{n} = {100*k/max(1,n):.1f}%; cluster-bootstrap 97.5% upper {100*bs[int(0.975*len(bs))]:.1f}%; wrong by either {sum(r['either'] for r in kept)}.",
       "", "Retention by type (types with at least 20 slots):", ""]
ql = [r for r in rows if r["kind"] == "qualified"]
if ql:
    out[6:6] = [f"Rule Q (secondary): reviewed Qualified slots {len(ql)}; value called wrong by both {sum(r['err'] for r in ql)}, by either {sum(r['either'] for r in ql)}, "
                f"correct for both {sum(all(v.startswith('correct') for v in r['v']) for r in ql)}."]
out += [f"- {t}: {tk[t]}/{c} ({100*tk[t]/c:.0f}%)" for t, c in ta.most_common() if c >= 20]
out += ["", "False kept (both):", ""] + [f"- [{r['person']}] {r['question']} | {r['answer']} | {r['v']}" for r in kept if r["err"]]
out += ["", "Wrong by one reviewer:", ""] + [f"- [{r['person']}] {r['question']} | {r['answer']} | {r['v']}" for r in kept if r["either"] and not r["err"]]
(D / "S41_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out[:8]))
