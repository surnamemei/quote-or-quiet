"""S53: the three registered secondary analyses on the frozen releases of a templated set (docs/S40_PLAN.md lines of 2026-11-10 20:12 and 22:26).
Rules compared on the quote shown for each release: displayed (first accepted span), W1 (frame check F, subject link S, sentence, quote-only reader G), R (sentence, question numbers, 4B judge YES, swapped answer NO),
SJ (sentence, small judge of S51 with p >= 0.5). Modes:
  cands  : CPU. Accepted spans per release with their flags.         python -B results/runs/s53/q_pipeline.py cands  <releases.jsonl> <outdir>
  judge  : GPU, 4B server on 18000 for G and judge prompts.            python -B results/runs/s53/q_pipeline.py judge  <outdir>
  small  : GPU, the small judge (venv_gpu python).                     venv_gpu/Scripts/python.exe -B results/runs/s53/q_pipeline.py small <outdir>
  sheet  : CPU. Decisions, the blind quote-only sheet (300 releases), key. python -B results/runs/s53/q_pipeline.py sheet <outdir>
  unblind: CPU. Counts from the verdict files Q_verdict_part{p}_{A,B}.csv. python -B results/runs/s53/q_pipeline.py unblind <outdir>"""
import csv, json, os, random, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s42"))
MODE = sys.argv[1]
OUT = Path(sys.argv[3] if MODE == "cands" else sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
GP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\n'
      "Answer in a few words with only what this sentence states. If the sentence does not state the answer to this exact question, reply NONE.")
DEATH = ["died", "death", "dies", "killed", "executed", "assassinated", "murdered"]
FRAME = {"death_year": DEATH, "birth_place": ["born", "birth", "native"], "birth_year": ["born", "birth"], "director": ["direct"],
         "author": ["writ", "wrote", "author", "novel", "book", "play", "poem", "story", " by "], "capital": ["capital"]}
YR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
RNG = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\s*(?:–|-|—|to|until)\s*(1[0-9]{3}|20[0-9]{2}|present|incumbent)?", re.I)


def shape(a):
    a = str(a).strip()
    return "year" if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", a) else ("number" if re.fullmatch(r"[\d,.]+", a) else "phrase")


