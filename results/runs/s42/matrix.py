"""S42 E1: paired outcome matrix on the S29 sealed set (n = 3,359): what happens to each answer of the raw model (B0, closed book) and of standard RAG (B2)
under the frozen system. Gold-relative labels (cached, alias-aware); the system's gold-wrong releases are split with the S29 adjudication (L2_result.md).
CPU only, reads existing outputs. OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/matrix.py"""
import json, os, re, sys
from collections import Counter
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402
from abstain_dev import grade  # noqa: E402
from vkg.s14_eval import ans  # noqa: E402
D = ROOT / "results/runs/s29/run_fsm"
rows = {r["id"]: r for r in map(json.loads, open(D / "wd_outputs.jsonl", encoding="utf-8"))}
S = {r["id"]: r for r in map(json.loads, open(D / "wd_releases.jsonl", encoding="utf-8"))}
C = {r["id"]: r for r in map(json.loads, open(D / "wd_closed.jsonl", encoding="utf-8"))}
n = len(rows)
# adjudication of the system's gold-wrong releases: kept (not cleared) and the one both reviewers called wrong
txt = (ROOT / "results/runs/s29/review/wd/L2_result.md").read_text(encoding="utf-8")
kept_q = set(re.findall(r"^- \[\w+\] (.+?) \| gold", txt.split("Kept errors:")[1].split("Removed errors:")[0], re.M))
truth_q = {q for q, a, b in re.findall(r"^- \[\w+\] (.+?) \| gold .*?\| A (.+?) \| B (.+)$", txt.split("Kept errors:")[1].split("Removed errors:")[0], re.M) if a.strip() == b.strip() == "answer wrong"}
def sys_state(i):
    if i not in S: return "Unresolved"
    g = S[i]["grade"]
    if g is True: return "Verified, matches gold"
    if g is False:
        q = S[i]["question"]
        return "Verified, wrong (both reviewers)" if q in truth_q else ("Verified, gold mismatch not cleared" if q in kept_q else "Verified, gold mismatch cleared by review")
    return "Verified, unlabelled"
def base_state(a, r):
    if not ans(a): return "no answer"
    g = grade(r["question"], r["gold"], a)
    return "right" if g is True else ("wrong" if g is False else "unlabelled")
COLS = ["Verified, matches gold", "Verified, gold mismatch cleared by review", "Verified, gold mismatch not cleared", "Verified, wrong (both reviewers)", "Verified, unlabelled", "Unresolved"]
out = ["# S42 E1: what the frozen system does with each baseline answer (S29 sealed set, n = 3,359)", "",
       "Rows: the baseline's own outcome against the reference answer. Columns: the frozen system's outcome on the same question.", ""]
res = {}
for name, get in (("B0 raw model, closed book", lambda i: C[i]["b0"]), ("B1 raw model + abstention prompt", lambda i: C[i]["b1"]), ("B2 standard RAG", lambda i: rows[i].get("combo_plain"))):
    M = Counter((base_state(get(i), rows[i]), sys_state(i)) for i in rows)
    cols = [c for c in COLS if any(M[(r, c)] for r in ("right", "wrong", "no answer", "unlabelled"))]
    out += [f"## {name}", "", "| baseline outcome | n | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    for r in ("wrong", "right", "no answer", "unlabelled"):
        t = sum(M[(r, c)] for c in COLS)
        if t: out.append(f"| {r} | {t} | " + " | ".join(f"{M[(r, c)]} ({100*M[(r, c)]/t:.1f}%)" for c in cols) + " |")
    w = sum(M[("wrong", c)] for c in COLS); rt = sum(M[("right", c)] for c in COLS)
    fixed = M[("wrong", COLS[0])]; silent = M[("wrong", "Unresolved")]; left = w - fixed - silent
    still = M[("wrong", COLS[2])] + M[("wrong", COLS[3])]
    hi = beta.ppf(0.975, still + 1, w - still) if w else float("nan")
    lost = M[("right", "Unresolved")]
    out += ["", f"Of the baseline's {w} gold-wrong answers: replaced by a verified answer that matches gold {fixed} ({100*fixed/w:.1f}%), turned into Unresolved {silent} ({100*silent/w:.1f}%), "
            f"released with a gold mismatch {left} ({100*left/w:.2f}%; {M[('wrong', COLS[1])]} cleared by review, {M[('wrong', COLS[2])]} not cleared, {M[('wrong', COLS[3])]} wrong for both reviewers). "
            f"Not cleared or wrong: {still} of {w}, one-sided 97.5% upper bound {100*hi:.2f}%.",
            f"Of the baseline's {rt} gold-right answers: kept as Verified {rt - lost - sum(M[('right', c)] for c in COLS[1:5])} ({100*(rt - lost - sum(M[('right', c)] for c in COLS[1:5]))/rt:.1f}%), "
            f"lost to Unresolved {lost} ({100*lost/rt:.1f}%), released with a gold mismatch {sum(M[('right', c)] for c in COLS[1:5])}.", ""]
    res[name] = {f"{r}|{c}": M[(r, c)] for r in ("wrong", "right", "no answer", "unlabelled") for c in COLS if M[(r, c)]}
(ROOT / "results/runs/s42/E1_matrix.md").write_text("\n".join(out), encoding="utf-8")
json.dump(res, open(ROOT / "results/runs/s42/E1_matrix.json", "w", encoding="utf-8"), indent=1)
print("\n".join(out))
L = [len(str(C[i]["b0"]).split()) for i in rows]
print("B0 answer length in words: <=4:", sum(x <= 4 for x in L), " >4:", sum(x > 4 for x in L))
