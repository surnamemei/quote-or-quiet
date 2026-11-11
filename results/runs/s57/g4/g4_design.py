"""S57 G4 design (design data only: the 200 Mintaka dev questions and the 2,000 Mintaka test questions of S19, whose sealed test is spent).
Quote-first release rule Q1: every distinct reader answer (six readers) is a candidate, most-supported first; pages = the local retriever's five pages plus the English Wikipedia
pages named in the web results (if in the snapshot); gate-accepted typed verbatim spans of the candidate, sentence windows with the question's numbers (as in S52);
a candidate is released when the 27B judge says YES for it and NO for a swapped answer of the same shape on one of its first 6 eligible spans (rule R27).
Variants computed offline: Q1 (first candidate with a witness), Q1c (abstain if a second, different candidate also has a witness), each with and without the
S22 time-sensitivity rule. Grading by the cached alias-aware judge labels of S21 (no new grading).
  cands : CPU.            OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s57/g4/g4_design.py cands
  judge : 27B on 11540.   python -B results/runs/s57/g4/g4_design.py judge
  report: CPU.            OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s57/g4/g4_design.py report"""
import json, os, random, re, sys
from pathlib import Path
from urllib.parse import unquote
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s42")); sys.path.insert(0, str(ROOT / "results/runs/s22"))
MODE = sys.argv[1]; D = ROOT / "results/runs/s57/g4"
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
SETS = [("mintaka_dev", ROOT / "results/runs/s19/mintaka_dev_outputs.jsonl"), ("mintaka_test", ROOT / "results/runs/s19/mintaka_test_outputs.jsonl")]
if os.environ.get("G4SET") == "s68":                      # S68 second sealed test of rule Q2 (docs/S68_G4B_PLAN.md)
    SETS = [("m68", ROOT / "results/runs/s68/run_fsm/m68_outputs.jsonl")]
elif os.environ.get("G4SET") == "s58":                      # S58 sealed test of rule Q2 (docs/S58_G4_PLAN.md)
    SETS = [("m58", ROOT / "results/runs/s58/run_fsm/m58_outputs.jsonl")]
elif os.environ.get("G4SET") == "s39":                      # second design check: the 600 Mintaka design items of S39
    SETS = [("s39_mintaka", ROOT / "results/runs/s57/g4/s39_mintaka_outputs.jsonl")]
yes = lambda o: str(o or "").strip().upper().startswith("YES")


def shape(a):
    a = str(a).strip()
    return "year" if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", a) else "number" if re.fullmatch(r"[\d,.]+", a) else "phrase"


def window(text, i, j):
    a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
    ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
    b = min(ends) if ends else len(text)
    while a < i and text[a].isspace():
        a += 1
    while b > j and text[b - 1].isspace():
        b -= 1
    if b - a > 300:
        a2 = max(a, min(i - 120, b - 300)); b2 = min(b, a2 + 300)
        if j > b2:
            b2 = j; a2 = max(a, b2 - 300)
        a, b = a2, b2
    return text[a:b]