if MODE == "cands":
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    import no_retrieval2  # noqa: F401
    from vkg import l3_checks2 as C, l3_verify as V, localwiki as LW
    import e7_lib as L

    def bounds(text, i, j):
        a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
        ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
        return a, (min(ends) if ends else len(text))

    def window(text, i, j):
        a, b = bounds(text, i, j)
        while a < i and text[a].isspace():
            a += 1
        while b > j and text[b - 1].isspace():
            b -= 1
        if b - a > 300:
            a2 = max(a, min(i - 120, b - 300)); b2 = min(b, a2 + 300)
            if j > b2:
                b2 = j; a2 = max(a, b2 - 300)
            a, b = a2, b2
        return text[a:b], i - a, j - a

    def frame_ok(rel, question, text, i, j):
        sent = C.sentence_at(text, i, j); low = sent.lower()
        if rel == "office":
            y = int(YR.findall(question)[-1])
            return str(y) in sent or any(int(a) <= y <= (int(b) if b and b.isdigit() else 9999) for a, b in RNG.findall(sent))
        if any(w in low for w in FRAME[rel]):
            return True
        if rel == "death_year":
            return bool(re.search(r"[–—-]\s*[\w ,.]{0,20}$", text[max(0, i - 25):i]))
        if rel == "birth_year":
            return bool(re.match(r"^[\w ,.]{0,20}\s*[–—-]", text[j:j + 25]))
        return False

    rel = [json.loads(l) for l in open(sys.argv[2], encoding="utf-8")]
    outp = Path(sys.argv[2]).parent / (Path(sys.argv[2]).name.split("_")[0] + "_outputs.jsonl")      # wd_releases -> wd_outputs, w3_frozen_releases -> w3_outputs
    titles = {o["id"]: o["wiki_titles"] for o in map(json.loads, open(outp, encoding="utf-8"))}
    for r in rel:
        r["wiki_titles"] = r.get("wiki_titles") or titles[r["id"]]
        r["release_doc"] = r.get("release_doc") or r.get("doc")
    pool = {}
    for r in rel:
        pool.setdefault(shape(r["answer"]), []).append(str(r["answer"]))
    rng = random.Random(5301); n_first = 0
    with open(OUT / "q_cands.jsonl", "w", encoding="utf-8") as f:
        for r in rel:
            relname = next((k for k, pat in L.TEMPLATE.items() if re.fullmatch(pat, r["question"].strip())), None) or (r.get("relation") if r.get("relation") in FRAME else None)
            cands, tried = [], 0
            for d in r["wiki_titles"]:
                text = LW.page_text(d)
                if not text:
                    continue
                h = V.doc_hash(text)
                for i, j in V.locate(str(r["answer"]), text):
                    if len(cands) >= 30 or tried >= 600:
                        break
                    tried += 1
                    ok, _ = V.verify(r["question"], {"answer": str(r["answer"]), "doc": d, "doc_sha256": h, "start": i, "end": j}, LW.page_text)
                    if ok:
                        ok, _ = C.extra(r["question"], text, i, j)
                    if not ok:
                        continue
                    q, o1, o2 = window(text, i, j); qt = set(L.toks(q))
                    need = [w for w in L.toks(r["question"]) if re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD]
                    sp = [x for x in pool[shape(r["answer"])] if x.casefold() != str(r["answer"]).casefold() and x.casefold() not in q.casefold()]
                    sw = rng.choice(sp) if sp else None
                    sent = not q.lstrip().startswith(("#", "-", "*", "|", "=")) and len(q) >= 40
                    cands.append({"doc": d, "quote": q, "o1": o1, "o2": o2, "span": text[i:j], "sent": sent, "N": all(w in qt or re.sub(r"\D", "", w) in qt for w in need),
                                  "F": bool(relname and frame_ok(relname, r["question"], text, i, j)), "S": L.subject_link(r["question"], d, q), "swap": sw})
            n_first += bool(cands) and cands[0]["doc"] == r["release_doc"]
            f.write(json.dumps({"id": r["id"], "question": r["question"], "answer": str(r["answer"]), "relation": relname, "cands": cands}, ensure_ascii=False) + "\n")
    print("releases", len(rel), "| first accepted span in the release doc", n_first, "| with candidates", sum(1 for l in open(OUT / "q_cands.jsonl", encoding="utf-8") if json.loads(l)["cands"]))

