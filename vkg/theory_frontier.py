"""Theory T1/T2: the error-yield frontier of any 'answer or abstain' system built on a scalar confidence signal.
A base system would answer correctly with probability pi. A gate keeps answers whose score > t.
  SER(t)   = (1 - pi) * FPR(t)      (kept wrong answers / all questions)
  yield(t) = pi * TPR(t)            (kept correct answers / all questions)
So at a target SER eps the best achievable yield is  Y*(eps) = pi * ROC(eps / (1 - pi)).
Binormal ROC with separation d' (AUROC A = Phi(d'/sqrt2)):  TPR = Phi(d' + Phi^-1(FPR)).
Part 3 checks the binormal prediction against the measured S7b frontier (4B plain answers, S7 probe as the score; CPU only).
Run (idle priority): python -B -m vkg.theory_frontier
"""
import json

import numpy as np
from scipy.stats import norm
from sklearn.metrics import roc_auc_score


def dprime(A):
    return np.sqrt(2) * norm.ppf(A)


def yield_at(pi, A, eps):
    fpr = eps / (1 - pi)
    return 0.0 if fpr <= 0 else pi * norm.cdf(dprime(A) + norm.ppf(min(fpr, 1 - 1e-12))) if fpr < 1 else pi


def required_auroc(pi, eps, frac):
    """AUROC needed so that yield = frac * pi at SER = eps (binormal)."""
    fpr = eps / (1 - pi)
    d = norm.ppf(frac) - norm.ppf(fpr)
    return norm.cdf(d / np.sqrt(2))


def part1_2(L):
    L += ["## T1: best achievable yield at a target silent-error rate (binormal ROC)", "",
          "pi = share of questions the base system would answer correctly; A = AUROC of the gate's signal for 'this answer is correct'.", "",
          "| setting | pi | A | yield at SER 5% | at 1% | at 0.1% |", "|---|---|---|---|---|---|"]
    for name, pi, A in (("closed-book 27B (raw strict-correct 4.4%), best S3 signal", 0.044, 0.795),
                        ("closed-book 4B TriviaQA, S5 probe", 0.485, 0.821),
                        ("4B + retrieval, plain answers, signal A=0.80", 0.593, 0.80),
                        ("4B + retrieval, plain answers, signal A=0.89", 0.593, 0.89),
                        ("4B + retrieval, plain answers, signal A=0.94", 0.593, 0.94),
                        ("4B + retrieval, plain answers, signal A=0.99", 0.593, 0.99)):
        L.append(f"| {name} | {pi:.3f} | {A:.3f} | " + " | ".join(f"{yield_at(pi, A, e):.3f}" for e in (0.05, 0.01, 0.001)) + " |")
    L += ["", "## T2: AUROC a signal must reach for a given goal (binormal)", "",
          "| pi | target SER | keep this share of the correct answers | required AUROC |", "|---|---|---|---|"]
    for pi in (0.044, 0.593, 0.9, 0.98):
        for eps in (0.01, 0.001):
            for frac in (0.5, 0.9):
                L.append(f"| {pi} | {eps} | {frac} | {required_auroc(pi, eps, frac):.4f} |")
    from scipy.stats import beta
    L += ["", "## T5: how many labelled questions are needed to VERIFY a low silent-error rate", "",
          "Accepted (answered) questions needed so that the exact 95% upper bound on the error rate among them is below the target, for a given number of errors observed.", "",
          "| target error rate among answers | 0 errors seen | 1 error | 3 errors |", "|---|---|---|---|"]
    for a in (0.05, 0.01, 0.001):
        cells = []
        for k in (0, 1, 3):
            nn = k + 1
            while beta.ppf(0.95, k + 1, nn - k) > a:
                nn = int(nn * 1.02) + 1
            lo, hi = max(k + 1, int(nn / 1.03) - 2), nn
            while lo < hi:
                mid = (lo + hi) // 2
                if beta.ppf(0.95, k + 1, mid - k) <= a:
                    hi = mid
                else:
                    lo = mid + 1
            cells.append(str(lo))
        L.append(f"| {a} | " + " | ".join(cells) + " |")
    L.append("")


def part3(L):
    from .probe_eval import correct, fit_layers, score_layers
    from .s7_run import OUT as S7OUT, S6B, load_sets
    from .s8_eval import non_answer
    train, sq, fa, sa = load_sets()
    F = np.load(S7OUT / "feats_trained.npy")
    n = len(train)
    ytr = np.array([t["target"] != "unknown" for t in train], int)
    j, C, ss, m, _ = fit_layers(F, np.concatenate([ytr, np.zeros(len(F) - n, int)]), np.arange(n))
    s = score_layers(F, j, ss, m, np.arange(len(F)))[n + len(sq) + len(fa):]
    outs = {o["id"]: o for o in map(json.loads, open(S6B / "eval_outputs.jsonl", encoding="utf-8")) if o["suite"] == "simpleqa_E"}
    rows = [outs[e["id"]] for e in sa]
    ans = np.array([not non_answer(r["plain"]) for r in rows])
    cor = np.array([bool(correct({"dataset": "simpleqa", "gold": r["gold"]}, r["plain"])) for r in rows]) & ans
    # questions with a non-answer can never become correct by gating: score them -inf (they are never 'kept wrong' either)
    keep = ans
    pi = cor.mean()
    A = roc_auc_score(cor[keep], s[keep])
    pi_ans = cor[keep].mean()
    L += ["## T3: does the binormal frontier predict a measured system? (4B plain answers on SimpleQA-E, n=300; score = S7 probe)", "",
          f"Plain answers (cleaner detector) on {keep.sum()} questions; correct on {cor.sum()} (pi over all = {pi:.3f}; over answered = {pi_ans:.3f}). "
          f"AUROC of the probe for 'this answer is correct' among answered: {A:.3f}.", "",
          "| target SER (of all 300) | measured best yield | binormal prediction |", "|---|---|---|"]
    order = np.argsort(-s[keep])
    c_sorted = cor[keep][order]
    tp = np.cumsum(c_sorted)
    fp = np.cumsum(~c_sorted)
    N = len(rows)
    for eps in (0.01, 0.02, 0.03, 0.05, 0.07, 0.10):
        ok = fp / N <= eps
        best = tp[ok].max() / N if ok.any() else 0.0
        frac_ans = keep.mean()
        pred = frac_ans * yield_at(pi_ans, A, eps / frac_ans)     # same formula inside the answered subset
        L.append(f"| {eps:.2f} | {best:.3f} | {pred:.3f} |")
    L += ["", "Reference points measured earlier on the same 300: 4B cautious prompt SER 7.0% at correct 53.0%; gate+cautious 4.0% at 44.7%; S8 DEV plain+check 10.0% at 58.3%.", ""]


def main():
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    L = ["# Theory tables (generated by vkg/theory_frontier.py)", ""]
    part1_2(L)
    part3(L)
    txt = "\n".join(L)
    from .probe_gen import ROOT
    (ROOT / "results" / "theory_frontier.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
