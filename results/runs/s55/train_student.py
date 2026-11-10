"""S55: the student judge: the S51 recipe (Qwen3-Embedding-0.6B, LoRA r=16, 3 epochs) trained on the S51 labelled training rows plus the silver rows labelled by the 27B. Evaluated on the S51
held-out rows and on the Mintaka review rows of S52. venv_gpu/Scripts/python.exe -B results/runs/s55/train_student.py"""
import csv, json, os, random, sys, time
from pathlib import Path
import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from scipy.stats import beta
from sklearn.metrics import roc_auc_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s55"
gold = [r for r in map(json.loads, open(ROOT / "data/quote_sufficiency/all.jsonl", encoding="utf-8")) if r["label"]]
for r in gold:
    r["y"] = int(r["label"] == "states"); r["test"] = int(r["group"], 16) % 5 == 0
    r["text"] = f"Question: {r['question']}\nProposed answer: {r['answer']}\nPage: {r['title']}\nQuote: {r['quote']}"
tr = [r for r in gold if not r["test"]]; te = [r for r in gold if r["test"]]
silver = [json.loads(l) for l in open(D / "silver_rows.jsonl", encoding="utf-8")]; lab = json.load(open(D / "silver_labels.json"))
tr_s = [{"y": int(v), "text": f"Question: {r['question']}\nProposed answer: {r['answer']}\nPage: {r['title']}\nQuote: {r['quote']}"} for r, v in zip(silver, lab)]
print("gold train", len(tr), "silver", len(tr_s), "silver YES share", round(float(np.mean(lab)), 3), "test", len(te), flush=True)
train = tr + tr_s
path = str(ROOT / "models/qwen3-embedding-0.6b")
tok = AutoTokenizer.from_pretrained(path); tok.padding_side = "right"
model = AutoModelForSequenceClassification.from_pretrained(path, num_labels=2, torch_dtype=torch.bfloat16)
if model.config.pad_token_id is None:
    model.config.pad_token_id = tok.pad_token_id
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"], task_type="SEQ_CLS", modules_to_save=["score"]))
model.cuda()
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=2e-4, weight_decay=0.01)
random.seed(5502); torch.manual_seed(5502)
EP, BS, ML = 3, 16, 384
steps = EP * ((len(train) + BS - 1) // BS); sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 30) * max(0.0, 1 - s / steps))


def batch(rs):
    enc = tok([r["text"] for r in rs], truncation=True, max_length=ML, padding=True, return_tensors="pt")
    return {k: v.cuda() for k, v in enc.items()}, torch.tensor([r["y"] for r in rs]).cuda()


def score(rows):
    model.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(rows), 32):
            x, _ = batch(rows[i:i + 32]); out += torch.softmax(model(**x).logits.float(), -1)[:, 1].cpu().tolist()
    return np.array(out)


t0 = time.time(); step = 0
for ep in range(EP):
    random.shuffle(train); model.train()
    for i in range(0, len(train), BS):
        x, y = batch(train[i:i + BS])
        loss = torch.nn.functional.cross_entropy(model(**x).logits.float(), y)
        loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad(); step += 1
        if step % 100 == 0:
            print("epoch", ep, "step", step, "of", steps, round(loss.item(), 4), f"{time.time()-t0:.0f}s", flush=True)
model.save_pretrained(str(D / "student_lora"))
# evaluation
M = []
for p in (1, 2, 3):
    S = {int(r["row"]): r for r in csv.DictReader(open(ROOT / f"results/runs/s52/M_sheet_part{p}.csv", encoding="utf-8-sig"))}
    V = {rv: {int(r["row"]): r["quote_verdict"].strip().casefold() for r in csv.DictReader(open(ROOT / f"results/runs/s52/M_verdict_part{p}_{rv}.csv", encoding="utf-8-sig"))} for rv in "AB"}
    for k in json.load(open(ROOT / "results/runs/s52/M_key.json"))[str(p)]:
        r = S[k["row"]]; a, b = V["A"][k["row"]], V["B"][k["row"]]
        if k["kind"] != "decoy":
            M.append({"text": f"Question: {r['question']}\nProposed answer: {r['answer']}\nPage: {r['page_title']}\nQuote: {r['quote']}", "y": int(a == b == "states"), "bad": int(a == b == "not")})
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
pt = score(te); yt = np.array([r["y"] for r in te]); pm = score(M); ym = np.array([r["y"] for r in M]); bm = np.array([r["bad"] for r in M])
out = ["# S55: the student judge (S51 recipe, gold plus 27B silver labels)", "", f"Training rows: {len(tr)} labelled + {len(tr_s)} silver (27B YES share {np.mean(lab):.3f}).", "",
       "| Set | AUROC for 'states' | accepted at 0.5 | measure among accepted |", "|---|---|---|---|"]
a = pt >= 0.5; n = int(a.sum()); b = int((1 - yt)[a].sum())
out.append(f"| held-out (n={len(te)}) | {roc_auc_score(yt, pt):.3f} | {n} ({100*n/len(te):.1f}%) | not 'states' {b} ({100*b/max(1,n):.1f}%, upper {up(b,n):.1f}%) |")
a = pm >= 0.5; n = int(a.sum()); b = int(bm[a].sum())
out.append(f"| Mintaka rows (n={len(M)}) | {roc_auc_score(ym, pm):.3f} | {n} ({100*n/len(M):.1f}%) | misleading {b} ({100*b/max(1,n):.1f}%, upper {up(b,n):.1f}%) |")
(D / "S55_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
