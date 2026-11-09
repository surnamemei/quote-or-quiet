"""Grader 5: LLM judge with the public SimpleQA Verified autorater prompt.

Prompt: vkg/sqav_grader_prompt.txt, the evaluation prompt from Haas et al., "SimpleQA Verified" (arXiv 2509.07968, Appendix A,
CC BY 4.0), decoded from the paper's embedded text attachment with only the LaTeX colour markup removed. It revises the original
SimpleQA grader (openai/simple-evals simpleqa_eval.py, MIT). Parsing as in simple-evals: first A/B/C in the reply, default C.
Judge: local qwen3.8-27b (Ollama), temperature 0, no thinking. It is the same model family as the systems graded (a limitation:
on 27B outputs it grades its own answers); it sees only question, gold and answer, never the passage or the system name.
"""
import re
from pathlib import Path

from .llm import chat

JUDGE = "qwen3.8-27b:latest"
TEMPLATE = (Path(__file__).resolve().parent / "sqav_grader_prompt.txt").read_text(encoding="utf-8")
LETTER = {"A": "CORRECT", "B": "INCORRECT", "C": "NOT_ATTEMPTED"}


def judge(question, gold, answer, model=JUDGE):
    prompt = TEMPLATE.format(question=question, target=gold, predicted_answer=answer)
    out = chat(model, [{"role": "user", "content": prompt}], temperature=0.0, max_tokens=8, think=False, json_mode=False, num_ctx=4096)
    m = re.search(r"(A|B|C)", out or "")
    return LETTER[m.group(0) if m else "C"]


def correct_judge(question, gold_list, answer):
    gold = gold_list[0] if isinstance(gold_list, (list, tuple)) else gold_list
    return judge(question, gold, str(answer)) == "CORRECT"
