"""Conditional-truth judge v2 (extraction): qwen3.8-27b re-reads the stated sense's excerpt and answers the question itself under
the assumption, or says NONE; the system answer is SUPPORTED only if it agrees with that independent reading
(vkg.s12_run.agree: normalised equality or containment), else NOT_SUPPORTED (NONE -> UNCLEAR).
Rationale: yes/no verification was lenient on DEV (cj_eval.md); an independent extraction cannot simply accept the proposal.
usage: VKG_OLLAMA_URL=http://127.0.0.1:11535 python -B cj_judge2.py <items.jsonl> -> <items>_judged2.jsonl"""
import json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535")
from vkg.llm import chat          # noqa: E402
from vkg.s12_run import agree     # noqa: E402

MODEL = "qwen3.8-27b:latest"
PROMPT = """Read the excerpt and answer the question. Assume the question is about "{e}" (the Wikipedia article the excerpt
comes from), even if the question could mean something else.

Excerpt:
<<<
{x}
>>>
Question (about "{e}"): {q}

Rules: answer only from the excerpt; give the shortest exact answer (a name, place, number or date as written in the excerpt);
if the excerpt does not state the answer for "{e}" itself, reply NONE.
Answer:"""


def read(x):
    out = chat(MODEL, [{"role": "user", "content": PROMPT.format(q=x["question"], e=x["sense"], x=x["excerpt"][:2500])}],
               temperature=0.0, max_tokens=40, think=False, json_mode=False, num_ctx=4096)
    return (out or "").strip().split("\n")[0].strip().strip('"').rstrip(".")


def verdict(x, r):
    if not r or re.fullmatch(r"(?i)none\.?", r):
        return "UNCLEAR"
    return "SUPPORTED" if agree(str(x["answer"]), r) else "NOT_SUPPORTED"


if __name__ == "__main__":
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    src = Path(sys.argv[1])
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    # one reading per (question, sense, excerpt): negatives share the system item's reading
    keys = {}
    for x in rows:
        keys.setdefault((x["question"], x["sense"], x["excerpt"]), x)
    with ThreadPoolExecutor(4) as ex:
        reads = dict(zip(keys, ex.map(read, keys.values())))
    out = src.with_name(src.stem + "_judged2.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for x in rows:
            r = reads[(x["question"], x["sense"], x["excerpt"])]
            f.write(json.dumps({**x, "reading": r, "cj": verdict(x, r)}, ensure_ascii=False) + "\n")
    print("judged", len(rows), "readings", len(reads), "->", out.name)
