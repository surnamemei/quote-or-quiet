"""S5a: question-text-only baseline. How well do features of the QUESTION alone predict (A) greedy-correct and (B) "known" (any of 9 answers correct)?

The model's activations and answers are NOT used as features here, except in the explicitly separate "S3 signals" comparison.
Protocol and pre-registered predictions: docs/S5a_QUESTION_BASELINE.md (hashes at the top). One command reproduces everything:

    python -B -m vkg.qbaseline all          # embed (cached) -> repeated CV -> 250/250 split -> tables
    python -B -m vkg.qbaseline embed|cv|split|tables   # individual stages

Only the small embedder qwen3-embedding:0.6b is called (never the 27B). The 300 forbidden test ids are used only in an assertion
(the 500 pool questions must be disjoint from them); they are never read, embedded or printed. grade_v3 / vkg.signals are black boxes.
"""
import os
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import base64
import json
import math
import random
import re
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import requests

from .grade_open import grade_v3
from .signals import GEN, POOL, build_table, load_emb, emb_agree, is_attempt   # black boxes (read-only reuse)

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "runs"
QEMB = RUNS / "s5a_question_embeddings.jsonl"
OOF = RUNS / "s5a_oof.npz"
METRICS = RUNS / "s5a_metrics.json"
TABLES = RUNS / "s5a_tables.md"
HOST = "http://localhost:11434"
EMB_MODEL = "qwen3-embedding:0.6b"

R_REPEATS = 20            # repeated stratified 5-fold CV, seeds 0..19
OUTER_K = 5
INNER_K = 3
BOOT = 2000
SC_EMB_TH = 0.90          # the S3 embedding-agreement threshold (chosen by S3 on its calibration half; fixed here)
GRID_TFIDF = [0.1, 1.0, 10.0, 100.0]
GRID_DENSE = [1e-3, 1e-2, 1e-1, 1.0, 10.0]
GRID_WIDE = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]       # many standardised columns (embedding): need stronger shrinkage
GRID_S3 = [1e-2, 1e-1, 1.0, 10.0]


# ----------------------------------------------------------------------------- data and labels
def load_data():
    recs = [json.loads(l) for l in open(GEN, encoding="utf-8") if l.strip()]
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    forbidden = set(random.Random(3000).sample(range(1000), 300))
    pos = [r["pos"] for r in recs]
    assert len(recs) == 500 and len(set(pos)) == 500
    assert not (set(pos) & forbidden), "pool overlaps the forbidden ids"
    assert set(pos) == set(pool["cal"]) | set(pool["test"])
    recs.sort(key=lambda r: r["pos"])
    return recs, pool


def answers_correct(r):
    """grade_v3 for greedy + 8 samples, mirroring vkg.signals.grade_rec (attempt = non-empty and not UNKNOWN_RE)."""
    out = []
    for a in [r["greedy_answer"]] + [s["answer"] for s in r["samples"]]:
        att = is_attempt(a)
        row = {"gold": [r["gold"]], "status": "answer" if att else "unknown", "answer": a}
        out.append(grade_v3(row) == "correct")
    return out


def labels(recs):
    yA, yB, nc = [], [], []
    for r in recs:
        c = answers_correct(r)
        yA.append(c[0])
        yB.append(any(c))
        nc.append(sum(c))
    return np.array(yA, bool), np.array(yB, bool), np.array(nc)


# ----------------------------------------------------------------------------- question embeddings (qwen3-embedding:0.6b)
def _post(path, payload, timeout=600, max_wait=3600):
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
        print("retry in", delay, "s:", err, flush=True)
        time.sleep(delay)
        delay = min(delay * 2, 120)


def embed_questions():
    recs, _ = load_data()
    have = set()
    if QEMB.exists():
        have = {json.loads(l)["qid"] for l in open(QEMB, encoding="utf-8") if l.strip()}
    todo = [r for r in recs if r["qid"] not in have]
    print(len(todo), "questions to embed", flush=True)
    with open(QEMB, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), 25):
            b = todo[i:i + 25]
            out = _post("/api/embed", {"model": EMB_MODEL, "input": [r["question"] for r in b]})["embeddings"]
            assert len(out) == len(b)
            for r, v in zip(b, out):
                f.write(json.dumps({"qid": r["qid"], "emb": base64.b64encode(np.asarray(v, np.float32).tobytes()).decode()}) + "\n")