if MODE == "cands":
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    import no_retrieval2  # noqa: F401
    from vkg import l3_checks2 as C, l3_verify as V, localwiki as LW, s17_eval as S
    from vkg.s12_run import agree
    from vkg.s14_eval import ans
    import e7_lib as L
    rng = random.Random({"s58": 5801, "s68": 6802}.get(os.environ.get("G4SET"), 5720))
    for name, f in SETS:
        rows = [json.loads(l) for l in open(f, encoding="utf-8")]
        pool = {}
        for r in rows:
            for k in S.ORDER:
                if ans(r[k]):
                    pool.setdefault(shape(r[k]), []).append(str(r[k]))
        out = open(D / f"{name}_cands.jsonl", "w", encoding="utf-8")
        for n, r in enumerate(rows):
            cs = []
            for k in S.ORDER:
                a = r[k]
                if ans(a) and not any(agree(str(a), c["answer"]) for c in cs):
                    cs.append({"answer": str(a).strip(), "support": S.support(r, a)})
            cs.sort(key=lambda c: -c["support"])
            webw = [unquote(u.split("/wiki/", 1)[1]).replace("_", " ").split("#")[0] for u in eval(r["web_urls"]) if "en.wikipedia.org/wiki/" in u] if isinstance(r["web_urls"], str) else \
                   [unquote(u.split("/wiki/", 1)[1]).replace("_", " ").split("#")[0] for u in r["web_urls"] if "en.wikipedia.org/wiki/" in u]
            titles = list(dict.fromkeys(list(eval(r["wiki_titles"]) if isinstance(r["wiki_titles"], str) else r["wiki_titles"]) + webw))
            texts = {t: LW.page_text(t) for t in titles}
            need = [w for w in L.toks(r["question"]) if re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD]
            for c in cs:
                c["spans"] = []
                for t, text in texts.items():
                    if not text or len(c["spans"]) >= 6:
                        continue
                    h = V.doc_hash(text); tried = 0
                    for i, j in V.locate(c["answer"], text):
                        if len(c["spans"]) >= 6 or tried >= 200:
                            break
                        tried += 1
                        ok, _ = V.verify(r["question"], {"answer": c["answer"], "doc": t, "doc_sha256": h, "start": i, "end": j}, LW.page_text)
                        if ok:
                            ok, _ = C.extra(r["question"], text, i, j)
                        if not ok:
                            continue
                        q = window(text, i, j); qt = set(L.toks(q))
                        if q.lstrip().startswith(("#", "-", "*", "|", "=")) or len(q) < 40 or not all(w in qt or re.sub(r"\D", "", w) in qt for w in need):
                            continue
                        sp = [a for a in pool[shape(c["answer"])] if not agree(a, c["answer"]) and a.casefold() not in q.casefold()]
                        c["spans"].append({"doc": t, "quote": q, "swap": rng.choice(sp) if sp else None})
            out.write(json.dumps({"set": name, "id": r["id"], "question": r["question"], "gold": r["gold"], "stratum": r.get("stratum"), "cands": cs}, ensure_ascii=False) + "\n")
            if n % 200 == 0:
                print(name, n, flush=True)
        out.close()
    print("cands done")

elif MODE == "judge":
    from vkg.llm import chat
    ask = lambda p: str(chat("qwen3.8-27b", [{"role": "user", "content": p}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))
    PF = D / "g4_judge.json"; J = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    n = 0
    for name, _ in SETS:
        for r in map(json.loads, open(D / f"{name}_cands.jsonl", encoding="utf-8")):
            for ci, c in enumerate(r["cands"]):
                for si, s in enumerate(c["spans"]):
                    key = f"{r['id']}|{ci}|{si}"
                    if key in J:
                        if J[key]["w"]:
                            break
                        continue
                    a = ask(JP.format(t=s["doc"], s=s["quote"], q=r["question"], a=c["answer"])); b = None
                    if yes(a) and s["swap"]:
                        b = ask(JP.format(t=s["doc"], s=s["quote"], q=r["question"], a=s["swap"]))
                    J[key] = {"a": a, "b": b, "w": yes(a) and not yes(b)}
                    n += 1
                    if n % 200 == 0:
                        json.dump(J, open(PF, "w", encoding="utf-8")); print(name, n, flush=True)
                    if J[key]["w"]:
                        break
    json.dump(J, open(PF, "w", encoding="utf-8")); print("judge done", len(J), flush=True)

elif MODE == "report":
    import no_retrieval2  # noqa: F401
    from temporal import time_sensitive
    from abstain_dev import grade
    J = json.load(open(D / "g4_judge.json", encoding="utf-8"))
    from scipy.stats import beta
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
    out = ["# S57 G4 design: quote-first release rule on Mintaka design data (gold-relative, cached grades)", "",
           "| set | variant | questions | released | coverage | wrong (gold) | ungraded | SER | upper |", "|---|---|---|---|---|---|---|---|---|"]
    for name, _ in SETS:
        R = [json.loads(l) for l in open(D / f"{name}_cands.jsonl", encoding="utf-8")]
        for var in ("Q1", "Q1c", "Q1+T", "Q1c+T"):
            rel = wr = un = 0
            for r in R:
                w = [ci for ci, c in enumerate(r["cands"]) if any(J.get(f"{r['id']}|{ci}|{si}", {}).get("w") for si in range(len(c["spans"])))]
                if not w or ("c" in var.split("+")[0] and len(w) > 1) or ("+T" in var and time_sensitive(r["question"])):
                    continue
                rel += 1; g = grade(r["question"], r["gold"], r["cands"][w[0]]["answer"])
                wr += g is False; un += g == "?"
            out.append(f"| {name} | {var} | {len(R)} | {rel} | {100*rel/len(R):.1f}% | {wr} | {un} | {100*wr/len(R):.2f}% | {up(wr, len(R)):.2f}% |")
    (D / "G4_design_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
