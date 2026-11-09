"""S6b: evidence-conditioned abstention on the 4B model. Train it to answer ONLY from a given passage, otherwise say "unknown".
Stages (inside venv_gpu): python -B -m vkg.s6b_run build | train | eval | analyze
Training: 3000 SQuAD 2.0 validation items (1500 answerable with the gold span, 1500 unanswerable -> "unknown"), disjoint (by id AND by
context paragraph) from every SQuAD2 evaluation sample used so far (seeds 0, 1000, 2000). Targets are gold spans from the PASSAGE, no parametric facts.
Eval (4B, three prompts/systems): SQuAD2 held-out (seed 1000, 300 items), FaithEval held-out (seed 1000, 300 items), and the 300 SimpleQA test
questions with the SAME variant-E Wikipedia passages the 27B saw. Systems: plain (passage + JSON answer), cautious (adds "use only the passage; else unknown"), trained (LoRA, plain prompt).
"""
import json
import random
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from . import tasks
from .probe_eval import correct
from .probe_gen import ROOT, parse
from .systems import UNKNOWN_RE
from .tasks import matches

MODEL = ROOT / "models" / "qwen3-4b-instruct-2507"
ADAPTER = ROOT / "models" / "s6b_lora_evidence"
OUT = ROOT / "results" / "runs" / "s6b"
PLAIN = 'Passage:\n{p}\n\nQuestion: {q}\nReply as JSON: {{"answer": "<short answer>"}}'
CAUTIOUS = ('Passage:\n{p}\n\nQuestion: {q}\nUse ONLY the passage. If the passage does not state the answer, or it is not clear, answer "unknown". '
            'Never guess.\nReply as JSON: {{"answer": "<short answer or unknown>"}}')


