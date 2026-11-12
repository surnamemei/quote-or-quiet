"""S72 gate G15, second test on v2 (docs/S72_G15B_PLAN.md): send the 1,000 requests of g15b_inputs.jsonl to the running service (127.0.0.1:18100) and check every response independently.
  run  : one request at a time, /answer requests at least 10 s apart start to start (live web search), timeout 900 s; resumable (g15_responses.jsonl).
  check: CPU. For every released statement (status Verified for /answer; every claim of /bio; every Verified reading of /readings): the page named by the response
         exists in the local snapshot, its sha256 equals the reported page_sha256, the quote occurs verbatim in the page text, and the released answer/value occurs in the quote
         (case-insensitive); for /answer also quote_checked is true. A release failing any of these is a violation. Also counts errors (HTTP 500), timeouts, latency.
python -B results/runs/s72/g15b_run.py run ; OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s72/g15b_run.py check"""
import json, os, statistics, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "results/runs/s72"; MODE = sys.argv[1]
IN = [json.loads(l) for l in open(D / "g15b_inputs.jsonl", encoding="utf-8")]
RF = D / "g15b_responses.jsonl"

if MODE == "run":
    import requests
    done = {json.loads(l)["n"] for l in open(RF, encoding="utf-8")} if RF.exists() else set()
    last = 0.0
    for x in IN:
        if x["n"] in done:
            continue
        if x["path"] in ("/answer", "/answer2"):
            time.sleep(max(0.0, 10.0 - (time.time() - last)))
        body = {"question": x["question"]} if x["path"] in ("/answer", "/answer2") else ({"question": x["question"], "answer": x["answer"], "page": x["page"]} if x["path"] == "/check" else ({"name": x["name"], "relation": x["relation"]} if x["path"] == "/readings" else {"name": x["name"]}))
        t0 = time.time(); last = t0
        try:
            r = requests.post("http://127.0.0.1:18100" + x["path"], json=body, timeout=900)
            rec = {"n": x["n"], "code": r.status_code, "sec": round(time.time() - t0, 2), "resp": r.json()}
        except requests.exceptions.Timeout:
            rec = {"n": x["n"], "code": "timeout", "sec": round(time.time() - t0, 2), "resp": None}
        except Exception as ex:
            rec = {"n": x["n"], "code": f"error: {type(ex).__name__}", "sec": round(time.time() - t0, 2), "resp": None}
        with open(RF, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if x["n"] % 25 == 0:
            print(x["n"], rec["code"], rec["sec"], flush=True)
    print("run done", flush=True)
else:
    sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20")]
    import no_retrieval2  # noqa: F401
    from vkg import localwiki as LW, l3_verify as V
    R = {json.loads(l)["n"]: json.loads(l) for l in open(RF, encoding="utf-8")}
    assert len(R) == len(IN), (len(R), len(IN))
    viol, rel_n, by = [], 0, {}
    def chk(n, title, sha, quote, value, need_checked=None):
        global rel_n
        rel_n += 1; text = LW.page_text(title) or ""; why = []
        if not text: why.append("page missing")
        elif V.doc_hash(text) != sha: why.append("sha256 differs")
        if quote not in text: why.append("quote not verbatim in page")
        if str(value).casefold() not in str(quote).casefold(): why.append("value not in quote")
        if need_checked is False: why.append("quote_checked false")
        if why: viol.append({"n": n, "why": why})
    for x in IN:
        r = R[x["n"]]; s = by.setdefault(x["kind"], {"n": 0, "released": 0, "http500": 0, "timeout": 0, "other_error": 0, "sec": []})
        s["n"] += 1; s["sec"].append(r["sec"])
        if r["code"] == 500: s["http500"] += 1
        elif r["code"] == "timeout": s["timeout"] += 1
        elif r["code"] != 200: s["other_error"] += 1
        res = r["resp"] or {}
        if x["path"] in ("/answer", "/answer2", "/check") and res.get("status") == "Verified":
            s["released"] += 1; chk(x["n"], res.get("source_title", ""), res.get("page_sha256"), res.get("quote", ""), res.get("answer", ""), bool(res.get("quote_checked")))
        elif x["path"] in ("/bio", "/bio2"):
            for c in res.get("claims", []) or []:
                s["released"] += 1; chk(x["n"], c.get("source_title", ""), c.get("page_sha256"), c.get("quote", ""), c.get("value", ""))
        elif x["path"] == "/readings":
            for g in res.get("readings", []) or []:
                if g.get("status") == "Verified":
                    s["released"] += 1; chk(x["n"], g.get("reading", ""), g.get("page_sha256"), g.get("quote", ""), g.get("answer", ""))
    allsec = [r["sec"] for r in R.values()]
    q = lambda v, p: sorted(v)[min(len(v) - 1, int(p * len(v)))]
    out = ["# S72 gate G15, second test: stress test of Quote or Quiet v2 (1,000 requests)", "",
           f"Released statements checked: {rel_n}; violations (page missing, hash differs, quote not verbatim, value not in quote, or quote not checked): {len(viol)}.",
           f"Latency over all requests: median {statistics.median(allsec):.1f} s, 95th percentile {q(allsec, 0.95):.1f} s, max {max(allsec):.1f} s.", "",
           "| input kind | requests | released statements | HTTP 500 | timeouts | other errors | median s | p95 s |", "|---|---|---|---|---|---|---|---|"]
    for k, s in by.items():
        out.append(f"| {k} | {s['n']} | {s['released']} | {s['http500']} | {s['timeout']} | {s['other_error']} | {statistics.median(s['sec']):.1f} | {q(s['sec'], 0.95):.1f} |")
    if viol:
        out += ["", "Violations (request number and reasons):"] + [f"- {v['n']}: {', '.join(v['why'])}" for v in viol[:50]]
    (D / "G15B_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
