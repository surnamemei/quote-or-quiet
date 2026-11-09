"""Conformal-style selective baseline on the same evidence and readers (design-time comparison, post hoc, cached outputs only, CPU).
Score of an answered question = number of the other six reader outputs that agree with the single-pass candidate (combo_plain)
(web_plain, web_cautious, wiki_plain, wiki_cautious, combo_cautious from the 4B, plus Phi-4 cautious): 0..6.
Release rule: score >= t. Calibration: SimpleQA design data (dev 300 + fresh 200 + S18 2000 = 2500 items, same distribution as FRESH-5).
Learn-then-Test fixed-sequence selection of t from strict to lax: accept t while the binomial test of H0 "SER >= 1%" rejects at 2.5%,
using the same false-credit correction E = ceil(k / (1 - 0.0082)) as the frozen system. Test: FRESH-5, once.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s23/conformal_base.py"""
import json, math, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from scipy.stats import binom, beta                                  # noqa: E402
from abstain_dev import grade                                        # noqa: E402
from vkg import s18_eval as E                                        # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402

RD = ROOT / "results/shared_eval/readers"
F = 0.0082
OTHERS = ("web_plain", "web_cautious", "wiki_plain", "wiki_cautious", "combo_cautious")


def load(name):
    if name == "s18":
        return E.load(["fresh3", "fresh4"]), {r["id"]: r["answer"] for r in map(json.loads, open(RD / "s18_combo_cautious_phi4.jsonl", encoding="utf-8"))}
    rows = [json.loads(l) for l in open(ROOT / f"results/runs/s19/{name}_outputs.jsonl", encoding="utf-8")]
    return rows, {r["id"]: r["answer"] for r in map(json.loads, open(RD / f"s19{name}_combo_cautious_phi4.jsonl", encoding="utf-8"))}


def scored(name):
    rows, phi = load(name)
    out = []
    for r in rows:
        cand = r.get("combo_plain")
        if not ans(cand):
            out.append((None, None)); continue
        sc = sum(1 for k in OTHERS if ans(r.get(k)) and agree(str(cand), str(r[k])))
        p = phi.get(r["id"])
        sc += int(bool(ans(p)) and agree(str(cand), str(p)))
        out.append((sc, grade(r["question"], r["gold"], cand)))
    return out


def corrected_upper(k, n):
    e = math.ceil(k / (1 - F))
    return beta.ppf(0.975, e + 1, n - e)


cal = []
for nm in ("dev", "fresh", "s18"):
    cal += scored(nm)
test = scored("fresh5")
lines = [f"# Conformal-style baseline (post hoc, design comparison)", "", f"calibration n = {len(cal)}, test (FRESH-5) n = {len(test)}", "",
         "| t | calib released | calib wrong | LTT p (H0: SER >= 1%) | test released (cov) | test wrong | test corrected upper |", "|---|---|---|---|---|---|---|"]
chosen = None
for t in range(6, -1, -1):
    rel = [g for sc, g in cal if sc is not None and sc >= t]
    k = sum(g is False for g in rel); n = len(cal)
    e = math.ceil(k / (1 - F)); p = binom.cdf(e, n, 0.01)
    trel = [g for sc, g in test if sc is not None and sc >= t]
    tk = sum(g is False for g in trel); nt = len(test)
    lines.append(f"| {t} | {len(rel)} | {k} | {p:.4f} | {len(trel)} ({len(trel)/nt:.3f}) | {tk} | {100*corrected_upper(tk, nt):.2f}% |")
    if p <= 0.025 and chosen is None and all(True for _ in [0]):
        pass
# fixed sequence from strict (t=6) to lax: stop at first failure
ok_t = None
for t in range(6, -1, -1):
    rel = [g for sc, g in cal if sc is not None and sc >= t]
    k = sum(g is False for g in rel); e = math.ceil(k / (1 - F))
    if binom.cdf(e, len(cal), 0.01) <= 0.025:
        ok_t = t
    else:
        break
lines.append("")
if ok_t is None:
    lines.append("No threshold passes the calibration test (even the strictest cannot certify 1% at n = %d)." % len(cal))
else:
    trel = [g for sc, g in test if sc is not None and sc >= ok_t]; tk = sum(g is False for g in trel)
    lines.append(f"Selected t = {ok_t}: FRESH-5 released {len(trel)} (coverage {len(trel)/len(test):.3f}), wrong {tk}, SER {100*tk/len(test):.2f}%, corrected upper {100*corrected_upper(tk, len(test)):.2f}%. Frozen system: coverage 0.372, 4 wrong, upper 0.76%.")
(ROOT / "results/runs/s23/conformal_base.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
