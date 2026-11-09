"""ROADMAP S3: confidence signals for closed-book SimpleQA Verified (protocol: docs/S3_PROTOCOL.md).

Stages (python -m vkg.signals <stage>):
  plan      write the pool/split file (indices only; the 300 forbidden test positions are never stored or printed)
  gen       call the model: greedy answer (+logprobs), B1 status, verbalized confidence, K sampled answers
  embed     embed the answer strings with qwen3-embedding:0.6b (run after gen so the 27B is not displaced mid-run)
  analyze   grade, build signals, fit thresholds on calibration, report on test (writes results/S3_signals.md body)
  selftest  synthetic checks of the metric code (no model calls)
No LLM judge: correctness = vkg.grade_open (strict / lenient / lenient2).
"""
import base64
import json
import math
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests

from .grade_open import grade, grade_v3, lenient2
from .systems import UNKNOWN_RE, _b1_prompt, _parse
from .tasks import Item, matches, norm

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "runs"
POOL = RUNS / "s3_pool.json"
GEN = RUNS / "s3_signals_raw.jsonl"
EMB = RUNS / "s3_embeddings.jsonl"
LOG = RUNS / "s3_gen.log"
LIMIT = RUNS / "s3_limit.txt"
FLAG = RUNS / "s3_gen_done.flag"
OUT_MD = ROOT / "results" / "S3_signals.md"
OUT_JSON = RUNS / "s3_metrics.json"

HOST = os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")
MODEL = "qwen3.8-27b"
EMB_MODEL = "qwen3-embedding:0.6b"
K = 8
TEMP = 0.8
SAMPLE_SEED0 = 1000
EMB_GRID = [0.70, 0.75, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97]
MIN_FRAC = 0.02          # coverage floor of the pass rule (share of ALL questions in the half)
BUDGETS = (0.10, 0.25)
PASS_PREC = 0.30
BOOT = 2000
SIGNALS = ["b1_status", "verbal", "sc_exact", "sc_emb", "logprob", "combo_lr", "combo_z"]


# ----------------------------------------------------------------------------- pool
def make_pool():
    forbidden = set(random.Random(3000).sample(range(1000), 300))     # test ids of the frozen runs: never touched
    rest = [i for i in range(1000) if i not in forbidden]
    assert len(rest) == 700
    pool = random.Random(5000).sample(rest, 500)
    assert not (set(pool) & forbidden) and len(set(pool)) == 500
    order = pool[:]
    random.Random(6000).shuffle(order)
    cal, test = order[:250], order[250:]
    inter = [x for pair in zip(cal, test) for x in pair]             # first 300 of this list = 150 cal + 150 test
    return {"cal": cal, "test": test, "order": inter}


def plan():
    p = make_pool()
    POOL.write_text(json.dumps(p), encoding="utf-8")
    print("pool written:", len(p["cal"]), len(p["test"]))


def load_pool():
    return json.loads(POOL.read_text(encoding="utf-8"))


def get_limit():
    try:
        return int(LIMIT.read_text().strip())
    except Exception:
        return 500


# ----------------------------------------------------------------------------- model calls
def _post(path, payload, timeout=600, max_wait=7200):
    """POST with retry; if the shared Ollama server is unreachable or busy we wait and retry (never restart it)."""
    t0, delay = time.time(), 5
    while True:
        try:
            r = requests.post(f"{HOST}{path}", json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            err = f"HTTP {r.status_code} {r.text[:200]}"
        except (requests.ConnectionError, requests.Timeout) as e:
            err = repr(e)[:200]
        if time.time() - t0 > max_wait:
            raise RuntimeError("Ollama unreachable too long: " + err)
        _log(f"retry in {delay}s: {err}")
        time.sleep(delay)
        delay = min(delay * 2, 120)


def call(prompt, temperature=0.0, seed=0, logprobs=False, max_tokens=400):
    payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": False,
               "format": "json",
               "options": {"temperature": temperature, "seed": seed, "num_predict": max_tokens, "num_ctx": 8192}}
    if logprobs:
        payload["logprobs"] = True
    d = _post("/api/chat", payload)
    return d["message"]["content"], d.get("logprobs")


_lock = threading.Lock()
_loglock = threading.Lock()


def _log(msg):
    with _loglock:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")


