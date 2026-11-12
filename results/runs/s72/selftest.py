"""S72: v2 self-test before the registered G15 second test (inputs outside g15b_inputs.jsonl). Checks that each v2 endpoint answers with HTTP 200 and that every released
statement passes the same check as g15b_run.py. Writes selftest_responses.jsonl and prints one line per request. python -B results/runs/s72/selftest.py"""
import json, sys, time
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[3]; D = ROOT / "results/runs/s72"
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20")]
import no_retrieval2  # noqa: F401
from vkg import localwiki as LW, l3_verify as V
T = [("/answer2", {"question": "Who wrote the novel Middlemarch?"}), ("/answer2", {"question": "In what year was the Eiffel Tower completed?"}),
     ("/check", {"question": "Who directed the film Jaws?", "answer": "Steven Spielberg", "page": "Jaws (film)"}),
     ("/check", {"question": "Who directed the film Jaws?", "answer": "Ridley Scott", "page": "Jaws (film)"}),
     ("/bio2", {"name": "Marie Curie"}), ("/readings", {"name": "Titanic", "relation": "director"}), ("/answer2", {"question": ""})]
bad = 0
for path, body in T:
    t0 = time.time(); r = requests.post("http://127.0.0.1:18100" + path, json=body, timeout=1800); res = r.json(); sec = round(time.time() - t0, 1)
    rel = []
    if path in ("/answer2", "/check") and res.get("status") == "Verified":
        rel = [(res.get("source_title"), res.get("page_sha256"), res.get("quote", ""), res.get("answer", ""))]
    elif path == "/bio2":
        rel = [(c.get("source_title"), c.get("page_sha256"), c.get("quote", ""), c.get("value", "")) for c in res.get("claims", []) or []]
    elif path == "/readings":
        rel = [(g.get("reading"), g.get("page_sha256"), g.get("quote", ""), g.get("answer", "")) for g in res.get("readings", []) or [] if g.get("status") == "Verified"]
    fails = 0
    for title, sha, quote, value in rel:
        text = LW.page_text(title or "") or ""
        fails += (not text) or V.doc_hash(text) != sha or quote not in text or str(value).casefold() not in str(quote).casefold()
    bad += fails + (r.status_code != 200)
    print(path, json.dumps(body, ensure_ascii=False)[:70], "| HTTP", r.status_code, "|", res.get("status"), "| released", len(rel), "| check failures", fails, "|", sec, "s", "|", str(res.get("answer") or res.get("reason") or "")[:80], flush=True)
    with open(D / "selftest_responses.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"path": path, "body": body, "code": r.status_code, "sec": sec, "resp": res}, ensure_ascii=False) + "\n")
print("SELFTEST", "OK" if bad == 0 else f"PROBLEMS {bad}")
