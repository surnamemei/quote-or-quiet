"""S37 version 2 decomposition (changes listed in docs/S37_DECOMPOSITION_PILOT_RESULT.md): one call per sentence with the person given,
deterministic filters (value verbatim in the sentence; subject is the person or a name in the sentence; no question words outside the sentence,
the subject and a short relation list), a second pass for uncovered numbers and names, a splitter that drops markdown headings.
Same drafts as version 1. Writes slots2.jsonl. Resumable. python -B results/runs/s37/lf_decompose2.py"""
import json, re
import requests
from pathlib import Path
D = Path(__file__).parent


def gen(prompt):
    for port in (11540,):
        try:
            r = requests.post(f"http://127.0.0.1:{port}/api/generate", json={"model": "phi4", "prompt": prompt, "stream": False, "format": "json",
                              "options": {"temperature": 0, "seed": 0, "num_predict": 700, "num_ctx": 4096}}, timeout=3600).json()
            return json.loads(r["response"]).get("claims", [])
        except requests.RequestException:
            continue
        except (ValueError, KeyError, AttributeError):
            return []
    raise RuntimeError("no Ollama instance reachable")


PROMPT = """Person: {name}
Previous sentence (context only): {prev}
Sentence: {s}

List every checkable fact stated in the Sentence. A checkable fact has one value of one of these kinds: a date, a year, a number, a place, a nationality, a person, an organisation, the title of a work, or an occupation.
Rules:
- "value": copied exactly, character for character, from the Sentence.
- "subject": "{name}" if the fact is about the person (also when the Sentence says he, she, his, her); otherwise the other entity's name exactly as written in the Sentence or the previous sentence.
- "question": a short question whose answer is the value, using only the subject and words that appear in the Sentence. Do not add names, places, works or dates that are not in the Sentence.
- "type": DATE, YEAR, NUMBER, PLACE, NATIONALITY, PERSON, ORG, WORK, OCCUPATION or OTHER.
Opinions, praise and summaries are not facts; leave them out.
Reply with compact JSON only: {{"claims": [{{"subject": "...", "question": "...", "value": "...", "type": "..."}}]}}"""

PASS2 = """Person: {name}
Sentence: {s}
These items in the Sentence are not yet covered by a fact: {items}
For each item that is the value of a checkable fact, give the fact with the same rules: value copied exactly from the Sentence; subject "{name}" or a name written in the Sentence; question using only the subject and words from the Sentence.
Reply with compact JSON only: {{"claims": [{{"subject": "...", "question": "...", "value": "...", "type": "..."}}]}}"""

STOP = set("""a an the of in on at to for from by with and or as is was were are be been being did does do has have had what which who whom whose when
where why how many much that this these those it its his her their he she they him them there than then into over under about after before during
between up out not no year years month day date name number first last according give tell known became become serve served work worked""".split())
NUM = re.compile(r"\b\d[\d,.]*\b")
CAP = re.compile(r"\b(?:[A-Z][\w'’.-]+)(?:\s+(?:of|de|von|van|the|and|al|bin|da|di|du|la|le|del)?\s*[A-Z][\w'’.-]+)*")


def sentences(text):
    lines = [l for l in text.split("\n") if l.strip() and not re.match(r"\s*(#+\s|\*\*[^*]+\*\*:?\s*$|[-*]\s*\*\*[^*]+\*\*:?\s*$)", l)]
    text = re.sub(r"\s+", " ", " ".join(lines).replace("**", "")).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", text)
    return [p.strip() for p in parts if len(p.split()) >= 4]


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.casefold())}


def keep(c, s, name):
    """Deterministic filters; returns the reason a claim is dropped, or None."""
    v, sub, q = str(c.get("value", "")).strip(), str(c.get("subject", "")).strip(), str(c.get("question", "")).strip()
    if not v or not q:
        return "empty"
    if v.casefold() not in s.casefold():
        return "value not verbatim in sentence"
    if sub != name and sub.casefold() not in s.casefold():
        return "subject neither the person nor a name in the sentence"
    # added qualifiers = capitalised words (names, places, works) and numbers in the question that are not in the sentence, the subject or the
    # person's name; ordinary words (role, club, began/begin) are allowed (build-time fix: the first version also rejected common words)
    toks = [re.sub(r"['’]s$", "", x) for x in re.findall(r"[A-Za-z][\w'’-]*|\d[\d,.]*", q)[1:]]
    allowed = words(s) | words(sub) | words(name)
    extra = {t for t in toks if (t[0].isupper() or t[0].isdigit()) and not words(t) <= allowed}
    if extra:
        return "question adds words not in the sentence: " + ", ".join(sorted(extra))
    return None


def uncovered(s, claims):
    vals = " ".join(str(c.get("value", "")) for c in claims).casefold()
    items = [n for n in NUM.findall(s) if n.casefold() not in vals] + [m.group(0) for m in CAP.finditer(s) if m.start() > 0 and m.group(0).casefold() not in vals]
    return list(dict.fromkeys(items))


if __name__ == "__main__":
    out = D / "slots2_rag.jsonl"
    done = {json.loads(l)["name"] for l in open(out, encoding="utf-8")} if out.exists() else set()
    for d in map(json.loads, open(D / "drafts_rag.jsonl", encoding="utf-8")):
        name = d["name"]
        if name in done:
            continue
        sents = sentences(d["draft"]); claims = []; dropped = []
        for i, s in enumerate(sents, 1):
            cs = gen(PROMPT.format(name=name, prev=sents[i - 2] if i > 1 else "(none)", s=s))
            un = uncovered(s, [c for c in cs if keep(c, s, name) is None])
            if un:
                cs += gen(PASS2.format(name=name, s=s, items="; ".join(un[:8])))
            seen = set()
            for c in cs:
                if not isinstance(c, dict):
                    continue
                key = (str(c.get("subject")), str(c.get("value")).casefold(), str(c.get("question")).casefold())
                if key in seen:
                    continue
                seen.add(key)
                why = keep(c, s, name)
                (claims if why is None else dropped).append({**c, "sentence": i, **({"dropped": why} if why else {})})
        rec = {"name": name, "sentences": sents, "claims": claims, "dropped": dropped, "parsed": True,
               "uncovered": [{"sentence": i, "items": uncovered(s, [c for c in claims if c["sentence"] == i])} for i, s in enumerate(sents, 1)]}
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(name, len(sents), "sentences", len(claims), "kept", len(dropped), "dropped", flush=True)
    print("decompose2 done")
