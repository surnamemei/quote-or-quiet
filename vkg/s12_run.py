"""S12: search-on-abstain v2 for the small model, targeting the two gaps S11 measured (results/S11_search_on_abstain.md):
(a) the answer page was fetched but its answer chunk did not fit the 1500-word passage, and (b) the 4B's own full-text queries
missed the answer page. Late answers in S11 were wrong a third of the time, so S12 also adds an agreement rule.
Only round-0 abstentions (4B cautious, code non-answer detector) are touched:
  round 1 "second chance": the next-best chunks (same BM25+dense ranking) from the round-0 pages, excluding the chunks already shown.
  round 2 "entity search": pages for the question's named entities (quoted strings and capitalised spans looked up as Wikipedia
          titles, 'go' search) plus the 4B's own 3 queries (as S11), pages not seen before (max 8), 1500 words.
  acceptance: in each round the 4B answers with the cautious prompt; an answer is accepted only if the plain prompt on the same
          passage gives the same answer (normalised tokens equal or one contains the other). Otherwise go on / abstain.
No gold information is used. Run (venv_gpu, via vkg.s12_wait): python -B -m vkg.s12_run -> results/runs/s12/outputs.jsonl"""
import json
import re
import time

from . import retrieval as R
from . import retrieval2 as R2
from .probe_gen import ROOT, parse
from .s11_run import QPROMPT, Small, items, queries
from .s6b_run import CAUTIOUS, PLAIN
from .s8_eval import non_answer
from .support_check import tokens

OUT = ROOT / "results" / "runs" / "s12"
QWORDS = {"what", "which", "who", "whom", "whose", "when", "where", "why", "how", "in", "on", "at", "the", "a", "an", "name", "during", "for"}


def entities(q):
    quoted = [a or b for a, b in re.findall(r'"([^"]{2,80})"|“([^”]{2,80})”', q)]
    bare = re.sub(r'"[^"]{1,80}"|“[^”]{1,80}”', lambda m: " " if len(m.group(0)) <= 12 else " | ", q)   # short quotes are nicknames inside names
    ents = []
    join = {"of", "de", "von", "van", "da", "du", "del", "la", "le"}
    for m in re.finditer(r"[A-Z][\w'’.\-]*(?:\s+(?:[A-Z][\w'’.\-]*|of|de|von|van|da|du|del|la|le))*", bare):
        words = m.group(0).split()
        while words and words[-1] in join:
            words = words[:-1]
        if words and words[0].lower() in QWORDS:
            words = words[1:]
        s = " ".join(words)
        if s and not (len(words) == 1 and m.start() == 0) and s not in ents:
            ents.append(s)
    for s in quoted:
        if len(s) > 10 and s not in ents:
            ents.insert(0, s)
    return ents[:5]


def go_titles(name, k=2):
    url, html = R._fetch({"search": name, "ns0": 1})
    path = url.split("en.wikipedia.org", 1)[-1]
    if path.startswith("/wiki/"):
        from urllib.parse import unquote
        return [unquote(path[len("/wiki/"):]).replace("_", " ")]
    raw = re.findall(r'class="mw-search-result-heading"><a href="/wiki/([^"#]+)"', html)
    from urllib.parse import unquote
    return [unquote(t).replace("_", " ") for t in raw[:k]]


def second_chance(question, titles, shown, max_words=1500):
    """Same ranking as retrieval2.passage, but skipping chunks already shown in the round-0 passage."""
    chunks = [(t, c) for t in titles for c in R._chunks(R.page_text(t), 120)]
    chunks = [(t, c) for t, c in chunks if c not in shown]
    if not chunks:
        return ""
    texts = [c for _, c in chunks]
    sc = R2._bm25_scores(question, texts)
    qv = R2._embed(["Instruct: Given a question, retrieve passages that contain the answer\nQuery: " + question])[0]
    dv = R2._embed([f"{t}: {c}" for t, c in chunks])
    ds = [sum(a * b for a, b in zip(qv, v)) for v in dv]
    fused = [0.0] * len(texts)
    for rk in (sorted(range(len(texts)), key=lambda i: -sc[i]), sorted(range(len(texts)), key=lambda i: -ds[i])):
        for pos, i in enumerate(rk):
            fused[i] += 1.0 / (60 + pos)
    picked, words = [], 0
    for i in sorted(range(len(texts)), key=lambda i: -fused[i]):
        n = len(texts[i].split())
        if words + n <= max_words:
            picked.append(i)
            words += n
    picked.sort()
    return "\n\n".join(f"[{chunks[i][0]}] {chunks[i][1]}" for i in picked)


