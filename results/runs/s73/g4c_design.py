"""S73 G4 redesign (design data only: the 1,500 NQ-open questions of S68, whose sealed test is spent). Rule Q3 = rule Q2 with the typed-span step replaced by
phrase extraction, for free-phrase answers:
  1. phrases: every reader answer of at most 6 tokens as it is; from longer answers every contiguous sub-phrase of 1 to 8 tokens, trimmed of stop words
     at both ends, that has a content token not in the question;
  2. support of a phrase = number of the six readers whose answer contains it (token-wise); phrases with support < 2 are dropped;
  3. a phrase needs a verbatim occurrence (case-insensitive, white space collapsed) in a sentence window of a retrieved Wikipedia page (local retriever's
     pages plus the pages named in the web results), the window at least 40 characters, not a list or table line, and containing the question's numbers and ordinals;
     only maximal phrases are kept (a phrase inside another found phrase is dropped); at most 4 phrases per question, most support then longest first;
  4. witness: the 27B judge says YES for the phrase and NO for a swapped phrase of the same shape (rule R27), on one of the first 4 windows;
  5. release when every two witnessed phrases occur together in one reader answer and the question is not time-sensitive; the released answer is the witnessed phrase
     with the most support (then the longest).
  cands : CPU.          OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s73/g4c_design.py cands
  judge : 27B on 11540. python -B results/runs/s73/g4c_design.py judge
  decide: 27B on 11540 (gold grading, cached). python -B results/runs/s73/g4c_design.py decide"""
import json, os, random, re, sys
from pathlib import Path
from urllib.parse import unquote
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20"), str(ROOT / "results/runs/s22"), str(ROOT / "results/runs/s42"), str(ROOT / "results/runs/s57/g4")]
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
MODE = sys.argv[1]; D = ROOT / "results/runs/s73"
SRC = Path(os.environ.get("G4C_SRC", ROOT / "results/runs/s68/run_fsm/m68_outputs.jsonl")); NAME = os.environ.get("G4C_NAME", "d68")
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
STOP = set("a an the of in on at to for by with from and or is was were are be been it its this that as into during about over after before than which who whom whose "
           "what when where why how did does do has have had he she they his her their there here also not no yes answer".split())
READERS = ("web_plain", "web_cautious", "wiki_plain", "wiki_cautious", "combo_plain", "combo_cautious")
TPLUS = re.compile(r"\b(this|last|next)\s+(year|season|month|week)\b|\brecent(ly)?\b|\bupcoming\b", re.I)
if os.environ.get("G4C_JUDGE") == "v2":             # S73 variant: the question read as a person would mean it (NQ questions are loosely worded); swap test unchanged
    JP = ('Question, as a person typed it into a search engine: {q}\nProposed answer: {a}\n\nPage title: {t}\nSentence from that page: "{s}"\n\n'
          "Reading the question the way the person most likely meant it, does this sentence show that the proposed answer is a correct answer to it? "
          "A sentence about a different subject, a different event, or that only mentions the answer without saying it answers the question does not count. Reply with only YES or NO.")
    JNAME = NAME + "v2"
else:
    JNAME = NAME
yes = lambda o: str(o or "").strip().upper().startswith("YES")
TOK = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|[A-Za-z0-9][A-Za-z0-9'’.\-:]*[A-Za-z0-9]|[A-Za-z0-9]")   # 195,000 stays one token
norm = lambda s: re.sub(r"\s+", " ", s).strip().casefold()


def toks(s):
    return re.findall(r"[a-z0-9]+", norm(s))


def contains(big, small):
    a, b = " " + " ".join(toks(big)) + " ", " " + " ".join(toks(small)) + " "
    return len(b) > 2 and b in a


def reader_answer(x):
    x = str(x or "").strip()
    if x.startswith("{"):
        try:
            x = str(json.loads(x).get("answer", ""))
        except Exception:
            pass
    return "" if norm(x) in ("", "unknown", "none", "n/a") else x


def phrases(ans, qtok):
    w = TOK.findall(ans)
    if not w:
        return []
    if len(w) <= 6:
        out = [" ".join(w)]
    else:
        out = []
        for i in range(len(w)):
            for j in range(i + 1, min(len(w), i + 8) + 1):
                out.append(" ".join(w[i:j]))
    res = []
    for p in out:
        t = p.split()
        while t and t[0].casefold() in STOP:
            t = t[1:]
        while t and t[-1].casefold() in STOP:
            t = t[:-1]
        if not t:
            continue
        p = " ".join(t)
        if any(x not in qtok and x not in STOP for x in toks(p)):
            res.append(p)
    return list(dict.fromkeys(res))


def shape(a):
    a = str(a).strip()
    return "year" if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", a) else "number" if re.fullmatch(r"[\d,.]+", a) else "date" if re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", a) else \
        "short" if len(a.split()) <= 2 else "phrase"


