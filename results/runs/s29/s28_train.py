"""S28: LoRA checker for "does this sentence state that this span answers this question" (docs/S28_PLAN.md).
Trains on results/runs/s29/s28_train.jsonl (SimpleQA design pool only), validates on 15% of the questions, then scores any jsonl file with fields
question, sentence, span:   venv_gpu/Scripts/python.exe -B results/runs/s29/s28_train.py train
                            venv_gpu/Scripts/python.exe -B results/runs/s29/s28_train.py score <in.jsonl> <out.jsonl>"""
import ctypes, json, random, sys, time
from pathlib import Path
import numpy as np
import torch
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "results/runs/s29"
MP = ROOT / "models/qwen3-4b-instruct-2507"
TEMPLATE = ("Question: {q}\nSentence from a source page: {s}\nCandidate answer: {a}\n"
            "Does the sentence state that the candidate answer is the answer to the question? Answer yes or no.")


def load_model(adapter=None):
    tok = AutoTokenizer.from_pretrained(MP); tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(MP, dtype=torch.bfloat16).cuda()
    if adapter:
        model = PeftModel.from_pretrained(model, adapter)
    return tok, model


def encode(tok, rows):
    texts = [tok.apply_chat_template([{"role": "user", "content": TEMPLATE.format(q=r["question"], s=r["sentence"][:700], a=r["span"][:120])}],
                                     add_generation_prompt=True, tokenize=False) for r in rows]
    return tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=640).to("cuda")


def margin(tok, model, rows):
    yes = tok.encode("yes", add_special_tokens=False)[0]; no = tok.encode("no", add_special_tokens=False)[0]
    enc = encode(tok, rows)
    out = model(**enc).logits[:, -1, :].float()
    return out[:, yes] - out[:, no]


def auroc(y, s):
    y = np.asarray(y); s = np.asarray(s)
    pos, neg = s[y == 1], s[y == 0]
    return float((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean())


def train():
    rows = [json.loads(l) for l in open(D / "s28_train.jsonl", encoding="utf-8")]
    ids = sorted({r["id"] for r in rows}); rng = random.Random(28); rng.shuffle(ids)
    val_ids = set(ids[: int(0.15 * len(ids))])
    tr = [r for r in rows if r["id"] not in val_ids]; va = [r for r in rows if r["id"] in val_ids]
    tok, model = load_model()
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM"))
    model.gradient_checkpointing_enable(); model.enable_input_require_grads(); model.config.use_cache = False
    torch.cuda.set_per_process_memory_fraction(0.6)      # leave headroom for the machine
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    bs, acc, epochs = 8, 2, 2                              # effective batch 16
    steps = epochs * (len(tr) // (bs * acc)); step = 0; t0 = time.time()
    pos_w = torch.tensor(sum(1 for r in tr if r["label"] == 0) / max(1, sum(1 for r in tr if r["label"] == 1)), device="cuda")
    for ep in range(epochs):
        rng.shuffle(tr); model.train()
        for s in range(0, len(tr) - bs * acc + 1, bs * acc):
            for a_ in range(acc):
                batch = tr[s + a_ * bs: s + (a_ + 1) * bs]
                m = margin(tok, model, batch)
                y = torch.tensor([float(r["label"]) for r in batch], device="cuda")
                loss = torch.nn.functional.binary_cross_entropy_with_logits(m, y, pos_weight=pos_w) / acc
                loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            for g in opt.param_groups:
                g["lr"] = 1e-4 * (1 - step / steps)
            opt.step(); opt.zero_grad(); step += 1
            if step % 50 == 0:
                print(f"step {step}/{steps} loss {loss.item() * acc:.3f} {time.time()-t0:.0f}s", flush=True)
    model.eval(); sc = []
    with torch.no_grad():
        for s in range(0, len(va), 16):
            sc += margin(tok, model, va[s:s + 16]).tolist()
    y = [r["label"] for r in va]
    print("validation questions", len(val_ids), "examples", len(va), "AUROC", round(auroc(y, sc), 4))
    for kind in ("year", "number", "name"):
        idx = [i for i, r in enumerate(va) if r["kind"] == kind]
        if len({y[i] for i in idx}) == 2:
            print("  ", kind, len(idx), round(auroc([y[i] for i in idx], [sc[i] for i in idx]), 4))
    model.save_pretrained(D / "s28_adapter")
    (D / "s28_val.json").write_text(json.dumps({"auroc": auroc(y, sc), "n": len(va)}), encoding="utf-8")


def score(inp, outp):
    rows = [json.loads(l) for l in open(inp, encoding="utf-8")]
    torch.cuda.set_per_process_memory_fraction(0.5)       # leave headroom for the machine
    tok, model = load_model(D / "s28_adapter"); model.eval(); out = []
    with torch.no_grad():
        for s in range(0, len(rows), 16):
            out += margin(tok, model, rows[s:s + 16]).tolist()
    with open(outp, "w", encoding="utf-8") as f:
        for r, m in zip(rows, out):
            r["margin"] = m; f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("scored", len(rows))


if __name__ == "__main__":
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x40)   # idle priority
    train() if sys.argv[1] == "train" else score(sys.argv[2], sys.argv[3])
