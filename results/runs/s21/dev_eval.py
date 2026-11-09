"""S21 DEV feasibility scorer (design data; may be inspected). Applies the frozen S19 H1 system (vkg/s19_eval.system_rows logic:
MS3 candidate -> l3_checks2.release2 -> Phi-4 cautious veto) to popqa_dev / mintaka_dev outputs from vkg.s17_run (VKG_WEB=ddg,
so outputs sit in results/runs/s19/) and reports coverage, errors and strata. Cached judge labels only:
    OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s21/dev_eval.py
Also flags graded-wrong answers that string-match a non-first gold alias (the judge only sees gold[0])."""
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S          # noqa: E402
from vkg.s12_run import agree                                            # noqa: E402
from vkg.s14_eval import ans, g6                                         # noqa: E402
from vkg.s19_eval import upper, FLOOR                                    # noqa: E402
from vkg.s21_judge import g6a                                            # noqa: E402

OUT = ROOT / "results" / "runs" / "s21"


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9 ]", " ", s).split()


def alias_hit(a, gold):
    t = " " + " ".join(norm(a)) + " "
    return any(g and (" " + " ".join(norm(g)) + " ") in t for g in gold[1:] if norm(g))


def rows(name):
    R = [json.loads(l) for l in open(ROOT / "results" / "runs" / "s19" / f"{name}_outputs.jsonl", encoding="utf-8")]
    phi = {r["id"]: r for r in map(json.loads, open(ROOT / "results" / "shared_eval" / "readers" / f"s21{name}_combo_cautious_phi4.jsonl", encoding="utf-8"))}
    out = []
    for r in R:
        a, s = S.cand(r)
        a = a if ans(a) else None
        rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
        pre = rel
        p = phi.get(r["id"], {}).get("answer")
        if rel and not (ans(p) and agree(str(rel), str(p))):
            rel = None
        reason = "released" if rel else ("vetoed" if pre else ("gate" if s >= 3 else f"support<3 ({s})"))
        cp = r["combo_plain"]
        out.append({"id": r["id"], "stratum": r["stratum"], "question": r["question"], "gold": r["gold"], "released": rel,
                    "reason": reason, "doc": rec.get("doc") if rel else None,
                    "graded": g6(r["question"], r["gold"], rel) if rel else None,
                    "graded_a": g6a(r["question"], r["gold"], rel) if rel else None,
                    "alias_hit": bool(rel) and alias_hit(rel, r["gold"]),
                    "cp": cp, "cp_graded": g6(r["question"], r["gold"], cp) if ans(cp) else None,
                    "web_n": len(r["web_kept"]), "wiki_titles": r["wiki_titles"][:3]})
    return out


def table(X, key):
    g = defaultdict(list)
    for x in X:
        g[key(x)].append(x)
    L = ["| stratum | n | released | coverage | wrong | combo_plain answered | combo_plain correct | combo_plain wrong |", "|---|" + "---|" * 7]
    for k in sorted(g) + ["ALL"]:
        v = X if k == "ALL" else g[k]
        rel = [x for x in v if x["released"]]
        L.append(f"| {k} | {len(v)} | {len(rel)} | {len(rel) / len(v):.3f} | {sum(x['graded'] is False for x in rel)} | "
                 f"{sum(x['cp_graded'] is not None for x in v)} | {sum(x['cp_graded'] is True for x in v)} | {sum(x['cp_graded'] is False for x in v)} |")
    return L


def main():
    lines = ["# S21 DEV feasibility (frozen S19 H1 system; design data)", ""]
    errs = {}
    for name in ("popqa_dev", "mintaka_dev"):
        p = ROOT / "results" / "runs" / "s19" / f"{name}_outputs.jsonl"
        if not p.exists():
            lines.append(f"## {name}: outputs missing")
            continue
        X = rows(name)
        n, rel = len(X), [x for x in X if x["released"]]
        k = sum(x["graded"] is False for x in rel)
        lines += [f"## {name} (n={n})", f"released {len(rel)} (coverage {len(rel) / n:.3f}, floor {FLOOR}); wrong k={k} "
                  f"(alias string-match among wrong: {sum(x['alias_hit'] and x['graded'] is False for x in rel)}); "
                  f"upper at this n {upper(k, n):.4f}; alias-aware grading (vkg/s21_judge.g6a): k={sum(x['graded_a'] is False for x in rel)}", ""]
        lines += table(X, lambda x: x["stratum"] if name == "popqa_dev" else x["stratum"]) + [""]
        lines.append("Abstention reasons: " + ", ".join(f"{a} {c}" for a, c in Counter(x["reason"] for x in X).most_common()))
        lines.append("")
        errs[name] = [x for x in rel if x["graded"] is False]
    (OUT / "dev_eval.md").write_text("\n".join(lines), encoding="utf-8")
    json.dump(errs, open(OUT / "dev_errors.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
