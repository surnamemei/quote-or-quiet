"""S42 E7 (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 8): reader checks on candidate quotes. 4B server on 18000.
Four prompts per candidate (question, question on the swapped quote, inverse question, contrasting question; e7_lib.prompts).
  python -B results/runs/s42/e7_run.py dev    items on the E6 sheet: the first span, plus up to 3 further spans that pass F and S
  python -B results/runs/s42/e7_run.py test   items outside the E6 sheet, same candidates (run only after the rule is fixed)"""
import json, os, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
os.environ.setdefault("OLLAMA_HOST_URL", os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402  (keeps the unused 37 GB embedding table out of RAM)
from vkg import pod                # noqa: E402
from vkg.lite import parse         # noqa: E402
import e7_lib as L                 # noqa: E402
D = ROOT / "results/runs/s42"; MODE = sys.argv[1]; assert MODE in ("dev", "test")
X = {x["id"]: x for x in (json.loads(l) for l in open(D / "e6_items.jsonl", encoding="utf-8"))}
CD = {c["id"]: c["cands"] for c in (json.loads(l) for l in open(D / "e7_cands.jsonl", encoding="utf-8"))}
sheet = {k["id"] for ks in json.load(open(D / "E6_key.json", encoding="utf-8")).values() for k in ks}   # decoys are built from sheet items too
ids = [i for i in X if (i in sheet) == (MODE == "dev")]
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
    raise SystemExit("e7 reader step gave up")


keys = []; prompts = []
for i in ids:
    x = X[i]; pick = [0]
    for k, c in enumerate(CD[i]):
        if k and len(pick) < 4 and c["F"] and L.subject_link(x["question"], c["doc"], c["quote"]):
            pick.append(k)
    for k in pick:
        keys.append(f"{i}|{k}"); prompts += L.prompts(x, CD[i][k])
print(MODE, "items", len(ids), "candidates", len(keys), "prompts", len(prompts), flush=True)
PF = D / f"e7_{MODE}_part.json"
part = json.load(open(PF, encoding="utf-8")) if PF.exists() else []
while len(part) < len(prompts):
    part += [o[0] for o in gen_resilient(prompts[len(part):len(part) + 200])]
    json.dump(part, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    print("prompts", len(part), "of", len(prompts), f"{time.time()-t0:.0f}s", flush=True)
json.dump({key: [parse(o) for o in part[4 * n:4 * n + 4]] for n, key in enumerate(keys)}, open(D / f"e7_{MODE}_out.json", "w", encoding="utf-8"), ensure_ascii=False)
print("e7", MODE, "done", f"{time.time()-t0:.0f}s", flush=True)
