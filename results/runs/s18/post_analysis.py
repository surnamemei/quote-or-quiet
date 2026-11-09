"""S18 post-verdict analyses (pre-specified in docs/S18_PROTOCOL.md as sensitivity / secondary): L1-A for G2 (R6),
contamination share (R7), and the list of released-but-wrong G3/G2 answers for the L3 assumption audit (R4)."""
import json, sys
import numpy as np
from vkg import s18_eval as E, s17_eval as S
rows = E.load(["fresh3", "fresh4"])
G = E.gated(rows)
n = len(G)
rng = np.random.default_rng(0)
out = []
for k, base in ((2, "wiki_plain"), (2, "combo_plain"), (2, "MSany"), (3, "wiki_plain")):
    a = np.array([bool(g["released"]) and g["support"] >= k for g in G])
    c = np.array([a[i] and G[i]["graded"] is True for i in range(n)])
    e = np.array([a[i] and G[i]["graded"] is False for i in range(n)])
    ab, cb, eb = S.outcomes(rows, S.SYSTEMS[base])
    s = S.lo_hi(e.astype(float) - 0.5 * eb.astype(float), rng)
    y = S.lo_hi(c.astype(int) - cb.astype(int), rng)
    cov = a.mean() - ab.mean()
    ok = (s[2] < 0, y[0] >= 0 and y[1] > -0.03, cov >= -0.03)
    out.append(f"G{k} vs {base}: (a) mean(e-0.5e_b) {s[0]:+.4f} up {s[2]:+.4f} {'pass' if ok[0] else 'fail'}; "
               f"(b) correct diff {y[0]:+.3f} lo {y[1]:+.3f} {'pass' if ok[1] else 'fail'}; (c) coverage diff {cov:+.3f} "
               f"{'pass' if ok[2] else 'fail'} -> {'MET' if all(ok) else 'NOT MET'}")
kept = sum(len(r["web_kept"]) for r in rows); drop = sum(len(r["web_dropped"]) for r in rows)
out.append(f"contamination: dropped {drop} of {kept + drop} fetched pages with text = {drop / max(1, kept + drop):.4f}")
print("\n".join(out))
with open(E.OUT / "released_wrong.jsonl", "w", encoding="utf-8") as f:
    for g in G:
        if g["released"] and g["graded"] is False:
            f.write(json.dumps({k: g[k] for k in ("id", "set", "stratum", "support", "question", "gold", "released", "doc", "span", "reason")}, ensure_ascii=False) + "\n")
