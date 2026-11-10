"""S42 E4 (docs/S42_CLAIM_AUDIT_AND_PLAN.md): sibling questions and their controls through the Wikipedia-only pipeline of S41, as question
answering: local-wiki evidence, Qwen3-4B plain + cautious readers, deductive gate release2, Phi-4 second reader on the same passage.
Rule (fixed 2026-11-10 before any output): Verified = both readers answer and agree, the gate finds the plain answer as a typed verbatim
span, Phi-4 agrees. Qualified (rule Q) = not Verified and the first answering reader's answer passes the gate. Else Unresolved.
Frame check (fixed at the same time, reported as a second system): a Verified item is moved to Qualified unless the quoted sentence holds
a word of the question's relation (FRAME below), or, for year questions, the year or a range that covers it.
  python -B results/runs/s42/e4_run.py readers   (needs the 4B server on 18000)
  python -B results/runs/s42/e4_run.py verify    (needs Ollama with Phi-4 on 11535)"""
import json, os, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
os.environ.setdefault("OLLAMA_HOST_URL", os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402  (keeps the unused 37 GB embedding table out of RAM)
from vkg import evidence_fast as E, pod, localwiki as LW, l3_checks2 as C   # noqa: E402
from vkg.lite import CAUTIOUS, PLAIN, parse   # noqa: E402
from vkg.llm import chat                      # noqa: E402
from vkg.s12_run import agree                 # noqa: E402
from vkg.s14_eval import ans                  # noqa: E402
D = ROOT / "results/runs/s42"
MODE = sys.argv[1]
items = [json.loads(l) for l in open(D / "e4_items.jsonl", encoding="utf-8")]
print("items", len(items), MODE, flush=True)
t0 = time.time()
EVF, RDF, PF = D / "e4_evidence.json", D / "e4_readers.json", D / "e4_readers_part.json"
DEATH = ["died", "death", "dies", "killed", "executed", "assassinated", "murdered"]
FRAME = {"death_place": DEATH, "death_year": DEATH, "birth_place": ["born", "birth", "native"], "birth_year": ["born", "birth"],
         "producer": ["produc"], "composer": ["music", "compos", "score", "soundtrack"], "director": ["direct"],
         "publisher": ["publish"], "translator": ["translat"], "author": ["writ", "wrote", "author", "novel", "book", "play", "poem", "story", " by "],
         "largest_city": ["largest", "most populous", "biggest"], "capital": ["capital"]}
YR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
RNG = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\s*(?:–|-|—|to|until)\s*(1[0-9]{3}|20[0-9]{2}|present|incumbent)?", re.I)


def gpu_used():
    import subprocess
    try:
        return int(subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits".split(), capture_output=True, text=True).stdout.strip()) / 1024
    except Exception:
        return 0.0


def frame_ok(x, text, i, j):
    sent = C.sentence_at(text, i, j); low = sent.lower()
    if x["type"] in ("year_shift", "office"):
        y = int(YR.findall(x["question"])[-1])
        if str(y) in sent:
            return True
        return any(int(a) <= y <= (int(b) if b and b.isdigit() else 9999) for a, b in RNG.findall(sent))
    if any(w in low for w in FRAME[x["type"]]):
        return True
    if x["type"] == "death_year":      # life span "(1918 – 2012)": the span is the end of a range
        return bool(re.search(r"[–—-]\s*[\w ,.]{0,20}$", text[max(0, i - 25):i]))
    if x["type"] == "birth_year":      # the span is the start of a range
        return bool(re.match(r"^[\w ,.]{0,20}\s*[–—-]", text[j:j + 25]))
    return False


def gen_resilient(batch, tries=40):
    import requests
    for t in range(tries):
        try:
            if gpu_used() > 27:
                pod.unload_gen(); print("gpu busy elsewhere: 4B unloaded, waiting", time.strftime("%H:%M"), flush=True)
                while gpu_used() > 10:
                    time.sleep(120)
            return pod.gen(batch, 40)
        except (requests.exceptions.RequestException, RuntimeError) as e:
            print("reader chunk retry", t, repr(e)[:160], flush=True); time.sleep(45)
    raise SystemExit("reader step gave up")


if MODE == "readers":
    if EVF.exists():
        ev = json.load(open(EVF, encoding="utf-8"))
    else:
        ev = E.wiki_build([{"id": x["id"], "question": x["question"]} for x in items], workers=4)
        json.dump(ev, open(EVF, "w", encoding="utf-8"), ensure_ascii=False)
    print("evidence", f"{time.time()-t0:.0f}s", flush=True)
    prompts, keys = [], []
    for x in items:
        p = ev[x["id"]]["passage"]
        if p:
            for k, t in (("plain", PLAIN), ("cautious", CAUTIOUS)):
                prompts.append(t.format(p=p, q=x["question"])); keys.append((x["id"], k))
    part = json.load(open(PF, encoding="utf-8")) if PF.exists() else []
    while len(part) < len(prompts):
        part += [o[0] for o in gen_resilient(prompts[len(part):len(part) + 120])]
        json.dump(part, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
        print("reader prompts", len(part), "of", len(prompts), f"{time.time()-t0:.0f}s", flush=True)
    R = {}
    for (i, k), o in zip(keys, part):
        R.setdefault(i, {})[k] = parse(o)
    json.dump(R, open(RDF, "w", encoding="utf-8"), ensure_ascii=False)
    print("readers", f"{time.time()-t0:.0f}s", flush=True)
    raise SystemExit(0)

ev = json.load(open(EVF, encoding="utf-8")); R = json.load(open(RDF, encoding="utf-8"))
n = {"Verified": 0, "Qualified": 0, "Unresolved": 0}
with open(D / "e4_out.jsonl", "w", encoding="utf-8") as f:
    for x in items:
        rd = R.get(x["id"], {}); pl, ca = rd.get("plain"), rd.get("cautious")
        support = bool(ans(pl) and ans(ca) and agree(str(pl), str(ca)))
        cand = pl if ans(pl) else (ca if ans(ca) else None)
        rel, rec = (C.release2(x["question"], str(cand).strip().strip("'\""), ev[x["id"]]["titles"], LW.page_text) if cand else (None, {"reason": "no answer"}))
        phi = None
        if rel and support:
            for t in range(40):
                try:
                    if gpu_used() > 26:
                        import requests
                        requests.post(os.environ["OLLAMA_HOST_URL"] + "/api/generate", json={"model": "phi4", "keep_alive": 0}, timeout=120)
                        print("gpu busy elsewhere: Phi-4 unloaded, waiting", time.strftime("%H:%M"), flush=True)
                        while gpu_used() > 10:
                            time.sleep(120)
                    phi = parse(chat("phi4", [{"role": "user", "content": CAUTIOUS.format(p=ev[x["id"]]["passage"], q=x["question"])}], temperature=0.0, seed=0,
                                     max_tokens=40, think=False, json_mode=False, num_ctx=24576, timeout=1800))
                    break
                except Exception as e:
                    print("phi4 retry", t, repr(e)[:160], flush=True); time.sleep(45)
            else:
                raise SystemExit("phi4 step gave up")
        verified = bool(rel and support and ans(phi) and agree(str(rel), str(phi)))
        state = "Verified" if verified else ("Qualified" if rel else "Unresolved")
        quote, fr = "", None
        if rel:
            text = LW.page_text(rec["doc"]); i, j = rec["start"], rec["end"]
            assert text[i:j] == rec["span"], "quote check failed"
            quote = C.sentence_at(text, i, j).strip()[:300]; fr = frame_ok(x, text, i, j)
        n[state] += 1
        f.write(json.dumps({**x, "readers": rd, "support": support, "answer": str(rel) if rel else None, "gate_reason": rec.get("reason"), "phi4": phi,
                            "state": state, "frame_ok": fr, "page": rec.get("doc"), "quote": quote}, ensure_ascii=False) + "\n")
print("states", n, f"{time.time()-t0:.0f}s", flush=True)
