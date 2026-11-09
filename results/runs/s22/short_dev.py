"""Short-answer rewrite on DEV: pin vs pinshort (Mintaka/PopQA DEV), s19 vs s19short (SimpleQA DEV); frozen and format gate."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from gate_fmt import release_any                                     # noqa: E402
from vkg import localwiki as LW, l3_checks2 as C, s17_eval as S      # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402
from abstain_dev import grade                                        # noqa: E402
D = ROOT / "results/runs/s22"
CASES = [("s19", "dev", ROOT / "results/runs/s19/dev_outputs.jsonl", ROOT / "results/shared_eval/readers/s19dev_combo_cautious_phi4.jsonl"),
         ("s19short", "dev", D / "s19short/dev_outputs.jsonl", D / "s19short/dev_phi4.jsonl")]
for v in ("pin", "pinshort"):
    for n in ("mintaka_dev", "popqa_dev"):
        CASES.append((v, n, D / v / f"{n}_outputs.jsonl", D / v / f"{n}_phi4.jsonl"))
L = []
rel_by = {}
for var, n, po, pp in CASES:
    rows = [json.loads(l) for l in open(po, encoding="utf-8")]
    phi = {r["id"]: r["answer"] for r in map(json.loads, open(pp, encoding="utf-8"))}
    res = {"frozen": {}, "fmt": {}}
    for r in rows:
        p = phi.get(r["id"])
        a, s = S.cand(r); a = a if ans(a) else None
        rel0 = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)[0] if s >= 3 else None
        rel1 = release_any(r, LW.page_text)[0]
        for k, rel in (("frozen", rel0), ("fmt", rel1)):
            if rel and ans(p) and agree(str(rel), str(p)):
                res[k][r["id"]] = (r["question"][:70], str(rel), r["gold"][0] if isinstance(r["gold"], list) else r["gold"], grade(r["question"], r["gold"], rel))
    rel_by[(var, n)] = res
    N = len(rows)
    L.append(f"| {var} | {n} | " + " | ".join(f"{len(res[k])} ({len(res[k]) / N:.3f}) / {sum(x[3] is False for x in res[k].values())} wrong, {sum(x[3] == '?' for x in res[k].values())} unl" for k in ("frozen", "fmt")) + " |")
out = ["# Short-answer rewrite on DEV (cached labels)", "", "| variant | set | frozen gate: released / wrong | format gate |", "|---|---|---|---|"] + L
for base, sh, n in (("s19", "s19short", "dev"), ("pin", "pinshort", "mintaka_dev"), ("pin", "pinshort", "popqa_dev")):
    a, b = rel_by[(base, n)]["fmt"], rel_by[(sh, n)]["fmt"]
    out += ["", f"## {n}: {sh} vs {base} (format gate)", f"new releases {len(set(b) - set(a))}, lost {len(set(a) - set(b))}"]
    out += [f"- NEW {b[i]}" for i in sorted(set(b) - set(a)) if b[i][3] is not True]
    out += [f"- LOST {a[i]}" for i in sorted(set(a) - set(b))][:15]
(D / "short_dev.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
