"""Track C, C1/C2: run the evidence-sensitivity suite on a model and score it mechanically.
  run BACKEND SYSTEM : (INFX_NOTHINK=1 turns thinking off on infernix, as think=False on Ollama.) BACKEND = infernix:PORT (OpenAI chat API of infernix-serve), ollama:MODEL (Ollama on 11540); SYSTEM = direct | material_only.
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
SUITE = os.environ.get("ESUITE", "esuite_v2")   # v2 since 2026-11-12 (v1 had base sentences that did not state the answer)
S = [json.loads(l) for l in open(D / f"{SUITE}.jsonl", encoding="utf-8")]
SYS = {"direct": "Material:\n{m}\n\nQuestion: {q}",
       "material_only": "Answer the question using only the material below. If the material does not state the answer, say that it does not. If the material gives different answers, "
                        "say that the records conflict and give each. Answer briefly.\n\nMaterial:\n{m}\n\nQuestion: {q}"}
ABST = re.compile(r"does not (state|say|mention|specify|provide|contain|include)|doesn't (state|say|mention|specify)|not (stated|mentioned|specified|provided|given|included)|"
                  r"no (information|mention|indication)|cannot (be )?determin|can't determine|unable to determine|not possible to determine|is unknown|unclear from|"
                  r"未(提及|说明|提到|给出|指明)|没有(提及|说明|提到|给出|相关|信息)|无法(确定|判断|得知)|不(清楚|确定)|材料中(并)?没有", re.I)
fold = lambda t: "".join(c for c in unicodedata.normalize("NFKD", str(t or "")) if not unicodedata.combining(c)).casefold()


_MID = None


def call(backend, prompt):
    import requests
    kind, arg = backend.split(":", 1)
    for t in range(6):
        try:
            if kind == "infernix":
                global _MID
                if not _MID:
                    _MID = requests.get(f"http://127.0.0.1:{arg}/v1/models", timeout=60).json()["data"][0]["id"]      # the served model's name
                r = requests.post(f"http://127.0.0.1:{arg}/v1/chat/completions", json={"model": _MID, "messages": [{"role": "user", "content": prompt}],
                                  "temperature": 0, "max_tokens": 160, **({"chat_template_kwargs": {"enable_thinking": False}} if os.environ.get("INFX_NOTHINK") == "1" else {})}, timeout=900).json()
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
    F = D / f"out_{SUITE}_{re.sub(r'[^a-z0-9]+', '_', backend.lower())}_{system}.jsonl"
    if F.exists():                                                   # rows without an answer (failed calls) are dropped and asked again
        keep = [l for l in open(F, encoding="utf-8") if json.loads(l)["answer"] is not None]
        open(F, "w", encoding="utf-8").writelines(keep)
    done = {json.loads(l)["id"] for l in open(F, encoding="utf-8")} if F.exists() else set()
    ctx = set(os.environ.get("CONTEXTS", "short,long").split(","))          # e.g. CONTEXTS=short; LONG_BASES=N keeps long prompts for the first N base items only
    lb = int(os.environ.get("LONG_BASES", "0")); bases = list(dict.fromkeys(x["base"] for x in S))[:lb] if lb else None
    for n, x in enumerate(S):
        if x["id"] in done or x["context"] not in ctx or (x["context"] == "long" and bases is not None and x["base"] not in bases):
            continue
        t0 = time.time(); a = call(backend, SYS[system].format(m=x["material"], q=x["question"]))
        if a is None:                                                  # server gone (e.g. unloaded): stop instead of writing empty rows
            print("no reply; stopping", backend, system, flush=True); sys.exit(2)
        with open(F, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": x["id"], "answer": a, "sec": round(time.time() - t0, 2)}, ensure_ascii=False) + "\n")
        if n % 200 == 0:
            print(backend, system, n, flush=True)
    print("run done", backend, system)
else:
    from collections import Counter, defaultdict
    X = {x["id"]: x for x in S}; out = ["# Track C, C1: evidence-sensitivity suite (development data; mechanical scoring)", ""]
    for F in sorted(D.glob(f"out_{SUITE}_*.jsonl")):
        R = [json.loads(l) for l in open(F, encoding="utf-8")]; tab = defaultdict(Counter); secs = [r["sec"] for r in R]
        for r in R:
            x = X[r["id"]]; v = judge(x, r["answer"])
            tab[(x["version"], x["context"], x["lang"])][v] += 1; tab[("all", "", "")][v] += 1
        out += [f"## {F.stem[4:]} ({len(R)} of {len(S)} prompts; median {sorted(secs)[len(secs)//2]:.1f} s per request)", "", "| version | context | language | n | correct | errors |", "|---|---|---|---|---|---|"]
        for k in sorted(tab, key=lambda k: (k[0] == "all", k)):
            c = tab[k]; n = sum(c.values())
            out.append(f"| {k[0]} | {k[1]} | {k[2]} | {n} | {c['correct']} ({100*c['correct']/max(1,n):.0f}%) | {', '.join(f'{e} {m}' for e, m in c.most_common() if e != 'correct')} |")
        out.append("")
    (D / f"ESUITE_{SUITE}_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
