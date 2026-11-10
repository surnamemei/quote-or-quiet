"""S43 revision on the design set (once, as the plan allows): which extra checks would have removed the false or misleading kept slots?
Checks: SENT = quote is a sentence (not a table row, heading or list line, at least 40 characters);
NUM = every number, year or ordinal word of the question occurs in the quote (excluding those inside the subject name).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s43/s43_refine.py"""
import csv, json, os, re, sys
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s43"
S = {s["id"]: s for s in map(json.loads, open(D / "s43_cands.jsonl", encoding="utf-8"))}
K = json.load(open(D / "S43_key.json", encoding="utf-8"))
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
def up(k, n): return 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
rows = []
for p, ks in K.items():
    V = {}
    for rv in ("A", "B"):
        for r in csv.DictReader(open(D / f"S43_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            V.setdefault(int(r["row"]), []).append((r["quote_verdict"].strip().casefold(), r["true_verdict"].strip().casefold()))
    for k in ks:
        if k["kind"] == "kept":
            v = V[k["row"]]; s = S[k["id"]]; q = s["cands"][k["k"]]["quote"]
            name = set(re.findall(r"[a-z0-9]+", s["person"].casefold()))
            qt = set(re.findall(r"[a-z0-9]+", q.casefold()))
            need = [w for w in re.findall(r"[a-z0-9]+", s["question"].casefold()) if (re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD) and w not in name]
            rows.append({"false": [b for _, b in v] == ["wrong", "wrong"], "mis": [a for a, _ in v] == ["not", "not"],
                         "SENT": not q.lstrip().startswith(("#", "-", "*", "|", "=")) and len(q) >= 40,
                         "NUM": all(w in qt or re.sub(r"\D", "", w) in qt for w in need), "type": s["type"]})
n = len(rows); print("kept", n, "false", sum(r["false"] for r in rows), "misleading", sum(r["mis"] for r in rows))
for name, f in (("SENT", lambda r: r["SENT"]), ("NUM", lambda r: r["NUM"]), ("SENT+NUM", lambda r: r["SENT"] and r["NUM"])):
    ps = [r for r in rows if f(r)]; k = sum(r["false"] for r in ps); m = sum(r["mis"] for r in ps)
    print(f"{name}: passes {len(ps)} ({100*len(ps)/1492:.1f}% of 1,492) | false {k} ({100*k/len(ps):.1f}%, upper {up(k,len(ps)):.1f}%) | misleading {m} ({100*m/len(ps):.1f}%)")
