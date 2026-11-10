"""S57 G6 + G6b: one blind sheet of every C2' chain of both batches plus 30 decoys per batch (country swapped within the batch), 3 parts; and the unblinding
(union and G6 alone). python -B results/runs/s57/g6_union.py sheet | unblind"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s57"
if sys.argv[1] == "sheet":
    rng = random.Random(5713); rows = []
    for b in ("g6", "g6b"):
        c2 = [i for i in json.load(open(D / b / "g6_out.json", encoding="utf-8")) if i.get("accepted")]
        rows += [dict(kind="accepted", b=b, i=i, a=i["country"]) for i in c2]
        for _ in range(30):
            i = rng.choice(c2); rows.append(dict(kind="decoy", b=b, i=i, a=rng.choice([x["country"] for x in c2 if x["country"].casefold() != i["country"].casefold()])))
    rng.shuffle(rows); key = {}
    for p in range(3):
        part = rows[p::3]
        with open(D / f"G6_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["row", "question", "answer", "page_1", "quote_1", "page_2", "quote_2"])
            for n, r in enumerate(part, 1):
                i = r["i"]; w.writerow([n, f"In which country was {i['person']} born?", r["a"], i["wit"]["doc"], i["wit"]["quote"], i["place"], i["s2"]])
        key[str(p + 1)] = [{"row": n, "id": r["i"]["id"], "batch": r["b"], "kind": r["kind"]} for n, r in enumerate(part, 1)]
    json.dump(key, open(D / "G6_key.json", "w"))
    print("sheet rows", len(rows), [len(rows[p::3]) for p in range(3)])
else:
    from scipy.stats import beta
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
    K = json.load(open(D / "G6_key.json")); A, Dc = [], []
    for p, ks in K.items():
        vs = {}
        for rv in "AB":
            for r in csv.DictReader(open(D / f"G6_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
                vs.setdefault(int(r["row"]), []).append((r["chain_verdict"].strip().casefold(), r["true_verdict"].strip().casefold()))
        for k in ks:
            assert len(vs[k["row"]]) == 2, (p, k)
            (Dc if k["kind"] == "decoy" else A).append((k["batch"], vs[k["row"]]))
    def line(name, X):
        n = len(X); mis = sum(a[0] == b[0] == "not" for _, (a, b) in X); fal = sum(a[1] == b[1] == "wrong" for _, (a, b) in X); st = sum(a[0] == b[0] == "states" for _, (a, b) in X)
        return f"| {name} | {n} | {mis} ({100*mis/max(1,n):.1f}%, upper {up(mis,n):.1f}%) | {fal} ({100*fal/max(1,n):.1f}%, upper {up(fal,n):.1f}%) | {st} ({100*st/max(1,n):.1f}%) |"
    dec = sum((a[0] == b[0] == "not") or (a[1] == b[1] == "wrong") for _, (a, b) in Dc)
    out = ["# S57 gate G6: chain rule C2' on fresh two-hop items, G6 and G6b (blind review)", "",
           f"Decoys (country swapped) misleading or wrong for both reviewers: {dec}/{len(Dc)} ({'VALID' if dec >= 0.9 * len(Dc) else 'INVALID'}; criterion at least 27 of 30 per batch).", "",
           "| Rows | n | misleading for both (chain 'not') | country wrong for both | 'states' for both |", "|---|---|---|---|---|",
           line("Accepted chains, G6 and G6b", A), line("Accepted chains, G6 alone", [x for x in A if x[0] == "g6"]), line("Accepted chains, G6b alone", [x for x in A if x[0] == "g6b"])]
    for b in ("g6", "g6b"):
        db = [x for x in Dc if x[0] == b]; out.append(f"\nDecoys {b}: {sum((a[0] == bb[0] == 'not') or (a[1] == bb[1] == 'wrong') for _, (a, bb) in db)}/{len(db)}")
    (D / "G6_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