def load_qemb(recs):
    d = {}
    for l in open(QEMB, encoding="utf-8"):
        if l.strip():
            j = json.loads(l)
            d[j["qid"]] = np.frombuffer(base64.b64decode(j["emb"]), dtype=np.float32).copy()
    return np.stack([d[r["qid"]] for r in recs])


# ----------------------------------------------------------------------------- features (question side only)
_YEAR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
_WH = ["what", "which", "who", "when", "where", "how", "in", "on", "other"]


def lex_features(q):
    toks = re.findall(r"[A-Za-z0-9'’\-\.]+", q)
    words = q.split()
    caps = sum(1 for i, w in enumerate(words) if i > 0 and w[:1].isupper())
    first = words[0].lower().strip("?,.") if words else ""
    wh = first if first in _WH[:-1] else "other"
    return [math.log(len(q) + 1), len(words), caps, caps / max(len(words), 1), len(_YEAR.findall(q)), float(bool(_YEAR.search(q))),
            sum(c.isdigit() for c in q), q.count(","), q.count('"') + q.count("'") + q.count("“"),
            float(np.mean([len(w) for w in words])) if words else 0.0] + [float(wh == w) for w in _WH]


LEX_NAMES = ["log_chars", "n_words", "n_cap", "cap_ratio", "n_years", "has_year", "n_digits", "n_commas", "n_quotes", "mean_wordlen"] + ["wh_" + w for w in _WH]


def build_features(recs):
    q = [r["question"] for r in recs]
    lex = np.array([lex_features(x) for x in q], float)
    topics = sorted({r["topic"] for r in recs})
    atypes = sorted({r["answer_type"] for r in recs})
    meta = np.array([[float(r["topic"] == t) for t in topics] + [float(r["answer_type"] == a) for a in atypes] for r in recs], float)
    emb = load_qemb(recs)
    return {"q": np.array(q, dtype=object), "lex": lex, "meta": meta, "emb": emb,
            "meta_names": ["topic=" + t for t in topics] + ["atype=" + a for a in atypes]}


def s3_matrix(recs):
    """The five S3 single signals per question (b1_status, verbal, sc_exact, sc_emb@0.90, logprob), standardised inside each fold later."""
    E = load_emb()
    rows = build_table(recs_to_dict(recs), E)
    rows.sort(key=lambda r: r["pos"])
    assert [r["pos"] for r in rows] == [r["pos"] for r in recs]
    cols = []
    for r in rows:
        assert r["verbal"] is not None and r["logprob"] is not None
        cols.append([r["verbal"], r["sc_exact"], float(np.mean([c >= SC_EMB_TH for c in r["cos"]])), r["logprob"], r["b1"]])
    return np.array(cols, float), ["verbal", "sc_exact", "sc_emb", "logprob", "b1_status"]


def recs_to_dict(recs):
    return {r["pos"]: r for r in recs}


# ----------------------------------------------------------------------------- classifiers
def _gs(pipe, grid, seed):
    from sklearn.model_selection import GridSearchCV, StratifiedKFold
    return GridSearchCV(pipe, {"lr__C": grid}, cv=StratifiedKFold(INNER_K, shuffle=True, random_state=seed), scoring="roc_auc", refit=True, n_jobs=1)


def _dense_pipe():
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    return Pipeline([("sc", StandardScaler()), ("lr", LogisticRegression(class_weight="balanced", max_iter=3000))])


