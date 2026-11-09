"""Thin Ollama client with an on-disk response cache (reruns are free and reproducible)."""
import hashlib
import json
import os
import time
from pathlib import Path

import requests

HOST = os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")
CACHE_DIR = Path(__file__).resolve().parent.parent / "results" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def chat(model, messages, temperature=0.0, seed=0, max_tokens=400, think=False,
         json_mode=True, num_ctx=8192, timeout=600):
    key_src = json.dumps([model, messages, temperature, seed, max_tokens, think, json_mode, num_ctx],
                         sort_keys=True, ensure_ascii=False)
    key = hashlib.sha256(key_src.encode("utf-8")).hexdigest()
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))["content"]

    if model.startswith("oai::"):       # "oai::http://127.0.0.1:3120::model-id"  (Infernix / any OpenAI-style server)
        _, base, mid = model.split("::", 2)
        payload = {"model": mid, "messages": messages, "temperature": temperature, "seed": seed,
                   "max_tokens": max_tokens, "stream": False,
                   "chat_template_kwargs": {"enable_thinking": bool(think)}}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        r = requests.post(f"{base}/v1/chat/completions", json=payload, timeout=timeout)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"] or ""
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"content": content}, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
        return content

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": think,
        "options": {"temperature": temperature, "seed": seed,
                    "num_predict": max_tokens, "num_ctx": num_ctx},
    }
    if json_mode:
        payload["format"] = "json"

    for attempt in range(3):
        r = requests.post(f"{HOST}/api/chat", json=payload, timeout=timeout)
        if r.status_code == 400 and "think" in r.text.lower():
            payload.pop("think", None)  # model has no thinking switch
            continue
        if r.status_code == 200:
            break
        time.sleep(2)
    r.raise_for_status()
    content = r.json()["message"]["content"]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"content": content}, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return content