def b0_prompt(q):
    return f"Question: {q}\n" + 'Reply as JSON: {"answer": "<short answer>"}'


def verbal_prompt(q, a):
    return (f"Question: {q}\nProposed answer: {a}\n"
            "How confident are you that the proposed answer is exactly correct? "
            "Give an integer from 0 (certainly wrong) to 100 (certainly correct).\n"
            'Reply as JSON: {"confidence": <integer>}')


def parse_answer(txt):
    return str(_parse(txt).get("answer", txt))


def parse_conf(txt):
    d = _parse(txt)
    v = d.get("confidence") if isinstance(d, dict) else None
    try:
        v = float(v)
    except (TypeError, ValueError):
        m = re.search(r"\d+(?:\.\d+)?", txt or "")
        v = float(m.group(0)) if m else None
    return None if v is None else max(0.0, min(100.0, v))


def lp_summary(lps):
    """Token log-probs of the greedy JSON output: mean over the tokens that spell the answer value (primary), plus extras."""
    if not lps:
        return None
    toks = [bytes(t["bytes"]) if t.get("bytes") else t["token"].encode("utf-8") for t in lps]
    vals = [float(t["logprob"]) for t in lps]
    full = b"".join(toks)
    ends = np.cumsum([len(t) for t in toks])
    starts = ends - np.array([len(t) for t in toks])
    m = re.search(rb'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', full, re.S)
    sel = []
    if m and m.end(1) > m.start(1):
        a, b = m.span(1)
        sel = [i for i in range(len(toks)) if starts[i] < b and ends[i] > a]
    use = [vals[i] for i in sel] if sel else vals
    return {"lp_ans_mean": float(np.mean(use)), "lp_ans_min": float(np.min(use)), "lp_ans_sum": float(np.sum(use)),
            "lp_all_mean": float(np.mean(vals)), "n_tok": len(vals), "n_ans_tok": len(sel)}


def gen_one(q, qid, extra=None):
    t0 = time.time()
    g_txt, lps = call(b0_prompt(q), logprobs=True)
    g_ans = parse_answer(g_txt)
    item = Item(qid, "sqa", "answerable", q)
    b1_txt, _ = call(_b1_prompt(item))
    d = _parse(b1_txt)
    b1_status = d.get("status", "answer") if isinstance(d, dict) else "answer"
    if b1_status not in ("answer", "unknown", "conflict"):
        b1_status = "answer"
    v_txt, _ = call(verbal_prompt(q, g_ans))
    samples = []
    for s in range(1, K + 1):
        txt, _ = call(b0_prompt(q), temperature=TEMP, seed=SAMPLE_SEED0 + s)
        samples.append({"raw": txt, "answer": parse_answer(txt)})
    rec = {"qid": qid, "question": q, "greedy_raw": g_txt, "greedy_answer": g_ans, "lp": lp_summary(lps),
           "b1_raw": b1_txt, "b1_status": b1_status, "b1_answer": str(d.get("answer", "")) if isinstance(d, dict) else "",
           "verbal_raw": v_txt, "verbal": parse_conf(v_txt), "samples": samples, "secs": round(time.time() - t0, 1)}
    if extra:
        rec.update(extra)
    return rec