def agree(a, b):
    ta, tb = " ".join(tokens(a)), " ".join(tokens(b))
    return bool(ta) and bool(tb) and (ta == tb or ta in tb or tb in ta)


def main():
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    OUT.mkdir(parents=True, exist_ok=True)
    sm = Small()
    its = items()
    path = OUT / "outputs.jsonl"
    done = {json.loads(l)["id"] for l in open(path, encoding="utf-8")} if path.exists() else set()
    with open(path, "a", encoding="utf-8") as f:
        for k, e in enumerate(its, 1):
            if e["id"] in done:
                continue
            rec = {"set": e["set"], "id": e["id"], "question": e["question"], "gold": e["gold"], "round0": e["round0"], "rounds": [],
                   "final": e["round0"], "final_nofilter": e["round0"], "gen_tokens": 0, "prompt_tokens": 0, "pages_fetched": 0, "sec": 0.0}
            if non_answer(e["round0"]):
                t0 = time.time()
                shown = {c.split("] ", 1)[1] for c in e["passage"].split("\n\n") if "] " in c}
                old_titles = list(dict.fromkeys((e.get("titles") or []) + re.findall(r"^\[([^\]\n]+)\]", e["passage"], re.M)))
                seen = set(old_titles)
                accepted = None
                for r in (1, 2):
                    rnd = {"round": r, "titles": [], "queries": [], "cautious": None, "plain": None, "passage": ""}
                    if r == 1:
                        p = second_chance(e["question"], old_titles, shown)
                    else:
                        new = []
                        for name in entities(e["question"]):
                            for t in go_titles(name):
                                if t not in seen and t not in new:
                                    new.append(t)
                        qtxt, pi, gi = sm.gen(QPROMPT.format(q=e["question"]))
                        rec["prompt_tokens"] += pi
                        rec["gen_tokens"] += gi
                        rnd["queries"] = queries(qtxt)
                        for q in rnd["queries"]:
                            for t in R._search_titles(q, 5):
                                if t not in seen and t not in new:
                                    new.append(t)
                        new = new[:8]
                        seen |= set(new)
                        rnd["titles"] = new
                        rec["pages_fetched"] += len(new)
                        p = R2.passage(e["question"], new, 1500) if new else ""
                    rnd["passage"] = p
                    if p:
                        c, pi, gi = sm.gen(CAUTIOUS.format(p=p, q=e["question"]), 40)
                        rec["prompt_tokens"] += pi
                        rec["gen_tokens"] += gi
                        rnd["cautious"] = parse(c)
                        if not non_answer(rnd["cautious"]):
                            if rec["final_nofilter"] == e["round0"]:
                                rec["final_nofilter"] = rnd["cautious"]
                            pl, pi, gi = sm.gen(PLAIN.format(p=p, q=e["question"]), 40)
                            rec["prompt_tokens"] += pi
                            rec["gen_tokens"] += gi
                            rnd["plain"] = parse(pl)
                            if agree(rnd["cautious"], rnd["plain"]):
                                accepted = rnd["cautious"]
                    rec["rounds"].append(rnd)
                    if accepted is not None:
                        rec["final"] = accepted
                        break
                rec["sec"] = round(time.time() - t0, 1)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if k % 25 == 0:
                print(f"  {k}/{len(its)}", flush=True)
    import pickle
    import os
    tmp = R2.EMB_FILE.with_suffix(".tmp")
    pickle.dump(dict(R2._EMB), open(tmp, "wb"))
    os.replace(tmp, R2.EMB_FILE)
    print("done")


if __name__ == "__main__":
    main()
