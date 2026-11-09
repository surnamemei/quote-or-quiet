"""S6a: three ways to stop a small model answering what it does not know, compared on the SAME model and questions.
  (1) cautious prompt ("answer only if certain, else unknown"), no training;
  (2) probe gate: abstain when a linear probe on the model's hidden states (S5) scores the question as unlikely to be answered correctly;
  (3) abstention taught by LoRA fine-tuning on the model's OWN known/unknown split (R-Tuning / Gekhman-style; no new facts are injected:
      target = the model's own greedy answer if it was correct, else "unknown").
Stages (run inside venv_gpu):  python -B -m vkg.s6_run gen_train | train | eval
Training questions: 3000 TriviaQA validation questions disjoint from the 2000 used by S5 (seed 7000). Eval: S5's in-distribution test
(TriviaQA, 500) and SimpleQA Verified pool (500, outside the 300 frozen test ids). No hyper-parameter is tuned on eval data.
"""
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .probe_eval import correct, fit_layers, score_layers
from .probe_gen import PROMPT, ROOT, load_questions, parse
from .systems import UNKNOWN_RE

MODEL = ROOT / "models" / "qwen3-4b-instruct-2507"
OUT = ROOT / "results" / "runs" / "s6"
ADAPTER = ROOT / "models" / "s6_lora_abstain"
CAUTIOUS = ('Question: {q}\nAnswer only if you are certain the answer is correct; if you do not reliably know it, answer "unknown". '
            'Never guess.\nReply as JSON: {{"answer": "<short answer or unknown>"}}')


def tok_model(adapter=False):
    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.padding_side = "left"
    m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda().eval()
    if adapter:
        from peft import PeftModel
        m = PeftModel.from_pretrained(m, ADAPTER).eval()
    return tok, m


def chat_prompts(tok, qs, template):
    return [tok.apply_chat_template([{"role": "user", "content": template.format(q=q)}], add_generation_prompt=True, tokenize=False) for q in qs]


def greedy(tok, m, prompts, bs=48):
    outs = []
    for s in range(0, len(prompts), bs):
        enc = tok(prompts[s:s + bs], return_tensors="pt", padding=True).to("cuda")
        with torch.no_grad():
            g = m.generate(**enc, do_sample=False, max_new_tokens=40, pad_token_id=tok.pad_token_id)
        for k in range(g.shape[0]):
            outs.append(parse(tok.decode(g[k, enc["input_ids"].shape[1]:], skip_special_tokens=True)))
        if (s // bs) % 10 == 0:
            print(f"  gen {s + len(prompts[s:s + bs])}/{len(prompts)}", flush=True)
    return outs


def stage_gen_train():
    import pandas as pd
    df = pd.read_parquet(ROOT / "data" / "triviaqa" / "rc.nocontext" / "validation-00000-of-00001.parquet")
    used = set(random.Random(6000).sample(range(len(df)), 2000))
    pool = [i for i in range(len(df)) if i not in used]
    idx = random.Random(7000).sample(pool, 3000)
    recs = []
    for i in idx:
        r = df.iloc[i]
        al = sorted({str(a) for a in list(r["answer"]["aliases"]) + [r["answer"]["value"]]})
        recs.append({"qid": f"tqa-{r['question_id']}", "dataset": "trivia", "question": r["question"], "gold": al})
    tok, m = tok_model()
    ans = greedy(tok, m, chat_prompts(tok, [r["question"] for r in recs], PROMPT))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "train_labels.jsonl", "w", encoding="utf-8") as f:
        for r, a in zip(recs, ans):
            r["greedy_answer"] = a
            r["correct"] = bool(correct(r, a))
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("train questions", len(recs), "base greedy correct", sum(r["correct"] for r in recs) / len(recs))


