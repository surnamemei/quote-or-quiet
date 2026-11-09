"""S41 (docs/S41_LONGFORM_E2E_PLAN.md): verify every version 2 slot of the 50 design biographies with the short-form machinery,
value as the only candidate: local-wiki evidence, Qwen3-4B plain + cautious support, deductive gate release2, Phi-4 second reader.
Needs the 4B server (18000) and Ollama with Phi-4 (11535). Writes results/runs/s41/verified.jsonl (one row per slot). Idle priority.
VKG_EMB=hf VKG_OLLAMA_URL=http://127.0.0.1:11535 python -B results/runs/s41/lf_verify.py"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT))
os.environ.setdefault("VKG_EMB", "hf")
os.environ.setdefault("OLLAMA_HOST_URL", os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
from vkg import evidence_fast as E, pod, localwiki as LW, l3_checks2 as C   # noqa: E402
from vkg.lite import CAUTIOUS, PLAIN, parse   # noqa: E402
from vkg.llm import chat                      # noqa: E402
from vkg.s12_run import agree                 # noqa: E402
from vkg.s14_eval import ans                  # noqa: E402
D = ROOT / "results/runs/s41"; D.mkdir(parents=True, exist_ok=True)
slots = []
for b in map(json.loads, open(ROOT / "results/runs/s37/slots2.jsonl", encoding="utf-8")):
    for n, c in enumerate(b["claims"]):
        slots.append({"id": f"{b['name']}#{n}", "person": b["name"], **c})
print("slots", len(slots), flush=True)
t0 = time.time()
ev = E.wiki_build([{"id": s["id"], "question": s["question"]} for s in slots], workers=4)
print("evidence", f"{time.time()-t0:.0f}s", flush=True)
prompts, keys = [], []
for s in slots:
    p = ev[s["id"]]["passage"]
    if p:
        for k, t in (("plain", PLAIN), ("cautious", CAUTIOUS)):
            prompts.append(t.format(p=p, q=s["question"])); keys.append((s["id"], k))
outs = pod.gen(prompts, 40)
R = {}
for (i, k), o in zip(keys, outs):
    R.setdefault(i, {})[k] = parse(o[0])
print("readers", f"{time.time()-t0:.0f}s", flush=True)
n_keep = 0
with open(D / "verified.jsonl", "w", encoding="utf-8") as f:
    for s in slots:
        v = str(s["value"]).strip().strip("'\"")
        rd = R.get(s["id"], {})
        gave = [a for a in rd.values() if ans(a)]
        support = bool(gave) and all(agree(v, str(a)) for a in gave)
        rel, rec = (C.release2(s["question"], v, ev[s["id"]]["titles"], LW.page_text) if support else (None, {"reason": "no support"}))
        phi = None
        if rel:
            phi = parse(chat("phi4", [{"role": "user", "content": CAUTIOUS.format(p=ev[s["id"]]["passage"], q=s["question"])}], temperature=0.0, seed=0,
                             max_tokens=40, think=False, json_mode=False, num_ctx=24576))
        keep = bool(rel) and ans(phi) and agree(v, str(phi))
        quote = ""
        if keep:
            n_keep += 1
            text = LW.page_text(rec["doc"]); i, j = rec["start"], rec["end"]
            quote = text[max(0, text.rfind("\n", 0, i) + 1):(text.find("\n", j) if text.find("\n", j) != -1 else len(text))].strip()[:300]
        f.write(json.dumps({**s, "value_clean": v, "readers": rd, "support": support, "gate": bool(rel), "gate_reason": rec.get("reason"),
                            "phi4": phi, "keep": bool(keep), "page": rec.get("doc"), "quote": quote}, ensure_ascii=False) + "\n")
print("kept", n_keep, "of", len(slots), f"{time.time()-t0:.0f}s", flush=True)
