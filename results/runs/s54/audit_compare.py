"""S54: compare an external reviewer's filled audit sheet with the two language-model reviewers (key). python -B audit_compare.py <filled.csv>
Reports: verdict counts, Cohen kappa (3 classes) against reviewer 1, reviewer 2 and the consensus where they agree, confusion by key kind,
and the share of 'both reviewers said not' rows the external reviewer also calls 'not' (misleading), and the decoys caught."""
import csv, json, sys, collections
from pathlib import Path
D = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
key = json.load(open(D / "human_audit_key.json", encoding="utf-8"))
V = ["states", "incomplete", "not"]
ext = {int(r["row"]): r["verdict (states / incomplete / not)"].strip().lower() for r in rows}
assert len(ext) == 180 and set(ext.values()) <= set(V), collections.Counter(ext.values())
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in V)
    return po, (po - pe) / (1 - pe)
out = ["# Audit sheet: external reviewer against the two language-model reviewers\n", f"Verdict counts: {dict(collections.Counter(ext.values()))}\n"]
e = [ext[k["row"]] for k in key]
for name, idx in (("reviewer 1", 0), ("reviewer 2", 1)):
    l = [k["labels"][idx] for k in key]
    ok = [(x, y) for x, y in zip(e, l) if y in V]
    po, ka = kappa([x for x, _ in ok], [y for _, y in ok]); out.append(f"{name}: n={len(ok)}, agreement {po:.3f}, Cohen kappa {ka:.3f}\n")
ag = [(ext[k["row"]], k["labels"][0]) for k in key if k["labels"][0] == k["labels"][1] and k["labels"][0] in V]
po, ka = kappa([x for x, _ in ag], [y for _, y in ag]); out.append(f"Rows where the two LM reviewers agree: n={len(ag)}, agreement {po:.3f}, kappa {ka:.3f}\n")
out.append("\nBy key kind (rows; external verdicts states/incomplete/not):\n")
for kind in ["not", "states", "incomplete", "split", "decoy"]:
    c = collections.Counter(ext[k["row"]] for k in key if k["kind"] == kind)
    out.append(f"- {kind}: {sum(c.values())} rows; states {c['states']}, incomplete {c['incomplete']}, not {c['not']}\n")
# binary: misleading (not) vs not misleading
nn = [k for k in key if k["labels"] == ["not", "not"]]
out.append(f"\nRows where both LM reviewers said 'not' (incl. decoys): {len(nn)}; external also 'not': {sum(ext[k['row']]=='not' for k in nn)} ({sum(ext[k['row']]=='not' for k in nn)/len(nn):.1%}).\n")
ss = [k for k in key if k["labels"] == ["states", "states"]]
out.append(f"Rows where both said 'states': {len(ss)}; external 'states' {sum(ext[k['row']]=='states' for k in ss)}, 'not' {sum(ext[k['row']]=='not' for k in ss)}.\n")
dec = [k for k in key if k["kind"] == "decoy"]
out.append(f"Decoys (answer of another row): {len(dec)}; external 'not' {sum(ext[k['row']]=='not' for k in dec)}.\n")
# binary kappa: 'not' vs other, for each reviewer
for name, idx in (("reviewer 1", 0), ("reviewer 2", 1)):
    ok = [k for k in key if k["labels"][idx] in V]
    a = ["not" if ext[k["row"]] == "not" else "ok" for k in ok]; b = ["not" if k["labels"][idx] == "not" else "ok" for k in ok]
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; pe = sum((a.count(c) / n) * (b.count(c) / n) for c in ("not", "ok"))
    out.append(f"Binary (not vs not-not) {name}: agreement {po:.3f}, kappa {(po-pe)/(1-pe):.3f}\n")
dis = [(k["row"], k["kind"], k["labels"], ext[k["row"]]) for k in key if k["labels"][0] == k["labels"][1] and k["labels"][0] != ext[k["row"]]]
out.append(f"\nRows where the LMs agree and the external reviewer differs: {len(dis)}\n")
(D / "Audit_external_result.md").write_text("".join(out), encoding="utf-8")
json.dump(dis, open(D / "audit_external_disagreements.json", "w"))
print("".join(out))
