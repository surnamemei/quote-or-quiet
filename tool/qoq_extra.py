"""Quote or Quiet, the three additions of S42 to S47 (docs/S42_CLAIM_AUDIT_AND_PLAN.md, docs/S43_LONGFORM_AND_AMBIGUITY_PLAN.md):
  witness(question, answer, titles)  rule W1 of E7 (plus: the quote must be a sentence, not a table row or list line; this extra condition was not in the test): among the spans of the answer that the gate accepts, show the first one whose sentence passes the frame check,
                                     the subject link and a quote-only reader; none means Unresolved. Only for the seven templated relations of the paper.
  bio(name)                          long-form: a biography written by Phi-4 from the subject's own page, split into claims, each kept only if rule W4 finds a
                                     sentence of the page that a quote-only reader says states it (and not a swapped value). Output is the kept claims with their quotes.
  readings(name, relation)           names that several films or people share: one answer per reading, each from its own page with its own witness.
Same code and thresholds as the experiments; nothing here is tuned. Needs the 4B server (port 18000) and Ollama with phi4 (OLLAMA_HOST_URL)."""
import importlib.util
import json
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VKG_EMB", "hf")
from vkg import pod, l3_checks2 as C, l3_verify as V, localwiki as LW   # noqa: E402
from vkg.lite import PLAIN, CAUTIOUS, parse                              # noqa: E402
from vkg.s12_run import agree                                            # noqa: E402
from vkg.s14_eval import ans                                             # noqa: E402

OLLAMA = os.environ.get("OLLAMA_HOST_URL", os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11540"))


def _load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, ROOT / path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


E7L = _load("results/runs/s42/e7_lib.py")                    # TEMPLATE, subject_link, toks, fold
DEC = _load("results/runs/s47/lf_decompose2_rag.py")         # sentences, PROMPT, PASS2, keep, uncovered (version 2 decomposition)
DEC.gen = lambda prompt: _ollama_claims(prompt)

GP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\n'
      "Answer in a few words with only what this sentence states. If the sentence does not state the answer to this exact question, reply NONE.")
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
FRAME = {"death_year": ["died", "death", "dies", "killed", "executed", "assassinated", "murdered"], "birth_place": ["born", "birth", "native"],
         "birth_year": ["born", "birth"], "director": ["direct"], "author": ["writ", "wrote", "author", "novel", "book", "play", "poem", "story", " by "],
         "capital": ["capital"]}
YR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
RNG = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\s*(?:–|-|—|to|until)\s*(1[0-9]{3}|20[0-9]{2}|present|incumbent)?", re.I)
STOPW = set("a an the of in on at to for from by with and or but is are was were be been being he she it they his her their its this that these those as has have had "
            "not no also which who whom whose when where what how into than then there here after before during over under about between".split())
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
FALLBACK = {"DATE": "June 1, 1900", "YEAR": "1900", "NUMBER": "7", "PLACE": "Paris", "ORG": "Acme Corporation", "PERSON": "John Smith", "WORK": "The Example",
            "NATIONALITY": "Canadian", "OCCUPATION": "pilot"}


def _ollama_claims(prompt):
    r = requests.post(f"{OLLAMA}/api/generate", json={"model": "phi4", "prompt": prompt, "stream": False, "format": "json",
                      "options": {"temperature": 0, "seed": 0, "num_predict": 700, "num_ctx": 4096}}, timeout=3600).json()
    try:
        return json.loads(r["response"]).get("claims", [])
    except (ValueError, KeyError, AttributeError):
        return []


def _bounds(text, i, j):
    a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
    ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
    return a, (min(ends) if ends else len(text))


def _window(text, i, j):
    a, b = _bounds(text, i, j)
    while a < i and text[a].isspace():
        a += 1
    while b > j and text[b - 1].isspace():
        b -= 1
    if b - a > 300:
        a2 = max(a, min(i - 120, b - 300)); b2 = min(b, a2 + 300)
        if j > b2:
            b2 = j; a2 = max(a, b2 - 300)
        a, b = a2, b2
    return text[a:b], i - a, j - a


