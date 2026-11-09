"""S22 design (DEV only): where does the frozen S19 H1 system abstain, and how good is the withheld candidate?
For each DEV item: reason (no candidate / support 1 / support 2 / gate:<V reason> / phi4 veto / released) and the alias-aware
grade of the max-support candidate (cached labels only).  OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s22/abstain_dev.py"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S      # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402
from vkg.s21_judge import aliases, J                                 # noqa: E402
from vkg.grade6 import veto                                          # noqa: E402

def grade(q, gold, a):
    if not ans(a): return None
    labs = [J.get((q, g, str(a))) for g in aliases(gold)]
    if any(l == "CORRECT" and not veto(q, g, str(a)) for l, g in zip(labs, aliases(gold))): return True
    return "?" if None in labs else False

def short(why):
    return re.sub(r"[\d'\"].*", "", str(why))[:40].strip()

def main():
    out, lines = {}, ["# S22 DEV: abstention breakdown of the frozen S19 H1 system", ""]
    for name in ("mintaka_dev", "popqa_dev"):
        rows = [json.loads(l) for l in open(ROOT / "results/runs/s19" / f"{name}_outputs.jsonl", encoding="utf-8")]
        phi = {r["id"]: r for r in map(json.loads, open(ROOT / "results/shared_eval/readers" / f"s21{name}_combo_cautious_phi4.jsonl", encoding="utf-8"))}
        X = []
        for r in rows:
            a, s = S.cand(r); a = a if ans(a) else None
            if not a: reason = "no candidate"
            elif s < 3: reason = f"support {s}"
            else:
                rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
                if not rel: reason = "gate: " + short(rec.get("reason"))
                else:
                    p = phi[r["id"]]["answer"]
                    reason = "released" if ans(p) and agree(str(rel), str(p)) else "phi4 veto"
            X.append({"id": r["id"], "stratum": r.get("stratum"), "q": r["question"], "gold": r["gold"][:3], "cand": a, "support": s,
                      "reason": reason, "g": grade(r["question"], r["gold"], a)})
        out[name] = X
        tab = defaultdict(Counter)
        for x in X: tab[x["reason"]][str(x["g"])] += 1
        lines += [f"## {name} (n={len(X)})", "", "| reason | n | cand correct | cand wrong | unlabelled |", "|---|---|---|---|---|"]
        for k, c in sorted(tab.items(), key=lambda kv: -sum(kv[1].values())):
            lines.append(f"| {k} | {sum(c.values())} | {c['True']} | {c['False']} | {c['?']} |")
        lines.append("")
        st = defaultdict(Counter)
        for x in X: st[x["stratum"]][x["reason"].split(":")[0]] += 1
        keys = ["released", "support 1", "support 2", "gate", "phi4 veto", "no candidate"]
        lines += ["| stratum | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
        for k in sorted(st): lines.append(f"| {k} | " + " | ".join(str(st[k][r]) for r in keys) + " |")
        lines.append("")
    R = ROOT / "results/runs/s22"
    (R / "abstain_dev.md").write_text("\n".join(lines), encoding="utf-8")
    json.dump(out, open(R / "abstain_dev.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("\n".join(lines))

if __name__ == "__main__":
    main()
