"""S5 step 1: for each question, (a) hidden states of the model at the last prompt token, for several layers, BEFORE it answers;
(b) a greedy answer with mean token log-probability; (c) 8 sampled answers (T=0.8). Same model for activations and labels.
Run inside venv_gpu:  venv_gpu\\Scripts\\python.exe -B -m vkg.probe_gen --model models/qwen3-4b-instruct-2507 --out results/runs/s5
--random-init : load the same architecture with random weights and extract activations only (control).
Datasets: TriviaQA rc.nocontext validation (2000 questions, seed 6000) and the 500-question SimpleQA Verified pool of S3
(results/runs/s3_pool.json; it excludes the 300 frozen test ids). No test id is ever read.
"""
import argparse
import json
import random
import re
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
LAYERS = [6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]          # hidden_states indices (0 = embeddings); Qwen3-4B has 36 layers
PROMPT = 'Question: {q}\nReply as JSON: {{"answer": "<short answer>"}}'


def load_questions(n_trivia, seed):
    import pandas as pd
    df = pd.read_parquet(ROOT / "data" / "triviaqa" / "rc.nocontext" / "validation-00000-of-00001.parquet")
    idx = random.Random(seed).sample(range(len(df)), n_trivia)
    qs = []
    for i in idx:
        r = df.iloc[i]
        ans = r["answer"]
        al = sorted({str(a) for a in list(ans["aliases"]) + [ans["value"]]})
        qs.append({"qid": f"tqa-{r['question_id']}", "dataset": "trivia", "question": r["question"], "gold": al})
    # the 500 SimpleQA Verified questions of the S3 pool (all outside the 300 frozen test ids), in file order
    for l in open(ROOT / "results" / "runs" / "s3_signals_raw.jsonl", encoding="utf-8"):
        r = json.loads(l)
        qs.append({"qid": r["qid"], "dataset": "simpleqa", "question": r["question"], "gold": [r["gold"]]})
    return qs


def parse(raw):
    m = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    return (m.group(1) if m else raw.strip().split("\n")[0])[:200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-trivia", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=6000)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--random-init", action="store_true")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(ROOT / a.model if not Path(a.model).is_absolute() else a.model)
    tok.padding_side = "left"
    mp = ROOT / a.model if not Path(a.model).is_absolute() else Path(a.model)
    if a.random_init:
        torch.manual_seed(0)
        model = AutoModelForCausalLM.from_config(AutoConfig.from_pretrained(mp), dtype=torch.bfloat16).cuda().eval()
    else:
        model = AutoModelForCausalLM.from_pretrained(mp, dtype=torch.bfloat16).cuda().eval()
    qs = load_questions(a.n_trivia, a.seed)
    if a.limit:
        qs = qs[:a.limit] + [q for q in qs if q["dataset"] == "simpleqa"][:a.limit]
    prompts = [tok.apply_chat_template([{"role": "user", "content": PROMPT.format(q=q["question"])}], add_generation_prompt=True, tokenize=False) for q in qs]
    feats = np.zeros((len(qs), len(LAYERS), model.config.hidden_size), dtype=np.float16)
    recs = []
    t0 = time.time()
    for s in range(0, len(qs), a.bs):
        batch = prompts[s:s + a.bs]
        enc = tok(batch, return_tensors="pt", padding=True).to("cuda")
        with torch.no_grad():
            hs = model(**enc, output_hidden_states=True).hidden_states
            for j, l in enumerate(LAYERS):
                feats[s:s + len(batch), j] = hs[l][:, -1, :].float().cpu().numpy().astype(np.float16)
            if not a.random_init:
                g = model.generate(**enc, do_sample=False, max_new_tokens=40, output_scores=True, return_dict_in_generate=True,
                                   pad_token_id=tok.pad_token_id)
                ts = model.compute_transition_scores(g.sequences, g.scores, normalize_logits=True).float().cpu()
                gen = g.sequences[:, enc["input_ids"].shape[1]:].cpu()
                smp = model.generate(**enc, do_sample=True, temperature=0.8, top_p=1.0, top_k=0, num_return_sequences=8,
                                     max_new_tokens=40, pad_token_id=tok.pad_token_id)
                smp = smp[:, enc["input_ids"].shape[1]:].cpu()
        if not a.random_init:
            for k in range(len(batch)):
                ids = gen[k]
                n = int((ids != tok.pad_token_id).sum()) or 1
                raw = tok.decode(ids, skip_special_tokens=True)
                lp = float(ts[k, :n].mean())
                samples = [parse(tok.decode(smp[k * 8 + m], skip_special_tokens=True)) for m in range(8)]
                recs.append({**qs[s + k], "greedy_raw": raw, "greedy_answer": parse(raw), "lp_mean": lp, "samples": samples})
        if (s // a.bs) % 10 == 0:
            print(f"{s + len(batch)}/{len(qs)}  {time.time() - t0:.0f}s", flush=True)
    tag = "random" if a.random_init else "trained"
    np.save(out / f"feats_{tag}.npy", feats)
    if not a.random_init:
        with open(out / "gen.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump({"layers": LAYERS, "n": len(qs), "model": a.model, "random_init": a.random_init, "seed": a.seed}, open(out / f"meta_{tag}.json", "w"))
    print("done", time.time() - t0)


if __name__ == "__main__":
    main()
