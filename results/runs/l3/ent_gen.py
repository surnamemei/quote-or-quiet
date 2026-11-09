"""Goal B step 1 (DEV only): the 4B states the entity it relied on. For each frozen S19 H1 release on the DEV sets, the same
combo passage and question as the frozen run, new prompt -> {"entity","answer"}. Raw generations kept (parser fixes need no GPU).
usage: VKG_POD_HOST=local python -B results/runs/l3/ent_gen.py   (needs vkg/podgen_server.py on 127.0.0.1:18000)"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3")); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from vkg import pod
from qualified_dev import releases, ALL
PROMPT = ('Passage:\n{p}\n\nQuestion: {q}\nUse ONLY the passage. First name the specific thing the question is about, exactly as the '
          'passage identifies it (full name; if several different things share the name, add the short qualifier that tells them apart, '
          'for example "Mercury (planet)" or "Jordan (country)"). Then give the short answer. If the passage does not state the answer, '
          'or it is not clear, answer "unknown". Never guess.\nReply as JSON: {{"entity": "<name>", "answer": "<short answer or unknown>"}}')
SETS = ["popqa_dev", "mintaka_dev", "dev", "fresh"]
out = ROOT / "results/runs/l3/ent_raw.jsonl"
done = set()
if out.exists():
    done = {(r["set"], r["id"]) for r in map(json.loads, open(out, encoding="utf-8"))}
for name in SETS:
    ev = json.load(open(ROOT / f"results/runs/s19/{name}_ev_combo.json", encoding="utf-8"))
    todo = [(r["id"], r["question"]) for r, rel, doc, m in releases(name) if (name, r["id"]) not in done and r["id"] in ev]
    prompts = [PROMPT.format(p=ev[i]["passage"], q=q) for i, q in todo]
    outs = pod.gen(prompts, 128) if prompts else []
    with open(out, "a", encoding="utf-8") as f:
        for (i, q), o in zip(todo, outs):
            f.write(json.dumps({"set": name, "id": i, "question": q, "raw": o[0]}, ensure_ascii=False) + "\n")
    print(name, len(todo), flush=True)
