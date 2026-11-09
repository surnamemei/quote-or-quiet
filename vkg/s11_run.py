"""S11: search-on-abstain for the small model (Qwen3-4B-Instruct-2507). target.txt Goal A: "when evidence is insufficient, seek
further evidence; if that fails, say unknown". Prior work: FLARE, DRAGIN, SeaKR (uncertainty-triggered retrieval), Search-R1 (trained).
Round 0 = the 4B cautious answer on the existing passage (reused: FRESH from S8, DEV SimpleQA-E from S6b).
If round 0 abstains (code non-answer detector), up to 2 more rounds:
  the 4B writes 3 new Wikipedia search queries itself (question only, no gold) -> MediaWiki full-text search, pages not seen before
  (at most 6 new) -> chunk ranking as before (retrieval2.passage, 1500 words) -> 4B cautious prompt on the new passage.
Stops at the first non-abstaining answer. Items answered at round 0 are never touched (no harm to them by construction).
Run (venv_gpu, via vkg.s11_wait): python -B -m vkg.s11_run -> results/runs/s11/outputs.jsonl"""
import json
import re
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from . import retrieval as R
from . import retrieval2 as R2
from .probe_gen import ROOT, parse
from .s6b_run import CAUTIOUS, MODEL
from .s8_eval import non_answer

OUT = ROOT / "results" / "runs" / "s11"
QPROMPT = ('Question: {q}\nThe Wikipedia passage you were given did not contain the answer. Write 3 different short search queries '
           '(3 to 8 words each) that would find a different Wikipedia article containing the answer. Use the names, places and dates in '
           'the question; do not answer it. Reply as JSON: {{"queries": ["...", "...", "..."]}}')
ROUNDS = 2
NEW_PAGES = 6


class Small:
    def __init__(self):
        self.tok = AutoTokenizer.from_pretrained(MODEL)
        self.m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda().eval()

    @torch.no_grad()
    def gen(self, content, max_new=80):
        p = self.tok.apply_chat_template([{"role": "user", "content": content}], add_generation_prompt=True, tokenize=False)
        enc = self.tok(p, return_tensors="pt").to("cuda")
        g = self.m.generate(**enc, do_sample=False, max_new_tokens=max_new, pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(g[0, enc["input_ids"].shape[1]:], skip_special_tokens=True), enc["input_ids"].shape[1], g.shape[1] - enc["input_ids"].shape[1]


def queries(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    try:
        qs = json.loads(m.group(0)).get("queries", []) if m else []
    except json.JSONDecodeError:
        qs = []
    return [q for q in qs if isinstance(q, str) and q.strip()][:3]


def items():
    fresh = json.load(open(ROOT / "results" / "runs" / "s8" / "fresh_items.json", encoding="utf-8"))
    f4 = {o["id"]: o for o in map(json.loads, open(ROOT / "results" / "runs" / "s8" / "fresh_4b.jsonl", encoding="utf-8"))}
    dev = [e for e in json.load(open(ROOT / "results" / "runs" / "s6b" / "eval_items.json", encoding="utf-8")) if e["suite"] == "simpleqa_E"]
    d4 = {o["id"]: o for o in map(json.loads, open(ROOT / "results" / "runs" / "s6b" / "eval_outputs.jsonl", encoding="utf-8")) if o["suite"] == "simpleqa_E"}
    out = []
    for e in fresh:
        out.append({"set": "fresh", **e, "round0": f4[e["id"]]["cautious"]})
    for e in dev:
        out.append({"set": "dev", **e, "round0": d4[e["id"]]["cautious"]})
    return out


def main():
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    OUT.mkdir(parents=True, exist_ok=True)
    sm = Small()
    its = items()
    done = set()
    path = OUT / "outputs.jsonl"
    if path.exists():
        done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")}
    with open(path, "a", encoding="utf-8") as f:
        for k, e in enumerate(its, 1):
            if e["id"] in done:
                continue
            rec = {"set": e["set"], "id": e["id"], "question": e["question"], "gold": e["gold"], "round0": e["round0"], "rounds": [],
                   "final": e["round0"], "gen_tokens": 0, "prompt_tokens": 0, "pages_fetched": 0, "sec": 0.0}
            if non_answer(e["round0"]):
                t0 = time.time()
                seen = set(e.get("titles") or []) | set(re.findall(r"^\[([^\]\n]+)\]", e["passage"], re.M))   # chunks start with "[Title]"
                for r in range(1, ROUNDS + 1):
                    qtxt, pi, gi = sm.gen(QPROMPT.format(q=e["question"]))
                    rec["prompt_tokens"] += pi
                    rec["gen_tokens"] += gi
                    qs = queries(qtxt)
                    new = []
                    for q in qs:
                        for t in R._search_titles(q, 5):
                            if t not in seen and t not in new:
                                new.append(t)
                    new = new[:NEW_PAGES]
                    seen |= set(new)
                    rnd = {"round": r, "queries": qs, "titles": new, "passage": "", "answer": None}
                    if new:
                        p = R2.passage(e["question"], new, 1500)
                        rec["pages_fetched"] += len(new)
                        out, pi, gi = sm.gen(CAUTIOUS.format(p=p, q=e["question"]), 40)
                        rec["prompt_tokens"] += pi
                        rec["gen_tokens"] += gi
                        rnd.update(passage=p, answer=parse(out))
                    rec["rounds"].append(rnd)
                    if rnd["answer"] is not None and not non_answer(rnd["answer"]):
                        rec["final"] = rnd["answer"]
                        break
                rec["sec"] = round(time.time() - t0, 1)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if k % 25 == 0:
                print(f"  {k}/{len(its)}", flush=True)
    R2.save_cache()
    print("done")


if __name__ == "__main__":
    main()
