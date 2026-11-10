"""S54: a larger prompted judge (Qwen3.8-27B through Ollama on OLLAMA_HOST_URL) on the same held-out rows as S51 (results/runs/s51/d_pred.json) and on the Mintaka review rows of S52,
with the YES/NO prompt of rule R (no swap control). Compared with the 4B prompt judge and the small trained judge. python -B results/runs/s54/j27.py"""
import csv, json, os, sys, time
from pathlib import Path
import numpy as np
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
from vkg.llm import chat   # noqa: E402
D = ROOT / "results/runs/s54"
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
P = json.load(open(ROOT / "results/runs/s51/d_pred.json", encoding="utf-8"))
J4 = json.load(open(ROOT / "results/runs/s51/d_judge.json", encoding="utf-8"))
rows = [{"set": "heldout", "t": r["title"], "s": r["quote"], "q": r["question"], "a": r["answer"], "y": r["y"], "bad": int(r["label"] == "not"), "p": r["p"], "j4": str(j).strip().upper().startswith("YES")} for r, j in zip(P, J4)]
M = []
for p in (1, 2, 3):
    S = {int(r["row"]): r for r in csv.DictReader(open(ROOT / f"results/runs/s52/M_sheet_part{p}.csv", encoding="utf-8-sig"))}
    V = {rv: {int(r["row"]): r["quote_verdict"].strip().casefold() for r in csv.DictReader(open(ROOT / f"results/runs/s52/M_verdict_part{p}_{rv}.csv", encoding="utf-8-sig"))} for rv in "AB"}
    for k in json.load(open(ROOT / "results/runs/s52/M_key.json"))[str(p)]:
        r = S[k["row"]]; a, b = V["A"][k["row"]], V["B"][k["row"]]
        if k["kind"] != "decoy":
            rows.append({"set": "mintaka", "t": r["page_title"], "s": r["quote"], "q": r["question"], "a": r["answer"], "y": int(a == b == "states"), "bad": int(a == b == "not"), "p": None, "j4": None})
done = json.load(open(D / "j27_part.json", encoding="utf-8")) if (D / "j27_part.json").exists() else []
t0 = time.time()
while len(done) < len(rows):
    r = rows[len(done)]
    for t in range(20):
        try:
            o = chat("qwen3.8-27b", [{"role": "user", "content": JP.format(t=r["t"], s=r["s"], q=r["q"], a=r["a"])}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=600)
            break
        except Exception as e:
            print("retry", t, repr(e)[:100], flush=True); time.sleep(30)
    else:
        raise SystemExit("gave up")
    done.append(str(o).strip().upper().startswith("YES"))
    if len(done) % 100 == 0:
        json.dump(done, open(D / "j27_part.json", "w")); print(len(done), "of", len(rows), f"{time.time()-t0:.0f}s", flush=True)
json.dump(done, open(D / "j27_part.json", "w"))
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
out = ["# S54: a 27B prompted judge against the 4B prompted judge and the small trained judge", "",
       "| Set | Judge | accepted | not 'states' (held-out) or misleading (Mintaka) among accepted |", "|---|---|---|---|"]
for st in ("heldout", "mintaka"):
    idx = [i for i, r in enumerate(rows) if r["set"] == st]
    y = np.array([rows[i]["y"] for i in idx]); bad = np.array([rows[i]["bad"] for i in idx]); j27 = np.array([done[i] for i in idx])
    measure = (1 - y) if st == "heldout" else bad
    cols = [("27B prompt", j27)]
    if st == "heldout":
        cols += [("4B prompt", np.array([rows[i]["j4"] for i in idx])), ("small judge 0.5", np.array([rows[i]["p"] >= 0.5 for i in idx]))]
    for name, a in cols:
        n = int(a.sum()); b = int(measure[a].sum())
        out.append(f"| {st} (n={len(idx)}) | {name} | {n} ({100*n/len(idx):.1f}%) | {b} ({100*b/max(1,n):.1f}%, upper {up(b,n):.1f}%) |")
(D / "J27_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