elif MODE == "judge":
    os.environ.setdefault("VKG_EMB", "hf")
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    import no_retrieval2  # noqa: F401
    from vkg import pod
    from vkg.lite import parse
    from vkg.s12_run import agree
    from vkg.s14_eval import ans
    S = [json.loads(l) for l in open(OUT / "q_cands.jsonl", encoding="utf-8")]
    keys, prompts = [], []
    for s in S:
        nW = nR = 0
        for k, c in enumerate(s["cands"]):
            if c["sent"] and c["F"] and c["S"] and nW < 4:
                nW += 1; keys.append(("G", s["id"], k)); prompts.append(GP.format(t=c["doc"], s=c["quote"], q=s["question"]))
            if c["sent"] and c["N"] and c["swap"] and nR < 6:
                nR += 1; keys += [("J", s["id"], k), ("JS", s["id"], k)]
                prompts += [JP.format(t=c["doc"], s=c["quote"], q=s["question"], a=s["answer"]), JP.format(t=c["doc"], s=c["quote"], q=s["question"], a=c["swap"])]
    print("prompts", len(prompts), flush=True)
    outs = []
    for i in range(0, len(prompts), 16):
        for t in range(40):
            try:
                outs += [o[0] for o in pod.gen(prompts[i:i + 16], 24)]; break
            except Exception as e:
                print("retry", t, repr(e)[:100], flush=True); time.sleep(30)
        else:
            raise SystemExit("gave up")
    res = {f"{kind}|{i}|{k}": o for (kind, i, k), o in zip(keys, outs)}
    json.dump(res, open(OUT / "q_judge.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("judge done", flush=True)

elif MODE == "judge27":
    os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
    from vkg.llm import chat
    S = [json.loads(l) for l in open(OUT / "q_cands.jsonl", encoding="utf-8")]
    PF = OUT / "q_judge27.json"; res = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    for s in S:
        n = 0
        for k, c in enumerate(s["cands"]):
            if c["sent"] and c["N"] and c["swap"] and n < 6:
                n += 1
                for tag, ans_ in (("J", s["answer"]), ("JS", c["swap"])):
                    key = f"{tag}|{s['id']}|{k}"
                    if key in res:
                        continue
                    for t in range(20):
                        try:
                            res[key] = str(chat("qwen3.8-27b", [{"role": "user", "content": JP.format(t=c["doc"], s=c["quote"], q=s["question"], a=ans_)}], temperature=0.0, seed=0, max_tokens=4,
                                                think=False, json_mode=False, num_ctx=4096, timeout=600)); break
                        except Exception as e:
                            print("retry", t, repr(e)[:100], flush=True); time.sleep(30)
                    else:
                        raise SystemExit("gave up")
        if len(res) % 200 < 2:
            json.dump(res, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(res, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    print("judge27 done", len(res), flush=True)

elif MODE == "small":
    import numpy as np
    import torch
    from peft import PeftModel
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    S = [json.loads(l) for l in open(OUT / "q_cands.jsonl", encoding="utf-8")]
    items = [(s["id"], k, f"Question: {s['question']}\nProposed answer: {s['answer']}\nPage: {c['doc']}\nQuote: {c['quote']}") for s in S for k, c in enumerate(s["cands"]) if c["sent"]]
    path = str(ROOT / "models/qwen3-embedding-0.6b")
    tok = AutoTokenizer.from_pretrained(path); tok.padding_side = "right"
    base = AutoModelForSequenceClassification.from_pretrained(path, num_labels=2, torch_dtype=torch.bfloat16)
    if base.config.pad_token_id is None:
        base.config.pad_token_id = tok.pad_token_id
    model = PeftModel.from_pretrained(base, str(ROOT / "results/runs/s51/judge_lora")).cuda().eval()
    res = {}
    with torch.no_grad():
        for i in range(0, len(items), 32):
            enc = tok([x[2] for x in items[i:i + 32]], truncation=True, max_length=384, padding=True, return_tensors="pt")
            p = torch.softmax(model(**{k: v.cuda() for k, v in enc.items()}).logits.float(), -1)[:, 1].cpu().tolist()
            for (rid, k, _), v in zip(items[i:i + 32], p):
                res[f"{rid}|{k}"] = v
    json.dump(res, open(OUT / "q_small.json", "w"))
    print("small judge scored", len(res), flush=True)

elif MODE == "sheet":
    import numpy as np
    import no_retrieval2  # noqa: F401
    from vkg.s12_run import agree
    from vkg.s14_eval import ans
    S = [json.loads(l) for l in open(OUT / "q_cands.jsonl", encoding="utf-8")]
    J = json.load(open(OUT / "q_judge.json", encoding="utf-8")); SM = json.load(open(OUT / "q_small.json", encoding="utf-8"))
    from vkg.lite import parse
    J27 = json.load(open(OUT / "q_judge27.json", encoding="utf-8")) if (OUT / "q_judge27.json").exists() else {}
    yes = lambda o: str(o or "").strip().upper().startswith("YES")
    said = lambda o: (lambda v: v if ans(v) and not str(v).upper().startswith("NONE") else None)(str(parse(o) or "").strip().strip("'\"."))
    for s in S:
        s["w1"] = s["r"] = s["sj"] = s["r27"] = None
        for k, c in enumerate(s["cands"]):
            g = J.get(f"G|{s['id']}|{k}")
            if s["w1"] is None and g is not None and c["sent"] and c["F"] and c["S"] and said(g) and agree(s["answer"], said(g)):
                s["w1"] = k
            if s["r"] is None and f"J|{s['id']}|{k}" in J and yes(J[f"J|{s['id']}|{k}"]) and not yes(J[f"JS|{s['id']}|{k}"]):
                s["r"] = k
            if s["sj"] is None and c["sent"] and SM.get(f"{s['id']}|{k}", 0) >= 0.5:
                s["sj"] = k
            if J27 and s["r27"] is None and f"J|{s['id']}|{k}" in J27 and yes(J27[f"J|{s['id']}|{k}"]) and not yes(J27[f"JS|{s['id']}|{k}"]):
                s["r27"] = k
    S = [s for s in S if s["cands"]]
    for name in ("w1", "r", "sj", "r27"):
        print(name, "keeps", sum(s[name] is not None for s in S), "of", len(S), f"({100*sum(s[name] is not None for s in S)/len(S):.1f}%)")
    json.dump({s["id"]: {"w1": s["w1"], "r": s["r"], "sj": s["sj"], "r27": s["r27"]} for s in S}, open(OUT / "q_decisions.json", "w"))
    rng = random.Random(5302); sample = rng.sample(S, min(300, len(S))); rows = []
    for s in sample:
        seen = set()
        for kind, k in (("displayed", 0), ("w1", s["w1"]), ("r", s["r"]), ("sj", s["sj"]), ("r27", s["r27"])):
            if k is None or s["cands"][k]["quote"] in seen:
                continue
            seen.add(s["cands"][k]["quote"]); rows.append(dict(kind=kind, s=s, answer=s["answer"], c=s["cands"][k]))
    for _ in range(30):
        s = rng.choice(sample); o = rng.choice([x for x in S if x["answer"].casefold() != s["answer"].casefold()])
        rows.append(dict(kind="decoy", s=s, answer=o["answer"], c=s["cands"][0]))
    rng.shuffle(rows); P = 3; key = {}
    for p in range(P):
        part = rows[p::P]
        with open(OUT / f"Q_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["row", "question", "answer", "page_title", "quote"])
            for i, r in enumerate(part, 1):
                w.writerow([i, r["s"]["question"], r["answer"], r["c"]["doc"], r["c"]["quote"]])
        key[str(p + 1)] = [{"row": i, "id": r["s"]["id"], "kind": r["kind"], "quote": r["c"]["quote"]} for i, r in enumerate(part, 1)]
    json.dump(key, open(OUT / "Q_key.json", "w"))
    print("sheet rows", len(rows), [len(rows[p::P]) for p in range(P)])

elif MODE == "unblind":
    from scipy.stats import beta
    K = json.load(open(OUT / "Q_key.json")); Dn = json.load(open(OUT / "q_decisions.json"))
    S = {s["id"]: s for s in map(json.loads, open(OUT / "q_cands.jsonl", encoding="utf-8"))}
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
    verdict = {}; decoys = []
    for p, ks in K.items():
        vs = {}
        for rv in "AB":
            for r in csv.DictReader(open(OUT / f"Q_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
                vs.setdefault(int(r["row"]), []).append(r["quote_verdict"].strip().strip("'\"").casefold())
        for k in ks:
            if k["kind"] == "decoy":
                decoys.append(vs[k["row"]])
            else:
                verdict[(k["id"], k["quote"])] = (k["kind"], vs[k["row"]])        # a quote that two rules share has one row, whose verdict serves both
    dec = decoys
    ids = sorted({i for (i, q), (kd, v) in verdict.items() if kd == "displayed"})
    def vq(i, k):
        return verdict.get((i, S[i]["cands"][k]["quote"]), (None, None))[1]
    out = ["# S53: displayed quote against rules W1, R and SJ (small judge) on the frozen releases (quote-only blind review)", "",
           f"Decoys misleading for both reviewers: {sum(v == ['not', 'not'] for v in dec)}/{len(dec)}.", "", "| Quotes | n | misleading for both | 'states' for both |", "|---|---|---|---|"]
    def row(name, vs):
        n = len(vs); m = sum(v == ["not", "not"] for v in vs); s_ = sum(v == ["states", "states"] for v in vs)
        return f"| {name} | {n} | {m} ({100*m/max(1,n):.1f}%, upper {up(m,n):.1f}%) | {s_} ({100*s_/max(1,n):.1f}%) |"
    out.append(row("Displayed quote (first accepted span), the sampled releases", [vq(i, 0) for i in ids]))
    for name, key in (("W1", "w1"), ("R", "r"), ("SJ", "sj"), ("R27", "r27")):
        kept = [i for i in ids if Dn[i][key] is not None]
        out.append(row(f"Displayed quote, the {len(kept)} releases kept by {name}", [vq(i, 0) for i in kept]))
        out.append(row(f"{name} quote, kept releases", [vq(i, Dn[i][key]) for i in kept]))
    (OUT / "Q_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