def _frame_ok(rel, question, text, i, j):
    sent = C.sentence_at(text, i, j); low = sent.lower()
    if rel == "office":
        y = int(YR.findall(question)[-1])
        return str(y) in sent or any(int(a) <= y <= (int(b) if b and b.isdigit() else 9999) for a, b in RNG.findall(sent))
    if any(w in low for w in FRAME[rel]):
        return True
    if rel == "death_year":
        return bool(re.search(r"[–—-]\s*[\w ,.]{0,20}$", text[max(0, i - 25):i]))
    if rel == "birth_year":
        return bool(re.match(r"^[\w ,.]{0,20}\s*[–—-]", text[j:j + 25]))
    return False


def _said(o):
    o = str(o or "").strip().strip("'\".")
    return o if ans(o) and not o.upper().startswith("NONE") else None


def relation_of(question):
    for rel, pat in E7L.TEMPLATE.items():
        if re.fullmatch(pat, question.strip()):
            return rel
    return None


# ---------------------------------------------------------------- rule W1 (short answers)
def witness(question, answer, titles, rel=None):
    """Returns {'doc','quote','sha','span'} for the first accepted span whose sentence passes F, S and the quote-only reader, or None.
    A question that is not one of the seven templated relations goes to witness_free (rule R of S48)."""
    rel = rel or relation_of(question)
    if rel is None:
        return witness_free(question, answer, titles)
    cands = []
    for d in titles:
        text = LW.page_text(d)
        if not text:
            continue
        h = V.doc_hash(text)
        for k, (i, j) in enumerate(V.locate(str(answer), text)):
            if len(cands) >= 30 or k >= 600:
                break
            ok, _ = V.verify(question, {"answer": str(answer), "doc": d, "doc_sha256": h, "start": i, "end": j}, LW.page_text)
            if ok:
                ok, _ = C.extra(question, text, i, j)
            if ok:
                q, o1, o2 = _window(text, i, j)
                cands.append({"doc": d, "quote": q, "span": text[i:j], "sha": h,
                              "F": _frame_ok(rel, question, text, i, j), "S": E7L.subject_link(question, d, q),
                              "sent": not q.lstrip().startswith(("#", "-", "*", "|", "=")) and len(q) >= 40})
    pick = [c for c in cands if c["F"] and c["S"] and c["sent"]][:4]    # stricter than the tested W1: the quote must also be a sentence, not a table row or list line
    if not pick:
        return None
    outs = pod.gen([GP.format(t=c["doc"], s=c["quote"], q=question) for c in pick], 24)
    for c, o in zip(pick, outs):
        g = _said(parse(o[0]))
        if g and agree(str(answer), g):
            return c
    return None


SHAPE_POOL = {"year": ["1912", "1987", "1956"], "number": ["7", "23", "112"], "phrase": ["the United States", "John Smith", "Paris"]}


def _shape(a):
    a = str(a).strip()
    if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", a):
        return "year"
    return "number" if re.fullmatch(r"[\d,.]+", a) else "phrase"


def witness_free(question, answer, titles):
    """Rule R of S48 (docs/S48_RELATION_FREE_PLAN.md), for any question: the first accepted span whose quote is a sentence, holds every number, year and ordinal
    word of the question, and which the quote-only 4B judge accepts for the answer and rejects for a swapped answer of the same shape. None if there is none."""
    nm = [w for w in E7L.toks(question) if re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD]
    cands = []
    for d in titles:
        text = LW.page_text(d)
        if not text:
            continue
        h = V.doc_hash(text)
        for k, (i, j) in enumerate(V.locate(str(answer), text)):
            if len(cands) >= 30 or k >= 600:
                break
            ok, _ = V.verify(question, {"answer": str(answer), "doc": d, "doc_sha256": h, "start": i, "end": j}, LW.page_text)
            if ok:
                ok, _ = C.extra(question, text, i, j)
            if not ok:
                continue
            q, o1, o2 = _window(text, i, j); qt = set(E7L.toks(q))
            if q.lstrip().startswith(("#", "-", "*", "|", "=")) or len(q) < 40 or not all(w in qt or re.sub(r"\D", "", w) in qt for w in nm):
                continue
            sw = next((x for x in SHAPE_POOL[_shape(answer)] if x.casefold() not in q.casefold() and x.casefold() != str(answer).casefold()), None)
            if sw:
                cands.append({"doc": d, "quote": q, "span": text[i:j], "sha": h, "swap": sw})
    cands = cands[:6]
    if not cands:
        return None
    prompts = []
    for c in cands:
        prompts += [JP.format(t=c["doc"], s=c["quote"], q=question, a=answer), JP.format(t=c["doc"], s=c["quote"], q=question, a=c["swap"])]
    outs = [str(o[0]).strip().upper() for o in pod.gen(prompts, 4)]
    for n, c in enumerate(cands):
        if outs[2 * n].startswith("YES") and not outs[2 * n + 1].startswith("YES"):
            return c
    return None


