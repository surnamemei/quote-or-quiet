"""Certificate-constrained answering (THEORY.md T4; bold direction 1). The model may only output
  span    : an answer that is a verbatim substring of the passage (enforced token by token during greedy decoding), or
  compute : two numbers copied verbatim from the passage plus an operation from a fixed set, evaluated by code, or
  unknown : abstain.
So every non-abstaining answer carries a certificate (spans + op) that `verify` re-checks with plain code; unsupported answers
cannot be produced. Related prior work (constrained copying of quotes/citations): PEER 2208.11663, ReClaim 2407.01796,
FullCite 2606.07130, CopyGen 2610.28393 (snippet-level check, 2026-11-05). Here the ANSWER itself is constrained and abstention is allowed.
Run: venv_gpu python -B -m vkg.cert_gen <suite: simpleqa_E|squad2|faitheval|fresh> [--cpu] [--limit N]
"""
import json
import re
import sys

import torch

from .probe_gen import ROOT

MODEL = ROOT / "models" / "qwen3-4b-instruct-2507"
OUT = ROOT / "results" / "runs" / "cert"
PROMPT = ('Passage:\n{p}\n\nQuestion: {q}\n'
          'Answer ONLY from the passage. Choose a mode:\n'
          '- "span": the answer is written in the passage; copy the shortest exact words from the passage that answer the question.\n'
          '- "compute": the answer is the difference or sum of two numbers that are both written in the passage (for example an age gap in years).\n'
          '- "unknown": the passage does not state the answer, or it is not clear. Never guess.\n'
          'Reply as JSON: {{"mode": "span|compute|unknown", ...}}')
MODES = ("span", "compute", "unknown")
OPS = ("subtract", "add")
TOPK = 64
MAXTOK = 24


def norm(s):
    return re.sub(r"\s+", " ", str(s)).lower()


def is_sub(cand, pnorm, numeric=False):
    c = norm(cand)
    if numeric and not re.fullmatch(r"[\d.,]*", c):
        return False
    return c in pnorm


def step_valid(prefix, piece, pnorm, numeric=False):
    """Returns ('close', text) | ('cont', text) | None."""
    if '"' in piece:
        cand = (prefix + piece.split('"')[0])
        cand = cand.lstrip() if not prefix else cand
        return ("close", cand) if cand.strip() and is_sub(cand.strip(), pnorm, numeric) else None
    cand = prefix + piece
    cand = cand.lstrip() if not prefix else cand
    return ("cont", cand) if cand and is_sub(cand, pnorm, numeric) else None


def to_num(s):
    s = s.replace(",", "").strip()
    return float(s) if re.fullmatch(r"\d+(\.\d+)?", s) else None


def fmt(x):
    return str(int(x)) if float(x).is_integer() else f"{x:g}"


def verify(rec, passage):
    """Independent re-check of a certificate with plain code."""
    pn = norm(passage)
    if rec["mode"] == "span":
        return bool(rec["answer"].strip()) and norm(rec["answer"]).strip() in pn
    if rec["mode"] == "compute":
        a, b = to_num(rec["a"]), to_num(rec["b"])
        if a is None or b is None or norm(rec["a"]).strip() not in pn or norm(rec["b"]).strip() not in pn:
            return False
        v = abs(a - b) if rec["op"] == "subtract" else a + b
        return rec["answer"] == fmt(v)
    return rec["mode"] == "unknown"


class Gen:
    def __init__(self, device="cuda"):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(MODEL)
        dt = torch.bfloat16
        self.m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=dt).to(device).eval()
        self.dev = device
        self.first = {w: self.tok.encode(w, add_special_tokens=False)[0] for w in MODES + OPS}
        assert len({self.first[w] for w in MODES}) == 3 and self.first["subtract"] != self.first["add"]

    def _ids(self, text):
        return torch.tensor([self.tok.encode(text, add_special_tokens=False)], device=self.dev)

    @torch.no_grad()
    def _choose(self, text, options):
        logits = self.m(self._ids(text), logits_to_keep=1).logits[0, -1]
        return max(options, key=lambda w: logits[self.first[w]].item())

    @torch.no_grad()
    def _copy(self, text, pnorm, numeric=False):
        """Greedy decoding constrained to a passage substring; ends at a closing quote. Returns (string, ok)."""
        out = self.m(self._ids(text), use_cache=True, logits_to_keep=1)
        past, logits = out.past_key_values, out.logits[0, -1]
        cur = ""
        for _ in range(MAXTOK):
            pick = None
            for tid in torch.topk(logits, TOPK).indices.tolist():
                piece = self.tok.decode([tid])
                r = step_valid(cur, piece, pnorm, numeric)
                if r:
                    pick = (tid, r)
                    break
            if pick is None:
                return cur.strip(), bool(cur.strip())
            tid, (kind, cand) = pick
            if kind == "close":
                return cand.strip(), True
            cur = cand
            out = self.m(torch.tensor([[tid]], device=self.dev), past_key_values=past, use_cache=True)
            past, logits = out.past_key_values, out.logits[0, -1]
        return cur.strip(), bool(cur.strip())

    def answer(self, passage, question):
        pnorm = norm(passage)
        base = self.tok.apply_chat_template([{"role": "user", "content": PROMPT.format(p=passage, q=question)}], add_generation_prompt=True, tokenize=False)
        text = base + '{"mode": "'
        mode = self._choose(text, MODES)
        rec = {"mode": mode, "answer": "", "a": "", "b": "", "op": ""}
        if mode == "span":
            ans, ok = self._copy(text + 'span", "answer": "', pnorm)
            rec.update(answer=ans) if ok else rec.update(mode="unknown", note="no valid span")
        elif mode == "compute":
            t = text + 'compute", "a": "'
            a, oka = self._copy(t, pnorm, numeric=True)
            t += a + '", "b": "'
            b, okb = self._copy(t, pnorm, numeric=True) if oka else ("", False)
            if not (oka and okb and to_num(a) is not None and to_num(b) is not None):
                rec.update(mode="unknown", note="no valid numbers")
            else:
                op = self._choose(t + b + '", "op": "', OPS)
                v = abs(to_num(a) - to_num(b)) if op == "subtract" else to_num(a) + to_num(b)
                rec.update(a=a, b=b, op=op, answer=fmt(v))
        rec["cert_ok"] = verify(rec, passage)
        return rec


def load(suite):
    if suite == "fresh":
        return json.load(open(ROOT / "results" / "runs" / "s8" / "fresh_items.json", encoding="utf-8"))
    ev = json.load(open(ROOT / "results" / "runs" / "s6b" / "eval_items.json", encoding="utf-8"))
    return [e for e in ev if e["suite"] == suite]


def main():
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    suite = sys.argv[1]
    cpu = "--cpu" in sys.argv
    lim = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    if cpu:
        torch.set_num_threads(4)
    items = load(suite)[:lim] if lim else load(suite)
    g = Gen("cpu" if cpu else "cuda")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (f"{suite}{'_smoke' if lim else ''}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for k, e in enumerate(items, 1):
            r = g.answer(e["passage"], e["question"])
            f.write(json.dumps({"id": e["id"], "kind": e.get("kind"), "question": e["question"], "gold": e.get("gold", []), **r}, ensure_ascii=False) + "\n")
            f.flush()
            if k % 20 == 0 or lim:
                print(f"  {k}/{len(items)} {r['mode']} {r['answer'][:40]!r} cert_ok={r['cert_ok']}", flush=True)
    print("done", path)


if __name__ == "__main__":
    main()
