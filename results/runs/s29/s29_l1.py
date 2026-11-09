"""L1 decisions on the S29 sealed set (rules in docs/CRITERIA_REVISION_L1.md; written before any sealed result).
Needs: s29_score.py output, review/<set>/key.json and the four L1 verdict files (L1_verdict_part{1,2}_{A,B}.csv).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s29/s29_l1.py <wd|wdp>"""
import csv, json, os, random, sys
from pathlib import Path
from scipy.stats import binom, beta
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402
from abstain_dev import grade  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans  # noqa: E402
name = sys.argv[1]
D = ROOT / "results/runs/s29/run_fsm"; R = ROOT / "results/runs/s29/review" / name
K = json.load(open(R / "key.json", encoding="utf-8")); meta = K["meta"]
OTHERS = ("web_plain", "web_cautious", "wiki_plain", "wiki_cautious", "combo_cautious")
rows = {r["id"]: r for r in map(json.loads, open(D / f"{name}_outputs.jsonl", encoding="utf-8"))}
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_phi4.jsonl", encoding="utf-8"))}
S = {r["id"]: r for r in map(json.loads, open(D / f"{name}_releases.jsonl", encoding="utf-8"))}
n = len(rows)
# reviewed truth errors
V = {}
for p in ("1", "2"):
    for rv in ("A", "B"):
        for x in csv.DictReader(open(R / f"L1_verdict_part{p}_{rv}.csv", encoding="utf-8")):
            V.setdefault((p, int(x["row"])), []).append(x["verdict"].strip().casefold())
err, reviewed = set(), {}
dec_ok = dec_n = 0
for p, lst in K["L1"].items():
    for k in lst:
        v = V[(p, k["row"])]; both = v == ["wrong", "wrong"]
        if k["kind"] == "decoy":
            dec_n += 1; dec_ok += both; continue
        key = (k["id"], k["answer"].strip().casefold())
        if both: err.add(key)
        for w in k["who"]:
            reviewed.setdefault((w, k["kind"]), []).append(both)
out = [f"# S29 {name}: L1 decisions", "", f"Decoys called wrong by both reviewers: {dec_ok}/{dec_n} ({'VALID' if dec_ok >= dec_n - 1 else 'INVALID'})", ""]
# ---- L1-a: system vs standard baselines, gold-relative, McNemar exact one-sided, Holm
std = {"B2 standard RAG": {i: r.get("combo_plain") for i, r in rows.items()}, "B3 RAG + abstention prompt": {i: r.get("combo_cautious") for i, r in rows.items()}}
cl = D / f"{name}_closed.jsonl"
if cl.exists():
    C = {r["id"]: r for r in map(json.loads, open(cl, encoding="utf-8"))}
    std = {"B0 raw model": {i: C[i]["b0"] for i in rows}, "B1 raw model + abstention prompt": {i: C[i]["b1"] for i in rows}, **std}
sys_err = {i for i, x in S.items() if x["grade"] is False}
k_sys_truth = sum((i, S[i]["answer"].strip().casefold()) in err for i in sys_err)
res = []
for b, A in std.items():
    bw = {i for i, a in A.items() if ans(a) and grade(rows[i]["question"], rows[i]["gold"], a) is False}
    cov = sum(1 for a in A.values() if ans(a)) / n
    n01, n10 = len(bw - sys_err), len(sys_err - bw)
    p = binom.cdf(n10, n01 + n10, 0.5) if n01 + n10 else 1.0
    tag = "B" + b[1]
    sample = reviewed.get((tag, "std_wrong_sample"), [])
    share = sum(sample) / len(sample) if sample else float("nan")
    lo_share = beta.ppf(0.025, sum(sample), len(sample) - sum(sample) + 1) if sample and sum(sample) else 0.0
    base_truth_lo = len(bw) * lo_share / n
    sys_truth_hi = beta.ppf(0.975, k_sys_truth + 1, n - k_sys_truth)
    res.append([b, cov, len(bw), n01, n10, p, share, base_truth_lo, sys_truth_hi])
order = sorted(range(len(res)), key=lambda j: res[j][5]); m = len(res); holm_ok = {}
running = True
for rank, j in enumerate(order):
    running = running and res[j][5] <= 0.05 / (m - rank); holm_ok[j] = running
