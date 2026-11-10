"""E11 post hoc revision (once): which extra lexical check removes the misleading or false kept slots of the reviewed sample?
COV = share of the value's content words that occur in the quote; vague = slot type OTHER, fact or role.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s43/e11_refine.py"""
import csv, json, re, unicodedata
from pathlib import Path
from scipy.stats import beta
D = Path(__file__).parent
STOP = set("a an the of in on at to for from by with and or but is are was were be been being he she it they his her their its this that these those as has have had not no also which who whom whose when where what how into than then there here after before during over under about between".split())
def fold(s): return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).casefold()
def toks(s): return re.findall(r"[a-z0-9]+", fold(s))
def cw(s): return {w for w in toks(s) if w not in STOP and len(w) > 2}
def up(k, n): return 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
S = {s["id"]: s for s in map(json.loads, open(D / "e11_cands.jsonl", encoding="utf-8"))}
K = json.load(open(D / "E11_key.json", encoding="utf-8"))
rows = []
for p, ks in K.items():
    V = {}
    for rv in "AB":
        for r in csv.DictReader(open(D / f"E11_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            V.setdefault(int(r["row"]), []).append((r["quote_verdict"].strip().casefold(), r["true_verdict"].strip().casefold()))
    for k in ks:
        if k["kind"] != "kept":
            continue
        v = V[k["row"]]; s = S[k["id"]]; q = s["cands"][k["k"]]["quote"]
        vw = cw(s["value"])
        rows.append(dict(false=[b for _, b in v] == ["wrong", "wrong"], mis=[a for a, _ in v] == ["not", "not"], cov=len(vw & cw(q)) / max(1, len(vw)),
                         vague=s["type"] in ("OTHER", "fact", "role"), states=[a for a, _ in v] == ["states", "states"]))
n = len(rows); print("kept reviewed", n)
def rep(name, f):
    ps = [r for r in rows if f(r)]; k = sum(r["false"] for r in ps); m = sum(r["mis"] for r in ps); st = sum(r["states"] for r in ps)
    print(f"{name}: passes {len(ps)} ({100*len(ps)/n:.0f}%) | false {k} ({100*k/len(ps):.1f}%, upper {up(k,len(ps)):.1f}) | misleading {m} ({100*m/len(ps):.1f}%, upper {up(m,len(ps)):.1f}) | states {100*st/len(ps):.0f}%")
rep("all", lambda r: True)
for t in (0.5, 0.75, 1.0):
    rep(f"cov>={t}", lambda r, t=t: r["cov"] >= t)
rep("not vague", lambda r: not r["vague"])
for t in (0.5, 0.75, 1.0):
    rep(f"not vague & cov>={t}", lambda r, t=t: (not r["vague"]) and r["cov"] >= t)
