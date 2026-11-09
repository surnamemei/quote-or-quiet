"""Final tables for an S29 run (pre-registered, see docs/SEALED_SET_DESIGN.md): frozen-system releases vs the LTT agreement-score baseline (threshold rule calibrated on the 2,500 SimpleQA design items, t = 6),
the baseline at the threshold that gives at least the system's coverage, gold-relative errors, per-relation breakdown, and corrected Clopper-Pearson upper bounds (E = ceil(k/(1-0.0082)), over all n).
Needs s29_score.py to have been run first. CPU only.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s29/s29_final.py <fsm|ddg> <wdp|wd>"""
import json, math, os, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from scipy.stats import beta  # noqa: E402
from abstain_dev import grade  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans  # noqa: E402

search, name = sys.argv[1], sys.argv[2]
D = ROOT / "results/runs/s29" / f"run_{search}"
F = 0.0082
OTHERS = ("web_plain", "web_cautious", "wiki_plain", "wiki_cautious", "combo_cautious")
rows = [json.loads(l) for l in open(D / f"{name}_outputs.jsonl", encoding="utf-8")]
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / f"{name}_phi4.jsonl", encoding="utf-8"))}
sys_rel = {r["id"]: r for r in map(json.loads, open(D / f"{name}_releases.jsonl", encoding="utf-8"))}
n = len(rows)


def upper(k, n_):
    e = math.ceil(k / (1 - F))
    return 100 * beta.ppf(0.975, e + 1, n_ - e)


base = []
for r in rows:
    cand = r.get("combo_plain")
    if not ans(cand):
        base.append((r, None, None)); continue
    sc = sum(1 for k in OTHERS if ans(r.get(k)) and agree(str(cand), str(r[k])))
    p = phi.get(r["id"]); sc += int(bool(ans(p)) and agree(str(cand), str(p)))
    base.append((r, sc, grade(r["question"], r["gold"], cand)))
k_sys = sum(x["grade"] is False for x in sys_rel.values())
lines = [f"# S29 {search}/{name}: n = {n}", "",
         f"Frozen system: released {len(sys_rel)} (coverage {len(sys_rel)/n:.3f}), gold-relative wrong {k_sys} ({100*k_sys/max(1,len(sys_rel)):.2f}% of releases), corrected upper bound over all questions {upper(k_sys, n):.2f}%", "",
         "| baseline threshold t | released (coverage) | wrong | corrected upper |", "|---|---|---|---|"]
match_t = None
for t in range(6, -1, -1):
    rel = [g for _, sc, g in base if sc is not None and sc >= t]; k = sum(g is False for g in rel)
    lines.append(f"| {t} | {len(rel)} ({len(rel)/n:.3f}) | {k} | {upper(k, n):.2f}% |")
    if match_t is None and len(rel) >= len(sys_rel):
        match_t = (t, len(rel), k)
lines += ["", f"Baseline at the strictest threshold with at least the system's coverage: t = {match_t[0]}, released {match_t[1]}, wrong {match_t[2]}" if match_t else "Baseline never reaches the system's coverage.", ""]
tot = Counter(r["stratum"] for r in rows)
by = {}
for x in sys_rel.values():
    b = by.setdefault(x["relation"], [0, 0]); b[0] += 1; b[1] += x["grade"] is False
lines += ["| relation | n | released | coverage | wrong |", "|---|---|---|---|---|"]
for rel_, c in tot.items():
    a = by.get(rel_, [0, 0]); lines.append(f"| {rel_} | {c} | {a[0]} | {a[0]/c:.2f} | {a[1]} |")
(D / f"{name}_final.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
