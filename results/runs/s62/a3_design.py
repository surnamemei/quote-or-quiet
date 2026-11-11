"""S62 design (after the S62 result; design data only): an attribution question for the 27B on the witness sentences of the 300 reviewed kept statements.
Rule A3 candidate = A2 and YES to AP below. Reports misleading / other party among the statements A3 would keep. 27B on 11540: python -B results/runs/s62/a3_design.py"""
import csv, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
from vkg.llm import chat
from scipy.stats import beta
D = ROOT / "results/runs/s62"
AP = ('Sentence: "{s}"\n\nStatement: {a}\n\nThe statement says that a particular party holds a view. Does the sentence itself say that this same party holds, states or argues this view? '
      "Answer NO if the sentence states the view as a plain fact without saying who holds it, if it names a different person or body, or if it only covers part of the view. Reply with only YES or NO.")
S = {json.loads(l)["id"]: json.loads(l) for l in open(D / "e12_cands.jsonl", encoding="utf-8")}; Dec = json.load(open(D / "a2_decisions.json")); K = json.load(open(D / "A2_key.json"))
PF = D / "a3_design.json"; R = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
rows = []
for p, ks in K.items():
    V = {}
    for rv in "AB":
        for r in csv.DictReader(open(D / f"A2_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            V.setdefault(int(r["row"]), []).append(r["verdict"].strip().lower())
    for k in ks:
        if k["kind"] != "witness":
            continue
        s = S[k["id"]]; q = s["cands"][Dec[k["id"]]]["quote"]
        if k["id"] not in R:
            R[k["id"]] = str(chat("qwen3.8-27b", [{"role": "user", "content": AP.format(s=q, a=s["stmt"])}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))
        rows.append((R[k["id"]].strip().upper().startswith("YES"), V[k["row"]]))
json.dump(R, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k)
for name, sel in (("A2 (all reviewed)", rows), ("A3: A2 and attribution YES", [r for r in rows if r[0]]), ("dropped by A3", [r for r in rows if not r[0]])):
    n = len(sel); m = sum(v[0] != "states" and v[1] != "states" for _, v in sel); a = sum(v[0] in ("other party", "opposite") and v[1] in ("other party", "opposite") for _, v in sel)
    print(f"{name}: n {n}, misleading {m} ({100*m/max(1,n):.1f}%, upper {up(m, n) if n else 0:.1f}%), other party/opposite {a}")
