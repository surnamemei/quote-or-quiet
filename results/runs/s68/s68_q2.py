"""S58 gate G4 (docs/S58_G4_PLAN.md): rule Q2 decisions on the sealed Mintaka set, grading, adjudication sheet and unblinding.
  decide : 27B on 11540 for grading. python -B results/runs/s68/s68_q2.py decide
  sheet  : CPU.  python -B results/runs/s68/s68_q2.py sheet
  unblind: CPU.  python -B results/runs/s68/s68_q2.py unblind"""
import csv, json, os, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20"), str(ROOT / "results/runs/s22")]
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
D = ROOT / "results/runs/s68"; G = ROOT / "results/runs/s57/g4"; MODE = sys.argv[1]
TPLUS = re.compile(r"\b(this|last|next)\s+(year|season|month|week)\b|\brecent(ly)?\b|\bupcoming\b", re.I)
from scipy.stats import beta
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if k < n else 100.0

if MODE == "decide":
    import no_retrieval2  # noqa: F401
    from temporal import time_sensitive
    from vkg.grade_judge import judge
    from vkg.grade6 import veto
    from vkg.s21_judge import aliases
    J = json.load(open(G / "g4_judge.json", encoding="utf-8"))
    gold = {json.loads(l)["id"]: json.loads(l)["gold"] for l in open(D / "run_fsm/m68_outputs.jsonl", encoding="utf-8")}
    R = [json.loads(l) for l in open(G / "m68_cands.jsonl", encoding="utf-8")]
    assert len(R) == 1500
    CF = D / "s68_grade_cache.json"; C = json.load(open(CF, encoding="utf-8")) if CF.exists() else {}
    out = []
    for r in R:
        w = [(ci, [si for si in range(len(c["spans"])) if J.get(f"{r['id']}|{ci}|{si}", {}).get("w")]) for ci, c in enumerate(r["cands"])]
        w = [(ci, s) for ci, s in w if s]
        why = "released"
        if not w: why = "no witness"
        elif len(w) > 1: why = "conflict"
        elif time_sensitive(r["question"]) or TPLUS.search(r["question"]): why = "time-sensitive"
        elif r["cands"][w[0][0]]["support"] < 2: why = "support 1"
        rec = {"id": r["id"], "why": why}
        if why == "released":
            ci, s = w[0]; c = r["cands"][ci]; sp = c["spans"][s[0]]
            ok = False
            for g in aliases(gold[r["id"]]):
                k = f"{r['question']}|{g}|{c['answer']}"
                if k not in C:
                    C[k] = judge(r["question"], g, c["answer"])
                if C[k] == "CORRECT" and not veto(r["question"], g, c["answer"]):
                    ok = True; break
            rec.update({"answer": c["answer"], "doc": sp["doc"], "quote": sp["quote"], "gold_ok": ok})
        out.append(rec)
    json.dump(C, open(CF, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(out, open(D / "s68_decisions.json", "w", encoding="utf-8"), ensure_ascii=False)
    from collections import Counter
    rel = [x for x in out if x["why"] == "released"]; wr = sum(not x["gold_ok"] for x in rel)
    print("reasons", dict(Counter(x["why"] for x in out)), "| released", len(rel), f"coverage {100*len(rel)/1500:.1f}%", "| gold-wrong", wr, f"({100*wr/1500:.2f}% of questions)")

elif MODE == "sheet":
    X = json.load(open(D / "s68_decisions.json", encoding="utf-8")); rel = [x for x in X if x["why"] == "released"]
    Q = {json.loads(l)["id"]: json.loads(l) for l in open(D / "run_fsm/m68_outputs.jsonl", encoding="utf-8")}
    rng = random.Random(6803)
    bad = [x for x in rel if not x["gold_ok"]]; good = rng.sample([x for x in rel if x["gold_ok"]], 24)
    rows = [dict(kind="error", x=x, a=x["answer"]) for x in bad] + [dict(kind="correct", x=x, a=x["answer"]) for x in good]
    for x in rng.sample(good, 12):
        other = rng.choice([y for y in rel if y["id"] != x["id"]]); rows.append(dict(kind="decoy", x=x, a=other["answer"]))
    rng.shuffle(rows)
    with open(D / "G4_adj_sheet.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "gold_answers", "system_answer", "system_page", "system_quote"])
        for n, r in enumerate(rows, 1):
            w.writerow([n, Q[r["x"]["id"]]["question"], " | ".join(map(str, Q[r["x"]["id"]]["gold"][:4])), r["a"], r["x"]["doc"], r["x"]["quote"]])
    json.dump([{"row": n, "id": r["x"]["id"], "kind": r["kind"]} for n, r in enumerate(rows, 1)], open(D / "G4_adj_key.json", "w"))
    print("sheet rows", len(rows), "| gold-wrong releases", len(bad))

elif MODE == "unblind":
    X = json.load(open(D / "s68_decisions.json", encoding="utf-8")); rel = [x for x in X if x["why"] == "released"]
    K = json.load(open(D / "G4_adj_key.json")); V = {}
    for rv in "AB":
        for r in csv.DictReader(open(D / f"G4_adj_verdict_{rv}.csv", encoding="utf-8-sig")):
            V.setdefault(int(r["row"]), []).append((r["verdict"].strip().casefold(), r.get("quote_found", "").strip().casefold()))
    removed = lambda v: v[0] == "answer right" or (v[0] in ("gold wrong", "equally acceptable") and v[1] == "yes")   # S68: answer right (equivalent to the gold) clears, registered before the run
    err = [k for k in K if k["kind"] == "error"]; e = sum(not (removed(V[k["row"]][0]) and removed(V[k["row"]][1])) for k in err)
    dec = [k for k in K if k["kind"] == "decoy"]; dk = sum(V[k["row"]][0][0] == V[k["row"]][1][0] == "answer wrong" for k in dec)
    cor = [k for k in K if k["kind"] == "correct"]; cw = sum(V[k["row"]][0][0] == V[k["row"]][1][0] == "answer wrong" for k in cor)
    cov = len(rel) / 1500; valid = dk >= 11 and cw <= 2
    out = ["# S68 gate G4 (second test): rule Q2 on 1,500 sealed NQ-open questions", "",
           f"Released {len(rel)} of 1,500 (coverage {100*cov:.1f}%). Gold-wrong releases {len(err)} ({100*len(err)/1500:.2f}% of questions).",
           f"Adjudication: decoys kept as wrong by both {dk}/{len(dec)}; gold-matching releases called wrong by both {cw}/{len(cor)} ({'VALID' if valid else 'INVALID'}).",
           f"Adjudicated errors {e}: {100*e/1500:.2f}% of questions, 97.5% upper bound {up(e, 1500):.2f}%.",
           f"Gate G4 T: coverage >= 35% {'met' if cov >= 0.35 else 'NOT met'}; upper bound < 1% {'met' if up(e, 1500) < 1 else 'NOT met'}."]
    (D / "G4_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