if MODE == "cands":
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    import no_retrieval2  # noqa: F401
    from vkg import localwiki as LW
    from g4_design import window
    rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
    rng = random.Random(7301); pool = {}
    for r in rows:
        for k in READERS:
            a = reader_answer(r[k])
            if a and len(a.split()) <= 6:
                pool.setdefault(shape(a), []).append(a)
    out = open(D / f"{NAME}_cands.jsonl", "w", encoding="utf-8")
    for n, r in enumerate(rows):
        qtok = set(toks(r["question"])); ans = [reader_answer(r[k]) for k in READERS]
        cand = {}
        for a in ans:
            for p in phrases(a, qtok):
                s = sum(bool(b) and contains(b, p) for b in ans)
                if s >= 2:
                    cand[p] = s
        urls = eval(r["web_urls"]) if isinstance(r["web_urls"], str) else r["web_urls"]
        webw = [unquote(u.split("/wiki/", 1)[1]).replace("_", " ").split("#")[0] for u in urls if "en.wikipedia.org/wiki/" in u]
        titles = list(dict.fromkeys(list(eval(r["wiki_titles"]) if isinstance(r["wiki_titles"], str) else r["wiki_titles"]) + webw))
        texts = {t: LW.page_text(t) for t in titles}; texts = {t: x for t, x in texts.items() if x}
        need = [w for w in toks(r["question"]) if re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD]
        found = {}
        for p in sorted(cand, key=lambda p: (-cand[p], -len(p))):
            pat = re.compile(r"(?<![A-Za-z0-9])" + r"\s+".join(map(re.escape, p.split())) + r"(?![A-Za-z0-9])", re.I)
            wins = []
            for t, text in texts.items():
                for m in pat.finditer(text):
                    q = window(text, m.start(), m.end()); qt = set(toks(q))
                    if q.lstrip().startswith(("#", "-", "*", "|", "=", "{")) or len(q) < 40 or not all(w in qt or re.sub(r"\D", "", w) in qt for w in need):
                        continue
                    wins.append({"doc": t, "quote": q, "match": m.group(0)})
                    if len(wins) >= 4:
                        break
                if len(wins) >= 4:
                    break
            if wins:
                found[p] = wins
        keep = [p for p in found if not any(p != o and contains(o, p) for o in found)]   # maximal phrases only
        keep = sorted(keep, key=lambda p: (-cand[p], -len(p)))[:4]
        cs = []
        for p in keep:
            sp = [a for a in pool.get(shape(p), []) if not contains(a, p) and not contains(p, a) and all(norm(a) not in norm(w["quote"]) for w in found[p])]
            cs.append({"answer": p, "support": cand[p], "spans": [dict(w, swap=rng.choice(sp) if sp else None) for w in found[p]]})
        out.write(json.dumps({"set": NAME, "id": r["id"], "question": r["question"], "gold": r["gold"], "answers": [a for a in ans if a], "cands": cs}, ensure_ascii=False) + "\n")
        if n % 100 == 0:
            print(n, flush=True)
    out.close(); print("cands done")

