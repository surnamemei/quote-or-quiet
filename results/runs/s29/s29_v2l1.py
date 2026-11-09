"""Item 9 of docs/SEALED_SET_DESIGN.md: L1 at V2's coverage. System = frozen releases + V2 added releases. Ablation = agreement score at the
strictest t whose releases reach V2's count, edge share interpolation (as s29_l1.py). Truth-relative errors from the L1, V2 and E4 reviews
(both reviewers 'wrong'); gold-correct answers count as correct (checked by the reviewed gold-correct samples).
Reports the original L1 (discordant binomial) and the revised L1-b (bootstrap 10,000, seed 0).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s29/s29_v2l1.py wd"""
import csv, json, os, random, sys
from pathlib import Path
from scipy.stats import binom
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402
from abstain_dev import grade  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans  # noqa: E402
name = sys.argv[1]
D = ROOT / "results/runs/s29/run_fsm"; R = ROOT / "results/runs/s29/review" / name
OTHERS = ("web_plain", "web_cautious", "wiki_plain", "wiki_cautious", "combo_cautious")
rows = {r["id"]: r for r in map(json.loads, open(D / f"{name}_outputs.jsonl", encoding="utf-8"))}
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_phi4.jsonl", encoding="utf-8"))}
S = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_releases.jsonl", encoding="utf-8"))}
G = {r["id"]: r["grade"] for r in map(json.loads, open(D / f"{name}_releases.jsonl", encoding="utf-8"))}
for x in map(json.loads, open(R / "V2_added.jsonl", encoding="utf-8")):
    if "V2" in x["rules"]:
        S[x["id"]] = x["answer"]; G[x["id"]] = x["grade"]
n = len(rows)
judged, err = set(), set()
def load(keyrows, files):
    V = {}
    for f in files:
        for x in csv.DictReader(open(f, encoding="utf-8")):
            V.setdefault(int(x["row"]), []).append(x["verdict"].strip().casefold())
    dec = []
    for k in keyrows:
        v = V[k["row"]]
        if k["kind"] == "decoy":
            dec.append(v == ["wrong", "wrong"]); continue
        key = (k["id"], k["answer"].strip().casefold()); judged.add(key)
        if v == ["wrong", "wrong"]:
            err.add(key)
    return dec
K = json.load(open(R / "key.json", encoding="utf-8")); KV = json.load(open(R / "V2_key.json", encoding="utf-8")); KE = json.load(open(R / "E4_key.json", encoding="utf-8"))
for p in ("1", "2"):
    load(K["L1"][p], [R / f"L1_verdict_part{p}_{r}.csv" for r in "AB"])
    load(KV[p], [R / f"V2_verdict_part{p}_{r}.csv" for r in "AB"])
dE = load(KE, [R / f"E4_verdict_{r}.csv" for r in "AB"])
out = [f"# S29 {name}: L1 at V2's coverage (item 9)", "", f"E4 decoys called wrong by both: {sum(dE)}/{len(dE)} ({'VALID' if sum(dE) >= len(dE) - 1 else 'INVALID'})"]
sc = {}
for i, r in rows.items():
    c = r.get("combo_plain")
    if ans(c):
        sc[i] = sum(1 for k in OTHERS if ans(r.get(k)) and agree(str(c), str(r[k]))) + int(bool(ans(phi.get(i))) and agree(str(c), str(phi.get(i))))
t = next(t for t in range(6, -1, -1) if sum(1 for v in sc.values() if v >= t) >= len(S))
top = sum(1 for v in sc.values() if v > t); edge = sum(1 for v in sc.values() if v == t); share = (len(S) - top) / edge
unj = []
Q = []
for i, r in rows.items():
    sr = i in S; se = False
    if sr and G[i] is False:
        key = (i, S[i].strip().casefold()); se = key in err
        if key not in judged: unj.append(("sys", key))
    cls = 0; be = False
    if i in sc:
        cls = 2 if sc[i] > t else (1 if sc[i] == t else 0)
        c = rows[i]["combo_plain"]
        if cls and grade(r["question"], r["gold"], c) is False:
            key = (i, str(c).strip().casefold()); be = key in err
            if key not in judged: unj.append(("base", key))
    Q.append((sr, se, cls, be))
out += [f"V2 releases {len(S)} (coverage {len(S)/n:.3f}); ablation t = {t}, above-edge {top}, edge {edge}, edge share {share:.4f}",
        f"Gold-wrong answers without a review verdict (counted as correct): {len(unj)} {unj[:10]}", ""]
rng = random.Random(0)
def stat(sample, rand=True):
    ds = dy = 0.0
    for sr, se, cls, be in sample:
        w = 1.0 if cls == 2 else ((1.0 if rng.random() < share else 0.0) if rand else share) if cls == 1 else 0.0
        ds += se - w * be; dy += (sr and not se) - w * (not be)
    return 100 * ds / len(sample), 100 * dy / len(sample)
pt = stat(Q, rand=False)
B = [stat([Q[rng.randrange(n)] for _ in range(n)]) for _ in range(10000)]
up = sorted(b[0] for b in B)[9500]; lo = sorted(b[1] for b in B)[500]
W = lambda q: 1.0 if q[2] == 2 else share if q[2] == 1 else 0.0
ks = sum(q[1] for q in Q); kb = sum(W(q) * q[3] for q in Q)
a = sum(q[1] * (1 - W(q) * q[3]) for q in Q); bb = sum(W(q) * q[3] * (1 - q[1]) for q in Q)
nd, kd = round(a + bb), round(a); pb = binom.cdf(kd, nd, 1 / 3) if nd else 1.0
out += [f"Truth-relative errors: V2 {ks}, ablation (expected, edge-weighted) {kb:.2f}",
        f"Original L1 (at least 50% fewer, discordant binomial p < 0.05): discordant {kd} of {nd}, p = {pb:.3f}: {'MET' if ks <= 0.5 * kb and pb < 0.05 else 'NOT MET'}",
        f"L1-b: SER difference {pt[0]:+.3f} points (one-sided 95% upper {up:+.3f}, margin +0.25); yield difference {pt[1]:+.3f} (lower {lo:+.3f}, margin -1): {'MET' if up < 0.25 and lo > -1 else 'NOT MET'}"]
(R / "V2_L1_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