def _tfidf_pipe():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    return Pipeline([("tf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
                     ("lr", LogisticRegression(class_weight="balanced", max_iter=3000))])


def fit_score(spec, tr, te, y, seed):
    """Fit on training rows `tr` (inner CV for C inside them only), return decision scores for `te`."""
    kind = spec["kind"]
    if kind == "tfidf":
        gs = _gs(_tfidf_pipe(), GRID_TFIDF, seed).fit(spec["X"][tr], y[tr])
        return gs.decision_function(spec["X"][te])
    if kind == "dense":
        gs = _gs(_dense_pipe(), spec["grid"], seed).fit(spec["X"][tr], y[tr])
        return gs.decision_function(spec["X"][te])
    if kind == "stack":
        from sklearn.base import clone
        from sklearn.model_selection import StratifiedKFold, cross_val_predict
        base = spec["base"]
        pipe, grid = (_tfidf_pipe(), GRID_TFIDF) if base["kind"] == "tfidf" else (_dense_pipe(), base["grid"])
        gs = _gs(pipe, grid, seed).fit(base["X"][tr], y[tr])
        q_te = gs.decision_function(base["X"][te])
        q_tr = cross_val_predict(clone(gs.best_estimator_), base["X"][tr], y[tr], method="decision_function",
                                 cv=StratifiedKFold(5, shuffle=True, random_state=seed + 7))
        Ftr = np.column_stack([spec["S3"][tr], q_tr])
        Fte = np.column_stack([spec["S3"][te], q_te])
        gs2 = _gs(_dense_pipe(), GRID_S3, seed).fit(Ftr, y[tr])
        return gs2.decision_function(Fte)
    raise ValueError(kind)


def make_specs(F, S3):
    d = lambda X, grid=GRID_DENSE: {"kind": "dense", "X": X, "grid": grid}
    lexmeta = np.hstack([F["lex"], F["meta"]])
    embfull = np.hstack([F["emb"], lexmeta])
    rng = np.random.default_rng(12345)
    specs = {
        "tfidf": {"kind": "tfidf", "X": F["q"]},
        "lex": d(F["lex"]),
        "meta": d(F["meta"]),
        "lex_meta": d(lexmeta),
        "emb": d(F["emb"], GRID_WIDE),
        "emb_lex_meta": d(embfull, GRID_WIDE),
        "ctrl_random16": d(rng.standard_normal((len(F["q"]), 16))),
        "ctrl_random1024": d(rng.standard_normal((len(F["q"]), 1024)), GRID_WIDE),
        "ctrl_shuffle_emb": d(F["emb"], GRID_WIDE),            # labels permuted inside run_task
        "ctrl_shuffle_lex_meta": d(lexmeta),
        "S3": d(S3, GRID_S3),
        "S3+lex_meta": d(np.hstack([S3, lexmeta]), GRID_DENSE),
        "S3+stack_emb": {"kind": "stack", "base": d(F["emb"], GRID_WIDE), "S3": S3},
        "S3+stack_lex_meta": {"kind": "stack", "base": d(lexmeta), "S3": S3},
        "S3+stack_tfidf": {"kind": "stack", "base": {"kind": "tfidf", "X": F["q"]}, "S3": S3},
    }
    return specs


# ----------------------------------------------------------------------------- metrics
def auroc_rows(S, y):
    """AUROC of each row of S (R x n) against bool y (n,), tie-aware."""
    from scipy.stats import rankdata
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.full(S.shape[0], np.nan)
    r = rankdata(S, axis=1)
    return (r[:, y].sum(1) - n1 * (n1 + 1) / 2) / (n1 * n0)


def ap_rows(S, y):
    n1 = int(y.sum())
    if n1 == 0:
        return np.full(S.shape[0], np.nan)
    order = np.argsort(-S, axis=1, kind="stable")
    yo = y[order].astype(float)
    prec = np.cumsum(yo, 1) / np.arange(1, S.shape[1] + 1)
    return (prec * yo).sum(1) / n1


def boot_idx(n, B=BOOT, seed=2026):
    rng = np.random.default_rng(seed)
    return [rng.integers(0, n, n) for _ in range(B)]


def boot_stats(S, y, idxs):
    """Mean over repeats (rows of S) of AUROC / AP per bootstrap resample of the questions. Returns arrays (B,)."""
    A, P = [], []
    for ix in idxs:
        yy = y[ix]
        if yy.sum() == 0 or yy.sum() == len(yy):
            A.append(np.nan)
            P.append(np.nan)
            continue
        A.append(np.nanmean(auroc_rows(S[:, ix], yy)))
        P.append(np.nanmean(ap_rows(S[:, ix], yy)))
    return np.array(A), np.array(P)


def pct(a):
    a = a[~np.isnan(a)]
    return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]


