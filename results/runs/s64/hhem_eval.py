"""S64 gate G13: HHEM-2.1-Open (Vectara, Apache-2.0; weights downloaded 2026-11-11 into models_external/hhem with the user's permission) as a second off-the-shelf checker on our reviewer labels,
next to MiniCheck (S54). The repository's custom code was read and not run: the same model is built here as T5ForTokenClassification from the flan-t5-base config (2 labels), the weights
loaded from model.safetensors with the 't5.' prefix removed, the published prompt used, and the probability of label 1 (consistent) taken at the first token. Premise = page title and quote;
hypothesis = 'The answer to the question "Q" is A.' Held-out rows of S51 and the Mintaka rows of S52. venv_gpu/Scripts/python.exe -I -B results/runs/s64/hhem_eval.py"""
import csv, json, sys
from pathlib import Path
import numpy as np
import torch
from scipy.stats import beta
from sklearn.metrics import roc_auc_score
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
ROOT = Path(r"F:\Projects\AI hallucinations"); D = ROOT / "results/runs/s64"; S54 = ROOT / "results/runs/s54"
sys.stdout.reconfigure(encoding="utf-8")
from safetensors.torch import load_file
from transformers import AutoConfig, T5ForTokenClassification
cfg = AutoConfig.from_pretrained(str(ROOT / "models_external/flan-t5-base-cfg")); cfg.num_labels = 2
tok = AutoTokenizer.from_pretrained(str(ROOT / "models_external/flan-t5-base-cfg"))
model = T5ForTokenClassification(cfg)
sd = {k[3:]: v for k, v in load_file(str(ROOT / "models_external/hhem/model.safetensors")).items() if k.startswith("t5.")}
missing, unexpected = model.load_state_dict(sd, strict=False); print("missing", missing, "unexpected", unexpected)
model = model.cuda().eval()
PROMPT = "<pad> Determine if the hypothesis is true given the premise?\n\nPremise: {text1}\n\nHypothesis: {text2}"
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
        texts = [PROMPT.format(text1=r["doc"], text2=r["claim"]) for r in batch]
        enc = tok(texts, truncation=True, max_length=2048, padding=True, return_tensors="pt").to("cuda")
        lg = model(**enc).logits[:, 0, :].float()
        probs += torch.softmax(lg, -1)[:, 1].cpu().tolist()
p = np.array(probs); json.dump(probs, open(D / "hhem_probs.json", "w"))
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
res = ["# S64 gate G13: HHEM-2.1-Open and MiniCheck against the 27B judge and the small judge on our reviewer labels", "", "| Set | Checker | AUROC for 'states' | accepted | measure among accepted |", "|---|---|---|---|---|"]
for st in ("heldout", "mintaka"):
    idx = np.array([i for i, r in enumerate(rows) if r["set"] == st]); y = np.array([rows[i]["y"] for i in idx]); bad = np.array([rows[i]["bad"] for i in idx]); pm = p[idx]
    measure = (1 - y) if st == "heldout" else bad; label = "not 'states'" if st == "heldout" else "misleading"
    def line(name, mask, auc):
        n = int(mask.sum()); b = int(measure[mask].sum())
        return f"| {st} (n={len(idx)}) | {name} | {auc} | {n} ({100*n/len(idx):.1f}%) | {label}: {b} ({100*b/max(1,n):.1f}%, upper {up(b,n):.1f}%) |"
    res.append(line("HHEM, threshold 0.5", pm >= 0.5, f"{roc_auc_score(y, pm):.3f}"))
    ps = np.array([rows[i]["p_small"] for i in idx]) if st == "heldout" else None
    if st == "heldout":
        res.append(line("small trained judge, 0.5", ps >= 0.5, f"{roc_auc_score(y, ps):.3f}"))
        k = int((ps >= 0.5).sum()); thr = np.sort(pm)[::-1][k - 1]
        res.append(line(f"HHEM at the small judge's acceptance ({k})", pm >= thr, ""))
    else:
        k = 154; thr = np.sort(pm)[::-1][k - 1]
        res.append(line("HHEM at the small judge's acceptance (154)", pm >= thr, ""))
    # equal-acceptance comparison with the 27B prompted judge (S54 j27_part.json, same row order) and MiniCheck (S54 minicheck_probs.json, same row order)
    j27 = np.array([bool(o) for o in json.load(open(S54 / "j27_part.json", encoding="utf-8"))])[idx]   # booleans (YES) as saved by s54/j27.py
    mc = np.array(json.load(open(S54 / "minicheck_probs.json")))[idx]
    k = int(j27.sum()); res.append(line("27B prompted judge (rule R27 prompt)", j27, ""))
    for nm, sc in (("HHEM", pm), ("MiniCheck", mc)):
        thr = np.sort(sc)[::-1][k - 1]; res.append(line(f"{nm} at the 27B judge's acceptance ({k})", sc >= thr, f"{roc_auc_score(y, sc):.3f}"))
(D / "HHEM_result.md").write_text("\n".join(res) + "\n", encoding="utf-8")
print("\n".join(res))
