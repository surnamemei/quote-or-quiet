"""Unblind S42 E4 (docs/S42_CLAIM_AUDIT_AND_PLAN.md): wrong rate among Verified sibling items against the 3-10% prediction, the control
arm, decoy validity, the effect of the frame check on both arms, whether wrong releases repeat the original relation's answer, and the
kept E2 claims. An item is an error when both reviewers say 'wrong' (same convention as S41).
python -B results/runs/s42/e4_unblind.py"""
import csv, json, sys
from collections import Counter, defaultdict
from pathlib import Path
from scipy.stats import beta
sys.stdout.reconfigure(encoding="utf-8")
D = Path(__file__).parent
K = json.load(open(D / "E4_key.json", encoding="utf-8"))
X = {x["id"]: x for x in (json.loads(l) for l in open(D / "e4_out.jsonl", encoding="utf-8"))}
A = list(X.values())


def up(k, n):
    return 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0


def same(a, b):
    a, b = str(a).casefold().strip(), str(b).casefold().strip()
    return bool(a and b and (a in b or b in a))


rows = []
for p, ks in K.items():
    V = {}
    for rv in ("A", "B"):
        for x in csv.DictReader(open(D / f"E4_verdict_part{p}_{rv}.csv", encoding="utf-8")):
            V.setdefault(int(x["row"]), []).append(x["verdict"].strip().strip("'\"").casefold())
    for k in ks:
        v = V[k["row"]]
        rows.append({**k, "v": v, "err": v == ["wrong", "wrong"], "either": "wrong" in v, "x": X.get(k["id"])})
out = ["# S42 E4: questions built to mislead the reader", ""]
for arm in ("sibling", "control"):
    a = [x for x in A if x["arm"] == arm]; c = Counter(x["state"] for x in a)
    fr = sum(1 for x in a if x["state"] == "Verified" and x["frame_ok"])
    out.append(f"{arm}: n {len(a)}; Verified {c['Verified']} ({100*c['Verified']/len(a):.1f}%), Qualified {c['Qualified']} ({100*c['Qualified']/len(a):.1f}%), "
               f"Unresolved {c['Unresolved']} ({100*c['Unresolved']/len(a):.1f}%); Verified that pass the frame check {fr} ({100*fr/len(a):.1f}%).")
dec = [r for r in rows if r["kind"] == "decoy"]; nd = sum(r["err"] for r in dec)
out += ["", f"Decoys called wrong by both reviewers: {nd}/{len(dec)} ({'VALID' if nd >= 0.9 * len(dec) else 'INVALID'}); by reviewer A {sum(r['v'][0] == 'wrong' for r in dec)}, B {sum(r['v'][1] == 'wrong' for r in dec)}.", ""]
out += ["| Arm | System | Reviewed releases | Wrong (both) | Rate | 97.5% upper | Wrong (either) |", "|---|---|---|---|---|---|---|"]
for arm in ("sibling", "control"):
    R = [r for r in rows if r["kind"] == arm]
    for name, sel in (("without frame check", R), ("with frame check", [r for r in R if r["x"]["frame_ok"]])):
        k, n = sum(r["err"] for r in sel), len(sel)
        out.append(f"| {arm} | {name} | {n} | {k} | {100*k/max(1,n):.1f}% | {up(k,n):.1f}% | {sum(r['either'] for r in sel)} |")
sib = [r for r in rows if r["kind"] == "sibling"]
out += ["", "Sibling arm by type (releases, wrong by both; with frame check in brackets):", ""]
bt = defaultdict(lambda: [0, 0, 0, 0])
for r in sib:
    t = bt[r["type"]]; t[0] += 1; t[1] += r["err"]
    if r["x"]["frame_ok"]:
        t[2] += 1; t[3] += r["err"]
tot = Counter(x["type"] for x in A if x["arm"] == "sibling")
out += [f"- {t}: {v[0]}/{tot[t]} released, {v[1]} wrong [{v[2]} released, {v[3]} wrong]" for t, v in sorted(bt.items())]
wr = [r for r in sib if r["err"]]
rep = [r for r in wr if same(r["answer"], r["x"].get("source_answer")) or same(r["answer"], r["x"].get("source_gold"))]
out += ["", f"Wrong sibling releases that repeat the original relation's answer: {len(rep)}/{len(wr)}.",
        f"Frame check on wrong sibling releases: removes {sum(1 for r in wr if not r['x']['frame_ok'])}/{len(wr)}; on the other reviewed sibling releases: removes {sum(1 for r in sib if not r['err'] and not r['x']['frame_ok'])}/{len(sib)-len(wr)}.",
        "", "Wrong for both reviewers (sibling):", ""]
out += [f"- {r['question']} | {r['answer']} | frame_ok {r['x']['frame_ok']} | original answer {r['x'].get('source_answer')} | quote: {r['x']['quote'][:160]}" for r in wr]
out += ["", "Wrong for one reviewer (sibling):", ""] + [f"- {r['question']} | {r['answer']} | {r['v']} | frame_ok {r['x']['frame_ok']}" for r in sib if r["either"] and not r["err"]]
out += ["", "Wrong for at least one reviewer (control):", ""] + [f"- {r['question']} | {r['answer']} | {r['v']} | frame_ok {r['x']['frame_ok']}" for r in rows if r["kind"] == "control" and r["either"]]
e2 = [r for r in rows if r["kind"] == "e2"]
out += ["", f"E2 kept gold-wrong claims, blind review: {len(e2)} rows; wrong for both {sum(r['err'] for r in e2)}, for either {sum(r['either'] for r in e2)}.", ""]
out += [f"- {r['question']} | {r['answer']} | {r['v']}" for r in e2]
(D / "E4_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out[:16]))