# ----------------------------------------------------------------------------- repeated CV
def run_task(args):
    lab, name, rep, seedbase = args
    y, spec = _G["y"][lab], _G["specs"][name]
    n = len(y)
    from sklearn.model_selection import StratifiedKFold
    ylab = y
    if name.startswith("ctrl_shuffle"):
        ylab = np.random.default_rng(777 + rep).permutation(y)          # break the feature-label link, same base rate
    skf = StratifiedKFold(OUTER_K, shuffle=True, random_state=rep)
    oof = np.zeros(n)
    fold_auc = []
    for k, (tr, te) in enumerate(skf.split(np.zeros(n), ylab)):
        oof[te] = fit_score(spec, tr, te, ylab, seedbase + 10 * rep + k)
        if ylab[te].sum() > 0:
            fold_auc.append(float(auroc_rows(oof[te][None, :], ylab[te])[0]))
    return lab, name, rep, oof, float(np.mean(fold_auc)), ylab


_G = {}


def init_G():
    recs, _ = load_data()
    yA, yB, _ = labels(recs)
    F = build_features(recs)
    S3, _ = s3_matrix(recs)
    _G.update({"y": {"A": yA, "B": yB}, "specs": make_specs(F, S3), "F": F, "S3": S3, "recs": recs})


def cv_stage(reps=R_REPEATS, names=None):
    from joblib import Parallel, delayed
    init_G()
    specs = _G["specs"]
    names = names or list(specs)
    tasks = [(lab, nm, r, 100) for lab in ("A", "B") for nm in names for r in range(reps)]
    t0 = time.time()
    res = Parallel(n_jobs=24, backend="loky", initializer=None)(delayed(_run_in_worker)(t) for t in tasks)
    print("cv done in %.0fs, %d tasks" % (time.time() - t0, len(tasks)), flush=True)
    store = {}
    for lab, nm, rep, oof, fa, ylab in res:
        d = store.setdefault((lab, nm), {"oof": np.zeros((reps, len(oof))), "fa": np.zeros(reps), "y": None})
        d["oof"][rep] = oof
        d["fa"][rep] = fa
        if nm.startswith("ctrl_shuffle"):
            d.setdefault("ys", np.zeros((reps, len(oof)), bool))[rep] = ylab
    np.savez_compressed(OOF, **{f"{lab}|{nm}|oof": d["oof"] for (lab, nm), d in store.items()},
                        **{f"{lab}|{nm}|fa": d["fa"] for (lab, nm), d in store.items()},
                        **{f"{lab}|{nm}|ys": d["ys"] for (lab, nm), d in store.items() if "ys" in d})
    return store


def _run_in_worker(t):
    if not _G:
        init_G()
    return run_task(t)