def gen():
    from datasets import load_dataset
    os.environ.setdefault("HF_HOME", str(ROOT / "data" / "hf"))
    d = load_dataset("google/simpleqa-verified", split="eval", cache_dir=os.environ["HF_HOME"])
    pool = load_pool()
    split_of = {i: "cal" for i in pool["cal"]} | {i: "test" for i in pool["test"]}
    done = set()
    if GEN.exists():
        done = {json.loads(l)["pos"] for l in open(GEN, encoding="utf-8") if l.strip()}
    todo = [(k, i) for k, i in enumerate(pool["order"]) if i not in done]
    t_start, n_done = time.time(), [0]
    nxt = [0]

    def worker():
        while True:
            with _lock:
                if nxt[0] >= len(todo):
                    return
                k, i = todo[nxt[0]]
                if k >= get_limit():
                    return
                nxt[0] += 1
            row = d[i]                                               # only pool positions are ever read
            rec = gen_one(row["problem"], f"sqa-{row['original_index']}",
                          {"pos": i, "split": split_of[i], "order_idx": k, "gold": row["answer"],
                           "topic": row["topic"], "answer_type": row["answer_type"]})
            with _lock:
                with open(GEN, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_done[0] += 1
                el = time.time() - t_start
                if n_done[0] % 10 == 0:
                    _log(f"done {n_done[0]}/{len(todo)} elapsed {el/60:.1f} min, {el/n_done[0]:.1f}s/question (all workers)")

    _log(f"gen start: {len(todo)} to do, {len(done)} already done, 2 workers")
    with ThreadPoolExecutor(2) as ex:
        futs = [ex.submit(worker) for _ in range(2)]
        for f in futs:
            f.result()
    _log("gen finished")
    FLAG.write_text("done\n")


# ----------------------------------------------------------------------------- embeddings
def _enc(v):
    return base64.b64encode(np.asarray(v, dtype=np.float16).tobytes()).decode()


def _dec(s):
    return np.frombuffer(base64.b64decode(s), dtype=np.float16).astype(np.float32)


def load_gen():
    lim = get_limit()
    pool = load_pool()
    allowed = set(pool["order"][:lim])
    recs = {}
    for l in open(GEN, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            if r["pos"] in allowed:
                recs[r["pos"]] = r
    return recs


def embed():
    recs = load_gen()
    texts = set()
    for r in recs.values():
        for a in [r["greedy_answer"]] + [s["answer"] for s in r["samples"]]:
            if a.strip():
                texts.add(a.strip())
    have = set()
    if EMB.exists():
        have = {json.loads(l)["text"] for l in open(EMB, encoding="utf-8") if l.strip()}
    texts = sorted(texts - have)
    print(len(texts), "texts to embed")
    with open(EMB, "a", encoding="utf-8") as f:
        for i in range(0, len(texts), 32):
            batch = texts[i:i + 32]
            out = _post("/api/embed", {"model": EMB_MODEL, "input": batch})["embeddings"]
            for t, v in zip(batch, out):
                f.write(json.dumps({"text": t, "emb": _enc(v)}, ensure_ascii=False) + "\n")


def load_emb():
    E = {}
    for l in open(EMB, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            v = _dec(r["emb"])
            E[r["text"]] = v / (np.linalg.norm(v) + 1e-9)
    return E


# ----------------------------------------------------------------------------- grading and signals
def is_attempt(ans):
    return bool(ans.strip()) and not UNKNOWN_RE.search(ans)


def grade_rec(r):
    ans = r["greedy_answer"]
    att = is_attempt(ans)
    row = {"gold": [r["gold"]], "status": "answer" if att else "unknown", "answer": ans}
    g = grade(row)
    strict = g == "correct_strict"
    old = g in ("correct_strict", "correct_lenient") or (att and lenient2(r["gold"], ans))
    v3 = grade_v3(row) == "correct"            # PRIMARY label (repaired grader, introduced after the run started)
    return att, bool(v3), bool(strict), bool(old)


def agree_exact(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    return na == nb or matches([na], nb) or matches([nb], na)


def build_table(recs, E):
    """One row per question: label and all raw signals (emb agreement kept per grid threshold)."""
    rows = []
    for pos, r in recs.items():
        att, corr, strict, old = grade_rec(r)
        g = r["greedy_answer"].strip()
        sam = [s["answer"].strip() for s in r["samples"]]
        sc_exact = float(np.mean([agree_exact(g, s) if (s and is_attempt(s)) else False for s in sam])) if att else 0.0
        cos = []
        for s in sam:
            if att and s and is_attempt(s) and g in E and s in E:
                cos.append(float(E[g] @ E[s]))
            else:
                cos.append(-1.0)
        lp = r.get("lp") or {}
        rows.append({"pos": pos, "split": r["split"], "attempt": att, "correct": corr, "correct_old": old, "strict": strict,
                     "b1": 1.0 if r["b1_status"] == "answer" else 0.0, "verbal": r["verbal"],
                     "sc_exact": sc_exact, "cos": cos, "logprob": lp.get("lp_ans_mean"),
                     "lp_all": lp.get("lp_all_mean"), "topic": r.get("topic"), "atype": r.get("answer_type")})
    return rows


# ----------------------------------------------------------------------------- metrics
def auroc(y, s):
    from scipy.stats import rankdata
    y, s = np.asarray(y, bool), np.asarray(s, float)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def boot_auroc(y, s, B=BOOT, seed=0):
    y, s = np.asarray(y, bool), np.asarray(s, float)
    rng = np.random.default_rng(seed)
    n, out = len(y), []
    for _ in range(B):
        i = rng.integers(0, n, n)
        a = auroc(y[i], s[i])
        if not math.isnan(a):
            out.append(a)
    if not out:
        return float("nan"), float("nan")
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def cp(k, n, alpha=0.05):
    from scipy.stats import beta
    if n == 0:
        return float("nan"), float("nan")
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def pick_threshold(s, y, att, target_wrong, n_half):
    """Largest-coverage threshold t (accept s >= t, attempts only) whose calibration wrong-rate <= target_wrong
    (precision >= 1 - target_wrong) with at least ceil(MIN_FRAC * n_half) accepted. None if no such threshold."""
    need = math.ceil(MIN_FRAC * n_half)
    s, y, att = np.asarray(s, float), np.asarray(y, bool), np.asarray(att, bool)
    best = None
    for t in sorted(set(s[att]), reverse=True):
        acc = att & (s >= t)
        n = int(acc.sum())
        if n < need:
            continue
        if 1 - y[acc].sum() / n <= target_wrong + 1e-12:
            best = t                                         # lower t = more coverage; keep scanning
    return best


def apply_threshold(t, s, y, att, n_half):
    if t is None:
        return {"t": None, "n_acc": 0, "k": 0, "coverage": 0.0, "precision": float("nan"), "ci": (float("nan"),) * 2}
    s, y, att = np.asarray(s, float), np.asarray(y, bool), np.asarray(att, bool)
    acc = att & (s >= t)
    n, k = int(acc.sum()), int(y[acc].sum())
    return {"t": float(t), "n_acc": n, "k": k, "coverage": n / n_half,
            "precision": (k / n if n else float("nan")), "ci": cp(k, n)}


def passes(res, base_rate, n_half):
    return (res["n_acc"] >= math.ceil(MIN_FRAC * n_half) and res["precision"] >= PASS_PREC
            and res["ci"][0] > base_rate)


def topk(s, y, att, k):
    s, y, att = np.asarray(s, float), np.asarray(y, bool), np.asarray(att, bool)
    idx = np.where(att)[0]
    if len(idx) == 0:
        return {"n_acc": 0, "k": 0, "precision": float("nan"), "ci": (float("nan"),) * 2}
    kk = min(k, len(idx))
    t = np.sort(s[idx])[::-1][kk - 1]
    acc = att & (s >= t)
    n, c = int(acc.sum()), int(y[acc].sum())
    return {"n_acc": n, "k": c, "precision": c / n, "ci": cp(c, n)}


# ----------------------------------------------------------------------------- analysis
def _arr(rows, key, fill=None):
    v = [r[key] for r in rows]
    if fill is not None:
        v = [fill if x is None else x for x in v]
    return np.array(v, float)


def emb_agree(rows, th):
    return np.array([np.mean([c >= th for c in r["cos"]]) for r in rows], float)


def build_signals(cal, test, lab="correct"):
    """Returns {name: (score_cal, score_test)}, plus info on thresholds/weights chosen on calibration only."""
    info = {}
    ycal = np.array([r[lab] for r in cal], bool)
    attc = np.array([r["attempt"] for r in cal], bool)
    # embedding threshold: best calibration AUROC of agreement fraction among attempts; ties -> stricter threshold
    best = None
    grid = {}
    for th in EMB_GRID:
        a = auroc(ycal[attc], emb_agree(cal, th)[attc])
        grid[th] = a
        if not math.isnan(a) and (best is None or a >= best[1]):
            best = (th, a)
    th = best[0] if best else 0.90
    info["emb_threshold"] = th
    info["emb_grid_cal_auroc"] = grid
    cs, ts = {}, {}
    vmed = float(np.median([r["verbal"] for r in cal if r["verbal"] is not None])) if any(r["verbal"] is not None for r in cal) else 50.0
    lmed = float(np.median([r["logprob"] for r in cal if r["logprob"] is not None])) if any(r["logprob"] is not None for r in cal) else -5.0
    for nm, f in (("b1_status", lambda R: _arr(R, "b1")),
                  ("verbal", lambda R: _arr(R, "verbal", vmed)),
                  ("sc_exact", lambda R: _arr(R, "sc_exact")),
                  ("sc_emb", lambda R: emb_agree(R, th)),
                  ("logprob", lambda R: _arr(R, "logprob", lmed))):
        cs[nm], ts[nm] = f(cal), f(test)
    feats = ["verbal", "sc_exact", "sc_emb", "logprob", "b1_status"]
    Xc = np.column_stack([cs[k] for k in feats])
    Xt = np.column_stack([ts[k] for k in feats])
    mu, sd = Xc[attc].mean(0), Xc[attc].std(0)
    sd[sd == 0] = 1.0
    Zc, Zt = (Xc - mu) / sd, (Xt - mu) / sd
    # combo_z: fit-free mean of the four continuous signals, z-scored with calibration moments
    cs["combo_z"], ts["combo_z"] = Zc[:, :4].mean(1), Zt[:, :4].mean(1)
    # combo_lr: L2 logistic regression (C=0.1) on all five, fitted on calibration attempts only
    from sklearn.linear_model import LogisticRegression
    if ycal[attc].sum() >= 2:
        lr = LogisticRegression(C=0.1, max_iter=1000).fit(Zc[attc], ycal[attc])
        cs["combo_lr"], ts["combo_lr"] = lr.decision_function(Zc), lr.decision_function(Zt)
        info["lr_coef"] = dict(zip(feats, [round(float(c), 3) for c in lr.coef_[0]]))
    else:
        cs["combo_lr"], ts["combo_lr"] = cs["combo_z"], ts["combo_z"]
        info["lr_coef"] = "too few calibration positives; fell back to combo_z"
    return cs, ts, info


def null_pass_rate(ycal, attc, ytest, attt, n_cal, n_test, base_test, reps=2000, seed=1):
    """How often a useless signal (iid random scores) 'passes' with the same procedure: chance level of the pass rule."""
    rng = np.random.default_rng(seed)
    npass = 0
    bud_ok = {b: 0 for b in BUDGETS}
    for _ in range(reps):
        sc, st = rng.random(len(ycal)), rng.random(len(ytest))
        t = pick_threshold(sc, ycal, attc, 1 - PASS_PREC, n_cal)
        res = apply_threshold(t, st, ytest, attt, n_test)
        npass += passes(res, base_test, n_test)
        for b in BUDGETS:
            tb = pick_threshold(sc, ycal, attc, b, n_cal)
            rb = apply_threshold(tb, st, ytest, attt, n_test)
            bud_ok[b] += (rb["n_acc"] >= math.ceil(MIN_FRAC * n_test) and rb["precision"] >= 1 - b)
    return npass / reps, {b: v / reps for b, v in bud_ok.items()}


def f3(x):
    return "nan" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def pct(x):
    return "nan" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100*x:.1f}%"


def analyze(lab="correct", tag=""):
    recs = load_gen()
    E = load_emb()
    rows = build_table(recs, E)
    cal = sorted([r for r in rows if r["split"] == "cal"], key=lambda r: r["pos"])
    test = sorted([r for r in rows if r["split"] == "test"], key=lambda r: r["pos"])
    n_cal, n_test = len(cal), len(test)
    ycal, yt = np.array([r[lab] for r in cal], bool), np.array([r[lab] for r in test], bool)
    attc, attt = np.array([r["attempt"] for r in cal], bool), np.array([r["attempt"] for r in test], bool)
    base_test = yt.sum() / n_test
    cs, ts, info = build_signals(cal, test, lab)
    out = {"n_cal": n_cal, "n_test": n_test, "info": {k: v for k, v in info.items()}}
    L = []
    P = L.append
    P(f"## Data (label = {'grade_v3 (primary)' if lab == 'correct' else 'old graders: strict/lenient/lenient2 (secondary)'})")
    P(f"- Questions analysed: calibration {n_cal}, test {n_test} (pool limit file: {get_limit()}).")
    P(f"- Greedy answer attempted (not an abstention): cal {attc.sum()}/{n_cal}, test {attt.sum()}/{n_test}.")
    P(f"- Correct (label above): cal {ycal.sum()}/{n_cal} ({pct(ycal.mean())}), test {yt.sum()}/{n_test} ({pct(base_test)}); "
      f"strict only: cal {sum(r['strict'] for r in cal)}, test {sum(r['strict'] for r in test)}.")
    P(f"- Verbalized confidence parsed: cal {sum(r['verbal'] is not None for r in cal)}/{n_cal}, test {sum(r['verbal'] is not None for r in test)}/{n_test}; "
      f"logprobs present: cal {sum(r['logprob'] is not None for r in cal)}, test {sum(r['logprob'] is not None for r in test)}.")
    P(f"- Embedding agreement threshold chosen on calibration: {info['emb_threshold']} (calibration AUROC per grid value: "
      + ", ".join(f"{k}: {f3(v)}" for k, v in info["emb_grid_cal_auroc"].items()) + ").")
    P(f"- Logistic-regression coefficients (standardised features, fitted on calibration): {info['lr_coef']}.")
    P("")
    # AUROC
    P("## AUROC for 'greedy answer is correct' (attempted answers only)")
    P("| signal | AUROC test | 95% bootstrap CI | AUROC calibration (fit half, descriptive) |")
    P("|---|---|---|---|")
    out["auroc"] = {}
    for nm in SIGNALS:
        a = auroc(yt[attt], ts[nm][attt])
        lo, hi = boot_auroc(yt[attt], ts[nm][attt], seed=11)
        ac = auroc(ycal[attc], cs[nm][attc])
        out["auroc"][nm] = {"test": a, "lo": lo, "hi": hi, "cal": ac}
        P(f"| {nm} | {f3(a)} | [{f3(lo)}, {f3(hi)}] | {f3(ac)} |")
    P("")
    # calibrated thresholds
    null_p, null_b = null_pass_rate(ycal, attc, yt, attt, n_cal, n_test, base_test)
    out["null"] = {"pass": null_p, "budget_ok": {str(k): v for k, v in null_b.items()}}
    P("## Thresholds fitted on calibration, applied to test")
    P(f"Rule: accept an answer if signal >= t. t = the lowest threshold whose calibration precision meets the target with at least "
      f"{math.ceil(MIN_FRAC*n_cal)} accepted answers (2% of the half). Coverage = accepted / all {n_test} test questions. "
      f"Precision CI: Clopper-Pearson 95%. Test base rate (correct / all questions) = {pct(base_test)}.")
    P("")
    P("| signal | target | t (cal) | accepted (test) | correct | coverage | precision | 95% CI | meets target (point) | passes S3 rule |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    out["calibrated"] = {}
    for nm in SIGNALS:
        for lab, tw in (("S3 rule: precision>=30%", 1 - PASS_PREC), ("wrong<=25%", 0.25), ("wrong<=10%", 0.10)):
            t = pick_threshold(cs[nm], ycal, attc, tw, n_cal)
            res = apply_threshold(t, ts[nm], yt, attt, n_test)
            meets = res["n_acc"] >= math.ceil(MIN_FRAC * n_test) and res["precision"] >= 1 - tw
            ps = passes(res, base_test, n_test) if lab.startswith("S3") else None
            out["calibrated"][f"{nm}|{lab}"] = {**res, "meets": bool(meets), "passes": ps}
            if t is None:
                P(f"| {nm} | {lab} | none feasible | 0 | 0 | 0.0% | n/a | n/a | no | {'no' if ps is not None else ''} |")
            else:
                P(f"| {nm} | {lab} | {t:.3f} | {res['n_acc']} | {res['k']} | {pct(res['coverage'])} | {pct(res['precision'])} | "
                  f"[{pct(res['ci'][0])}, {pct(res['ci'][1])}] | {'yes' if meets else 'no'} | "
                  f"{'' if ps is None else ('YES' if ps else 'no')} |")
    P("")
    P(f"Chance level of this procedure (iid random scores, same labels and splits, 2000 simulations): P(passes S3 rule) = {pct(null_p)}; "
      f"P(meets wrong<=25% target on test with >=2% coverage) = {pct(null_b[0.25])}; P(meets wrong<=10%) = {pct(null_b[0.10])}.")
    P("")
    # risk-coverage
    P("## Risk-coverage table on test (top-k by signal; operating points chosen ON TEST, so optimistic and descriptive)")
    ks = [(math.ceil(0.02 * n_test), "2%"), (math.ceil(0.05 * n_test), "5%"), (math.ceil(0.10 * n_test), "10%"),
          (math.ceil(0.20 * n_test), "20%"), (math.ceil(0.50 * n_test), "50%"), (10 ** 6, "all attempted")]
    P("| signal | " + " | ".join(f"top {lab}" for _, lab in ks) + " |")
    P("|---|" + "---|" * len(ks))
    out["riskcov"] = {}
    for nm in SIGNALS:
        cells = []
        for k, lab in ks:
            r = topk(ts[nm], yt, attt, k)
            out["riskcov"][f"{nm}|{lab}"] = r
            cells.append(f"{r['k']}/{r['n_acc']} = {pct(r['precision'])} [{pct(r['ci'][0])}, {pct(r['ci'][1])}]")
        P(f"| {nm} | " + " | ".join(cells) + " |")
    P("")
    P("Cell format: correct / accepted = precision [95% CI]. Ties at the cut are all accepted, so 'accepted' can exceed the nominal k "
      "(discrete signals such as b1_status and sc_exact).")
    ex = []
    for nm in SIGNALS:
        for k, lab in ks[:5]:
            r = topk(ts[nm], yt, attt, k)
            if r["n_acc"] >= math.ceil(MIN_FRAC * n_test) and r["precision"] >= PASS_PREC and r["ci"][0] > base_test:
                ex.append(f"{nm} (top {lab}: {r['k']}/{r['n_acc']})")
    P("")
    P("Optimistic (test-selected) version of the S3 rule, NOT the pre-registered one: signals with some top-k point satisfying "
      "precision>=30%, >=2% coverage and CP lower bound above base rate: " + (", ".join(ex) if ex else "none") + ".")
    out["optimistic_pass"] = ex
    P("")
    # base-rate context
    P("## Context")
    P(f"- Distribution of sc_exact among test attempts: " + ", ".join(
        f"{v:.3f}: {int(((ts['sc_exact'] == v) & attt).sum())}" for v in sorted(set(ts['sc_exact'][attt]))) + ".")
    full_agree = (ts["sc_exact"] == 1.0) & attt
    P(f"- Test answers with all {K} samples agreeing exactly: {int(full_agree.sum())}, of which correct {int(yt[full_agree].sum())}.")
    ver = np.array([r["verbal"] if r["verbal"] is not None else np.nan for r in test])
    P(f"- Verbalized confidence on test attempts: median {np.nanmedian(ver[attt]):.0f}, share >= 80: {np.nanmean(ver[attt] >= 80):.2f}.")
    (RUNS / f"s3_metrics{tag}.json").write_text(json.dumps(out, indent=1, default=lambda o: None if isinstance(o, float) and math.isnan(o) else str(o)), encoding="utf-8")
    body = "\n".join(L)
    (RUNS / f"s3_tables{tag}.md").write_text(body, encoding="utf-8")
    print(body)


# ----------------------------------------------------------------------------- selftest
def selftest():
    rng = np.random.default_rng(0)
    y = rng.random(2000) < 0.1
    s = rng.random(2000) + y * 1.0
    print("auroc informative", round(auroc(y, s), 3), "random", round(auroc(y, rng.random(2000)), 3))
    print("cp(3,10)", cp(3, 10), "cp(0,10)", cp(0, 10))
    att = np.ones(2000, bool)
    t = pick_threshold(s, y, att, 0.7, 1000)
    print("threshold", t, apply_threshold(t, s, y, att, 2000))
    print("topk", topk(s, y, att, 50))
    toks = [{"token": '{"', "logprob": -0.1, "bytes": [123, 34]}, {"token": "answer", "logprob": -0.0, "bytes": list(b"answer")},
            {"token": '":', "logprob": 0, "bytes": [34, 58]}, {"token": ' "', "logprob": 0, "bytes": [32, 34]},
            {"token": "Par", "logprob": -2.0, "bytes": list(b"Par")}, {"token": "is", "logprob": -1.0, "bytes": list(b"is")},
            {"token": '"}', "logprob": -0.5, "bytes": [34, 125]}]
    print("lp", lp_summary(toks))
    print("agree", agree_exact("Paris", "paris, France"), agree_exact("1987", "1988"), agree_exact("John", "Sir John Smith"))
    print("pool", {k: len(v) for k, v in make_pool().items()})


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "analyze":
        analyze("correct", "")
        print("\n\n=========== SECONDARY: old graders ===========\n")
        analyze("correct_old", "_oldgrader")
    else:
        {"plan": plan, "gen": gen, "embed": embed, "selftest": selftest}[stage]()
