"""S43 part A reader step: for every candidate, the quote-only reader (G) and the swapped-span reader (W), Qwen3-4B on port 18000.
python -B results/runs/s43/s43_run.py"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import pod            # noqa: E402
from vkg.lite import parse     # noqa: E402
D = ROOT / "results/runs/s43"
slots = [json.loads(l) for l in open(D / "s43_cands.jsonl", encoding="utf-8")]
keys, prompts = [], []
for s in slots:
    for k, c in enumerate(s["cands"]):
        keys.append(f"{s['id']}|{k}"); prompts += [c["g_prompt"], c["g_prompt_swap"] or c["g_prompt"]]
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
            return pod.gen(batch, 24)
        except (requests.exceptions.RequestException, RuntimeError) as e:
            print("chunk retry", t, repr(e)[:160], flush=True); time.sleep(45)
    raise SystemExit("s43 reader step gave up")


PF = D / "s43_part.json"
part = json.load(open(PF, encoding="utf-8")) if PF.exists() else []
while len(part) < len(prompts):
    part += [o[0] for o in gen_resilient(prompts[len(part):len(part) + 200])]
    json.dump(part, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    print("prompts", len(part), "of", len(prompts), f"{time.time()-t0:.0f}s", flush=True)
json.dump({key: [parse(part[2 * n]), parse(part[2 * n + 1])] for n, key in enumerate(keys)}, open(D / "s43_out.json", "w", encoding="utf-8"), ensure_ascii=False)
print("s43 done", f"{time.time()-t0:.0f}s", flush=True)
