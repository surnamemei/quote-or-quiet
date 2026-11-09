"""Outcome classification and statistics (cluster = original question)."""
import random
from collections import defaultdict

from scipy.stats import beta

from .tasks import matches


def classify(item, out):
    """-> one of: correct, correct_qualified, safe_abstain, over_abstain, silent_error"""
    st = out["status"]
    if item.kind == "answerable":
        if st == "answer":
            return "correct" if matches(item.gold, out["answer"]) else "silent_error"
        return "false_conflict" if st == "conflict" else "over_abstain"
    if item.kind == "unanswerable":
        # claiming a conflict that the source does not contain is an unjustified assertion, not a safe abstention
        return {"answer": "silent_error", "conflict": "false_conflict", "unknown": "safe_abstain"}[st]
    # conflict
    return {"answer": "silent_error", "conflict": "correct_qualified", "unknown": "safe_abstain"}[st]


def clopper_pearson_upper(k, n, alpha=0.05):
    return 1.0 if k >= n else float(beta.ppf(1 - alpha, k + 1, n - k)) if n else 1.0


def summarize(rows):
    """rows: list of dict(outcome, kind). Returns metrics dict."""
    n = len(rows)
    c = defaultdict(int)
    for r in rows:
        c[r["outcome"]] += 1
    ans_items = [r for r in rows if r["kind"] == "answerable"]
    answered = c["correct"] + [r["outcome"] for r in rows].count("silent_error")
    return {
        "n": n,
        "SER": c["silent_error"] / n if n else float("nan"),
        "SER_strict": (c["silent_error"] + c["false_conflict"]) / n if n else float("nan"),
        "SER_ub95": clopper_pearson_upper(c["silent_error"], n),
        "selective_risk": c["silent_error"] / answered if answered else 0.0,
        "answer_yield": (c["correct"] / len(ans_items)) if ans_items else float("nan"),
        "over_abstain": (c["over_abstain"] / len(ans_items)) if ans_items else float("nan"),
        "safe_handling": ((c["safe_abstain"] + c["correct_qualified"]) /
                          max(1, sum(r["kind"] != "answerable" for r in rows))),
        "counts": dict(c),
    }


def paired_bootstrap_delta(a, b, stat, B=2000, seed=0):
    """a, b: dict qid -> row (same keys). Returns (delta, lo, hi) for stat(b)-stat(a)."""
    keys = list(a)
    rng = random.Random(seed)
    vals = []
    for _ in range(B):
        s = [keys[rng.randrange(len(keys))] for _ in keys]
        vals.append(stat([b[k] for k in s]) - stat([a[k] for k in s]))
    vals.sort()
    d = stat([b[k] for k in keys]) - stat([a[k] for k in keys])
    return d, vals[int(0.025 * B)], vals[int(0.975 * B)]


def ser(rows):
    return sum(r["outcome"] == "silent_error" for r in rows) / len(rows)


def yld(rows):
    ans = [r for r in rows if r["kind"] == "answerable"]
    return sum(r["outcome"] == "correct" for r in ans) / len(ans) if ans else float("nan")