out += ["## L1-a (system SER vs standard baselines; gold-relative; McNemar one-sided, Holm)", "",
        f"System: released {len(S)} (coverage {len(S)/n:.3f}), gold-wrong {len(sys_err)} (SER {100*len(sys_err)/n:.2f}%), truth-relative errors {k_sys_truth}", "",
        "| baseline | coverage | gold-wrong (SER) | baseline-only errors | system-only errors | p | Holm | truth share of reviewed baseline errors | robustness (baseline truth SER lower bound > system truth SER upper bound) |", "|---|---|---|---|---|---|---|---|---|"]
for j, (b, cov, nb, n01, n10, p, share, blo, shi) in enumerate(res):
    out.append(f"| {b} | {cov:.3f} | {nb} ({100*nb/n:.2f}%) | {n01} | {n10} | {p:.2e} | {'pass' if holm_ok[j] else 'fail'} | {share:.2f} | {100*blo:.2f}% vs {100*shi:.2f}%: {'pass' if blo > shi else 'fail'} |")
l1a = all(holm_ok.values()) and len(res) == 4
out += ["", f"L1-a: {'MET' if l1a else 'NOT MET'}" + ("" if len(res) == 4 else " (closed-book baselines missing)"), ""]
# ---- L1-b: non-inferiority to the agreement-score ablation at exactly matched coverage (truth-relative)
t = meta["t"]; share_edge = (meta["sys_released"] - meta["base_n_top"]) / meta["base_n_edge"] if meta["base_n_edge"] else 0.0
Q = []
for i, r in rows.items():
    c = r.get("combo_plain"); cls = 0
    if ans(c):
        s_ = sum(1 for k in OTHERS if ans(r.get(k)) and agree(str(c), str(r[k]))) + int(bool(ans(phi.get(i))) and agree(str(c), str(phi.get(i))))
        cls = 2 if s_ > t else (1 if s_ == t else 0)
    sr = i in S; se = sr and (i, S[i]["answer"].strip().casefold()) in err
    be = cls > 0 and (i, str(c).strip().casefold()) in err
    Q.append((sr, se, cls, be))
rng = random.Random(0)
def stat(sample, rand=True):
    ds = dy = 0.0
    for sr, se, cls, be in sample:
        w = 1.0 if cls == 2 else ((1.0 if rng.random() < share_edge else 0.0) if rand else share_edge) if cls == 1 else 0.0
        ds += se - w * be; dy += (sr and not se) - w * (not be)
    return 100 * ds / len(sample), 100 * dy / len(sample)
pt = stat(Q, rand=False)
B = [stat([Q[rng.randrange(n)] for _ in range(n)]) for _ in range(10000)]
up = sorted(b[0] for b in B)[9500]; lo = sorted(b[1] for b in B)[500]
l1b = up < 0.25 and lo > -1.0
out += ["## L1-b (non-inferiority to the agreement-score ablation, matched coverage, truth-relative; bootstrap 10,000, seed 0)", "",
        f"SER difference {pt[0]:+.3f} points, one-sided 95% upper bound {up:+.3f} (margin +0.25)", f"Yield difference {pt[1]:+.3f} points, one-sided 95% lower bound {lo:+.3f} (margin -1)",
        f"L1-b: {'MET' if l1b else 'NOT MET'}", ""]
# ---- original L1: 50% lower than the ablation (discordant binomial)
ks = sum(q[1] for q in Q); kb = sum((1.0 if q[2] == 2 else share_edge if q[2] == 1 else 0.0) * q[3] for q in Q)
a = sum(q[1] * (1 - (1.0 if q[2] == 2 else share_edge if q[2] == 1 else 0.0) * q[3]) for q in Q)
bb = sum((1.0 if q[2] == 2 else share_edge if q[2] == 1 else 0.0) * q[3] * (1 - q[1]) for q in Q)
nd, kd = round(a + bb), round(a); pb = binom.cdf(kd, nd, 1 / 3) if nd else 1.0
out += ["## Original L1 (at least 50% lower than the ablation)", "", f"k_sys {ks}, E[k_base] {kb:.2f}, discordant {kd} of {nd}, p = {pb:.3f}: {'MET' if ks <= 0.5 * kb and pb < 0.05 else 'NOT MET'}", "",
        f"## Revised L1 (L1-a and L1-b): {'MET' if l1a and l1b else 'NOT MET'}"]
(R / "L1_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
