"""Goal B step 1, variant 2 (closed choice, DEV only): the 4B picks which sense of the question's mention the question means.
Candidates = titles in the sense inventory used by the rule layer (primary topic + typed senses, max 9, longest pages first, the
release page's sense always included), each with the first 150 characters of its page; plus 'none of these'. usage as ent_gen.py."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/l3")); sys.path.insert(0, str(ROOT / "results/runs/s22"))
from vkg import pod, localwiki as LW
from qualified_dev import releases
from qualified import decide, senses, norm
PROMPT = ('Question: {q}\n\nThe question mentions "{m}". Several Wikipedia articles could be what it means:\n{opts}\n'
          'Which one does the question mean? Reply with the letter only.')
out = ROOT / "results/runs/l3/ent2_raw.jsonl"
done = {(r["set"], r["id"]) for r in map(json.loads, open(out, encoding="utf-8"))} if out.exists() else set()
for name in ["popqa_dev", "mintaka_dev", "dev", "fresh"]:
    todo = []
    for r, rel, doc, meta in releases(name):
        if (name, r["id"]) in done:
            continue
        st, sense, info = decide(r["question"], rel, doc, strict=True)
        m = info.get("mention")
        if not m or info.get("n", 0) < 2:
            continue
        ss = sorted(senses(norm(m), m), key=lambda x: -x[2])
        cands = [t for t, q, n in ss][:9]
        for t in (sense, doc):
            if t and t not in cands and any(t == x[0] for x in ss):
                cands[-1:] = [t]
        if len(cands) < 2:
            continue
        opts = "\n".join(chr(65 + i) + ". " + c + " - " + (LW.page_text(c) or "")[:150].replace("\n", " ") for i, c in enumerate(cands))
        opts += "\n" + chr(65 + len(cands)) + ". none of these / cannot tell"
        todo.append((r["id"], r["question"], m, cands, PROMPT.format(q=r["question"], m=m, opts=opts)))
    outs = pod.gen([t[4] for t in todo], 8) if todo else []
    with open(out, "a", encoding="utf-8") as f:
        for t, o in zip(todo, outs):
            f.write(json.dumps({"set": name, "id": t[0], "question": t[1], "mention": t[2], "cands": t[3], "raw": o[0]}, ensure_ascii=False) + "\n")
    print(name, len(todo), flush=True)
