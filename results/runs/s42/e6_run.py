"""S42 E6: the quote-only reader G (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 7). The model sees the page title, the quote and the question,
nothing else. Two prompts per item: the quote as it is, and the quote with the span replaced by another item's span.
  python -B results/runs/s42/e6_run.py g4     all items, 4B server on 18000
  python -B results/runs/s42/e6_run.py phi    reviewed rows only, Phi-4 through Ollama on 11535 (secondary)"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
os.environ.setdefault("OLLAMA_HOST_URL", os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402  (keeps the unused 37 GB embedding table out of RAM)
from vkg import pod                # noqa: E402
from vkg.lite import parse         # noqa: E402
from vkg.llm import chat           # noqa: E402
D = ROOT / "results/runs/s42"; MODE = sys.argv[1]
items = [json.loads(l) for l in open(D / "e6_items.jsonl", encoding="utf-8")]
t0 = time.time()


def gpu_used():
    import subprocess
    try:
        return int(subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits".split(), capture_output=True, text=True).stdout.strip()) / 1024
    except Exception:
        return 0.0


def gen_resilient(batch, tries=40):
    import requests
    for t in range(tries):
        try:
            if gpu_used() > 27:
                pod.unload_gen(); print("gpu busy elsewhere: 4B unloaded, waiting", time.strftime("%H:%M"), flush=True)
                while gpu_used() > 10:
                    time.sleep(120)
            return pod.gen(batch, 24)
        except (requests.exceptions.RequestException, RuntimeError) as e:
            print("chunk retry", t, repr(e)[:160], flush=True); time.sleep(45)
    raise SystemExit("g4 step gave up")


if MODE == "g4":
    prompts = [p for x in items for p in (x["g_prompt"], x["g_prompt_swap"])]
    PF = D / "e6_g4_part.json"
    part = json.load(open(PF, encoding="utf-8")) if PF.exists() else []
    while len(part) < len(prompts):
        part += [o[0] for o in gen_resilient(prompts[len(part):len(part) + 200])]
        json.dump(part, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
        print("prompts", len(part), "of", len(prompts), f"{time.time()-t0:.0f}s", flush=True)
    json.dump({x["id"]: [parse(part[2 * k]), parse(part[2 * k + 1])] for k, x in enumerate(items)}, open(D / "e6_g4.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("g4 done", f"{time.time()-t0:.0f}s", flush=True)
else:
    ids = {k["id"] for ks in json.load(open(D / "E6_key.json", encoding="utf-8")).values() for k in ks if not k["kind"].startswith("decoy")}
    PF = D / "e6_gphi.json"
    out = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    for x in items:
        if x["id"] not in ids or x["id"] in out:
            continue
        o = []
        for p in (x["g_prompt"], x["g_prompt_swap"]):
            for t in range(40):
                try:
                    if gpu_used() > 26:
                        import requests
                        requests.post(os.environ["OLLAMA_HOST_URL"] + "/api/generate", json={"model": "phi4", "keep_alive": 0}, timeout=120)
                        print("gpu busy elsewhere: Phi-4 unloaded, waiting", time.strftime("%H:%M"), flush=True)
                        while gpu_used() > 10:
                            time.sleep(120)
                    o.append(parse(chat("phi4", [{"role": "user", "content": p}], temperature=0.0, seed=0, max_tokens=24, think=False, json_mode=False,
                                        num_ctx=4096, timeout=600)))
                    break
                except Exception as e:
                    print("phi4 retry", t, repr(e)[:160], flush=True); time.sleep(45)
            else:
                raise SystemExit("phi4 step gave up")
        out[x["id"]] = o
        if len(out) % 50 == 0:
            json.dump(out, open(PF, "w", encoding="utf-8"), ensure_ascii=False); print("phi rows", len(out), "of", len(ids), f"{time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    print("phi done", len(out), f"{time.time()-t0:.0f}s", flush=True)