# ---------------------------------------------------------------- rule W4 (long-form)
def _page_sentences(text):
    out = []
    for para in text.split("\n"):
        if para.lstrip().startswith(("#", "-", "*", "|", "=", ">")) or not para.strip():
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", para.strip()):
            if len(s) >= 40:
                out.append(s[:400])
    return out


def _cw(s):
    return {w for w in E7L.toks(s) if w not in STOPW and len(w) > 2}


def bio(name, judge=None):
    text = LW.page_text(name)
    if not text:
        return {"status": "Unresolved", "reason": f"no page titled '{name}' in the pinned Wikipedia snapshot; try readings() for ambiguous names"}
    P = ("Wikipedia article text:\n\"\"\"\n{t}\n\"\"\"\n\nUsing only facts stated in the article text above, tell me a bio of {n}. "
         "Write 6 to 10 plain sentences and do not add anything that is not in the text.")
    r = requests.post(f"{OLLAMA}/api/generate", json={"model": "phi4", "prompt": P.format(t=text[:14000], n=name), "stream": False,
                      "options": {"temperature": 0, "seed": 0, "num_predict": 350, "num_ctx": 8192}}, timeout=3600).json()
    draft = r["response"]
    sents = DEC.sentences(draft); claims = []
    for i, s in enumerate(sents, 1):
        cs = DEC.gen(DEC.PROMPT.format(name=name, prev=sents[i - 2] if i > 1 else "(none)", s=s))
        un = DEC.uncovered(s, [c for c in cs if isinstance(c, dict) and DEC.keep(c, s, name) is None])
        if un:
            cs += DEC.gen(DEC.PASS2.format(name=name, s=s, items="; ".join(un[:8])))
        seen = set()
        for c in cs:
            if not isinstance(c, dict):
                continue
            key = (str(c.get("subject")), str(c.get("value")).casefold(), str(c.get("question")).casefold())
            if key in seen or DEC.keep(c, s, name) is not None:
                continue
            seen.add(key); claims.append({"question": str(c["question"]).strip(), "value": str(c["value"]).strip().strip("'\""), "type": str(c.get("type", "OTHER")), "sentence": s})
    page = _page_sentences(text); nm = set(E7L.toks(name)); bytype = {}
    for c in claims:
        bytype.setdefault(c["type"], []).append(c["value"])
    prompts, meta = [], []
    for ci, c in enumerate(claims):
        dw = _cw(c["sentence"]) | _cw(c["value"])
        need = [w for w in E7L.toks(c["question"]) if (re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD) and w not in nm]
        top = sorted(((len(dw & _cw(x)), k) for k, x in enumerate(page)), key=lambda t: (-t[0], t[1]))[:3]
        pool = [v for v in bytype.get(c["type"], []) if v.casefold() != c["value"].casefold()]
        sw = pool[0] if pool else FALLBACK.get(c["type"])
        vw = _cw(c["value"])
        for ov, k in top:
            q = page[k]
            if ov < 2 or not sw or q.casefold().find(sw.casefold()) != -1:
                continue
            qt = set(E7L.toks(q))
            if not all(w in qt or re.sub(r"\D", "", w) in qt for w in need) or len(vw & _cw(q)) / max(1, len(vw)) < 0.75:
                continue
            meta.append((ci, q)); prompts += [JP.format(t=name, s=q, q=c["question"], a=c["value"]), JP.format(t=name, s=q, q=c["question"], a=sw)]
    outs = ([judge(p_) for p_ in prompts] if judge else [o[0] for o in pod.gen(prompts, 4)]) if prompts else []   # v2 passes the 27B judge (rule W4-27)
    kept = {}
    for n, (ci, q) in enumerate(meta):
        if ci in kept:
            continue
        if str(outs[2 * n]).strip().upper().startswith("YES") and not str(outs[2 * n + 1]).strip().upper().startswith("YES"):
            kept[ci] = q
    out = [{"question": claims[ci]["question"], "value": claims[ci]["value"], "quote": q, "source_title": name,
            "source_url": "https://en.wikipedia.org/wiki/" + name.replace(" ", "_"), "page_sha256": V.doc_hash(text)} for ci, q in sorted(kept.items())]
    return {"status": "Verified claims" if out else "Unresolved", "name": name, "claims": out, "kept": len(out), "checked": len(claims),
            "snapshot": "FineWiki, English Wikipedia, August 2025",
            "note": ("Each claim is shown with a sentence of the page that states it. Claims without such a sentence are left out, not marked false. "
                     "Measured on 50 fresh subjects: 1 of 400 reviewed kept claims false, 1 of 400 quotes not stating its claim (paper section 5.12). "
                     "The page is an August 2025 snapshot.")}


