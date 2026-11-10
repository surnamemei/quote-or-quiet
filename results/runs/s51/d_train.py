"""S51 part D: a small quote-sufficiency judge. Qwen3-Embedding-0.6B with a classification head, LoRA, trained on the two-reviewer labels of S42 to S49 (data/quote_sufficiency/all.jsonl,
rows where the reviewers agree). Target: 'states' (the quote states the answer) against 'incomplete' or 'not'. Split by question: group hash mod 5 == 0 is the test set.
Writes results/runs/s51/d_pred.json (test probabilities). venv_gpu/Scripts/python.exe -B results/runs/s51/d_train.py"""
import json, os, random, sys, time
from pathlib import Path
import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForSequenceClassification, AutoTokenizer
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s51"
rows = [r for r in map(json.loads, open(ROOT / "data/quote_sufficiency/all.jsonl", encoding="utf-8")) if r["label"]]
for r in rows:
    r["y"] = int(r["label"] == "states")
    r["test"] = int(r["group"], 16) % 5 == 0
    r["text"] = f"Question: {r['question']}\nProposed answer: {r['answer']}\nPage: {r['title']}\nQuote: {r['quote']}"
tr = [r for r in rows if not r["test"]]; te = [r for r in rows if r["test"]]
print("train", len(tr), "test", len(te), "states share train", np.mean([r["y"] for r in tr]).round(3), flush=True)
path = str(ROOT / "models/qwen3-embedding-0.6b")
tok = AutoTokenizer.from_pretrained(path); tok.padding_side = "right"
model = AutoModelForSequenceClassification.from_pretrained(path, num_labels=2, torch_dtype=torch.bfloat16)
if model.config.pad_token_id is None:
    model.config.pad_token_id = tok.pad_token_id
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                                         task_type="SEQ_CLS", modules_to_save=["score"]))
model.cuda()
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-4, weight_decay=0.01)
random.seed(5101); torch.manual_seed(5101)
EP, BS, ML = 3, 16, 384
steps = EP * ((len(tr) + BS - 1) // BS); sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 30) * max(0.0, 1 - s / steps))


def batch(rs):
    enc = tok([r["text"] for r in rs], truncation=True, max_length=ML, padding=True, return_tensors="pt")
    return {k: v.cuda() for k, v in enc.items()}, torch.tensor([r["y"] for r in rs]).cuda()


t0 = time.time(); step = 0
for ep in range(EP):
    random.shuffle(tr); model.train()
    for i in range(0, len(tr), BS):
        x, y = batch(tr[i:i + BS])
        loss = torch.nn.functional.cross_entropy(model(**x).logits.float(), y)
        loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad(); step += 1
        if step % 50 == 0:
            print("epoch", ep, "step", step, "of", steps, "loss", round(loss.item(), 4), f"{time.time()-t0:.0f}s", flush=True)
model.eval(); out = []
with torch.no_grad():
    for i in range(0, len(te), 32):
        x, _ = batch(te[i:i + 32])
        p = torch.softmax(model(**x).logits.float(), -1)[:, 1].cpu().numpy()
        out += [float(v) for v in p]
json.dump([{"src": r["src"], "group": r["group"], "y": r["y"], "label": r["label"], "p": p, "question": r["question"], "answer": r["answer"], "title": r["title"], "quote": r["quote"]}
           for r, p in zip(te, out)], open(D / "d_pred.json", "w", encoding="utf-8"), ensure_ascii=False)
model.save_pretrained(str(D / "judge_lora"))
print("done", f"{time.time()-t0:.0f}s", flush=True)