def stage_build():
    import os
    os.environ.setdefault("HF_HOME", str(ROOT / "data" / "hf"))
    from datasets import load_dataset
    OUT.mkdir(parents=True, exist_ok=True)
    d = load_dataset("rajpurkar/squad_v2", split="validation", cache_dir=os.environ["HF_HOME"])
    used_ids, used_ctx = set(), set()
    for seed, ex in ((0, None), (1000, 0), (2000, 1000)):
        for it in tasks.squad2(150, seed, ex):
            used_ids.add(it.id.split("-", 1)[1])
            used_ctx.add(it.passage)
    ans = [i for i in range(len(d)) if d[i]["answers"]["text"] and d[i]["id"] not in used_ids and d[i]["context"] not in used_ctx]
    una = [i for i in range(len(d)) if not d[i]["answers"]["text"] and d[i]["id"] not in used_ids and d[i]["context"] not in used_ctx]
    rng = random.Random(8000)
    train = []
    for i in rng.sample(ans, 1500):
        train.append({"passage": d[i]["context"], "question": d[i]["question"], "target": d[i]["answers"]["text"][0]})
    for i in rng.sample(una, 1500):
        train.append({"passage": d[i]["context"], "question": d[i]["question"], "target": "unknown"})
    rng.shuffle(train)
    json.dump(train, open(OUT / "train.json", "w", encoding="utf-8"), ensure_ascii=False)
    ev = []
    for it in tasks.squad2(150, 1000, 0):
        ev.append({"suite": "squad2", "id": it.id, "kind": it.kind, "question": it.question, "passage": it.passage, "gold": it.gold or []})
    for it in tasks.faitheval(150, 1000, 0):
        ev.append({"suite": "faitheval", "id": it.id, "kind": it.kind, "question": it.question, "passage": it.passage, "gold": []})
    for it in tasks.simpleqa_rag(300, 3000, "hybrid"):
        ev.append({"suite": "simpleqa_E", "id": it.id, "kind": it.kind, "question": it.question, "passage": it.passage, "gold": it.gold})
    json.dump(ev, open(OUT / "eval_items.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("train", len(train), "(1500 answerable / 1500 unanswerable); eval items", len(ev),
          {s: sum(e["suite"] == s for e in ev) for s in ("squad2", "faitheval", "simpleqa_E")})
    print("overlap check: train contexts shared with eval-sample contexts:", len({t["passage"] for t in train} & used_ctx))


def stage_train(epochs=2, bs=16, lr=1e-4):
    from peft import LoraConfig, get_peft_model
    train = json.load(open(OUT / "train.json", encoding="utf-8"))
    tok = AutoTokenizer.from_pretrained(MODEL)
    m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda()
    m.gradient_checkpointing_enable()          # the GPU is shared with another job: ~10 GB available
    m.enable_input_require_grads()
    m.config.use_cache = False
    m = get_peft_model(m, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    for p in m.parameters():
        if p.requires_grad:
            p.data = p.data.float()
    end_id = tok.convert_tokens_to_ids("<|im_end|>")
    ex = []
    for r in train:
        prompt = tok.apply_chat_template([{"role": "user", "content": PLAIN.format(p=r["passage"], q=r["question"])}], add_generation_prompt=True, tokenize=False)
        pi = tok(prompt, add_special_tokens=False)["input_ids"]
        ti = tok(json.dumps({"answer": r["target"]}, ensure_ascii=False), add_special_tokens=False)["input_ids"] + [end_id]
        ex.append((pi + ti, [-100] * len(pi) + ti))
    params = [p for p in m.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.0)
    steps = epochs * (len(ex) // bs)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 20) * max(0.0, 1 - s / steps))
    rng = random.Random(0)
    m.train()
    step, t0 = 0, time.time()
    for ep in range(epochs):
        order = list(range(len(ex)))
        rng.shuffle(order)
        for b in range(0, len(order) - bs + 1, bs):
            batch = [ex[i] for i in order[b:b + bs]]
            for mb in range(0, bs, 4):                 # 4 micro-batches of 4 = effective batch 16
                sub = batch[mb:mb + 4]
                L = max(len(x[0]) for x in sub)
                ids = torch.tensor([x[0] + [tok.pad_token_id] * (L - len(x[0])) for x in sub]).cuda()
                lab = torch.tensor([x[1] + [-100] * (L - len(x[1])) for x in sub]).cuda()
                att = torch.tensor([[1] * len(x[0]) + [0] * (L - len(x[0])) for x in sub]).cuda()
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    loss = m(input_ids=ids, attention_mask=att, labels=lab).loss
                (loss * (len(sub) / bs)).backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if step % 25 == 0:
                print(f"step {step}/{steps} loss {loss.item():.4f} {time.time() - t0:.0f}s", flush=True)
    m.save_pretrained(ADAPTER)
    print("adapter saved", ADAPTER)


def gen(tok, m, items, template, bs=3):
    prompts = [tok.apply_chat_template([{"role": "user", "content": template.format(p=e["passage"], q=e["question"])}], add_generation_prompt=True, tokenize=False) for e in items]
    order = sorted(range(len(prompts)), key=lambda i: len(prompts[i]))         # length-sorted batches
    outs = [None] * len(prompts)
    for s in range(0, len(order), bs):
        idx = order[s:s + bs]
        enc = tok([prompts[i] for i in idx], return_tensors="pt", padding=True).to("cuda")
        with torch.no_grad():
            g = m.generate(**enc, do_sample=False, max_new_tokens=40, pad_token_id=tok.pad_token_id)
        for k, i in enumerate(idx):
            outs[i] = parse(tok.decode(g[k, enc["input_ids"].shape[1]:], skip_special_tokens=True))
        if (s // bs) % 20 == 0:
            print(f"  gen {s + len(idx)}/{len(order)}", flush=True)
    return outs


def stage_eval():
    ev = json.load(open(OUT / "eval_items.json", encoding="utf-8"))
    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.padding_side = "left"
    base = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda().eval()
    res = {"plain": gen(tok, base, ev, PLAIN), "cautious": gen(tok, base, ev, CAUTIOUS)}
    from peft import PeftModel
    tr = PeftModel.from_pretrained(base, ADAPTER).eval()
    res["trained"] = gen(tok, tr, ev, PLAIN)
    with open(OUT / "eval_outputs.jsonl", "w", encoding="utf-8") as f:
        for i, e in enumerate(ev):
            f.write(json.dumps({**{k: e[k] for k in ("suite", "id", "kind", "question", "gold")}, **{s: res[s][i] for s in res}}, ensure_ascii=False) + "\n")
    print("eval outputs", len(ev))


def is_unknown(a):
    a = str(a).strip()
    return (not a) or bool(UNKNOWN_RE.search(a))


def outcome(r, ans):
    """Returns (answered, correct, silent_error)."""
    answered = not is_unknown(ans)
    if r["suite"] == "squad2" and r["kind"] == "answerable":
        ok = answered and matches(r["gold"], ans)
    elif r["suite"] == "simpleqa_E":
        ok = answered and bool(correct({"dataset": "simpleqa", "gold": r["gold"]}, ans))
    else:
        ok = False                                    # unanswerable / inconsistent: any definite answer is a silent error
    return answered, ok, answered and not ok


def analyze():
    rows = [json.loads(l) for l in open(OUT / "eval_outputs.jsonl", encoding="utf-8")]
    rng = random.Random(0)
    L = ["# S6b: evidence-conditioned abstention, Qwen3-4B-Instruct-2507 (generated by vkg/s6b_run.py analyze)", "",
         "SER = silent errors / all items of the suite (an answer to an unanswerable or inconsistent item, or a wrong answer); yield = correct / answerable items. Abstention = project UNKNOWN_RE.", ""]
    ref = {}
    for sysname in ("plain", "cautious", "trained"):
        for suite in ("squad2", "faitheval", "simpleqa_E"):
            sel = [r for r in rows if r["suite"] == suite]
            o = [outcome(r, r[sysname]) for r in sel]
            ref[(suite, sysname)] = o
    for suite, name in (("squad2", "SQuAD 2.0 held-out (150 answerable + 150 unanswerable)"), ("faitheval", "FaithEval held-out (150 unanswerable + 150 inconsistent)"),
                        ("simpleqa_E", "SimpleQA test questions with the same variant-E Wikipedia passages as the 27B (n=300)")):
        sel = [r for r in rows if r["suite"] == suite]
        n = len(sel)
        ans_idx = [i for i, r in enumerate(sel) if (r["kind"] == "answerable")]
        L += [f"## {name}", "", "| system | coverage | yield (correct / answerable) | SER (silent errors / all) | precision |", "|---|---|---|---|---|"]
        for sysname in ("plain", "cautious", "trained"):
            o = ref[(suite, sysname)]
            cov = sum(a for a, _, _ in o) / n
            y = sum(o[i][1] for i in ans_idx) / len(ans_idx) if ans_idx else float("nan")
            ser = sum(s for _, _, s in o) / n
            prec = sum(c for _, c, _ in o) / max(1, sum(a for a, _, _ in o))
            L.append(f"| {sysname} | {cov:.3f} | {y:.3f} | {ser:.3f} | {prec:.3f} |")
        L += ["", "Paired differences (95% bootstrap CI over items):", ""]
        for a, b in (("trained", "cautious"), ("trained", "plain"), ("cautious", "plain")):
            for lab, k in (("SER", 2), ("yield", 1)):
                if lab == "yield" and not ans_idx:
                    continue
                idx = ans_idx if lab == "yield" else list(range(n))
                d = [float(ref[(suite, a)][i][k]) - float(ref[(suite, b)][i][k]) for i in idx]
                bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(2000))
                L.append(f"- {a} minus {b}, {lab}: {sum(d)/len(d):+.3f} [{bs[50]:+.3f}, {bs[1949]:+.3f}]")
        L.append("")
    # reference: the 27B with the same passages (results/runs/openworld_simpleqa_hybrid_*), same 300 questions, repaired grader
    from .analyze_open import cor_rep, att
    big = [json.loads(l) for l in open(ROOT / "results" / "runs" / "openworld_simpleqa_hybrid_qwen3.8-27b_s3000_n300.jsonl", encoding="utf-8")]
    sel = {r["id"]: r for r in rows if r["suite"] == "simpleqa_E"}
    L += ["## Reference: Qwen3.8-27B on the same 300 questions and passages (frozen run), repaired grader", "", "| system | coverage | correct | wrong (SER) |", "|---|---|---|---|"]
    for s in ("B1_abstain", "B2_strict", "VKG_v2"):
        x = [r for r in big if r["system"] == s]
        L.append(f"| 27B {s} | {sum(map(att, x))/300:.3f} | {sum(map(cor_rep, x))/300:.3f} | {sum(att(r) and not cor_rep(r) for r in x)/300:.3f} |")
    B1 = {r["id"]: r for r in big if r["system"] == "B1_abstain"}
    ids = sorted(sel)
    idx_of = {r["id"]: i for i, r in enumerate([r for r in rows if r["suite"] == "simpleqa_E"])}
    for lab, f4, f27 in (("SER", lambda o: float(o[2]), lambda r: float(att(r) and not cor_rep(r))), ("correct", lambda o: float(o[1]), lambda r: float(cor_rep(r)))):
        o4 = ref[("simpleqa_E", "trained")]
        d = [f4(o4[idx_of[i]]) - f27(B1[i]) for i in ids]
        bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(2000))
        L.append(f"- 4B trained minus 27B B1_abstain, {lab}: {sum(d)/len(d):+.3f} [{bs[50]:+.3f}, {bs[1949]:+.3f}]")
    txt = "\n".join(L)
    (OUT / "S6b_tables.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    {"build": stage_build, "train": stage_train, "eval": stage_eval, "analyze": analyze}[sys.argv[1]]()
