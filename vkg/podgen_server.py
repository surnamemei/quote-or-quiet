"""Batched greedy generation server for Qwen3-4B-Instruct-2507 (runs on the rented pod; self-contained, stdlib HTTP).
POST /gen    {"contents": [str], "max_new": int}  -> {"outs": [{"text", "prompt_tokens", "gen_tokens"}]}
             Chat template applied to each content (one user turn), left padding, length-sorted batches, do_sample=False.
POST /embed  {"texts": [str]} -> {"vecs": [[float]]}  Qwen3-Embedding-0.6B (official HF weights, float32), last-token pooling,
             L2-normalised, as in the model card; texts are used verbatim (callers add the query instruction themselves).
POST /unload -> frees the GPU (model reloads on the next /gen).   GET /health -> {"loaded": bool}
Listens on 127.0.0.1:18000 only (reached through an SSH tunnel).
Run on pod: venv/bin/python podgen_server.py /workspace/vkg/models/qwen3-4b-instruct-2507
Batch size adapts to prompt length so that batch_size * max_len stays under TOKENS_PER_BATCH (bounded GPU memory)."""
import gc
import os
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import torch
from transformers import AutoModel, AutoModelForCausalLM, AutoTokenizer

MODEL = sys.argv[1]
EMB_MODEL = sys.argv[2] if len(sys.argv) > 2 else None
TOKENS_PER_BATCH = 24_000
EMB_TOKENS_PER_BATCH = 32_768
# The pod GPU is shared (mini-kimi training): hard cap on this process; an OOM here is reported to the client, never spread.
torch.cuda.set_per_process_memory_fraction(float(os.environ.get("VKG_MEM_FRAC", "0.26")))   # shared pod: 0.26; dedicated GPU: set higher
LOCK = threading.Lock()
S = {}


def load():
    if "m" not in S:
        S["tok"] = AutoTokenizer.from_pretrained(MODEL)
        S["tok"].padding_side = "left"
        S["m"] = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).cuda().eval()
    return S["tok"], S["m"]


def load_emb():
    if "em" not in S:
        S["etok"] = AutoTokenizer.from_pretrained(EMB_MODEL, padding_side="left")
        S["em"] = AutoModel.from_pretrained(EMB_MODEL, dtype=torch.bfloat16, attn_implementation="sdpa").cuda().eval()
    return S["etok"], S["em"]


@torch.no_grad()
def embed(texts):
    tok, m = load_emb()
    lens = [len(x) for x in tok(texts, truncation=True, max_length=1024)["input_ids"]]
    order = sorted(range(len(texts)), key=lambda i: lens[i])
    out = [None] * len(texts)
    s = 0
    while s < len(order):
        bs = 1
        while s + bs < len(order) and (bs + 1) * lens[order[s + bs]] <= EMB_TOKENS_PER_BATCH and bs < 256:
            bs += 1
        idx = order[s:s + bs]
        enc = tok([texts[i] for i in idx], padding=True, truncation=True, max_length=1024, return_tensors="pt").to("cuda")
        h = m(**enc).last_hidden_state[:, -1].float()  # left padding: the last position is each text's last token
        h = torch.nn.functional.normalize(h, p=2, dim=1)
        for k, i in enumerate(idx):
            out[i] = h[k].tolist()
        s += bs
    return out


@torch.no_grad()
def gen(contents, max_new):
    tok, m = load()
    prompts = [tok.apply_chat_template([{"role": "user", "content": c}], add_generation_prompt=True, tokenize=False) for c in contents]
    ids = [tok(p)["input_ids"] for p in prompts]
    order = sorted(range(len(prompts)), key=lambda i: len(ids[i]))
    outs = [None] * len(prompts)
    s = 0
    while s < len(order):
        bs = 1
        while s + bs < len(order) and (bs + 1) * (len(ids[order[s + bs]]) + max_new) <= TOKENS_PER_BATCH and bs < 64:
            bs += 1
        idx = order[s:s + bs]
        enc = tok([prompts[i] for i in idx], return_tensors="pt", padding=True).to("cuda")
        g = m.generate(**enc, do_sample=False, max_new_tokens=max_new, pad_token_id=tok.pad_token_id)
        L = enc["input_ids"].shape[1]
        for k, i in enumerate(idx):
            new = g[k, L:]
            n = int((new != tok.pad_token_id).sum())
            outs[i] = {"text": tok.decode(new, skip_special_tokens=True), "prompt_tokens": len(ids[i]), "gen_tokens": n}
        s += bs
    return outs


class H(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send({"loaded": "m" in S})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
        with LOCK:
            try:
                if self.path == "/gen":
                    self._send({"outs": gen(body["contents"], int(body.get("max_new", 40)))})
                elif self.path == "/embed":
                    self._send({"vecs": embed(body["texts"])})
                elif self.path == "/unload":
                    S.clear()
                    gc.collect()
                    torch.cuda.empty_cache()
                    self._send({"ok": True})
                else:
                    self._send({"error": "unknown path"}, 404)
            except Exception as e:      # report, never hang the client
                self._send({"error": repr(e)}, 500)
            finally:
                torch.cuda.empty_cache()    # give memory back to the shared GPU after every request

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 18000), H).serve_forever()
