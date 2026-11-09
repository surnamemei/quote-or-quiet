"""Systems under test.

  B0_raw       answer directly; no abstain option offered (natural abstentions detected by regex)
  B1_abstain   structured output with an explicit unknown/conflict option and an abstention instruction
  VKG_min      routed minimum verification system:
                 formal  -> model writes a Python expression, deterministic executor produces the value,
                            published only if 3 independent samples agree
                 closed  -> B1 + deterministic evidence verifier (verbatim quotes), one recovery retry
                 open    -> B1 + self-consistency gate (k=5 @ T=0.8, need >=4 agreeing answers)
Final output is always the structured record; no free-text re-generation, so no re-fabrication step.
"""
import json
import re
from collections import Counter
from datetime import date, timedelta

from .llm import chat
from .tasks import norm, matches

UNKNOWN_RE = re.compile(r"\b(unknown|not (mentioned|stated|specified|provided|available|known)|"
                        r"no (information|record|evidence)|cannot (be )?(determine|answer|find)|"
                        r"can'?t (determine|answer)|i (do not|don'?t) (know|have)|unable to|"
                        r"does not (mention|specify|state)|there is no)\b", re.I)


def _parse(txt):
    try:
        d = json.loads(txt)
        return d if isinstance(d, dict) else {}
    except Exception:
        m = re.search(r"\{.*\}", txt or "", re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {}


def _ctx(item):
    return f"Passage:\n{item.passage}\n\n" if item.passage else ""


# ------------------------------------------------------------------ B0
def b0_raw(item, model):
    prompt = (f"{_ctx(item)}Question: {item.question}\n"
              'Reply as JSON: {"answer": "<short answer>"}')
    txt = chat(model, [{"role": "user", "content": prompt}])
    ans = str(_parse(txt).get("answer", txt))
    status = "unknown" if UNKNOWN_RE.search(ans) else "answer"
    return {"status": status, "answer": ans, "raw": txt}


# ------------------------------------------------------------------ B1
def _b1_prompt(item, strict_quote=False):
    if item.passage:
        rules = ("Use ONLY the passage. status=\"answer\" if the passage states the answer; "
                 "status=\"unknown\" if the passage does not state it; "
                 "status=\"conflict\" if the passage gives contradictory values with no way to choose.\n"
                 "evidence_quotes must be exact verbatim sentences copied from the passage "
                 "(for a conflict, quote both).")
    else:
        rules = ("status=\"answer\" only if you are certain the answer is correct and the entities really exist; "
                 "if you do not reliably know it, or you cannot confirm the entity exists, use status=\"unknown\". "
                 "Never guess or invent names, dates or citations.")
    extra = "\nYour previous quotes were not verbatim. Copy the sentence character-for-character." if strict_quote else ""
    return (f"{_ctx(item)}Question: {item.question}\n{rules}{extra}\n"
            'Reply as JSON: {"status": "answer|unknown|conflict", "answer": "<short answer or empty>", '
            '"evidence_quotes": ["..."]}')


def _run_b1(item, model, temperature=0.0, seed=0, strict_quote=False):
    txt = chat(model, [{"role": "user", "content": _b1_prompt(item, strict_quote)}],
               temperature=temperature, seed=seed)
    d = _parse(txt)
    status = d.get("status", "answer")
    if status not in ("answer", "unknown", "conflict"):
        status = "answer"
    return {"status": status, "answer": str(d.get("answer", "")), "quotes": d.get("evidence_quotes") or [],
            "raw": txt}


def b1_abstain(item, model):
    return _run_b1(item, model)


def b2_strict(item, model):
    """Matched-coverage control: same single call as B1, with a much more cautious instruction (no verifier)."""
    base = _b1_prompt(item)
    extra = ("\nBe conservative: answer ONLY if one sentence of the passage directly and unambiguously states the answer "
             "to exactly this question about exactly this entity. If the passage merely mentions related facts, other "
             "entities, or requires any inference, use status=\"unknown\".") if item.passage else ""
    txt = chat(model, [{"role": "user", "content": base + extra}])
    d = _parse(txt)
    st = d.get("status", "answer")
    st = st if st in ("answer", "unknown", "conflict") else "answer"
    return {"status": st, "answer": str(d.get("answer", "")), "quotes": d.get("evidence_quotes") or [], "raw": txt}


# ------------------------------------------------------------------ verifier (closed evidence)
def _verbatim(q, passage):
    return bool(q) and re.sub(r"\s+", " ", str(q)).strip().lower() in re.sub(r"\s+", " ", passage).lower()


def verify_closed(item, r):
    quotes = [q for q in r["quotes"] if isinstance(q, str)]
    if r["status"] == "unknown":
        return True, "abstain"
    if not quotes or not all(_verbatim(q, item.passage) for q in quotes):
        return False, "quote_not_verbatim"
    if r["status"] == "answer":
        if not matches([r["answer"]], " ".join(quotes)) and not norm(r["answer"]) in norm(" ".join(quotes)):
            return False, "answer_not_in_quote"
        return True, "ok"
    if r["status"] == "conflict":
        return (len(set(map(norm, quotes))) >= 2), "conflict_needs_two_quotes"
    return False, "bad_status"


def _relevant_sentences(item, model):
    prompt = (f"Passage:\n{item.passage}\n\nQuestion: {item.question}\n"
              "List EVERY sentence of the passage that states a value for the attribute asked about, for the "
              "entity named in the question. Include sentences that refer to that entity indirectly "
              "(\"it\", \"the institute\", \"the organisation\"), and include sources that disagree. "
              "Ignore other entities and other attributes. Copy each sentence "
              'verbatim. Reply as JSON: {"sentences": ["..."]}')
    d = _parse(chat(model, [{"role": "user", "content": prompt}]))
    return [s for s in (d.get("sentences") or []) if isinstance(s, str) and _verbatim(s, item.passage)]


def vkg_closed(item, model, conflict_check=True):
    r = _run_b1(item, model)
    ok, why = verify_closed(item, r)
    trace = [("first", r["status"], why)]
    if not ok:                              # recovery: one retry demanding verbatim evidence
        r2 = _run_b1(item, model, strict_quote=True, seed=1)
        ok2, why2 = verify_closed(item, r2)
        trace.append(("retry", r2["status"], why2))
        if ok2:
            r, ok = r2, True
    if not ok:
        r = {"status": "unknown", "answer": "", "quotes": [], "raw": r["raw"]}
    elif conflict_check and r["status"] == "answer":
        # independent adversarial pass: does any other relevant sentence disagree with the chosen answer?
        sents = _relevant_sentences(item, model)
        if len(sents) >= 2 and not all(matches([r["answer"]], s) for s in sents):
            r = {"status": "conflict", "answer": "", "quotes": sents, "raw": r["raw"]}
            trace.append(("conflict_check", "conflict", len(sents)))
    r["trace"] = trace
    return r


# ------------------------------------------------------------------ open world: consistency gate
def vkg_open(item, model, k=5, need=4):
    base = _run_b1(item, model)
    if base["status"] != "answer":
        base["trace"] = ["base_abstained"]
        return base
    votes = [norm(base["answer"])]
    for s in range(1, k):
        r = _run_b1(item, model, temperature=0.8, seed=100 + s)
        votes.append(norm(r["answer"]) if r["status"] == "answer" else "<unk>")
    top, n = Counter(votes).most_common(1)[0]
    if top != "<unk>" and n >= need and top == votes[0]:
        base["trace"] = [f"agree {n}/{k}"]
        return base
    return {"status": "unknown", "answer": "", "quotes": [], "raw": base["raw"], "trace": [f"disagree {votes}"]}


# ------------------------------------------------------------------ formal: tool route
_SAFE_BUILTINS = {"int": int, "str": str, "len": len, "sum": sum, "min": min, "max": max, "abs": abs,
                  "round": round, "float": float, "range": range}
_BANNED = ("__", "import", "open", "exec", "eval", "getattr", "globals", "compile", "input")


def _safe_eval(expr):
    if any(b in expr for b in _BANNED):
        raise ValueError("banned token")
    v = eval(expr, {"__builtins__": _SAFE_BUILTINS, "date": date, "timedelta": timedelta}, {})
    if isinstance(v, float) and v == int(v):
        v = int(v)
    if isinstance(v, date):
        v = v.isoformat()
    return str(v)


def _expr(item, model, temperature, seed):
    prompt = (f"Question: {item.question}\n"
              "Write ONE Python expression that evaluates to the answer. Allowed names: int, str, len, sum, "
              "min, max, abs, round, date(y,m,d), timedelta(days=n), string methods like .count(). "
              "Dates must be returned as ISO strings via .isoformat(). Do not compute the value yourself.\n"
              'Reply as JSON: {"expression": "..."}')
    return _parse(chat(model, [{"role": "user", "content": prompt}], temperature=temperature, seed=seed)
                  ).get("expression", "")


def vkg_formal(item, model, k=3):
    vals = []
    for s in range(k):
        try:
            vals.append(_safe_eval(_expr(item, model, 0.0 if s == 0 else 0.7, s)))
        except Exception as e:
            vals.append(f"<err:{type(e).__name__}>")
    top, n = Counter(vals).most_common(1)[0]
    if n == k and not top.startswith("<err"):
        return {"status": "answer", "answer": top, "quotes": [], "raw": str(vals), "trace": [f"exec agree {n}/{k}"]}
    return {"status": "unknown", "answer": "", "quotes": [], "raw": str(vals), "trace": [f"exec disagree {vals}"]}


# ------------------------------------------------------------------ v2: evidence-only support checks
CROSS_CHECKER = "qwen3-vl:8b-instruct"   # smaller model, different training recipe/size (same family: only partly independent)


def _support_check(item, answer, quotes, checker):
    """Checker sees ONLY the question, candidate answer and the quoted evidence (not the generator's reasoning)."""
    prompt = ("Question: " + item.question + "\nCandidate answer: " + str(answer) + "\nEvidence (the only source):\n- "
              + "\n- ".join(quotes) + "\n\nDoes the evidence explicitly state that the candidate answer is the answer to "
              "exactly this question (same entity, same attribute, no outside knowledge, no inference beyond the text)? "
              'Reply as JSON: {"supported": true|false}')
    return _parse(chat(checker, [{"role": "user", "content": prompt}])).get("supported") is True


def _incompatible_check(item, sents, checker):
    prompt = ("Question: " + item.question + "\nSentences:\n- " + "\n- ".join(sents) +
              "\n\nDo these sentences give mutually incompatible answers to this exact question, so that both cannot be "
              'true at once? Different but compatible details do not count. Reply as JSON: {"incompatible": true|false}')
    return _parse(chat(checker, [{"role": "user", "content": prompt}])).get("incompatible") is True


def vkg_closed_v2(item, model, checker):
    r = _run_b1(item, model)
    trace = []
    if r["status"] == "unknown":
        r["trace"] = ["abstain"]
        return r
    quotes = [q for q in r["quotes"] if isinstance(q, str)]
    if not quotes or not all(_verbatim(q, item.passage) for q in quotes):
        trace.append("quote_not_verbatim")
        r2 = _run_b1(item, model, strict_quote=True, seed=1)
        q2 = [q for q in r2["quotes"] if isinstance(q, str)]
        if r2["status"] != "unknown" and q2 and all(_verbatim(q, item.passage) for q in q2):
            r, quotes = r2, q2
        else:
            return {"status": "unknown", "answer": "", "quotes": [], "raw": r["raw"], "trace": trace}
    if r["status"] == "answer":
        if not _support_check(item, r["answer"], quotes, checker):
            return {"status": "unknown", "answer": "", "quotes": quotes, "raw": r["raw"], "trace": trace + ["support_failed"]}
        sents = _relevant_sentences(item, model)
        if len(sents) >= 2 and not all(matches([r["answer"]], s) for s in sents) and _incompatible_check(item, sents, checker):
            return {"status": "conflict", "answer": "", "quotes": sents, "raw": r["raw"], "trace": trace + ["conflict_confirmed"]}
        return {**r, "trace": trace + ["supported"]}
    if r["status"] == "conflict":
        if len(set(map(norm, quotes))) >= 2 and _incompatible_check(item, quotes, checker):
            return {**r, "trace": trace + ["conflict_confirmed"]}
        return {"status": "unknown", "answer": "", "quotes": quotes, "raw": r["raw"], "trace": trace + ["conflict_rejected"]}
    return r


def _route2(item, model, checker):
    if item.family == "formal":
        return vkg_formal(item, model)
    if item.passage:
        return vkg_closed_v2(item, model, checker)
    return vkg_open(item, model)


def vkg_v2(item, model):               # checker = generator model (shared errors possible)
    return _route2(item, model, model)


def vkg_v2x(item, model):              # checker = different, smaller model
    return _route2(item, model, CROSS_CHECKER)


def _route(item, model, conflict_check):
    if item.family == "formal":
        return vkg_formal(item, model)
    if item.passage:
        return vkg_closed(item, model, conflict_check)
    return vkg_open(item, model)


def vkg_min(item, model):
    return _route(item, model, True)


def vkg_noconf(item, model):          # ablation: verbatim-evidence verifier only
    return _route(item, model, False)


SYSTEMS = {"B0_raw": b0_raw, "B1_abstain": b1_abstain, "VKG_noconf": vkg_noconf, "VKG_min": vkg_min,
           "VKG_v2": vkg_v2, "VKG_v2x": vkg_v2x, "B2_strict": b2_strict}