# ----------------------------------------------------------------------------- summarise
def summarise_cv():
    init_G()
    Z = np.load(OOF)
    idxs = boot_idx(500)
    out = {"cv": {}, "delta": {}, "n_pos": {}, "reps": R_REPEATS, "boot": BOOT}
    yy = _G["y"]
    for lab in ("A", "B"):
        out["n_pos"][lab] = int(yy[lab].sum())
    names = [k.split("|")[1] for k in Z.files if k.startswith("A|") and k.endswith("|oof")]
    boots = {}
    for lab in ("A", "B"):
        y = yy[lab]
        for nm in names:
            S = Z[f"{lab}|{nm}|oof"]
            if nm.startswith("ctrl_shuffle"):
                # each repeat has its own permuted labels: bootstrap questions, score each repeat against its own permuted labels
                Ys = Z[f"{lab}|{nm}|ys"]
                A_b, P_b = [], []
                for ix in idxs:
                    a = [auroc_rows(S[r:r + 1, ix], Ys[r][ix])[0] for r in range(S.shape[0])]
                    p = [ap_rows(S[r:r + 1, ix], Ys[r][ix])[0] for r in range(S.shape[0])]
                    A_b.append(np.nanmean(a)); P_b.append(np.nanmean(p))
                A_b, P_b = np.array(A_b), np.array(P_b)
                aucs = np.array([auroc_rows(S[r:r + 1], Ys[r])[0] for r in range(S.shape[0])])
                aps = np.array([ap_rows(S[r:r + 1], Ys[r])[0] for r in range(S.shape[0])])
            else:
                A_b, P_b = boot_stats(S, y, idxs)
                aucs, aps = auroc_rows(S, y), ap_rows(S, y)
            boots[(lab, nm)] = (A_b, P_b)
            out["cv"][f"{lab}|{nm}"] = {"auroc": float(aucs.mean()), "auroc_ci": pct(A_b), "auroc_sd_over_repeats": float(aucs.std(ddof=1)),
                                         "ap": float(aps.mean()), "ap_ci": pct(P_b), "auroc_perfold_mean": float(Z[f"{lab}|{nm}|fa"].mean()),
                                         "n_pos": int(y.sum()), "base_rate": float(y.mean())}
    pairs = [("S3+stack_emb", "S3"), ("S3+stack_lex_meta", "S3"), ("S3+stack_tfidf", "S3"), ("S3+lex_meta", "S3"),
             ("emb", "lex_meta"), ("emb", "tfidf"), ("emb_lex_meta", "emb"), ("emb", "ctrl_random1024")]
    for lab in ("A", "B"):
        for a, b in pairs:
            dA = boots[(lab, a)][0] - boots[(lab, b)][0]
            dP = boots[(lab, a)][1] - boots[(lab, b)][1]
            out["delta"][f"{lab}|{a} - {b}"] = {"dauroc": float(out["cv"][f"{lab}|{a}"]["auroc"] - out["cv"][f"{lab}|{b}"]["auroc"]), "dauroc_ci": pct(dA),
                                                 "dap": float(out["cv"][f"{lab}|{a}"]["ap"] - out["cv"][f"{lab}|{b}"]["ap"]), "dap_ci": pct(dP)}
    # unfitted single S3 signals over all 500 (descriptive; for label B the sc_* signals share the 8 samples that define B: circular)
    S3 = _G["S3"]
    single = {}
    for lab in ("A", "B"):
        y = yy[lab]
        for j, nm in enumerate(["verbal", "sc_exact", "sc_emb", "logprob", "b1_status"]):
            s = S3[:, j]
            a_b = np.array([auroc_rows(s[ix][None, :], y[ix])[0] if 0 < y[ix].sum() < len(ix) else np.nan for ix in idxs])
            single[f"{lab}|{nm}"] = {"auroc": float(auroc_rows(s[None, :], y)[0]), "ci": pct(a_b)}
    out["s3_single_unfitted_all500"] = single
    out["label_counts"] = {"A": int(yy["A"].sum()), "B": int(yy["B"].sum())}
    METRICS.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


