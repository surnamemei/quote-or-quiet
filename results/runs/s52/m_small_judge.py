"""S52: does the small quote-sufficiency judge of S51 (trained without any Mintaka row) transfer to the Mintaka reviews? Scores the 390 sheet rows with the saved LoRA model and compares with the reviewers.
venv_gpu/Scripts/python.exe -B results/runs/s52/m_small_judge.py"""
import csv, json, os, sys
from pathlib import Path
import numpy as np
import torch
from peft import PeftModel
from scipy.stats import beta
from sklearn.metrics import roc_auc_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s52"; S51 = ROOT / "results/runs/s51"
rows = []
for p in (1, 2, 3):
    S = {int(r["row"]): r for r in csv.DictReader(open(D / f"M_sheet_part{p}.csv", encoding="utf-8-sig"))}
    V = {rv: {int(r["row"]): r["quote_verdict"].strip().casefold() for r in csv.DictReader(open(D / f"M_verdict_part{p}_{rv}.csv", encoding="utf-8-sig"))} for rv in "AB"}
    K = json.load(open(D / "M_key.json"))[str(p)]
    for k in K:
        r = S[k["row"]]; a, b = V["A"][k["row"]], V["B"][k["row"]]
        rows.append({"kind": k["kind"], "id": k["id"], "text": f"Question: {r['question']}\nProposed answer: {r['answer']}\nPage: {r['page_title']}\nQuote: {r['quote']}", "y": int(a == "states" and b == "states"),
                     "bad": int(a == "not" and b == "not"), "agree": a == b})
path = str(ROOT / "models/qwen3-embedding-0.6b")
tok = AutoTokenizer.from_pretrained(path); tok.padding_side = "right"
base = AutoModelForSequenceClassification.from_pretrained(path, num_labels=2, torch_dtype=torch.bfloat16)
if base.config.pad_token_id is None:
    base.config.pad_token_id = tok.pad_token_id
model = PeftModel.from_pretrained(base, str(S51 / "judge_lora")).cuda().eval()
ps = []
with torch.no_grad():
    for i in range(0, len(rows), 32):
        enc = tok([r["text"] for r in rows[i:i + 32]], truncation=True, max_length=384, padding=True, return_tensors="pt")
        ps += torch.softmax(model(**{k: v.cuda() for k, v in enc.items()}).logits.float(), -1)[:, 1].cpu().tolist()
p = np.array(ps); y = np.array([r["y"] for r in rows]); bad = np.array([r["bad"] for r in rows]); kind = np.array([r["kind"] for r in rows])
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
nd = kind != "decoy"
out = ["# S52: the small judge of S51 on the Mintaka review rows (no Mintaka row in its training)", "",
       f"Rows {len(rows)}; without decoys {int(nd.sum())}; 'states' for both {int(y[nd].sum())} ({100*y[nd].mean():.1f}%). AUROC for 'states' (without decoys): {roc_auc_score(y[nd], p[nd]):.3f}", "",
       "| Quotes judged | n | accepted at 0.5 | misleading (both 'not') among accepted |", "|---|---|---|---|"]
for name, m in (("displayed quote (first accepted span)", (kind == "frozen")), ("rule R witness (differs from the displayed quote)", (kind == "rule"))):
    a = m & (p >= 0.5); b = int((bad == 1)[a].sum())
    out.append(f"| {name} | {int(m.sum())} | {int(a.sum())} | {b} ({100*b/max(1,int(a.sum())):.1f}%, upper {up(b,int(a.sum())):.1f}%) |")
a = nd & (p >= 0.5); b = int((bad == 1)[a].sum())
out.append(f"| all non-decoy rows | {int(nd.sum())} | {int(a.sum())} | {b} ({100*b/max(1,int(a.sum())):.1f}%, upper {up(b,int(a.sum())):.1f}%) |")
(D / "M_small_judge.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
