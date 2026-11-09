"""Apply the Qualified decision (results/runs/l3/qualified.py) to the frozen S19 H1 releases on DEV/used sets.
PopQA DEV carries the intended subject page (meta.s_wiki_title), so assumption correctness is measured there directly.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/l3/qualified_dev.py"""
import json, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3")); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S      # noqa: E402
from vkg.s12_run import agree                                        # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402
from abstain_dev import grade                                        # noqa: E402
from qualified import decide, norm                                   # noqa: E402

RD = ROOT / "results/shared_eval/readers"
STRICT = "mid" if "--mid" in sys.argv else ("--lenient" not in sys.argv)
ALL = {"popqa_dev": "s21", "mintaka_dev": "s21", "dev": "s19", "fresh": "s19",
       "fresh5": "s19", "mintaka_test": "s21", "popqa_test": "s21"}       # test sets: already unsealed and scored (S19, S21)
TEST = "--tests" in sys.argv
SETS = {k: v for k, v in ALL.items() if (k in ("fresh5", "mintaka_test", "popqa_test")) == TEST}


def releases(name):
    rows = [json.loads(l) for l in open(ROOT / f"results/runs/s19/{name}_outputs.jsonl", encoding="utf-8")]
    phi = {r["id"]: r["answer"] for r in map(json.loads, open(RD / f"{ALL[name]}{name}_combo_cautious_phi4.jsonl", encoding="utf-8"))}
    meta = {}
    p = ROOT / f"results/runs/s21/{name}.json"
    if p.exists():
        meta = {e["id"]: e.get("meta", {}) for e in json.load(open(p, encoding="utf-8"))}
    for r in rows:
        a, s = S.cand(r)
        if s < 3 or not ans(a):
            continue
        rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
        pp = phi.get(r["id"])
        if not rel or not (pp is not None and ans(pp) and agree(str(rel), str(pp))):
            continue
        yield r, rel, rec["doc"], meta.get(r["id"], {})


def main():
    lines = [f"# Qualified output state on frozen S19 H1 releases (DEV and used sets; design data; {STRICT if STRICT == 'mid' else ('strict' if STRICT else 'lenient')})", ""]
    detail = []
    for name in SETS:
        tab = Counter(); n = sum(1 for _ in open(ROOT / f"results/runs/s19/{name}_outputs.jsonl", encoding="utf-8"))
        for r, rel, doc, m in releases(name):
            g = grade(r["question"], r["gold"], rel)
            st, sense, info = decide(r["question"], rel, doc, strict=STRICT)
            intended = m.get("s_wiki_title")
            match = None if not intended or sense is None else (norm(sense) == norm(intended))
            tab[(st, str(g))] += 1
            if match is not None and st == "Qualified":
                tab[("Qualified sense = intended", match)] += 1
            if st != "Verified" or g is False:
                detail.append({"set": name, "q": r["question"], "gold": r["gold"][:2], "rel": rel, "doc": doc, "state": st,
                               "sense": sense, "intended": intended, "graded": g, **info})
        lines += [f"## {name} (n={n})", "", "| state | graded correct | graded wrong |", "|---|---|---|"]
        for st in ("Verified", "Qualified", "Unresolved"):
            lines.append(f"| {st} | {tab[(st, 'True')]} | {tab[(st, 'False')]} |")
        if tab[("Qualified sense = intended", True)] + tab[("Qualified sense = intended", False)]:
            lines.append(f"\nQualified sense equals the intended subject page (PopQA meta): {tab[('Qualified sense = intended', True)]} yes, "
                         f"{tab[('Qualified sense = intended', False)]} no")
        lines.append("")
    (ROOT / f"results/runs/l3/qualified_{'tests' if TEST else 'dev'}{'_mid' if STRICT == 'mid' else ('' if STRICT else '_lenient')}.md").write_text("\n".join(lines), encoding="utf-8")
    json.dump(detail, open(ROOT / f"results/runs/l3/qualified_{'tests' if TEST else 'dev'}{'_mid' if STRICT == 'mid' else ''}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