# ----------------------------------------------------------------------------- original cal -> test split (secondary)
def split_stage():
    init_G()
    recs = _G["recs"]
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    cal = np.array([r["pos"] in set(pool["cal"]) for r in recs])
    tr, te = np.where(cal)[0], np.where(~cal)[0]
    out = {"n_cal": int(len(tr)), "n_test": int(len(te)), "rows": {}}
    idxs = boot_idx(len(te), seed=909)
    for lab in ("A", "B"):
        y = _G["y"][lab]
        out["rows"][lab] = {"cal_pos": int(y[tr].sum()), "test_pos": int(y[te].sum()), "test_base": float(y[te].mean())}
        for nm, spec in _G["specs"].items():
            ylab = np.random.default_rng(777).permutation(y) if nm.startswith("ctrl_shuffle") else y
            s = fit_score(spec, tr, te, ylab, 55)
            yt = ylab[te]
            a_b, p_b = boot_stats(s[None, :], yt, idxs)
            out["rows"][lab][nm] = {"auroc": float(auroc_rows(s[None, :], yt)[0]), "auroc_ci": pct(a_b),
                                     "ap": float(ap_rows(s[None, :], yt)[0]), "ap_ci": pct(p_b)}
    (RUNS / "s5a_split_metrics.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


# ----------------------------------------------------------------------------- tables
ORDER = ["tfidf", "lex", "meta", "lex_meta", "emb", "emb_lex_meta", "ctrl_random16", "ctrl_random1024", "ctrl_shuffle_emb", "ctrl_shuffle_lex_meta",
         "S3", "S3+lex_meta", "S3+stack_emb", "S3+stack_lex_meta", "S3+stack_tfidf"]


def tables():
    m = json.loads(METRICS.read_text(encoding="utf-8"))
    sp = json.loads((RUNS / "s5a_split_metrics.json").read_text(encoding="utf-8"))
    L = [f"# S5a tables (generated by vkg/qbaseline.py; {m['reps']} repeats of stratified 5-fold CV, {m['boot']} bootstrap resamples)\n"]
    L.append(f"Label counts: A (greedy correct, grade_v3) = {m['label_counts']['A']}/500, B (any of 9 answers correct) = {m['label_counts']['B']}/500.\n")
    for lab, desc in (("A", "A: greedy answer correct"), ("B", "B: known (>=1 of 9 answers correct)")):
        L.append(f"\n## Repeated CV, label {desc}\n")
        L.append("| model | positives/n (base rate) | AUROC mean [95% boot CI] | SD over repeats | AP mean [95% boot CI] | mean per-fold AUROC |")
        L.append("|---|---|---|---|---|---|")
        for nm in ORDER:
            c = m["cv"][f"{lab}|{nm}"]
            L.append(f"| {nm} | {c['n_pos']}/500 ({c['base_rate']:.3f}) | {c['auroc']:.3f} [{c['auroc_ci'][0]:.3f}, {c['auroc_ci'][1]:.3f}] | {c['auroc_sd_over_repeats']:.3f} | "
                     f"{c['ap']:.3f} [{c['ap_ci'][0]:.3f}, {c['ap_ci'][1]:.3f}] | {c['auroc_perfold_mean']:.3f} |")
        L.append(f"\nPaired differences, label {lab} (same bootstrap resamples):\n")
        L.append("| comparison | dAUROC [95% CI] | dAP [95% CI] |")
        L.append("|---|---|---|")
        for k, v in m["delta"].items():
            if k.startswith(lab + "|"):
                L.append(f"| {k[2:]} | {v['dauroc']:+.3f} [{v['dauroc_ci'][0]:+.3f}, {v['dauroc_ci'][1]:+.3f}] | {v['dap']:+.3f} [{v['dap_ci'][0]:+.3f}, {v['dap_ci'][1]:+.3f}] |")
        L.append(f"\nUnfitted single S3 signals over all 500 questions, label {lab}" + (" (CIRCULAR for B: sc_exact and sc_emb are computed from the same 8 samples that define B)" if lab == "B" else "") + ":\n")
        L.append("| signal | AUROC [95% boot CI] | positives/n |")
        L.append("|---|---|---|")
        for nm in ["verbal", "sc_exact", "sc_emb", "logprob", "b1_status"]:
            c = m["s3_single_unfitted_all500"][f"{lab}|{nm}"]
            L.append(f"| {nm} | {c['auroc']:.3f} [{c['ci'][0]:.3f}, {c['ci'][1]:.3f}] | {m['n_pos'][lab]}/500 |")
    L.append("\n## Original S3 split: fit on calibration (250), score the test half (250)\n")
    for lab in ("A", "B"):
        r = sp["rows"][lab]
        L.append(f"\nLabel {lab}: calibration positives {r['cal_pos']}/250, test positives {r['test_pos']}/250 (test base rate {r['test_base']:.3f}).\n")
        L.append("| model | test AUROC [95% boot CI] | test AP [95% boot CI] |")
        L.append("|---|---|---|")
        for nm in ORDER:
            c = r[nm]
            L.append(f"| {nm} | {c['auroc']:.3f} [{c['auroc_ci'][0]:.3f}, {c['auroc_ci'][1]:.3f}] | {c['ap']:.3f} [{c['ap_ci'][0]:.3f}, {c['ap_ci'][1]:.3f}] |")
    TABLES.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    st = sys.argv[1] if len(sys.argv) > 1 else "all"
    if st in ("embed", "all"):
        embed_questions()
    if st in ("cv", "all"):
        cv_stage()
        summarise_cv()
    if st == "summarise":
        summarise_cv()
    if st in ("split", "all"):
        split_stage()
    if st in ("tables", "all"):
        tables()
    if st == "labels":
        recs, _ = load_data()
        yA, yB, nc = labels(recs)
        print("A", int(yA.sum()), "B", int(yB.sum()), "counts", np.bincount(nc, minlength=10).tolist())
