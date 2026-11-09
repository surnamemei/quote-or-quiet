"""Client side of the rented pod (tunnels: localhost:18000 -> pod 4B generation server, localhost:11435 -> pod Ollama).
  gen(contents, max_new)   batched greedy Qwen3-4B generation (vkg/podgen_server.py); returns [(text, prompt_tokens, gen_tokens)]
  unload_gen()             free the 4B's GPU memory (run before judging: the pod GPU is shared, one model of mine at a time)
  unload_judge()           unload the pod judge
  judge_many(triples, workers=8)   grader-5 judge labels for (question, gold, answer) in parallel via the pod Ollama
Results go through the same on-disk cache as vkg.llm (prompt-keyed; backend not recorded, see results/audit2/pod_judge_check.md)."""
import os
from concurrent.futures import ThreadPoolExecutor

import requests

GEN = "http://localhost:18000"
JUDGE_URL = os.environ.get("VKG_OLLAMA_URL", "http://localhost:11435")   # 2026-11-08: configurable; 11435 fell into a Windows excluded port range


def gen(contents, max_new=40, chunk=400):
    out = []
    for s in range(0, len(contents), chunk):
        r = requests.post(f"{GEN}/gen", json={"contents": contents[s:s + chunk], "max_new": max_new}, timeout=7200)
        j = r.json()
        if "error" in j:
            raise RuntimeError(f"pod gen failed: {j['error']}")
        out += [(o["text"], o["prompt_tokens"], o["gen_tokens"]) for o in j["outs"]]
    return out


def unload_gen():
    requests.post(f"{GEN}/unload", json={}, timeout=120)


def unload_judge():
    from .grade_judge import JUDGE
    requests.post(f"{JUDGE_URL}/api/generate", json={"model": JUDGE, "keep_alive": 0}, timeout=60)


def judge_many(triples, workers=4):
    os.environ["OLLAMA_HOST_URL"] = JUDGE_URL
    from . import llm
    llm.HOST = JUDGE_URL
    from .grade_judge import judge
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda t: judge(*t), triples))


def wait_free(gib, port=None, every=120, log=print):
    """Block until the shared pod GPU has at least `gib` GiB free (checked with nvidia-smi over SSH every `every` s)."""
    import subprocess
    import time
    port = port or os.environ.get("VKG_POD_PORT", "10282")
    host = os.environ.get("VKG_POD_HOST", "216.243.220.171")
    said = False
    while True:
        q = "nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits"
        if host == "local":       # S19 on the user's own GPU: same gate, checked locally (waits while the user's jobs use it)
            out = subprocess.run(q.split(), capture_output=True, text=True).stdout
        else:
            out = subprocess.run(["ssh", "-i", os.path.expanduser("~/.ssh/runpod_ed25519"), "-p", str(port), f"root@{host}", q],
                                 capture_output=True, text=True).stdout
        free = int(out.strip() or 0) / 1024
        if free >= gib:
            return free
        if not said:
            log(f"waiting for {gib} GiB free on the pod GPU (now {free:.1f})")
            said = True
        time.sleep(every)
