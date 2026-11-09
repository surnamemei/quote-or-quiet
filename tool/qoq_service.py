"""Local HTTP service for Quote or Quiet (main project environment). POST /answer {"question": "..."} -> JSON result of qoq_core.answer.
Needs the 4B generation server on 127.0.0.1:18000 and Ollama with phi4 on VKG_OLLAMA_URL (default 127.0.0.1:11535); see tool/README.md.
python -B tool/qoq_service.py [port=18100]"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qoq_core  # noqa: E402

LOCK = threading.Lock()     # one question at a time (GPU memory)


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/answer":
            self.send_error(404); return
        q = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}").get("question", "").strip()
        try:
            with LOCK:
                res = qoq_core.answer(q) if q else {"status": "Unresolved", "reason": "empty question"}
            code = 200
        except Exception as ex:                       # never invent an answer on failure
            res, code = {"status": "Unresolved", "reason": f"pipeline error: {type(ex).__name__}: {ex}"}, 500
        body = json.dumps(res, ensure_ascii=False).encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        body = b'{"ok": true}'
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18100
    print(f"Quote or Quiet service on 127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
