"""S19 design re-measurement on DEV + FRESH with DuckDuckGo evidence (docs/S19_DESIGN.md): the L2 system (L3 gate V1-V5 +
G3 + Phi-4 cautious veto) and its parts, plus the L1 baselines, from results/runs/s19/{dev,fresh}_outputs.jsonl.
Cached judge labels only. usage: OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s19/design_eval.py"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())
from vkg import l3_checks2 as C, l3_verify as V, localwiki as LW, s17_eval as S  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans, g6  # noqa: E402

R = Path("results/runs/s19")
RD = Path("results/shared_eval/readers")
T = ["| set | system | coverage | correct | SER | errors |", "|---|---|---|---|---|---|"]
for name in ("dev", "fresh"):
    rows = [json.loads(l) for l in open(R / f"{name}_outputs.jsonl", encoding="utf-8")]
    phi = {r["id"]: r for r in map(json.loads, open(RD / f"s19{name}_combo_cautious_phi4.jsonl", encoding="utf-8"))}
    n = len(rows)
    res = {k: [] for k in ("wiki_plain", "combo_plain", "combo_cautious", "MSany", "G2 V1-V4", "G3 V1-V4", "G3 V1-V5", "G3 V1-V5 + Phi-4 veto", "G2 V1-V5 + Phi-4 veto")}
    for r in rows:
        for b in ("wiki_plain", "combo_plain", "combo_cautious"):
            res[b].append((r["question"], r["gold"], r[b]))
        a, s = S.cand(r)
        a = a if ans(a) else None
        res["MSany"].append((r["question"], r["gold"], a))
        r1, _ = V.release(r["question"], a, r["wiki_titles"], LW.page_text)
        r2, _ = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
        p = phi.get(r["id"], {}).get("answer")
        ok = bool(r2) and ans(p) and agree(str(r2), str(p))
        res["G2 V1-V4"].append((r["question"], r["gold"], r1 if s >= 2 else None))
        res["G3 V1-V4"].append((r["question"], r["gold"], r1 if s >= 3 else None))
        res["G3 V1-V5"].append((r["question"], r["gold"], r2 if s >= 3 else None))
        res["G3 V1-V5 + Phi-4 veto"].append((r["question"], r["gold"], r2 if s >= 3 and ok else None))
        res["G2 V1-V5 + Phi-4 veto"].append((r["question"], r["gold"], r2 if s >= 2 and ok else None))
    for k, L in res.items():
        got = [g6(q, g, a) if ans(a) else None for q, g, a in L]
        cov = sum(x is not None for x in got) / n
        T.append(f"| {name} (n={n}) | {k} | {cov:.3f} | {sum(x is True for x in got) / n:.3f} | {sum(x is False for x in got) / n:.4f} | {sum(x is False for x in got)} |")
txt = "\n".join(["# S19 design re-measurement on DuckDuckGo evidence (results/runs/s19/design_eval.py)", ""] + T)
(R / "DESIGN_EVAL.md").write_text(txt, encoding="utf-8")
print(txt)
