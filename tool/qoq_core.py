"""Quote or Quiet, one question at a time: the frozen S19 pipeline (as run on the S29 sealed set with the free-search-mcp pool).
  evidence : web pages (search result URLs from the cache results/cache/web_fsm, written by the MCP front end; DuckDuckGo if absent),
             local FineWiki top 5, and the combined passage
  readers  : Qwen3-4B-Instruct-2507 (plain + cautious) on each of the three passages, 40 tokens, greedy
  release  : the candidate must be supported by all three sources, pass the deductive gate V1-V5 (verbatim, typed span in a hash-pinned
             Wikipedia page) and be confirmed by Phi-4 (cautious prompt on the combined passage)
Returns Verified with the quote and its page, or Unresolved with the reason. Nothing here is tuned beyond the frozen system."""
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VKG_EMB", "hf")
os.environ.setdefault("VKG_WEB", "ddg")
os.environ.setdefault("OLLAMA_HOST_URL", os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11540"))

from vkg import evidence_fast as E, pod, websearch as W, localwiki as LW, l3_checks2 as C, s17_eval as S, l3_verify as V   # noqa: E402
from vkg.lite import CAUTIOUS, PLAIN, parse   # noqa: E402
from vkg.llm import chat                      # noqa: E402
from vkg.s12_run import agree                 # noqa: E402
from vkg.s14_eval import ans                  # noqa: E402

W.CACHE = ROOT / "results" / "cache" / "web_fsm"
W.CACHE.mkdir(parents=True, exist_ok=True)
NAMES = ("web", "wiki", "combo")


def answer(question):
    t0 = time.time()
    item = [{"id": "q", "question": question}]
    web = E.build(item, backend="ddg", k=8, max_pages=8, workers=4)["q"]
    wiki = E.wiki_build(item, workers=1)["q"]
    combo = {"passage": E.combo_passage(question, web["kept"], wiki["titles"])}
    ev = {"web": web, "wiki": wiki, "combo": combo}
    prompts, keys = [], []
    for s in NAMES:
        if ev[s]["passage"]:
            for k, tmpl in (("plain", PLAIN), ("cautious", CAUTIOUS)):
                prompts.append(tmpl.format(p=ev[s]["passage"], q=question)); keys.append(f"{s}_{k}")
    outs = pod.gen(prompts, 40) if prompts else []
    r = {k: None for k in S.ORDER}
    r.update({k: parse(o[0]) for k, o in zip(keys, outs)})
    readers = {k: r[k] for k in S.ORDER}
    a, support = S.cand(r)
    base = {"question": question, "readers": readers, "support": support, "web_pages": web["kept"], "wiki_titles": wiki["titles"]}
    if not ans(a):
        return {**base, "status": "Unresolved", "reason": "no reader gave an answer", "seconds": round(time.time() - t0, 1)}
    if support < 3:
        return {**base, "status": "Unresolved", "candidate": a, "reason": f"only {support} of 3 evidence sources support the candidate", "seconds": round(time.time() - t0, 1)}
    rel, rec = C.release2(question, a, wiki["titles"], LW.page_text)
    if not rel:
        return {**base, "status": "Unresolved", "candidate": a, "reason": f"not found as a verified span in the pinned Wikipedia pages ({rec.get('reason')})", "seconds": round(time.time() - t0, 1)}
    p = parse(chat("phi4", [{"role": "user", "content": CAUTIOUS.format(p=combo["passage"], q=question)}], temperature=0.0, seed=0,
                   max_tokens=40, think=False, json_mode=False, num_ctx=24576)) if combo["passage"] else None
    if not (ans(p) and agree(str(rel), str(p))):
        return {**base, "status": "Unresolved", "candidate": a, "second_reader": p, "reason": "the second reader (Phi-4) does not confirm the answer", "seconds": round(time.time() - t0, 1)}
    text = LW.page_text(rec["doc"])
    i, j = rec["start"], rec["end"]
    ctx = text[max(0, text.rfind("\n", 0, i) + 1):(text.find("\n", j) if text.find("\n", j) != -1 else len(text))]
    doc, quote, sha = rec["doc"], ctx.strip()[:400], rec["doc_sha256"]
    quote_checked = False
    import qoq_extra as X
    w = X.witness(question, str(rel), wiki["titles"])      # rule W1 (docs/S42) for the seven templated relations, rule R (docs/S48) for any other question: the shown quote must state the answer
    if isinstance(w, dict):
        doc, quote, sha, quote_checked = w["doc"], w["quote"], w["sha"], True
    elif w is None:
        return {**base, "status": "Unresolved", "candidate": str(rel), "reason": "the answer is on a pinned page but no sentence of it states the answer to this question (rule W1)", "seconds": round(time.time() - t0, 1)}
    else:                                        # not reachable since rule R handles untemplated questions; kept as a fallback
        best = _support_sentence(question, str(rel), [rec["doc"]] + [t for t in wiki["titles"] if t != rec["doc"]])
        if best:
            doc, quote, sha = best
    return {**base, "status": "Verified", "answer": str(rel), "quote": quote, "span": rec["span"], "gate_page": rec["doc"], "gate_context": ctx.strip()[:400],
            "quote_checked": quote_checked, "source_title": doc, "source_url": "https://en.wikipedia.org/wiki/" + doc.replace(" ", "_"), "snapshot": "FineWiki, English Wikipedia, August 2025",
            "page_sha256": sha, "second_reader": p, "seconds": round(time.time() - t0, 1)}


STOP = set("what which who whom whose when where why how was were is are did does the and for with from that this into play born year name "
           "film book novel song city country".split())


def _support_sentence(question, answer, docs):
    """Best verbatim sentence (from the pinned pages already used) that contains the answer and the most content words of the question."""
    kw = {w for w in re.findall(r"[A-Za-z0-9']+", question.casefold()) if len(w) > 3 and w not in STOP}
    names = {w.casefold() for w in re.findall(r"[A-Za-z0-9']+", question)[1:] if w[:1].isupper() or w.isdigit()}   # names and years count double
    a = answer.casefold()
    best, score = None, 0
    for d in docs:
        text = LW.page_text(d)
        if not text:
            continue
        for s in re.split(r"(?<=[.!?])\s+|\n+", text):
            s = s.strip()
            if not (20 <= len(s) <= 400) or s.startswith("#") or a not in s.casefold():
                continue
            ws = set(re.findall(r"[A-Za-z0-9']+", s.casefold()))
            k = len(kw & ws) + len(names & ws)
            if k > score:
                best, score = (d, s, V.doc_hash(text)), k
    return best
