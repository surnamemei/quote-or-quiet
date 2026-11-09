"""Conditional-truth judge for Qualified outputs ("A, assuming the subject is E"). Local qwen3.8-27b (Ollama 11435),
temperature 0, no thinking. The judge sees the question, the stated sense E, an excerpt of E's local-wiki page (lead + sentences
holding the answer) and the answer; it never sees gold or which items are injected negatives.
Verdict letters: A = the excerpt shows A answers the question for E (SUPPORTED), B = it does not (NOT_SUPPORTED), C = unclear.
usage: python -B cj_judge.py <items.jsonl>  -> <items>_judged.jsonl"""
import json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11435")
from vkg.llm import chat  # noqa: E402

MODEL = "qwen3.8-27b:latest"
PROMPT = """You check one answer to a factual question under a stated assumption about what the question refers to.

Question: {q}
Assumption: the question is about "{e}" (the Wikipedia article with that title).
Excerpt from that article:
<<<
{x}
>>>
Proposed answer: {a}

Decide, using only the excerpt and treating the assumption as given:
A) The excerpt shows that the proposed answer correctly answers the question for "{e}".
B) The excerpt does not show this: the answer is wrong for "{e}", answers a different question, or names something else
   mentioned in the excerpt.
C) The excerpt is not enough to decide.
Reply with a single letter: A, B or C."""
LET = {"A": "SUPPORTED", "B": "NOT_SUPPORTED", "C": "UNCLEAR"}


def judge(x):
    out = chat(MODEL, [{"role": "user", "content": PROMPT.format(q=x["question"], e=x["sense"], x=x["excerpt"][:2500], a=x["answer"])}],
               temperature=0.0, max_tokens=4, think=False, json_mode=False, num_ctx=4096)
    m = re.search(r"\b(A|B|C)\b", out or "")
    return LET[m.group(1)] if m else "UNCLEAR"


if __name__ == "__main__":
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    src = Path(sys.argv[1])
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    with ThreadPoolExecutor(4) as ex:
        verdicts = list(ex.map(judge, rows))
    out = src.with_name(src.stem + "_judged.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for x, v in zip(rows, verdicts):
            f.write(json.dumps({**x, "cj": v}, ensure_ascii=False) + "\n")
    print("judged", len(rows), "->", out.name)
