"""S54: a sheet for a human audit of the language-model reviewers. 180 rows drawn from data/quote_sufficiency/all.jsonl (not the web rows): 40 where both reviewers said 'not', 40 'states' for both,
30 'incomplete' for both, 30 where they disagreed, and 40 decoys made here (the answer of another row of the same source). The user sees question, answer, page title and quote only.
Writes human_audit_sheet.csv (utf-8 with BOM for Excel), human_audit_key.json and human_audit_README.md. python -B results/runs/s54/human_sheet.py"""
import csv, json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; D = ROOT / "results/runs/s54"
rows = [r for r in map(json.loads, open(ROOT / "data/quote_sufficiency/all.jsonl", encoding="utf-8")) if r["src"] != "web" and r["quote"].strip()]
rng = random.Random(5401)
def pick(pred, n):
    pool = [r for r in rows if pred(r)]; rng.shuffle(pool); return pool[:n]
sel = [("not", r) for r in pick(lambda r: r["label"] == "not", 40)] + [("states", r) for r in pick(lambda r: r["label"] == "states", 40)] + \
      [("incomplete", r) for r in pick(lambda r: r["label"] == "incomplete", 30)] + [("split", r) for r in pick(lambda r: r["label"] is None, 30)]
dec = []
for r in pick(lambda r: r["label"] == "states", 40):
    o = rng.choice([x for x in rows if x["src"] == r["src"] and x["answer"].casefold() != r["answer"].casefold() and x["answer"].casefold() not in r["quote"].casefold()])
    dec.append(("decoy", {**r, "answer": o["answer"], "labels": ["not", "not"], "label": "not"}))
sel += dec; rng.shuffle(sel)
with open(D / "human_audit_sheet.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["row", "question", "answer", "page_title", "quote", "verdict (states / incomplete / not)", "note"])
    for n, (k, r) in enumerate(sel, 1):
        w.writerow([n, r["question"], r["answer"], r["title"], r["quote"], "", ""])
json.dump([{"row": n, "kind": k, "src": r["src"], "labels": r["labels"]} for n, (k, r) in enumerate(sel, 1)], open(D / "human_audit_key.json", "w", encoding="utf-8"))
(D / "human_audit_README.md").write_text("""# 人工核对表：请只看“引文”本身，判断它是否说出了答案

文件：human_audit_sheet.csv，180 行。每行有：问题、给出的答案、维基页面标题、一句引文。请在第 6 列填一个词：

- `states`（说出）：引文本身（页面标题可作为主语）明确说，这个答案就是这个问题的答案（主体、关系、时间都对）。
- `incomplete`（不完整）：主体和关系对、与答案一致，但问题的某一部分（年份、哪个职位、哪一个人）不在引文里，读者还得打开页面。
- `not`（没说）：引文讲的是别的主体、别的关系或别的时间，或者根本没说这件事。

规则：不要上网，不要凭自己的常识判断答案是否真实，只判断“这句话说没说出这个答案”。不要看别的文件（key 文件里有语言模型审阅员的判定，看了会失去盲审的意义）。
时间：每行约 20 秒，一个小时左右。可以分几次做。做完后告诉我，我来统计人与两位语言模型审阅员的一致程度（Cohen kappa），以及“被审阅员判为误导”的引文，人是否也判为没说出。
""", encoding="utf-8")
print("rows", len(sel))
