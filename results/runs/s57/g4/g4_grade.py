"""S57 G4 second design check: grade the releases of the S39 Mintaka design items with the alias-aware grader (27B judge per alias, veto as grader 6.1/S21),
and report rule variants Q1c+T and Q2 (Q1c+T and reader support at least 2). 27B on 11540: python -B results/runs/s57/g4/g4_grade.py"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20"), str(ROOT / "results/runs/s22"), str(ROOT / "results/runs/s57/g4")]
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540"); os.environ["G4SET"] = "s39"
import no_retrieval2  # noqa: F401
from g4_subject import releases
from vkg.grade_judge import judge
from vkg.grade6 import veto
from vkg.s21_judge import aliases
from scipy.stats import beta
D = ROOT / "results/runs/s57/g4"; CF = D / "g4_grade_cache.json"
C = json.load(open(CF, encoding="utf-8")) if CF.exists() else {}
J = json.load(open(D / "g4_judge.json", encoding="utf-8"))
gold = {json.loads(l)["id"]: json.loads(l)["gold"] for l in open(D / "s39_mintaka_outputs.jsonl", encoding="utf-8")}
rows = []
for r, c, s in releases("s39_mintaka", J):
    ok = False
    for g in aliases(gold[r["id"]]):
        k = f"{r['question']}|{g}|{c['answer']}"
        if k not in C:
            C[k] = judge(r["question"], g, c["answer"])
        if C[k] == "CORRECT" and not veto(r["question"], g, c["answer"]):
            ok = True; break
    rows.append((c["support"], ok, r["question"], c["answer"], gold[r["id"]][:2]))
json.dump(C, open(CF, "w", encoding="utf-8"), ensure_ascii=False)
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k)
n = 600; out = ["# S57 G4 second design check: S39 Mintaka design items (600), gold-relative", "", "| variant | released | coverage | wrong (gold) | SER | upper |", "|---|---|---|---|---|---|"]
for var, m in (("Q1c+T", 1), ("Q2 (support >= 2)", 2)):
    sel = [x for x in rows if x[0] >= m]; wr = sum(not x[1] for x in sel)
    out.append(f"| {var} | {len(sel)} | {100*len(sel)/n:.1f}% | {wr} | {100*wr/n:.2f}% | {up(wr, n):.2f}% |")
(D / "G4_design_s39_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
for x in rows:
    if not x[1] and x[0] >= 2:
        print("wrong:", x[2][:80], "|", x[3][:40], "|", x[4])
