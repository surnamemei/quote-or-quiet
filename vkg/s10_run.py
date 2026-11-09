"""S10: reading curriculum (vkg/reading_curriculum.py) on top of the S6b evidence training, Qwen3-4B-Instruct-2507 + LoRA.
Stages (venv_gpu): python -B -m vkg.s10_run build | train | eval     (polite: idle priority; run via vkg.s10_wait)
- build: train = the S6b training set (3000 SQuAD2: 1500 answerable, 1500 -> "unknown") + 2000 synthetic reading items (seed 10).
         synthetic test = 300 new synthetic items (seed 11; same templates, new random facts).
- train: identical recipe to S6b (LoRA r16 on all projections, 2 epochs, bs 16, lr 1e-4, plain prompt), adapter models/s10_lora_reading.
- eval : plain prompt with the S6b adapter ("s6b") and the S10 adapter ("s10") on FRESH (200), the S6b eval suites (SimpleQA-E 300,
         SQuAD2 300, FaithEval 300) and the synthetic test; the base model's plain and cautious prompts on the synthetic test.
         (Base plain/cautious on FRESH and the S6b suites, and S6b on the S6b suites, already exist and are reused.)
"""
import json
import random
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .probe_gen import ROOT
from .reading_curriculum import make
from .s6b_run import CAUTIOUS, MODEL, PLAIN, gen

S6B = ROOT / "results" / "runs" / "s6b"
OUT = ROOT / "results" / "runs" / "s10"
ADAPTER = ROOT / "models" / "s10_lora_reading"
S6B_ADAPTER = ROOT / "models" / "s6b_lora_evidence"


def stage_build():
    OUT.mkdir(parents=True, exist_ok=True)
    train = json.load(open(S6B / "train.json", encoding="utf-8"))
    syn = make(2000, 10)
    train = train + [{"passage": s["passage"], "question": s["question"], "target": s["target"]} for s in syn]
    random.Random(10).shuffle(train)
    json.dump(train, open(OUT / "train.json", "w", encoding="utf-8"), ensure_ascii=False)
    test = make(300, 11)
    for k, t in enumerate(test):
        t["id"] = f"syn-{k}"
    json.dump(test, open(OUT / "synth_test.json", "w", encoding="utf-8"), ensure_ascii=False)
    tr_p = {s["passage"] for s in syn}
    print("train", len(train), "(3000 SQuAD2 + 2000 synthetic); synthetic test", len(test), "passage overlap", sum(t["passage"] in tr_p for t in test))


def stage_train(epochs=2, bs=16, lr=1e-4):
    from peft import LoraConfig, get_peft_model
    train = json.load(open(OUT / "train.json", encoding="utf-8"))
    tok = AutoTokenizer.from_pretrained(MODEL)
    m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda()
    m.gradient_checkpointing_enable()
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
            for mb in range(0, bs, 4):
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


def stage_eval():
    from peft import PeftModel
    fresh = json.load(open(ROOT / "results" / "runs" / "s8" / "fresh_items.json", encoding="utf-8"))
    for e in fresh:
        e["suite"] = "fresh"
    ev = json.load(open(S6B / "eval_items.json", encoding="utf-8"))
    syn = json.load(open(OUT / "synth_test.json", encoding="utf-8"))
    for e in syn:
        e["suite"], e["gold"], e["kind"] = "synth", [e["target"]], ("answerable" if e["answerable"] else "unanswerable") + ":" + e["kind"]
    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.padding_side = "left"
    base = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda().eval()
    res = {"base_plain_synth": gen(tok, base, syn, PLAIN), "base_cautious_synth": gen(tok, base, syn, CAUTIOUS)}
    m6 = PeftModel.from_pretrained(base, S6B_ADAPTER).eval()
    res["s6b_fresh"] = gen(tok, m6, fresh, PLAIN)
    res["s6b_synth"] = gen(tok, m6, syn, PLAIN)
    del m6, base
    torch.cuda.empty_cache()
    base = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda().eval()
    m10 = PeftModel.from_pretrained(base, ADAPTER).eval()
    res["s10_fresh"] = gen(tok, m10, fresh, PLAIN)
    res["s10_dev"] = gen(tok, m10, ev, PLAIN)
    res["s10_synth"] = gen(tok, m10, syn, PLAIN)
    with open(OUT / "eval_outputs.jsonl", "w", encoding="utf-8") as f:
        for name, items in (("fresh", fresh), ("dev", ev), ("synth", syn)):
            for i, e in enumerate(items):
                row = {"set": name, "suite": e["suite"], "id": e["id"], "kind": e.get("kind"), "question": e["question"], "gold": e.get("gold", [])}
                for k, v in res.items():
                    if k.endswith("_" + name):
                        row[k.rsplit("_", 1)[0]] = v[i]
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("eval outputs written")


if __name__ == "__main__":
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    {"build": stage_build, "train": stage_train, "eval": stage_eval}[sys.argv[1]]()
