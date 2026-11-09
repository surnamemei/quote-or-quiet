"""S22 design on the closed S21 Mintaka test (now design data): score the combination rule
   R = S19 releases ∪ (pin releases that are not time-sensitive and not subject-ambiguous)
and build a blind adjudication sheet (system errors + baseline-wrong decoys + system-correct decoys + injected-false decoys).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s22/combo_s21test.py"""
import csv, json, random, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from entity_dev import ambiguous                                     # noqa: E402
from temporal import time_sensitive                                  # noqa: E402
from abstain_dev import grade                                        # noqa: E402
from gate_fmt import release_any                                     # noqa: E402
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW, s17_run as S17      # noqa: E402
from vkg.s12_run import agree, tokens                                # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402
N = sys.argv[1] if len(sys.argv) > 1 else "mintaka_test"
FMT = "--frozen-gate" not in sys.argv
R = ROOT / "results/runs/s22"


def releases(out, phi):
    rows = [json.loads(l) for l in open(out, encoding="utf-8")]
    ph = {r["id"]: r["answer"] for r in map(json.loads, open(phi, encoding="utf-8"))}
    res = {}
    for r in rows:
        if FMT:
            rel, rec = release_any(r, LW.page_text)
        else:
            a, s = S.cand(r); a = a if ans(a) else None
            rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
        p = ph.get(r["id"])
        if rel and not (ans(p) and agree(str(rel), str(p))): rel = None
        res[r["id"]] = (r, rel, rec.get("doc"))
    return res


PRE = "s19" if N in ("dev", "fresh", "fresh5") else "s21"
s19 = releases(ROOT / f"results/runs/s19/{N}_outputs.jsonl", ROOT / f"results/shared_eval/readers/{PRE}{N}_combo_cautious_phi4.jsonl")
pin = releases(R / f"pin/{N}_outputs.jsonl", R / f"pin/{N}_phi4.jsonl")
items = {e["id"]: e for e in S17.items(N)}
final = {}
docs = {}
for i, (r, rel, doc) in s19.items():
    if rel:
        final[i] = (r, rel, "s19"); docs[i] = doc
for i, (r, rel, doc) in pin.items():
    if i in final or not rel:
        continue
    if time_sensitive(r["question"]) or ambiguous(r["question"], r["wiki_titles"], doc)[0]:
        continue
    final[i] = (r, rel, "pin"); docs[i] = doc
n = len(s19)
g = {i: grade(r["question"], r["gold"], rel) for i, (r, rel, src) in final.items()}
# release file for downstream post-processing (L3 Qualified secondary): page text via vkg.localwiki.page_text(release_doc)
with open(R / f"{N}_releases{'' if FMT else '_frozen'}.jsonl", "w", encoding="utf-8") as f:
    for i, (r, rel, src) in final.items():
        f.write(json.dumps({"id": i, "question": r["question"], "gold": r["gold"], "answer": str(rel), "source": src,
                            "release_doc": docs[i], "wiki_titles": r["wiki_titles"], "grade": g[i]}, ensure_ascii=False) + "\n")
lines = [f"# S22 combination rule on {N} (n = {len(s19)}; gate: {'format-relaxed' if FMT else 'frozen'})", "",
         f"released {len(final)} (coverage {len(final)/n:.3f}); from S19 {sum(v[2]=='s19' for v in final.values())}, added by pin {sum(v[2]=='pin' for v in final.values())}",
         f"graded wrong (gold-relative, alias-aware): {sum(x is False for x in g.values())} (S19 part {sum(g[i] is False for i,v in final.items() if v[2]=='s19')}, pin part {sum(g[i] is False for i,v in final.items() if v[2]=='pin')}); unlabelled {sum(x == '?' for x in g.values())}"]
pinall = [i for i, v in pin.items() if v[1]]
lines.append(f"pin alone: released {len(pinall)} ({len(pinall)/n:.3f}), graded wrong {sum(grade(pin[i][0]['question'], pin[i][0]['gold'], pin[i][1]) is False for i in pinall)}")
# blind sheet
rng = random.Random(22)
wrong = [i for i in final if g[i] is False]
right = [i for i in final if g[i] is True]
basew = [i for i, (r, rel, d) in s19.items() if i not in final and ans(r["combo_plain"]) and grade(r["question"], r["gold"], r["combo_plain"]) is False]
k = len(wrong)
rows = [("system", i, final[i][1]) for i in wrong]
rows += [("decoy_baseline_wrong", i, s19[i][0]["combo_plain"]) for i in rng.sample(basew, min(k, len(basew)))]
dc = rng.sample(right, min(2 * k, len(right)))
rows += [("decoy_system_correct", i, final[i][1]) for i in dc[:k]]
# injected-false: answer replaced by another item's gold of the same answer type
bytype = {}
for e in items.values():
    bytype.setdefault(e.get("meta", {}).get("answerType"), []).append(e)
for i in dc[k:]:
    e = items[i]; pool = [o for o in bytype.get(e.get("meta", {}).get("answerType"), []) if o["id"] != i and o["gold"]]
    gold_t = {" ".join(tokens(x)) for x in e["gold"]}
    for _ in range(50):
        o = rng.choice(pool); cand = o["gold"][0]
        if " ".join(tokens(cand)) not in gold_t and not any(agree(str(cand), str(x)) for x in e["gold"]):
            rows.append(("decoy_injected_false", i, cand)); break
rng.shuffle(rows)
with open(R / f"{N}_adj_sheet.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["row", "question", "gold", "answer", "verdict", "note"])
    for j, (_, i, a) in enumerate(rows, 1):
        w.writerow([j, items[i]["question"], " | ".join(items[i]["gold"]), a, "", ""])
json.dump([{"row": j, "kind": kd, "id": i} for j, (kd, i, _) in enumerate(rows, 1)], open(R / f"{N}_adj_key.json", "w", encoding="utf-8"))
lines.append(f"blind sheet: {len(rows)} rows (system {k}, baseline-wrong {min(k, len(basew))}, system-correct {len(dc[:k])}, injected-false {sum(1 for x in rows if x[0]=='decoy_injected_false')}) -> {N}_adj_sheet.csv; key {N}_adj_key.json")
(R / f"combo_{N}{'' if FMT else '_frozen'}.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
