"""One-off: record the S55 distillation result; add a 27B arm (rule R27) to the S53 pipeline; register it in the S40 plan before any S40 output."""
import datetime
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations"); tm = datetime.datetime.now().strftime("%H:%M")
p = ROOT / "docs/S55_DISTILLATION_PLAN.md"; s = p.read_text(encoding="utf-8").rstrip("\n")
s += f"""

## Result ({tm}; results/runs/s55/S55_result.md)

Silver rows: 3,368 candidate sentences (Mintaka releases outside the review sample 2,576, FRESH-5 371, web 421); the 27B said YES to 958 (28.4%). Student: 3,656 labelled training rows plus the silver rows, S51 recipe.

| Set | AUROC for 'states' | accepted at 0.5 | measure among accepted |
|---|---|---|---|
| held-out (n=939) | 0.988 | 745 (79.3%) | not 'states' 16 (2.1%, 97.5% upper 3.5%) |
| Mintaka rows (n=361) | 0.911 | 163 (45.2%) | misleading 13 (8.0%, upper 13.3%) |

Against the predictions: Mintaka acceptance at least 38%: met (45.2%). Mintaka misleading among accepted at most 3%: FAILED (8.0%). Mintaka AUROC at least 0.93: FAILED (0.911; the S51 judge had 0.897). Held-out AUROC at least 0.98: met (0.988).
Held-out not 'states' at most 2.2% at an acceptance of at least 75%: met (2.1% at 79.3%).
Reading: distilling the 27B on 3,368 silver rows raised the AUROC on the unseen set a little (0.897 to 0.911) but did not close the gap (8.0% misleading at the default threshold against 1.9% for the 27B itself). As planned, the recommendation is to use the 27B as the judge
where a GPU of about 20 GB is available, and to keep the small judge as the cheap option. No further work on the student.
"""
p.write_text(s + "\n", encoding="utf-8")

m = ROOT / "paper/manuscript.md"; t = m.read_text(encoding="utf-8")
old = "AlignScore and HHEM were not run."
assert t.count(old) == 1
t = t.replace(old, "AlignScore and HHEM were not run. Distilling the 27B judge into the 0.6B model on 3,368 silver-labelled rows raised its AUROC on the Mintaka rows only from 0.897 to 0.911 (8.0% misleading among the accepted at the default threshold, against 1.9% for the 27B), so where a GPU of about 20 GB is available the prompted 27B is the judge to use.", 1)
m.write_text(t, encoding="utf-8")

# the S53 pipeline: a 27B arm
q = ROOT / "results/runs/s53/q_pipeline.py"; c = q.read_text(encoding="utf-8")
old = 'elif MODE == "small":'
new = '''elif MODE == "judge27":
    os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
    from vkg.llm import chat
    S = [json.loads(l) for l in open(OUT / "q_cands.jsonl", encoding="utf-8")]
    PF = OUT / "q_judge27.json"; res = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    for s in S:
        n = 0
        for k, c in enumerate(s["cands"]):
            if c["sent"] and c["N"] and c["swap"] and n < 6:
                n += 1
                for tag, ans_ in (("J", s["answer"]), ("JS", c["swap"])):
                    key = f"{tag}|{s['id']}|{k}"
                    if key in res:
                        continue
                    for t in range(20):
                        try:
                            res[key] = str(chat("qwen3.8-27b", [{"role": "user", "content": JP.format(t=c["doc"], s=c["quote"], q=s["question"], a=ans_)}], temperature=0.0, seed=0, max_tokens=4,
                                                think=False, json_mode=False, num_ctx=4096, timeout=600)); break
                        except Exception as e:
                            print("retry", t, repr(e)[:100], flush=True); time.sleep(30)
                    else:
                        raise SystemExit("gave up")
        if len(res) % 200 < 2:
            json.dump(res, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(res, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    print("judge27 done", len(res), flush=True)

elif MODE == "small":'''
assert c.count(old) == 1; c = c.replace(old, new, 1)
# sheet: R27 decisions and rows
c = c.replace('        s["w1"] = s["r"] = s["sj"] = None\n', '        s["w1"] = s["r"] = s["sj"] = s["r27"] = None\n', 1)
c = c.replace('            if s["sj"] is None and c["sent"] and SM.get(f"{s[\'id\']}|{k}", 0) >= 0.5:\n                s["sj"] = k\n',
              '            if s["sj"] is None and c["sent"] and SM.get(f"{s[\'id\']}|{k}", 0) >= 0.5:\n                s["sj"] = k\n            if J27 and s["r27"] is None and f"J|{s[\'id\']}|{k}" in J27 and yes(J27[f"J|{s[\'id\']}|{k}"]) and not yes(J27[f"JS|{s[\'id\']}|{k}"]):\n                s["r27"] = k\n', 1)
c = c.replace('    from vkg.lite import parse\n    yes = lambda o:', '    from vkg.lite import parse\n    J27 = json.load(open(OUT / "q_judge27.json", encoding="utf-8")) if (OUT / "q_judge27.json").exists() else {}\n    yes = lambda o:', 1)
c = c.replace('for name in ("w1", "r", "sj"):\n        print(name', 'for name in ("w1", "r", "sj", "r27"):\n        print(name', 1)
c = c.replace('json.dump({s["id"]: {"w1": s["w1"], "r": s["r"], "sj": s["sj"]} for s in S}', 'json.dump({s["id"]: {"w1": s["w1"], "r": s["r"], "sj": s["sj"], "r27": s["r27"]} for s in S}', 1)
c = c.replace('for kind, k in (("displayed", 0), ("w1", s["w1"]), ("r", s["r"]), ("sj", s["sj"])):', 'for kind, k in (("displayed", 0), ("w1", s["w1"]), ("r", s["r"]), ("sj", s["sj"]), ("r27", s["r27"])):', 1)
c = c.replace('for name, key in (("W1", "w1"), ("R", "r"), ("SJ", "sj")):', 'for name, key in (("W1", "w1"), ("R", "r"), ("SJ", "sj"), ("R27", "r27")):', 1)
q.write_text(c, encoding="utf-8")

d = ROOT / "docs/S40_PLAN.md"; x = d.read_text(encoding="utf-8")
k = "- No rule was added for the S29 failure modes"
add = f"- Dated 2026-11-10 {tm}, still before any S40 run: a fourth secondary analysis is registered, from the S40 outputs without new generation: rule R27, rule R of docs/S48_RELATION_FREE_PLAN.md with the YES and NO judgements made by Qwen3.8-27B (Ollama, temperature 0, the same prompt) instead of the 4B (candidate sentences, number check and swapped answers as in R). It is reviewed on the same random 300 releases as (1) to (3). Prediction: R27 keeps 45 to 80% of the releases and its quote is misleading for at most 3% of those (upper bound reported). Reason: on the Mintaka review rows the 27B judge left 1.9% misleading where the 4B left 24.0% (docs/S54_LARGER_JUDGE_RESULT.md). Reported whatever the result.\n"
assert k in x; d.write_text(x.replace(k, add + k, 1), encoding="utf-8")
print("ok")