# ---------------------------------------------------------------- ambiguous names
PERS = re.compile(r"footballer|politician|actor|actress|singer|musician|writer|author|poet|painter|cricketer|boxer|wrestler|director|journalist|"
                  r"basketball|baseball|general|physician|composer|rapper|swimmer|lawyer|judge|bishop|priest|businessman|athlete")
REL_Q = {"director": "Who directed the film {t}?", "birth_year": "In what year was {t} born?", "birth_place": "Where was {t} born?",
         "death_year": "In what year did {t} die?", "author": "Who wrote {t}?"}


def readings(name, relation="birth_year", limit=4):
    if relation not in REL_Q:
        return {"status": "Unresolved", "reason": f"relation must be one of {sorted(REL_Q)}"}
    db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
    rows = db.execute("select title, qual, len from t where core = ? and qual != '' and len >= 2000", (name,)).fetchall()
    if relation == "director":
        rows = [r for r in rows if re.fullmatch(r"\d{4} (?:\w+ )?film", r[1])]
    elif relation in ("birth_year", "birth_place", "death_year"):
        rows = [r for r in rows if PERS.search(r[1])]
    else:
        rows = [r for r in rows if re.search(r"novel|book|play|poem|story|film", r[1])]
    rows = sorted(rows, key=lambda r: -r[2])[:limit]
    if not rows:
        return {"status": "Unresolved", "reason": f"no pages that share the name '{name}' for relation {relation}"}
    res = []
    for t, qual, ln in rows:
        text = LW.page_text(t) or ""
        q = REL_Q[relation].format(t=t if relation in ("director", "author") else name)
        p = f"[{t}] " + text[:3000]
        o = pod.gen([PLAIN.format(p=p, q=q), CAUTIOUS.format(p=p, q=q)], 40)
        a1, a2 = parse(o[0][0]), parse(o[1][0])
        if not (ans(a1) and ans(a2) and agree(str(a1), str(a2))):
            res.append({"reading": t, "status": "Unresolved", "reason": "the reader gave no consistent answer from this page"}); continue
        w = witness(q, str(a1).strip(), [t], rel=relation)
        if not isinstance(w, dict):
            res.append({"reading": t, "status": "Unresolved", "reason": "no sentence of the page states the answer", "candidate": str(a1)}); continue
        res.append({"reading": t, "status": "Verified", "question": q, "answer": str(a1).strip(), "quote": w["quote"],
                    "source_url": "https://en.wikipedia.org/wiki/" + t.replace(" ", "_"), "page_sha256": w["sha"]})
    return {"status": "Readings", "name": name, "relation": relation, "readings": res,
            "note": "One answer per reading, each from its own page. Which reading you meant is not decided; all are listed (paper section 5.13)."}
