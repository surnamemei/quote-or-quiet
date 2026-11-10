"""S51: compare the small judge with the 4B prompt judge on the held-out questions. Counts only in D_result.md. python -B results/runs/s51/d_eval.py"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.stats import beta
from sklearn.metrics import roc_auc_score
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s51"
P = json.load(open(D / "d_pred.json", encoding="utf-8")); J = json.load(open(D / "d_judge.json", encoding="utf-8"))
y = np.array([r["y"] for r in P]); p = np.array([r["p"] for r in P]); j = np.array([str(v).strip().upper().startswith("YES") for v in J])
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
out = ["# S51: a small quote-sufficiency judge against the 4B prompt judge (held-out questions)", "",
       f"Test rows {len(y)}; 'states' for both reviewers {int(y.sum())} ({100*y.mean():.1f}%).", ""]
def rate(mask):
    n = int(mask.sum()); bad = int(((y == 0) & mask).sum())
    return n, bad, (f"accepted {n} ({100*n/len(y):.1f}%), not 'states' among accepted {bad} ({100*bad/max(1,n):.1f}%, upper {up(bad,n):.1f}%)")
out += ["| Judge | AUROC | Acceptance and error |", "|---|---|---|",
        f"| Small judge (0.6B, LoRA) | {roc_auc_score(y, p):.3f} | at 0.5: {rate(p >= 0.5)[2]} |",
        f"| 4B prompt judge (YES/NO) | {roc_auc_score(y, j.astype(float)):.3f} | {rate(j)[2]} |"]
n4 = int(j.sum()); thr = np.sort(p)[::-1][max(0, n4 - 1)]
out += [f"| Small judge at the 4B acceptance rate | | threshold {thr:.3f}: {rate(p >= thr)[2]} |"]
for target in (0.05, 0.03):
    best = None
    for t in np.unique(p):
        n, bad, _ = rate(p >= t)
        if n and bad / n <= target:
            best = (t, n, bad) if best is None or n > best[1] else best
    out.append(f"| Small judge, most accepted rows with at most {int(target*100)}% not 'states' | | " + (f"threshold {best[0]:.3f}: {rate(p >= best[0])[2]} |" if best else "none reaches it |"))
out += ["", "By source (small judge at 0.5):", "", "| Source | rows | 'states' share | accepted | not 'states' among accepted |", "|---|---|---|---|---|"]
for s in sorted({r["src"] for r in P}):
    m = np.array([r["src"] == s for r in P]); a = m & (p >= 0.5); bad = int(((y == 0) & a).sum())
    out.append(f"| {s} | {int(m.sum())} | {100*y[m].mean():.0f}% | {int(a.sum())} | {bad} ({100*bad/max(1,int(a.sum())):.1f}%) |")
inq = np.array([str(r["answer"]).casefold() in r["quote"].casefold() for r in P])
allrows = [json.loads(l) for l in open(ROOT / "data/quote_sufficiency/all.jsonl", encoding="utf-8")]
trq = {r["quote"] for r in allrows if r["label"] and int(r["group"], 16) % 5 != 0}
shared = np.array([r["quote"] in trq for r in P])
def sub(mask, name):
    if mask.sum() < 20 or len(set(y[mask])) < 2:
        return
    a = mask & (p >= 0.5); aj = mask & j
    out.append(f"| {name} | {int(mask.sum())} | {100*y[mask].mean():.0f}% | {roc_auc_score(y[mask], p[mask]):.3f} | {int(a.sum())} / {int(((y == 0) & a).sum())} | {int(aj.sum())} / {int(((y == 0) & aj).sum())} |")
out += ["", "Harder subsets (accepted / not 'states' among accepted):", "", "| Subset | rows | 'states' share | small judge AUROC | small judge at 0.5 | 4B judge |", "|---|---|---|---|---|---|"]
sub(inq, "answer string occurs in the quote"); sub(~inq, "answer string does not occur in the quote (includes the decoys)")
sub(~shared, "the quote does not occur in the training rows"); sub(shared, "the quote also occurs in the training rows (with another question)")
sub(inq & ~shared, "answer in the quote and quote unseen in training")
(D / "D_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
