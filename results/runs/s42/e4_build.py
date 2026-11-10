"""S42 E4 (docs/S42_CLAIM_AUDIT_AND_PLAN.md): sibling questions that keep the subject of an S29 question and change the relation,
so that the retrieved page holds a typed span that answers the old question. Control arm: the original questions of the same subjects.
Sources: S29 released questions (opened set), except the year-shift type, which samples all S29 questions with a year.
Seed 4242. Writes results/runs/s42/e4_items.jsonl. No model, no network.
python -B results/runs/s42/e4_build.py"""
import json, random, re, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s29/run_fsm"
rows = {r["id"]: r for r in map(json.loads, open(D / "wd_outputs.jsonl", encoding="utf-8"))}
REL = {r["id"]: r for r in map(json.loads, open(D / "wd_releases.jsonl", encoding="utf-8"))}
# (source relation, source pattern, sibling type, sibling template, sample size)
TYPES = [("birth_place", r"^Where was (.+) born\?$", "death_place", "Where did {s} die?", 120),
         ("birth_year", r"^In what year was (.+) born\?$", "death_year", "In what year did {s} die?", 120),
         ("director", r"^Who directed the film (.+)\?$", "producer", "Who produced the film {s}?", 100),
         ("director", r"^Who directed the film (.+)\?$", "composer", "Who composed the music for the film {s}?", 100),
         ("author", r"^Who wrote (.+)\?$", "publisher", "Who published {s}?", 80),
         ("author", r"^Who wrote (.+)\?$", "translator", "Who translated {s} into English?", 80),
         ("capital", r"^What is the capital of (.+)\?$", "largest_city", "What is the largest city of {s}?", 41)]
rng = random.Random(4242)
used, out = set(), []
for rel, pat, sib, tpl, n in TYPES:
    pool = [i for i, x in sorted(REL.items()) if x["relation"] == rel and i not in used and re.match(pat, x["question"])]
    for i in rng.sample(pool, min(n, len(pool))):
        used.add(i); s = re.match(pat, REL[i]["question"]).group(1)
        base = {"source_id": i, "subject": s, "source_relation": rel, "source_question": REL[i]["question"], "source_answer": REL[i]["answer"], "source_gold": REL[i]["gold"]}
        out.append({"id": f"{i}|{sib}", "arm": "sibling", "type": sib, "question": tpl.format(s=s), **base})
        out.append({"id": f"{i}|orig", "arm": "control", "type": rel, "question": REL[i]["question"], **base})
YP = r"^Who was the head of government of (.+) in (\d{4})\?$"
pool = [i for i, r in sorted(rows.items()) if re.match(YP, r["question"])]
for i in rng.sample(pool, 100):
    s, y = re.match(YP, rows[i]["question"]).groups()
    base = {"source_id": i, "subject": s, "source_relation": "office", "source_question": rows[i]["question"], "source_answer": REL.get(i, {}).get("answer"), "source_gold": rows[i]["gold"]}
    out.append({"id": f"{i}|year_shift", "arm": "sibling", "type": "year_shift", "question": f"Who was the head of government of {s} in {int(y) - 9}?", **base})
    out.append({"id": f"{i}|orig", "arm": "control", "type": "office", "question": rows[i]["question"], **base})
with open(ROOT / "results/runs/s42/e4_items.jsonl", "w", encoding="utf-8") as f:
    for x in out:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
print(len(out), Counter((x["arm"], x["type"]) for x in out))
for x in out[:4] + out[-2:]:
    print(x["id"], "|", x["question"])
