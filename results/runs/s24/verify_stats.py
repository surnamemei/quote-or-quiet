"""Recompute every bound, rate and test quoted in paper/manuscript.md from the underlying counts, with a different code path from the one used while writing
(binomial-tail inversion by root finding instead of the beta quantile), and check that the manuscript text contains the recomputed value.
python -I -B results/runs/s24/verify_stats.py"""
import math, re
from pathlib import Path
from scipy.optimize import brentq
from scipy.stats import binom
ROOT = Path(__file__).resolve().parents[3]
TEXT = (ROOT / "paper" / "manuscript.md").read_text(encoding="utf-8")
F = 0.0082


def upper(k, n, delta=0.025):
    """Clopper-Pearson one-sided upper limit: the p with P(Bin(n,p) <= k) = delta."""
    if k >= n:
        return 1.0
    return brentq(lambda p: binom.cdf(k, n, p) - delta, 1e-9, 1 - 1e-9)


def corrected(k, n):
    return upper(math.ceil(k / (1 - F)), n)


checks = []   # (description, computed string, must appear in manuscript)
def add(desc, val, fmt):
    s = fmt.format(val)
    checks.append((desc, s, s in TEXT))


for desc, k, n, fmt in [("FRESH-5 SER bound", 4, 1526, "{:.2f}%"), ("Mintaka SER bound", 28, 2000, "{:.2f}%"), ("PopQA SER bound", 17, 2100, "{:.2f}%"),
                        ("Mintaka adjudicated bound", 9, 2000, "{:.2f}%"), ("LTT baseline bound", 9, 1526, "{:.2f}%"), ("closed bound", 0, 1500, "{:.2f}%")]:
    add(desc, 100 * corrected(k, n), fmt)
for desc, k, n in [("FRESH-5 per released", 4, 568), ("Mintaka per released gold", 28, 620), ("Mintaka per released adjudicated", 9, 620), ("PopQA per released", 17, 401)]:
    add(desc, 100 * corrected(k, n), "{:.2f}%")
# rates
for desc, a, b in [("FRESH-5 coverage", 568, 1526), ("Mintaka coverage", 620, 2000), ("PopQA coverage", 401, 2100), ("pin Mintaka coverage", 1005, 2000), ("closed A coverage", 813, 1500),
                   ("closed B coverage", 854, 1500), ("LTT coverage", 552, 1526)]:
    add(desc, 100 * a / b, "{:.1f}%")
for desc, a, b in [("FRESH-5 raw SER", 4, 1526), ("Mintaka raw SER", 28, 2000), ("PopQA raw SER", 17, 2100), ("Mintaka adjudicated SER", 9, 2000), ("LTT SER", 9, 1526),
                   ("added error Mintaka", 20, 385), ("added error FRESH-5", 10, 159), ("pooled added error", 5, 73), ("title-based added", 2, 31), ("pin added", 11, 53),
                   ("selective FRESH-5", 4, 568), ("selective Mintaka", 28, 620), ("selective PopQA", 17, 401)]:
    add(desc, 100 * a / b, "{:.1f}%" if "added" in desc else "{:.2f}%")
# one-sided binomial test, 4 of 13 at p = 0.5
add("4 vs 9 test", binom.cdf(4, 13, 0.5), "{:.2f}")
# L2 allowance: largest k with corrected bound < 1%
for n in (1526, 2000, 1500):
    k = 0
    while corrected(k + 1, n) < 0.01:
        k += 1
    checks.append((f"L2 allowance n={n}", f"k <= {k}", f"k ≤ {k}" in TEXT or f"k <= {k}" in TEXT))
# ratios in Section 5.2
add("single-pass / system Mintaka", 12.85 / 1.40, "{:.0f}")
bad = [c for c in checks if not c[2]]
for d, s, ok in checks:
    print(("OK   " if ok else "MISSING"), d, s)
print(len(checks), "checked,", len(bad), "not found verbatim in the manuscript")
