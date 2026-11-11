"""Quote or Quiet v2: the rules that passed their registered gates (docs/PROGRESS_TRACKER.md), with the 27B judge.
  check(question, answer, page)  gate G14: release a draft answer of any model only when a sentence of the given page holds it as a gate-accepted typed span and the 27B judge
                                 says YES for it and NO for a swapped answer of the same shape (rule R27 on the subject's page).
  answer2(question)              rule Q2 (gate G4; its second test is pending): the frozen pipeline's six readers, every answer given by at least two of them is a candidate,
                                 released when exactly one candidate has a 27B witness on the retrieved or web-named Wikipedia pages and the question is not time-sensitive.
  bio2(name)                     gate G8 (rule W4-27): claims of a draft written from the page, each kept with a sentence the 27B accepts; the value shown is the words of the
                                 quote that match the claim (the G15 finding), so every shown value occurs verbatim in its quote.
Differences from the tested runs, so that their numbers are not claimed for these exactly: check() and answer2() draw the swapped answer from a fixed list of plausible values of
the same shape (the tests drew it from other answers of the same run); the 4B reader is unloaded before the 27B judge is called (memory), which changes timing, not outputs.
Needs the 4B server (18000) and Ollama (11540) with qwen3.8-27b and phi4."""
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent), str(ROOT / "results/runs/s22")]
from vkg import pod, l3_checks2 as C, l3_verify as V, localwiki as LW   # noqa: E402
from vkg.llm import chat                                                 # noqa: E402
import qoq_extra as X                                                    # noqa: E402

JP = X.JP
ORD = X.ORD
SWAP = {"phrase": ["John Smith", "Paris", "the Acme Corporation", "Brazil", "The Example"], "year": None, "number": None}
TPLUS = re.compile(r"\b(this|last|next)\s+(year|season|month|week)\b|\brecent(ly)?\b|\bupcoming\b", re.I)


def _yn(o):
    """Strict reading of a judge reply: True for YES, False for NO, None for anything else (empty, malformed, error text)."""
    t = str(o or "").strip().upper()
    return True if t.startswith("YES") else False if t.startswith("NO") else None


def _yes(o):
    return _yn(o) is True


