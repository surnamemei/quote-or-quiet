"""S71: agreement of the project's reviewers and judge with existing human labels (docs/S71_HUMAN_LABELS_PLAN.md). Not a human review of our own rows (gate G12 stays open).
VitaminC test (tals/vitaminc; human-written claims and Wikipedia evidence sentences with human labels SUPPORTS / REFUTES / NOT ENOUGH INFO; CC BY-SA 3.0).
  build  : 600 rows, 200 per label, seed 7101; blind sheet (claim, evidence) in 2 parts and a key.        python -B results/runs/s71/hl.py build
  judge  : the 27B judge with the project's prompt adapted to a claim (YES = the sentence states it).   python -B results/runs/s71/hl.py judge
  score  : agreement with the human labels (YES vs SUPPORTS; NO vs REFUTES or NOT ENOUGH INFO), false accepts (YES on a non-SUPPORTS row), false rejects, kappa; for reviewers and judge.
           python -B results/runs/s71/hl.py score"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; D = ROOT / "results/runs/s71"
sys.stdout.reconfigure(encoding="utf-8"); os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
JPC = ('Sentence: "{s}"\n\nClaim: {c}\n\nDoes this sentence state that the claim is true: the same subject, the same relation and the same value or time, '
       'not a different or opposite one? Reply with only YES or NO.')
if sys.argv[1] == "build":
    L = [json.loads(l) for l in open(ROOT / "data/external/vitaminc/test.jsonl", encoding="utf-8")]
    rng = random.Random(7101); rows = []
    for lab in ("SUPPORTS", "REFUTES", "NOT ENOUGH INFO"):
        rows += rng.sample([x for x in L if x["label"] == lab and 20 <= len(x["evidence"]) <= 600], 200)
    rng.shuffle(rows)
    for p in range(2):
        part = rows[p::2]
        with open(D / f"HL_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["row", "claim", "sentence"])
            for n, x in enumerate(part, 1):
                w.writerow([n, x["claim"], x["evidence"]])
    json.dump({str(p + 1): [{"row": n, "id": x["unique_id"], "label": x["label"], "claim": x["claim"], "evidence": x["evidence"]} for n, x in enumerate(rows[p::2], 1)] for p in range(2)}, open(D / "HL_key.json", "w", encoding="utf-8"))
    print("rows", len(rows), "per part", [len(rows[p::2]) for p in range(2)])
elif sys.argv[1] == "judge":
    sys.path.insert(0, str(ROOT))
    from vkg.llm import chat
    K = json.load(open(D / "HL_key.json", encoding="utf-8")); F = D / "hl_judge27.json"; J = json.load(open(F, encoding="utf-8")) if F.exists() else {}
    for p, ks in K.items():
        for k in ks:
            if k["id"] not in J:
                J[k["id"]] = str(chat("qwen3.8-27b", [{"role": "user", "content": JPC.format(s=k["evidence"], c=k["claim"])}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))
    json.dump(J, open(F, "w", encoding="utf-8")); print("judged", len(J))
else:
    K = json.load(open(D / "HL_key.json", encoding="utf-8")); rows = []
    V = {}
    for p in ("1", "2"):
        for rv in "AB":
            f = D / f"HL_verdict_part{p}_{rv}.csv"
            if f.exists():
                for r in csv.DictReader(open(f, encoding="utf-8-sig")):
                    V.setdefault((p, int(r["row"])), {})[rv] = r["verdict"].strip().casefold()
    J = json.load(open(D / "hl_judge27.json", encoding="utf-8")) if (D / "hl_judge27.json").exists() else {}
    for p, ks in K.items():
        for k in ks:
            v = V.get((p, k["row"]), {})
            rows.append({"label": k["label"], "A": v.get("A"), "B": v.get("B"), "j": (str(J[k["id"]]).strip().upper()[:3] if k["id"] in J else None)})
    def stats(name, pred):
        xs = [(r["label"] == "SUPPORTS", pred(r)) for r in rows if pred(r) is not None]
        if not xs:
            return f"| {name} | 0 | | | | |"
        n = len(xs); agree = sum(h == m for h, m in xs) / n
        fa = sum(m and not h for h, m in xs); nonsup = sum(not h for h, _ in xs); fr = sum(h and not m for h, m in xs); sup = sum(h for h, _ in xs)
        po = agree; pe = (sum(h for h, _ in xs) / n) * (sum(m for _, m in xs) / n) + (sum(not h for h, _ in xs) / n) * (sum(not m for _, m in xs) / n); ka = (po - pe) / (1 - pe)
        byl = {lab: sum(m for (h, m), r in zip(xs, [r for r in rows if pred(r) is not None]) if r["label"] == lab) for lab in ("REFUTES", "NOT ENOUGH INFO")}
        return f"| {name} | {n} | {agree:.3f} | {ka:.3f} | {fa} of {nonsup} ({100*fa/max(1,nonsup):.1f}%; REFUTES {byl['REFUTES']}, NEI {byl['NOT ENOUGH INFO']}) | {fr} of {sup} ({100*fr/max(1,sup):.1f}%) |"
    out = ["# S71: the project's reviewers and judge against human labels (VitaminC test, 600 rows, 200 per label)", "",
           "| reviewer | n | agreement | kappa | false accepts (says it states the claim; humans: not supports) | false rejects |", "|---|---|---|---|---|---|",
           stats("Claude reviewer A", lambda r: None if r["A"] is None else r["A"] == "states"),
           stats("Claude reviewer B", lambda r: None if r["B"] is None else r["B"] == "states"),
           stats("Claude pair, both 'states'", lambda r: None if r["A"] is None or r["B"] is None else (r["A"] == "states" and r["B"] == "states")),
           stats("27B judge (YES)", lambda r: None if r["j"] is None else r["j"].startswith("YES"))]
    (D / "HL_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
