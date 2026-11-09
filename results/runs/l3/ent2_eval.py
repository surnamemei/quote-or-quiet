import json, sys
from collections import Counter
from pathlib import Path
ROOT = Path("F:/Projects/AI hallucinations")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3")); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from qualified_dev import releases
from qualified import decide, norm
from abstain_dev import grade
raw = {(r["set"], r["id"]): r for r in map(json.loads, open(ROOT / "results/runs/l3/ent2_raw.jsonl", encoding="utf-8"))}
L = ["# Closed-choice entity (ent_gen2) on DEV", ""]
c = Counter(); rows = []
for name in ("popqa_dev", "mintaka_dev", "dev", "fresh"):
    for r, rel, doc, m in releases(name):
        k = (name, r["id"])
        if k not in raw: continue
        x = raw[k]; ch = (x["raw"].strip()[:1] or "?").upper(); i = ord(ch) - 65
        pick = x["cands"][i] if 0 <= i < len(x["cands"]) else None
        st, sense, info = decide(r["question"], rel, doc, strict=True)
        g = grade(r["question"], r["gold"], rel); it = m.get("s_wiki_title")
        rule = sense if sense else doc
        c[(name, "n")] += 1; c[(name, "none")] += pick is None
        c[(name, "agrees_rule")] += (pick is not None and norm(pick) == norm(rule))
        if it:
            c["intended_n"] += 1; c["pick=intended"] += (pick is not None and norm(pick) == norm(it)); c["rule=intended"] += (norm(rule) == norm(it))
            c["pick=intended | rule wrong"] += (pick is not None and norm(pick) == norm(it) and norm(rule) != norm(it))
            c["rule=intended | pick wrong"] += (norm(rule) == norm(it) and not (pick is not None and norm(pick) == norm(it)))
        if pick is not None and norm(pick) != norm(rule) and st == "Verified":
            c["verified_disagree"] += 1; c["verified_disagree_wrong" if g is False else "verified_disagree_ok"] += 1
        if g is False: rows.append((name, r["question"][:55], st, rule, pick, it))
L += [f"- items asked (multi-sense mention): " + ", ".join(f"{n} {c[(n,'n')]}" for n in ("popqa_dev", "mintaka_dev", "dev", "fresh")),
      f"- pick = none/invalid: " + ", ".join(f"{n} {c[(n,'none')]}" for n in ("popqa_dev", "mintaka_dev", "dev", "fresh")),
      f"- pick agrees with rule sense: " + ", ".join(f"{n} {c[(n,'agrees_rule')]}" for n in ("popqa_dev", "mintaka_dev", "dev", "fresh")),
      "", f"PopQA DEV with intended sense, asked: {c['intended_n']}: pick=intended {c['pick=intended']}, rule=intended {c['rule=intended']}, "
      f"pick right where rule wrong {c['pick=intended | rule wrong']}, rule right where pick wrong {c['rule=intended | pick wrong']}",
      f"Verified releases where the pick disagrees with the rule's page: {c['verified_disagree']} (graded wrong {c['verified_disagree_wrong']}, graded correct {c['verified_disagree_ok']})",
      "", "graded-wrong releases that were asked:"] + [f"- {a} | {b} | {s} | rule={ru} | pick={p} | intended={i}" for a, b, s, ru, p, i in rows]
(ROOT / "results/runs/l3/ent2_eval.md").write_text("\n".join(L), encoding="utf-8"); print("\n".join(L))
