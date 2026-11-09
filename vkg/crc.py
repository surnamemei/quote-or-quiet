"""Conformal risk control for selective answering (L3: a formal guarantee within a stated scope).
Setting: each item i has a confidence score s_i (higher = more trustworthy) and, if answered, a loss e_i in {0, 1}
(1 = silent error: answered and wrong, as graded by grader 6.1). The system answers iff s_i >= lam.
Loss L_i(lam) = e_i * 1[s_i >= lam] is non-increasing in lam and bounded by B = 1.
CRC (Angelopoulos, Bates, Fisch, Lei, Schuster, "Conformal Risk Control", ICLR 2024), Theorem 1: with n exchangeable
calibration items and a test item, choosing
    lam_hat = inf{ lam : n/(n+1) * R_n(lam) + B/(n+1) <= alpha },   R_n = mean calibration loss,
guarantees E[L_test(lam_hat)] <= alpha. Here that bound is on the expected silent-error rate (SER) per item,
over the randomness of calibration and test draws.
Scope of the guarantee: exchangeability between calibration and test items (same item distribution, same pipeline,
same grader as loss oracle). It says nothing about other distributions, and grader errors count as true losses.
  calibrate(scores, errs, alpha) -> (lam_hat, cal_SER_at_lam, cal_coverage)
  apply(scores, lam) -> answer mask"""
import numpy as np


def calibrate(scores, errs, alpha, B=1.0):
    s = np.asarray(scores, float)
    e = np.asarray(errs, float)
    n = len(s)
    cands = np.concatenate([np.unique(s), [np.inf]])          # lam = inf: answer nothing, loss 0
    for lam in cands:                                         # ascending: first feasible = least conservative
        R = (e * (s >= lam)).mean()
        if n / (n + 1) * R + B / (n + 1) <= alpha:
            ans = s >= lam
            return float(lam), float((e * ans).mean()), float(ans.mean())
    return float("inf"), 0.0, 0.0


def apply(scores, lam):
    return np.asarray(scores, float) >= lam


def selftest():
    rng = np.random.default_rng(0)
    alpha, hits = 0.05, []
    for _ in range(2000):                                     # synthetic check of the guarantee
        s = rng.random(501)
        err = rng.random(501) < 0.25 * (1 - s)                # lower score -> more errors
        lam, _, _ = calibrate(s[:500], err[:500], alpha)
        hits.append(err[500] and s[500] >= lam)
    m = float(np.mean(hits))
    assert m <= alpha + 0.01, m
    return m


if __name__ == "__main__":
    print("synthetic test-item SER at alpha=0.05:", round(selftest(), 4))