def judge27(prompt):
    return str(chat("qwen3.8-27b", [{"role": "user", "content": prompt}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))


def _swap(answer, quote):
    a = answer.strip()
    if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", a):
        c = [str(int(a) + d) for d in (13, -11, 27)]
    elif re.fullmatch(r"[\d,.]+", a):
        n = float(a.replace(",", "")) if re.fullmatch(r"[\d,]*\.?\d+", a.replace(",", "")) else 7
        c = [f"{int(n * 2 + 3):,}", f"{int(n / 2 + 1):,}"]
    else:
        c = SWAP["phrase"]
    c = [x for x in c if x.casefold() not in quote.casefold() and x.casefold() != a.casefold()]
    return c[0] if c else None


def _spans(question, answer, title, limit=6):
    text = LW.page_text(title) or ""
    if not text:
        return []
    h = V.doc_hash(text); out = []
    need = [w for w in X.E7L.toks(question) if re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD]
    for i, j in list(V.locate(answer, text))[:60]:
        if len(out) >= limit:
            break
        ok, _ = V.verify(question, {"answer": answer, "doc": title, "doc_sha256": h, "start": i, "end": j}, LW.page_text)
        if ok:
            ok, _ = C.extra(question, text, i, j)
        if not ok:
            continue
        q = X._window(text, i, j)
        if isinstance(q, tuple):
            q = q[0]
        qt = set(X.E7L.toks(q))
        if q.lstrip().startswith(("#", "-", "*", "|", "=")) or len(q) < 40 or not all(w in qt or re.sub(r"\D", "", w) in qt for w in need):
            continue
        out.append({"doc": title, "quote": q, "sha": h})
    return out


def _witness27(question, answer, titles):
    for t in titles:
        for s in _spans(question, answer, t):
            sw = _swap(answer, s["quote"])
            if not sw:
                continue
            if _yn(judge27(JP.format(t=t, s=s["quote"], q=question, a=answer))) is True and _yn(judge27(JP.format(t=t, s=s["quote"], q=question, a=sw))) is False:
                return s                                          # the swap control must be an explicit NO; an empty or malformed reply withholds
    return None


def check(question, answer, page):
    t0 = time.time(); a = str(answer or "").strip()
    if not a or not (page and LW.page_text(page)):
        return {"status": "Unresolved", "reason": "empty answer or no such page in the snapshot", "seconds": round(time.time() - t0, 1)}
    try:
        pod.unload_gen()
    except Exception:
        pass
    w = _witness27(question, a, [page])
    if not w:
        return {"status": "Unresolved", "candidate": a, "reason": "no sentence of the page states this answer to this question (27B judge with a swapped-answer control)", "seconds": round(time.time() - t0, 1)}
    return {"status": "Verified", "answer": a, "quote": w["quote"], "source_title": page, "source_url": "https://en.wikipedia.org/wiki/" + page.replace(" ", "_"),
            "page_sha256": w["sha"], "quote_checked": True, "quote_rule": "R27 (gate G14)", "snapshot": "FineWiki, English Wikipedia, August 2025", "seconds": round(time.time() - t0, 1)}


def answer2(question):
    import qoq_core as Q
    from temporal import time_sensitive
    from urllib.parse import unquote
    t0 = time.time()
    if time_sensitive(question) or TPLUS.search(question):
        return {"status": "Unresolved", "reason": "time-sensitive question (no Verified answer from a fixed snapshot)", "seconds": round(time.time() - t0, 1)}
    r = Q.readers_only(question)
    cands = []
    for k in Q.S.ORDER:
        v = r["readers"].get(k)
        if Q.ans(v) and not any(Q.agree(str(v), c["answer"]) for c in cands):
            cands.append({"answer": str(v).strip(), "support": Q.S.support(r["readers"], v)})
    cands = sorted([c for c in cands if c["support"] >= 2], key=lambda c: -c["support"])
    webw = [unquote(u.split("/wiki/", 1)[1]).replace("_", " ").split("#")[0] for u in r["web_pages"] if "en.wikipedia.org/wiki/" in u]
    titles = list(dict.fromkeys(list(r["wiki_titles"]) + webw))
    try:
        pod.unload_gen()
    except Exception:
        pass
    wits = [(c, _witness27(question, c["answer"], titles)) for c in cands]
    wits = [(c, w) for c, w in wits if w]
    base = {"question": question, "readers": r["readers"], "wiki_titles": titles, "seconds": round(time.time() - t0, 1)}
    if len(wits) != 1:
        return {**base, "status": "Unresolved", "reason": "no candidate has a 27B witness" if not wits else "two different candidates have witnesses (conflict)"}
    c, w = wits[0]
    return {**base, "status": "Verified", "answer": c["answer"], "quote": w["quote"], "source_title": w["doc"], "source_url": "https://en.wikipedia.org/wiki/" + w["doc"].replace(" ", "_"),
            "page_sha256": w["sha"], "quote_checked": True, "quote_rule": "Q2", "support": c["support"], "snapshot": "FineWiki, English Wikipedia, August 2025"}


def _shown_value(value, quote):
    """The words of the quote that match the claim's value: the value itself if it occurs; else the shortest stretch of the quote containing all of the value's content words."""
    if value.casefold() in quote.casefold():
        i = quote.casefold().index(value.casefold()); return quote[i:i + len(value)]
    vw = [w for w in re.findall(r"[a-z0-9]+", X._fold(value) if hasattr(X, "_fold") else value.casefold()) if w.isdigit() or (w not in X.STOPW and len(w) > 2)]
    if not vw:
        return None
    toks = [(m.start(), m.end(), m.group(0).casefold()) for m in re.finditer(r"[A-Za-z0-9]+", quote)]
    best = None
    for s in range(len(toks)):
        seen = set()
        for e in range(s, len(toks)):
            if toks[e][2] in vw:
                seen.add(toks[e][2])
            if set(vw) <= seen:
                if best is None or toks[e][1] - toks[s][0] < best[1] - best[0]:
                    best = (toks[s][0], toks[e][1])
                break
    return quote[best[0]:best[1]] if best else None


def bio2(name):
    out = X.bio(name, judge=judge27) if "judge" in X.bio.__code__.co_varnames else X.bio(name)
    if not out.get("claims"):
        return out
    kept = []
    for c in out["claims"]:
        sv = _shown_value(c["value"], c["quote"])
        if sv and sv in c["quote"]:
            kept.append({**c, "value": sv, "draft_value": c["value"]})
    return {**out, "claims": kept, "kept": len(kept), "status": "Verified claims" if kept else "Unresolved", "quote_rule": "W4-27 (gate G8); shown value taken from the quote (G15)"}
