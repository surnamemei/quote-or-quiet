"""S43 part C reader step: YES/NO judge on every candidate sentence, with the value and with the swapped value. 4B on port 18000.
python -B results/runs/s43/e11_run.py"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import pod  # noqa: E402
D = ROOT / "results/runs/s49"
slots = [json.loads(l) for l in open(D / "c_cands.jsonl", encoding="utf-8")]
keys, prompts = [], []
for s in slots:
    n = 0
    for k, c in enumerate(s["cands"]):
        if c["sent"] and c["N"] and c["swap"] and n < 6:       # the rule needs a sentence quote that holds the question's numbers; at most six tried per item
            n += 1; keys.append(f"{s['id']}|{k}"); prompts += [c["j"], c["j_swap"]]
print("candidates", len(keys), "prompts", len(prompts), flush=True)
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
            return pod.gen(batch, 4)
        except (requests.exceptions.RequestException, RuntimeError) as e:
            print("chunk retry", t, repr(e)[:160], flush=True); time.sleep(45)
    raise SystemExit("c judge step gave up")


PF = D / "c_part.json"
part = json.load(open(PF, encoding="utf-8")) if PF.exists() else []
while len(part) < len(prompts):
    part += [o[0] for o in gen_resilient(prompts[len(part):len(part) + 200])]
    json.dump(part, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    print("prompts", len(part), "of", len(prompts), f"{time.time()-t0:.0f}s", flush=True)
json.dump({key: [part[2 * n], part[2 * n + 1]] for n, key in enumerate(keys)}, open(D / "c_out.json", "w", encoding="utf-8"), ensure_ascii=False)
print("c done", f"{time.time()-t0:.0f}s", flush=True)
