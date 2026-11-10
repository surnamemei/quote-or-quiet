"""S54: MiniCheck-Flan-T5-Large (Tang, Laban, Durrett, EMNLP 2024; MIT; weights downloaded 2026-11-10 into models_external/minicheck-ft5-large, no script from the repository is run) as an off-the-shelf
checker on our reviewer labels. Input and decoding as in the authors' inference code (read, not run): 'predict: ' + document + eos + claim, one decoder step from a zero start token, softmax over the
logits of token ids 3 (no support) and 209 (support). Document = page title and quote; claim = 'The answer to the question "Q" is A.' Held-out rows of S51 and the Mintaka rows of S52.
venv_gpu/Scripts/python.exe -I -B results/runs/s54/minicheck_eval.py"""
import csv, json, sys
from pathlib import Path
import numpy as np
import torch
from scipy.stats import beta
from sklearn.metrics import roc_auc_score
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
ROOT = Path(r"F:\Projects\AI hallucinations"); D = ROOT / "results/runs/s54"
sys.stdout.reconfigure(encoding="utf-8")
path = str(ROOT / "models_external/minicheck-ft5-large")
tok = AutoTokenizer.from_pretrained(path)
model = AutoModelForSeq2SeqLM.from_pretrained(path, torch_dtype=torch.bfloat16).cuda().eval()
P = json.load(open(ROOT / "results/runs/s51/d_pred.json", encoding="utf-8"))
rows = [{"set": "heldout", "doc": f"{r['title']}: {r['quote']}", "claim": f"The answer to the question \"{r['question']}\" is {r['answer']}.", "y": r["y"], "bad": int(r["label"] == "not"), "p_small": r["p"]} for r in P]
for p in (1, 2, 3):
    S = {int(r["row"]): r for r in csv.DictReader(open(ROOT / f"results/runs/s52/M_sheet_part{p}.csv", encoding="utf-8-sig"))}
    V = {rv: {int(r["row"]): r["quote_verdict"].strip().casefold() for r in csv.DictReader(open(ROOT / f"results/runs/s52/M_verdict_part{p}_{rv}.csv", encoding="utf-8-sig"))} for rv in "AB"}
    for k in json.load(open(ROOT / "results/runs/s52/M_key.json"))[str(p)]:
        r = S[k["row"]]; a, b = V["A"][k["row"]], V["B"][k["row"]]
        if k["kind"] != "decoy":
            rows.append({"set": "mintaka", "doc": f"{r['page_title']}: {r['quote']}", "claim": f"The answer to the question \"{r['question']}\" is {r['answer']}.", "y": int(a == b == "states"), "bad": int(a == b == "not"), "p_small": None})
probs = []
with torch.no_grad():
    for i in range(0, len(rows), 16):
        batch = rows[i:i + 16]
        texts = ["predict: " + tok.eos_token.join([r["doc"], r["claim"]]) for r in batch]
        enc = tok(texts, truncation=True, max_length=2048, padding=True, return_tensors="pt").to("cuda")
        out = model(**enc, decoder_input_ids=torch.zeros((len(batch), 1), dtype=torch.long, device="cuda"))
        lg = out.logits[:, 0, :][:, [3, 209]].float()
        probs += torch.softmax(lg, -1)[:, 1].cpu().tolist()
p = np.array(probs); json.dump(probs, open(D / "minicheck_probs.json", "w"))
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
res = ["# S54: MiniCheck-Flan-T5-Large on our reviewer labels", "", "| Set | Checker | AUROC for 'states' | accepted | measure among accepted |", "|---|---|---|---|---|"]
for st in ("heldout", "mintaka"):
    idx = np.array([i for i, r in enumerate(rows) if r["set"] == st]); y = np.array([rows[i]["y"] for i in idx]); bad = np.array([rows[i]["bad"] for i in idx]); pm = p[idx]
    measure = (1 - y) if st == "heldout" else bad; label = "not 'states'" if st == "heldout" else "misleading"
    def line(name, mask, auc):
        n = int(mask.sum()); b = int(measure[mask].sum())
        return f"| {st} (n={len(idx)}) | {name} | {auc} | {n} ({100*n/len(idx):.1f}%) | {label}: {b} ({100*b/max(1,n):.1f}%, upper {up(b,n):.1f}%) |"
    res.append(line("MiniCheck, threshold 0.5", pm >= 0.5, f"{roc_auc_score(y, pm):.3f}"))
    ps = np.array([rows[i]["p_small"] for i in idx]) if st == "heldout" else None
    if st == "heldout":
        res.append(line("small trained judge, 0.5", ps >= 0.5, f"{roc_auc_score(y, ps):.3f}"))
        k = int((ps >= 0.5).sum()); thr = np.sort(pm)[::-1][k - 1]
        res.append(line(f"MiniCheck at the small judge's acceptance ({k})", pm >= thr, ""))
    else:
        k = 154; thr = np.sort(pm)[::-1][k - 1]
        res.append(line("MiniCheck at the small judge's acceptance (154)", pm >= thr, ""))
(D / "MiniCheck_result.md").write_text("\n".join(res) + "\n", encoding="utf-8")
print("\n".join(res))