def stage_train(epochs=2, bs=16, lr=1e-4):
    from peft import LoraConfig, get_peft_model
    recs = [json.loads(l) for l in open(OUT / "train_labels.jsonl", encoding="utf-8")]
    tok = AutoTokenizer.from_pretrained(MODEL)
    m = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda()
    m = get_peft_model(m, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
                                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    for p in m.parameters():
        if p.requires_grad:
            p.data = p.data.float()
    end_id = tok.convert_tokens_to_ids("<|im_end|>")
    ex = []
    for r in recs:
        prompt = tok.apply_chat_template([{"role": "user", "content": PROMPT.format(q=r["question"])}], add_generation_prompt=True, tokenize=False)
        target = json.dumps({"answer": r["greedy_answer"] if r["correct"] else "unknown"}, ensure_ascii=False)
        pi = tok(prompt, add_special_tokens=False)["input_ids"]
        ti = tok(target, add_special_tokens=False)["input_ids"] + [end_id]
        ex.append((pi + ti, [-100] * len(pi) + ti))
    print("examples", len(ex), "unknown targets", sum(not r["correct"] for r in recs))
    params = [p for p in m.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.0)
    steps = epochs * (len(ex) // bs)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 20) * max(0.0, 1 - s / steps))
    rng = random.Random(0)
    m.train()
    step = 0
    t0 = time.time()
    for ep in range(epochs):
        order = list(range(len(ex)))
        rng.shuffle(order)
        for b in range(0, len(order) - bs + 1, bs):
            batch = [ex[i] for i in order[b:b + bs]]
            L = max(len(x[0]) for x in batch)
            ids = torch.tensor([x[0] + [tok.pad_token_id] * (L - len(x[0])) for x in batch]).cuda()
            lab = torch.tensor([x[1] + [-100] * (L - len(x[1])) for x in batch]).cuda()
            att = torch.tensor([[1] * len(x[0]) + [0] * (L - len(x[0])) for x in batch]).cuda()
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = m(input_ids=ids, attention_mask=att, labels=lab).loss
            loss.backward()
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
    qs = load_questions(2000, 6000)
    gen = [json.loads(l) for l in open(ROOT / "results" / "runs" / "s5" / "gen.jsonl", encoding="utf-8")]
    assert [g["qid"] for g in gen] == [q["qid"] for q in qs]
    te = list(range(1500, 2000))
    ood = list(range(2000, 2500))
    ev = te + ood
    tok, base = tok_model()
    cautious = greedy(tok, base, chat_prompts(tok, [qs[i]["question"] for i in ev], CAUTIOUS))
    del base
    torch.cuda.empty_cache()
    tok, tr = tok_model(adapter=True)
    trained = greedy(tok, tr, chat_prompts(tok, [qs[i]["question"] for i in ev], PROMPT))
    rows = []
    for k, i in enumerate(ev):
        rows.append({"qid": qs[i]["qid"], "dataset": qs[i]["dataset"], "question": qs[i]["question"], "gold": qs[i]["gold"], "idx": i,
                     "plain": gen[i]["greedy_answer"], "cautious": cautious[k], "trained": trained[k]})
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "eval_outputs.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("eval outputs written", len(rows))


def is_unknown(a):
    a = str(a).strip()
    return (not a) or bool(UNKNOWN_RE.search(a))


def analyze():
    rows = [json.loads(l) for l in open(OUT / "eval_outputs.jsonl", encoding="utf-8")]
    gen = [json.loads(l) for l in open(ROOT / "results" / "runs" / "s5" / "gen.jsonl", encoding="utf-8")]
    F = np.load(ROOT / "results" / "runs" / "s5" / "feats_trained.npy")
    yA = np.array([correct(r, r["greedy_answer"]) for r in gen], dtype=int)
    tr = np.arange(0, 1500)
    j, C, ss, mdl, _ = fit_layers(F, yA, tr)
    probe = score_layers(F, j, ss, mdl, np.arange(len(gen)))
    L = ["# S6a: cautious prompt vs probe gate vs fine-tuned abstention, same 4B model (generated by vkg/s6_run.py analyze)", "",
         f"Probe for the gate: label A (greedy answer correct), trained on TriviaQA train only, layer hidden_states[{[6,9,12,15,18,21,24,27,30,33,36][j]}], C={C}. "
         "Silent error rate (SER) = wrong answers / all questions; yield = correct answers / all questions; coverage = answered / all.", ""]
    rng = np.random.default_rng(0)
    for name, sel in (("In-distribution (TriviaQA test, n=500)", [r for r in rows if r["dataset"] == "trivia"]),
                      ("Out-of-distribution (SimpleQA Verified pool, n=500)", [r for r in rows if r["dataset"] == "simpleqa"])):
        n = len(sel)
        L += [f"## {name}", "", "| system | coverage | yield (correct/all) | SER (wrong/all) | precision |", "|---|---|---|---|---|"]
        res = {}
        for sysname in ("plain", "cautious", "trained"):
            ans = [not is_unknown(r[sysname]) for r in sel]
            cor = [a and bool(correct(r, r[sysname])) for a, r in zip(ans, sel)]
            wrong = [a and not c for a, c in zip(ans, cor)]
            res[sysname] = (np.array(ans), np.array(cor), np.array(wrong))
            cov = sum(ans) / n
            L.append(f"| {sysname} | {cov:.3f} | {sum(cor)/n:.3f} | {sum(wrong)/n:.3f} | {(sum(cor)/sum(ans) if sum(ans) else float('nan')):.3f} |")
        # probe gate applied to the PLAIN answers, at the coverage of each other system
        ps = np.array([probe[r["idx"]] for r in sel])
        plain_cor = res["plain"][1] | (~res["plain"][0] & False)
        plain_ans = res["plain"][0]
        order = np.argsort(-ps)
        gates = {}
        for tgt in ("cautious", "trained"):
            k = int(res[tgt][0].sum())
            mask = np.zeros(n, bool)
            mask[order[:k]] = True
            mask &= plain_ans
            cor = mask & res["plain"][1]
            wrong = mask & ~res["plain"][1]
            gates[tgt] = (mask, cor, wrong)
            L.append(f"| probe gate matched to {tgt} coverage | {mask.sum()/n:.3f} | {cor.sum()/n:.3f} | {wrong.sum()/n:.3f} | {(cor.sum()/mask.sum() if mask.sum() else float('nan')):.3f} |")
        L += ["", "Paired differences in SER (wrong/all), 95% bootstrap CI over questions (negative = first system has fewer silent errors):", ""]
        def diff(a_wrong, b_wrong):
            d = a_wrong.astype(float) - b_wrong.astype(float)
            bs = sorted(rng.choice(d, n).mean() for _ in range(2000))
            return d.mean(), bs[50], bs[1949]
        pairs = [("trained minus cautious prompt", res["trained"][2], res["cautious"][2]),
                 ("trained minus probe gate (same coverage as trained)", res["trained"][2], gates["trained"][2]),
                 ("cautious prompt minus probe gate (same coverage as cautious)", res["cautious"][2], gates["cautious"][2]),
                 ("trained minus plain", res["trained"][2], res["plain"][2])]
        for lab, a, b in pairs:
            m_, lo, hi = diff(a, b)
            L.append(f"- {lab}: {m_:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        def diffy(a_c, b_c):
            d = a_c.astype(float) - b_c.astype(float)
            bs = sorted(rng.choice(d, n).mean() for _ in range(2000))
            return d.mean(), bs[50], bs[1949]
        L += ["", "Paired differences in yield (correct/all):", ""]
        for lab, a, b in (("trained minus cautious prompt", res["trained"][1], res["cautious"][1]),
                          ("trained minus probe gate (same coverage as trained)", res["trained"][1], gates["trained"][1])):
            m_, lo, hi = diffy(a, b)
            L.append(f"- {lab}: {m_:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        L.append("")
    txt = "\n".join(L)
    (OUT / "S6_tables.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    {"gen_train": stage_gen_train, "train": stage_train, "eval": stage_eval, "analyze": analyze}[sys.argv[1]]()