elif MODE == "judge":
    from vkg.llm import chat
    ask = lambda p: str(chat("qwen3.8-27b", [{"role": "user", "content": p}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))
    PF = D / f"{JNAME}_judge.json"; J = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    n = 0
    for r in map(json.loads, open(D / f"{NAME}_cands.jsonl", encoding="utf-8")):
        for ci, c in enumerate(r["cands"]):
            for si, s in enumerate(c["spans"]):
                key = f"{r['id']}|{c['answer']}|{si}"
                if key in J:
                    if J[key]["w"]:
                        break
                    continue
                a = ask(JP.format(t=s["doc"], s=s["quote"], q=r["question"], a=c["answer"])); b = None
                if yes(a) and s["swap"]:
                    b = ask(JP.format(t=s["doc"], s=s["quote"], q=r["question"], a=s["swap"]))
                J[key] = {"a": a, "b": b, "w": yes(a) and bool(s["swap"]) and not yes(b)}
                n += 1
                if n % 200 == 0:
                    json.dump(J, open(PF, "w", encoding="utf-8")); print(n, flush=True)
                if J[key]["w"]:
                    break
    json.dump(J, open(PF, "w", encoding="utf-8")); print("judge done", len(J), flush=True)

elif MODE == "decide":
    import no_retrieval2  # noqa: F401
    from temporal import time_sensitive
    from vkg.grade_judge import judge
    from vkg.grade6 import veto
    from vkg.s21_judge import aliases
    from scipy.stats import beta
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if k < n else 100.0
    J = json.load(open(D / f"{JNAME}_judge.json", encoding="utf-8"))
    CF = D / f"{NAME}_grade_cache.json"; C = json.load(open(CF, encoding="utf-8")) if CF.exists() else {}
    old = ROOT / "results/runs/s68/s68_grade_cache.json"
    if old.exists() and NAME == "d68":
        C = {**json.load(open(old, encoding="utf-8")), **C}
    out = []
    for r in map(json.loads, open(D / f"{NAME}_cands.jsonl", encoding="utf-8")):
        gold = eval(r["gold"]) if isinstance(r["gold"], str) else r["gold"]
        w = [c for c in r["cands"] if any(J.get(f"{r['id']}|{c['answer']}|{si}", {}).get("w") for si in range(len(c["spans"])))]
        why = "released"
        if not w: why = "no witness"
        elif not all(any(contains(x, a["answer"]) and contains(x, b["answer"]) for x in r["answers"]) for a in w for b in w): why = "conflict"   # compatible: one reader answer holds both
        elif time_sensitive(r["question"]) or TPLUS.search(r["question"]): why = "time-sensitive"
        rec = {"id": r["id"], "why": why}
        if why == "released":
            c = max(w, key=lambda c: (c["support"], len(c["answer"]))); si = next(si for si in range(len(c["spans"])) if J.get(f"{r['id']}|{c['answer']}|{si}", {}).get("w")); sp = c["spans"][si]
            ok = False
            for g in aliases(gold):
                k = f"{r['question']}|{g}|{c['answer']}"
                if k not in C:
                    C[k] = judge(r["question"], g, c["answer"])
                if C[k] == "CORRECT" and not veto(r["question"], g, c["answer"]):
                    ok = True; break
            rec.update({"answer": c["answer"], "doc": sp["doc"], "quote": sp["quote"], "gold_ok": ok})
        out.append(rec)
    json.dump(C, open(CF, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(out, open(D / f"{JNAME}_decisions.json", "w", encoding="utf-8"), ensure_ascii=False)
    from collections import Counter
    N = len(out); rel = [x for x in out if x["why"] == "released"]; wr = sum(not x["gold_ok"] for x in rel)
    s = (f"{JNAME}: reasons {dict(Counter(x['why'] for x in out))} | released {len(rel)} of {N}, coverage {100*len(rel)/N:.1f}% | gold-wrong {wr} "
         f"({100*wr/N:.2f}% of questions, {100*wr/max(1,len(rel)):.1f}% of releases; upper bound if all were errors {up(wr, N):.2f}%)")
    (D / f"G4C_{JNAME}_result.md").write_text("# S73 rule Q3 on design data\n\n" + s + "\n", encoding="utf-8"); print(s)
