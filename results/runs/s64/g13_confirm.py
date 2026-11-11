"""S64 gate G13 confirmatory comparison (docs/S64_G13_BASELINES_PLAN.md): the 300 displayed quotes of the S40 quote analysis with their blind labels;
27B judge (from the S40 run) against MiniCheck and HHEM at equal acceptance. Counts only. venv_gpu/Scripts/python.exe -I -B results/runs/s64/g13_confirm.py"""
import csv, json, sys
from pathlib import Path
import numpy as np, torch
from scipy.stats import beta
from safetensors.torch import load_file
from transformers import AutoConfig, AutoModelForSeq2SeqLM, AutoTokenizer, T5ForTokenClassification
ROOT = Path(r"F:\Projects\AI hallucinations"); Q = ROOT / "results/runs/s40/quote_analysis"; D = ROOT / "results/runs/s64"
sys.stdout.reconfigure(encoding="utf-8")
S = {s["id"]: s for s in map(json.loads, open(Q / "q_cands.jsonl", encoding="utf-8"))}; J27 = json.load(open(Q / "q_judge27.json", encoding="utf-8"))
K = json.load(open(Q / "Q_key.json")); lab = {}
for p, ks in K.items():
    vs = {}
    for rv in "AB":
        for r in csv.DictReader(open(Q / f"Q_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            vs.setdefault(int(r["row"]), []).append(r["quote_verdict"].strip().strip("'\"").casefold())
    for k in ks:
        if k["kind"] == "displayed":
            lab[k["id"]] = vs[k["row"]]
ids = sorted(lab); assert len(ids) == 300, len(ids)
rows = [{"id": i, "doc": f"{S[i]['cands'][0]['doc']}: {S[i]['cands'][0]['quote']}", "claim": f"The answer to the question \"{S[i]['question']}\" is {S[i]['answer']}.",
         "j27": str(J27.get(f"J|{i}|0", "")).strip().upper().startswith("YES"), "v": lab[i]} for i in ids]
# MiniCheck (as S54)
tok = AutoTokenizer.from_pretrained(str(ROOT / "models_external/minicheck-ft5-large"))
m = AutoModelForSeq2SeqLM.from_pretrained(str(ROOT / "models_external/minicheck-ft5-large"), torch_dtype=torch.bfloat16).cuda().eval(); mc = []
with torch.no_grad():
    for i in range(0, len(rows), 16):
        b = rows[i:i + 16]; enc = tok(["predict: " + tok.eos_token.join([r["doc"], r["claim"]]) for r in b], truncation=True, max_length=2048, padding=True, return_tensors="pt").to("cuda")
        lg = m(**enc, decoder_input_ids=torch.zeros((len(b), 1), dtype=torch.long, device="cuda")).logits[:, 0, :][:, [3, 209]].float(); mc += torch.softmax(lg, -1)[:, 1].cpu().tolist()
del m; torch.cuda.empty_cache()
# HHEM (as hhem_eval.py)
cfg = AutoConfig.from_pretrained(str(ROOT / "models_external/flan-t5-base-cfg")); cfg.num_labels = 2
tk = AutoTokenizer.from_pretrained(str(ROOT / "models_external/flan-t5-base-cfg")); h = T5ForTokenClassification(cfg)
h.load_state_dict({k[3:]: v for k, v in load_file(str(ROOT / "models_external/hhem/model.safetensors")).items() if k.startswith("t5.")}, strict=False); h = h.cuda().eval(); hh = []
PROMPT = "<pad> Determine if the hypothesis is true given the premise?\n\nPremise: {text1}\n\nHypothesis: {text2}"
with torch.no_grad():
    for i in range(0, len(rows), 16):
        b = rows[i:i + 16]; enc = tk([PROMPT.format(text1=r["doc"], text2=r["claim"]) for r in b], truncation=True, max_length=2048, padding=True, return_tensors="pt").to("cuda")
        hh += torch.softmax(h(**enc).logits[:, 0, :].float(), -1)[:, 1].cpu().tolist()
up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
notst = np.array([r["v"] != ["states", "states"] for r in rows]); mis = np.array([r["v"] == ["not", "not"] for r in rows])
j = np.array([r["j27"] for r in rows]); k = int(j.sum())
out = ["# S64 gate G13 confirmatory: displayed quotes of S40 (300, chosen by no judge)", "", f"Not 'states' among all 300: {int(notst.sum())}; misleading: {int(mis.sum())}.", "",
       "| Checker | accepted | not 'states' among accepted | misleading among accepted |", "|---|---|---|---|"]
def line(name, mask):
    n = int(mask.sum()); a = int(notst[mask].sum()); b = int(mis[mask].sum())
    return f"| {name} | {n} | {a} ({100*a/max(1,n):.1f}%, upper {up(a,n):.1f}%) | {b} ({100*b/max(1,n):.1f}%, upper {up(b,n):.1f}%) |"
out.append(line("27B judge (rule R prompt)", j))
for nm, sc in (("MiniCheck", np.array(mc)), ("HHEM", np.array(hh))):
    thr = np.sort(sc)[::-1][k - 1]; out.append(line(f"{nm} at the same acceptance ({k})", sc >= thr))
(D / "G13_confirm_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
