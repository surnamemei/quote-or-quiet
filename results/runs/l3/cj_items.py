"""Conditional-truth judge, step 1: collect Qualified outputs (strict v3) and build judge items.
Each item: question, stated sense E, answer A, excerpt = E's lead (first 600 chars) + the sentence(s) of E's page that contain A
(up to 2, 400 chars each). Injected negatives (ground truth: false): 'easy' = the answer of another Qualified item of the same
set; 'hard' = another capitalised phrase or number from the same sentence of E's page, not overlapping A.
Writes results/runs/l3/cj_items_<group>.jsonl. usage: python -B cj_items.py dev|tests"""
import json, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3")); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from qualified_dev import releases                    # noqa: E402
from qualified import decide, norm                    # noqa: E402
from abstain_dev import grade                         # noqa: E402
from vkg import localwiki as LW                       # noqa: E402

GROUPS = {"dev": ["popqa_dev", "mintaka_dev", "dev", "fresh"], "tests": ["fresh5", "mintaka_test", "popqa_test"]}


def sentences_with(text, a, k=2):
    out = []
    na = " " + norm(a) + " "
    for s in re.split(r"(?<=[.!?])\s+|\n+", text):
        if na in " " + norm(s) + " ":
            out.append(s.strip()[:400])
            if len(out) >= k:
                break
    return out


def hard_negative(sents, a, rng):
    na = norm(a)
    cands = []
    for s in sents:
        for m in re.finditer(r"(?:[A-Z][\w'’.-]+(?:\s+(?:of|de|da|van|von|the|and)?\s*[A-Z][\w'’.-]+)*)|\b\d[\d,.]*\b", s):
            c = m.group(0).strip()
            nc = norm(c)
            if nc and nc not in na and na not in nc and len(c) > 2:
                cands.append(c)
    return rng.choice(cands) if cands else None


def main(group):
    rng = random.Random(3)
    items = []
    for name in GROUPS[group]:
        Q = []
        for r, rel, doc, m in releases(name):
            st, sense, info = decide(r["question"], rel, doc, strict=True)
            if st != "Qualified":
                continue
            text = LW.page_text(sense) or ""
            sents = sentences_with(text, rel)
            Q.append({"set": name, "id": r["id"], "question": r["question"], "sense": sense, "answer": rel, "gold": r["gold"][:4],
                      "graded_vs_gold": grade(r["question"], r["gold"], rel), "intended": m.get("s_wiki_title"),
                      "excerpt": (text[:600] + "\n...\n" + "\n".join(sents)).strip(), "sents": sents, "kind": "system"})
        for x in Q:
            items.append(x)
            others = [y["answer"] for y in Q if norm(y["answer"]) != norm(x["answer"]) and norm(y["answer"]) not in norm(x["excerpt"])]
            if others:
                items.append({**x, "answer": rng.choice(others), "kind": "neg_easy", "graded_vs_gold": None})
            h = hard_negative(x["sents"], x["answer"], rng)
            if h:
                items.append({**x, "answer": h, "kind": "neg_hard", "graded_vs_gold": None})
    for x in items:
        x.pop("sents", None)
    out = ROOT / f"results/runs/l3/cj_items_{group}.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for x in items:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    from collections import Counter
    print(group, Counter((x["set"], x["kind"]) for x in items))


if __name__ == "__main__":
    main(sys.argv[1])
