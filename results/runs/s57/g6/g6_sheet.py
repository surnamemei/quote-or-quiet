"""S57 G6: blind sheet of every C2' chain plus 30 decoys (country swapped), split in 3 parts; and the unblinding.
python -B results/runs/s57/g6/g6_sheet.py sheet | unblind"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s57/g6"
if sys.argv[1] == "sheet":
    I = json.load(open(D / "g6_out.json", encoding="utf-8")); c2 = [i for i in I if i.get("accepted")]
    rng = random.Random(5709); rows = [dict(kind="accepted", i=i, a=i["country"]) for i in c2]
    for _ in range(30):
        i = rng.choice(c2); rows.append(dict(kind="decoy", i=i, a=rng.choice([x["country"] for x in c2 if x["country"].casefold() != i["country"].casefold()])))
    rng.shuffle(rows); key = {}
    for p in range(3):
        part = rows[p::3]
        with open(D / f"G6_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["row", "question", "answer", "page_1", "quote_1", "page_2", "quote_2"])
            for n, r in enumerate(part, 1):
                i = r["i"]; w.writerow([n, f"In which country was {i['person']} born?", r["a"], i["wit"]["doc"], i["wit"]["quote"], i["place"], i["s2"]])
        key[str(p + 1)] = [{"row": n, "id": r["i"]["id"], "kind": r["kind"]} for n, r in enumerate(part, 1)]
    json.dump(key, open(D / "G6_key.json", "w"))
    print("accepted chains", len(c2), "| sheet rows", len(rows), [len(rows[p::3]) for p in range(3)])
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
            (Dc if k["kind"] == "decoy" else A).append(vs[k["row"]])
    n = len(A); mis = sum(a[0] == b[0] == "not" for a, b in A); fal = sum(a[1] == b[1] == "wrong" for a, b in A); st = sum(a[0] == b[0] == "states" for a, b in A)
    dec = sum((a[0] == b[0] == "not") or (a[1] == b[1] == "wrong") for a, b in Dc)
    out = ["# S57 gate G6: chain rule C2' on fresh two-hop items (blind review)", "",
           f"Decoys (country swapped) misleading or wrong for both reviewers: {dec}/{len(Dc)} ({'VALID' if dec >= 27 else 'INVALID'}).", "",
           "| Rows | n | misleading for both (chain 'not') | country wrong for both | 'states' for both |", "|---|---|---|---|---|",
           f"| Accepted chains | {n} | {mis} ({100*mis/max(1,n):.1f}%, upper {up(mis,n):.1f}%) | {fal} ({100*fal/max(1,n):.1f}%, upper {up(fal,n):.1f}%) | {st} ({100*st/max(1,n):.1f}%) |"]
    (D / "G6_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
