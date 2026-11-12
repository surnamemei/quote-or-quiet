"""Track C, C1/C2: run the evidence-sensitivity suite on a model and score it mechanically.
  run BACKEND SYSTEM : BACKEND = infernix:PORT (OpenAI chat API of infernix-serve), ollama:MODEL (Ollama on 11540); SYSTEM = direct | material_only.
                       One request at a time, temperature 0, max 160 output tokens; resumable; records seconds per request.
  score              : per model and system, per version (A to E), context (short/long) and language: correct share and error kinds.
python -B results/runs/s70/esuite_run.py run infernix:11951 material_only ; python -B results/runs/s70/esuite_run.py score
Scoring (mechanical, by construction): text folded to lower case; 'contains v' = the value occurs in the answer; 'abstains' = the answer says the material does not state it
(English and Chinese phrases below). answer items: correct = contains the expected value, none of the forbidden values, and no abstention; errors: wrong value from the
material (a forbidden value), abstained, other (no expected value: an unsupported addition). missing items: correct = abstains and names no candidate value; error: guessed.
conflict items: correct = names both values; errors: picked one, abstained, other."""
import json, os, re, sys, time, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; D = ROOT / "results/runs/s70"
sys.stdout.reconfigure(encoding="utf-8")
S = [json.loads(l) for l in open(D / "esuite.jsonl", encoding="utf-8")]
SYS = {"direct": "Material:\n{m}\n\nQuestion: {q}",
       "material_only": "Answer the question using only the material below. If the material does not state the answer, say that it does not. If the material gives different answers, "
                        "say that the records conflict and give each. Answer briefly.\n\nMaterial:\n{m}\n\nQuestion: {q}"}
ABST = re.compile(r"does not (state|say|mention|specify|provide|contain|include)|doesn't (state|say|mention|specify)|not (stated|mentioned|specified|provided|given|included)|"
                  r"no (information|mention|indication)|cannot (be )?determin|can't determine|unable to determine|not possible to determine|is unknown|unclear from|"
                  r"未(提及|说明|提到|给出|指明)|没有(提及|说明|提到|给出|相关|信息)|无法(确定|判断|得知)|不(清楚|确定)|材料中(并)?没有", re.I)
fold = lambda t: "".join(c for c in unicodedata.normalize("NFKD", str(t or "")) if not unicodedata.combining(c)).casefold()


def call(backend, prompt):
    import requests
    kind, arg = backend.split(":", 1)
    for t in range(6):
        try:
            if kind == "infernix":
                r = requests.post(f"http://127.0.0.1:{arg}/v1/chat/completions", json={"model": "default", "messages": [{"role": "user", "content": prompt}],
                                  "temperature": 0, "max_tokens": 160}, timeout=900).json()
                return r["choices"][0]["message"]["content"]
            r = requests.post("http://127.0.0.1:11540/api/chat", json={"model": arg, "messages": [{"role": "user", "content": prompt}], "stream": False, "think": False,
                              "options": {"temperature": 0, "seed": 0, "num_predict": 160, "num_ctx": 16384}}, timeout=900).json()
            return r["message"]["content"]
        except Exception as ex:
            print("retry", t, repr(ex)[:100], flush=True); time.sleep(15)
    return None


def judge(x, a):
    if a is None:
        return "no reply"
    t = fold(a); has = lambda v: fold(v) in t; ab = bool(ABST.search(a))
    if x["kind"] == "answer":
        if any(has(v) for v in x["forbid"]):
            return "wrong value from material"
        if has(x["expect"][0]) and not ab:
            return "correct"
        return "abstained" if ab else "other (unsupported)"
    if x["kind"] == "missing":
        cands = [v for v in x["forbid"]]
        return "guessed" if (any(has(v) for v in cands) or not ab) else "correct"
    if all(has(v) for v in x["expect"]):
        return "correct"
    return "picked one" if any(has(v) for v in x["expect"]) else ("abstained" if ab else "other")


if sys.argv[1] == "run":
    backend, system = sys.argv[2], sys.argv[3]
    F = D / f"out_{re.sub(r'[^a-z0-9]+', '_', backend.lower())}_{system}.jsonl"
    done = {json.loads(l)["id"] for l in open(F, encoding="utf-8")} if F.exists() else set()
    for n, x in enumerate(S):
        if x["id"] in done:
            continue
        t0 = time.time(); a = call(backend, SYS[system].format(m=x["material"], q=x["question"]))
        with open(F, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": x["id"], "answer": a, "sec": round(time.time() - t0, 2)}, ensure_ascii=False) + "\n")
        if n % 200 == 0:
            print(backend, system, n, flush=True)
    print("run done", backend, system)
else:
    from collections import Counter, defaultdict
    X = {x["id"]: x for x in S}; out = ["# Track C, C1: evidence-sensitivity suite (development data; mechanical scoring)", ""]
    for F in sorted(D.glob("out_*.jsonl")):
        R = [json.loads(l) for l in open(F, encoding="utf-8")]; tab = defaultdict(Counter); secs = [r["sec"] for r in R]
        for r in R:
            x = X[r["id"]]; v = judge(x, r["answer"])
            tab[(x["version"], x["context"], x["lang"])][v] += 1; tab[("all", "", "")][v] += 1
        out += [f"## {F.stem[4:]} ({len(R)} of {len(S)} prompts; median {sorted(secs)[len(secs)//2]:.1f} s per request)", "", "| version | context | language | n | correct | errors |", "|---|---|---|---|---|---|"]
        for k in sorted(tab, key=lambda k: (k[0] == "all", k)):
            c = tab[k]; n = sum(c.values())
            out.append(f"| {k[0]} | {k[1]} | {k[2]} | {n} | {c['correct']} ({100*c['correct']/max(1,n):.0f}%) | {', '.join(f'{e} {m}' for e, m in c.most_common() if e != 'correct')} |")
        out.append("")
    (D / "ESUITE_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
