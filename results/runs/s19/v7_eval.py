"""Draft V7 (2026-11-07, designed on one S19-design FRESH error): a released span that sits in a table row ('|' on its line)
must share at least one content word (vkg/l3_checks2.content_words: 5-letter stems, page-title words excluded) with the
question in that row. Measured on S19 DEV/FRESH (DuckDuckGo evidence; design data) and on the used S18 sets (post hoc).
System: G3 + V1-V5 + Phi-4 cautious veto. usage: OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s19/v7_eval.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.getcwd())
from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S, s18_eval as E  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans, g6  # noqa: E402


def row_ok(question, doc, text, i, j):
    a = text.rfind("\n", 0, i) + 1
    b = text.find("\n", j)
    line = text[a:b if b != -1 else len(text)]
    if "|" not in line:
        return True, False
    cw = C.content_words(question, doc)
    rw = {C._stem(w) for w in re.findall(r"[a-z0-9]+", line.casefold())}
    return bool(cw & rw), True


SETS = {"s19 dev": ([json.loads(l) for l in open("results/runs/s19/dev_outputs.jsonl", encoding="utf-8")], "results/shared_eval/readers/s19dev_combo_cautious_phi4.jsonl"),
        "s19 fresh": ([json.loads(l) for l in open("results/runs/s19/fresh_outputs.jsonl", encoding="utf-8")], "results/shared_eval/readers/s19fresh_combo_cautious_phi4.jsonl"),
        "s18 (post hoc)": (E.load(["fresh3", "fresh4"]), "results/shared_eval/readers/s18_combo_cautious_phi4.jsonl")}
print("| set | released (V1-V5+veto) | wrong | in a table row | V7 blocks wrong | V7 blocks correct |")
print("|---|---|---|---|---|---|")
for name, (rows, pf) in SETS.items():
    phi = {r["id"]: r for r in map(json.loads, open(pf, encoding="utf-8"))}
    rel = wr = tab = bw = bc = 0
    for r in rows:
        a, s = S.cand(r)
        if s < 3 or not ans(a):
            continue
        r2, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
        p = phi.get(r["id"], {}).get("answer")
        if not (r2 and ans(p) and agree(str(r2), str(p))):
            continue
        g = g6(r["question"], r["gold"], r2)
        rel += 1
        wr += g is False
        ok, intab = row_ok(r["question"], rec["doc"], LW.page_text(rec["doc"]), rec["start"], rec["end"])
        tab += intab
        if not ok:
            bw += g is False
            bc += g is True
    print(f"| {name} | {rel} | {wr} | {tab} | {bw} | {bc} |")
