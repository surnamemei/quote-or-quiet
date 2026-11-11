"""S65 gate G14 (docs/S65_G14_OTHER_MODELS_PLAN.md): the quote check placed after three models of other families on 2,001 sealed PopQA questions.
Each model answers closed-book; a draft is released when a sentence of the subject's own Wikipedia page (PopQA s_wiki_title, local snapshot) holds the answer as a gate-accepted typed span,
is a sentence with the question's numbers, and the 27B judge says YES for the answer and NO for a swapped answer of the same shape (rule R27). Otherwise the model's answer is withheld.
  draft M : the model answers (Ollama 11540).          python -B results/runs/s65/g14.py draft llama3.1:8b
  cands   : CPU, candidate sentences for all models.   OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s65/g14.py cands
  judge   : 27B.                                       python -B results/runs/s65/g14.py judge
  decide  : releases and alias-aware grading (27B).    python -B results/runs/s65/g14.py decide
  sheet   : blind sheets (quote review; truth check of gold-wrong releases).  python -B results/runs/s65/g14.py sheet
  unblind : counts.                                    python -B results/runs/s65/g14.py unblind"""
import csv, json, os, random, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20"), str(ROOT / "results/runs/s42")]
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
D = ROOT / "results/runs/s65"; MODE = sys.argv[1]
MODELS = ["llama3.1:8b", "gemma3:12b", "mistral-nemo:12b"]
tag = lambda m: re.sub(r"[^a-z0-9]+", "_", m.lower())
ITEMS = [json.loads(l) for l in open(D / "sealed/items.jsonl", encoding="utf-8")]
DP = ("Answer the question with a short answer only: a name, a place, a date or a number, with no explanation. If you are not sure, answer UNKNOWN.\nQuestion: {q}\nAnswer:")
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
ORD = "first second third fourth fifth sixth seventh eighth ninth tenth debut final last only".split()
yes = lambda o: str(o or "").strip().upper().startswith("YES")
load = lambda f: json.load(open(D / f, encoding="utf-8")) if (D / f).exists() else {}
save = lambda f, o: json.dump(o, open(D / f, "w", encoding="utf-8"), ensure_ascii=False)
clean = lambda a: re.sub(r"\s+", " ", str(a or "").strip().split("\n")[0]).strip(" .\"'*")


def window(text, i, j):
    """Sentence window around a span (as results/runs/s57/g4/g4_design.py)."""
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


def shape(a):
    return "year" if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", a) else "number" if re.fullmatch(r"[\d,.]+", a) else "phrase"


if MODE == "draft":
    import requests
    m = sys.argv[2]; F = f"drafts_{tag(m)}.json"; R = load(F)
    for n, e in enumerate(ITEMS):
        if e["id"] in R:
            continue
        for t in range(10):
            try:
                r = requests.post(os.environ["OLLAMA_HOST_URL"] + "/api/generate", json={"model": m, "prompt": DP.format(q=e["q"]), "stream": False,
                                  "options": {"temperature": 0, "seed": 0, "num_predict": 24, "num_ctx": 2048}}, timeout=600).json()["response"]
                break
            except Exception as ex:
                print("retry", t, repr(ex)[:80], flush=True); time.sleep(20)
        R[e["id"]] = clean(r)
        if n % 200 == 0:
            save(F, R); print(m, n, flush=True)
    save(F, R); print("drafts done", m, sum(1 for v in R.values() if v and "UNKNOWN" not in v.upper()), "answered of", len(R))

elif MODE == "cands":
    import no_retrieval2  # noqa: F401
    from vkg import l3_checks2 as C, l3_verify as V, localwiki as LW
    import e7_lib as L

    rng = random.Random(6501)
    out = {}
    for m in MODELS:
        R = load(f"drafts_{tag(m)}.json"); pool = {}
        for a in R.values():
            if a and "UNKNOWN" not in a.upper():
                pool.setdefault(shape(a), []).append(a)
        out[m] = {}
        for e in ITEMS:
            a = R.get(e["id"], ""); cands = []
            if a and "UNKNOWN" not in a.upper() and len(a) <= 80:
                text = LW.page_text(e["page"]) or ""
                if text:
                    h = V.doc_hash(text); need = [w for w in L.toks(e["q"]) if re.fullmatch(r"\d+(st|nd|rd|th)?", w) or w in ORD]
                    for i, j in list(V.locate(a, text))[:60]:
                        if len(cands) >= 6:
                            break
                        ok, _ = V.verify(e["q"], {"answer": a, "doc": e["page"], "doc_sha256": h, "start": i, "end": j}, LW.page_text)
                        if ok:
                            ok, _ = C.extra(e["q"], text, i, j)
                        if not ok:
                            continue
                        q = window(text, i, j); qt = set(L.toks(q))
                        if q.lstrip().startswith(("#", "-", "*", "|", "=")) or len(q) < 40 or not all(w in qt or re.sub(r"\D", "", w) in qt for w in need):
                            continue
                        sp = [x for x in pool.get(shape(a), []) if x.casefold() != a.casefold() and x.casefold() not in q.casefold()]
                        sw = rng.choice(sp) if sp else None
                        cands.append({"quote": q, "swap": sw, "j": JP.format(t=e["page"], s=q, q=e["q"], a=a), "j_swap": JP.format(t=e["page"], s=q, q=e["q"], a=sw) if sw else None})
            out[m][e["id"]] = {"answer": a, "cands": cands}
        print(m, "answered", sum(1 for v in out[m].values() if v["answer"] and "UNKNOWN" not in v["answer"].upper()), "with a candidate", sum(1 for v in out[m].values() if v["cands"]), flush=True)
    save("g14_cands.json", out)

elif MODE == "judge":
    from vkg.llm import chat
    ask = lambda p: str(chat("qwen3.8-27b", [{"role": "user", "content": p}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))
    Cd = load("g14_cands.json"); J = load("g14_judge.json"); n = 0
    for m in MODELS:
        for i, v in Cd[m].items():
            for k, c in enumerate(v["cands"]):
                key = f"{tag(m)}|{i}|{k}"
                if key in J:
                    if J[key]["w"]:
                        break
                    continue
                a = ask(c["j"]); b = ask(c["j_swap"]) if (yes(a) and c["j_swap"]) else None
                J[key] = {"a": a, "b": b, "w": yes(a) and c["j_swap"] is not None and not yes(b)}; n += 1
                if n % 200 == 0:
                    save("g14_judge.json", J); print("judged", n, flush=True)
                if J[key]["w"]:
                    break
    save("g14_judge.json", J); print("judge done", len(J))

elif MODE == "decide":
    import no_retrieval2  # noqa: F401
    from vkg.grade_judge import judge
    from vkg.grade6 import veto
    from vkg.s21_judge import aliases
    Cd = load("g14_cands.json"); J = load("g14_judge.json"); G = load("g14_grade_cache.json"); gold = {e["id"]: e["gold"] for e in ITEMS}; qq = {e["id"]: e["q"] for e in ITEMS}
    def grade(i, a):
        for g in aliases(gold[i]):
            k = f"{qq[i]}|{g}|{a}"
            if k not in G:
                G[k] = judge(qq[i], g, a)
            if G[k] == "CORRECT" and not veto(qq[i], g, a):
                return True
        return False
    dec = {}
    for m in MODELS:
        dec[m] = {}
        for i, v in Cd[m].items():
            ans_ = v["answer"] and "UNKNOWN" not in v["answer"].upper()
            w = next((k for k in range(len(v["cands"])) if J.get(f"{tag(m)}|{i}|{k}", {}).get("w")), None)
            dec[m][i] = {"answered": bool(ans_), "draft_ok": grade(i, v["answer"]) if ans_ else None, "k": w}
            if w is not None:
                dec[m][i]["quote"] = v["cands"][w]["quote"]
        rel = [i for i, d in dec[m].items() if d["k"] is not None]; ansd = [i for i, d in dec[m].items() if d["answered"]]
        print(f"{m}: answered {len(ansd)}, draft wrong (gold) {sum(not dec[m][i]['draft_ok'] for i in ansd)} | released {len(rel)} ({100*len(rel)/len(ITEMS):.1f}%), gold-wrong released {sum(not dec[m][i]['draft_ok'] for i in rel)}", flush=True)
        save("g14_grade_cache.json", G)
    save("g14_decisions.json", dec)

elif MODE == "sheet":
    dec = load("g14_decisions.json"); Cd = load("g14_cands.json"); E = {e["id"]: e for e in ITEMS}; rng = random.Random(6502)
    rows = []; trows = []
    for m in MODELS:
        rel = sorted(i for i, d in dec[m].items() if d["k"] is not None)
        rev = rel if len(rel) <= 300 else rng.sample(rel, 300)
        rows += [dict(kind="witness", m=m, i=i, a=Cd[m][i]["answer"], quote=dec[m][i]["quote"]) for i in rev]
        sw = [i for i in rev if Cd[m][i]["cands"][dec[m][i]["k"]]["swap"]]
        rows += [dict(kind="decoy", m=m, i=i, a=Cd[m][i]["cands"][dec[m][i]["k"]]["swap"], quote=dec[m][i]["quote"]) for i in rng.sample(sw, min(10, len(sw)))]
        bad = [i for i in rel if not dec[m][i]["draft_ok"]]
        trows += [dict(kind="goldwrong", m=m, i=i, a=Cd[m][i]["answer"]) for i in bad]
        good = [i for i in rel if dec[m][i]["draft_ok"]]
        trows += [dict(kind="goldright", m=m, i=i, a=Cd[m][i]["answer"]) for i in rng.sample(good, min(8, len(good)))]
        trows += [dict(kind="tdecoy", m=m, i=i, a=Cd[m][j]["answer"]) for i, j in zip(rng.sample(good, min(4, len(good))), rng.sample(good, min(4, len(good)))) if Cd[m][i]["answer"].casefold() != Cd[m][j]["answer"].casefold()]
    rng.shuffle(rows); rng.shuffle(trows); key = {}
    for p in range(3):
        part = rows[p::3]
        with open(D / f"G14_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["row", "question", "answer", "page_title", "quote"])
            for n, r in enumerate(part, 1):
                w.writerow([n, E[r["i"]]["q"], r["a"], E[r["i"]]["page"], r["quote"]])
        key[str(p + 1)] = [{"row": n, "m": r["m"], "id": r["i"], "kind": r["kind"]} for n, r in enumerate(part, 1)]
    with open(D / "G14_truth_sheet.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "subject_page"])
        for n, r in enumerate(trows, 1):
            w.writerow([n, E[r["i"]]["q"], r["a"], E[r["i"]]["page"]])
    key["truth"] = [{"row": n, "m": r["m"], "id": r["i"], "kind": r["kind"]} for n, r in enumerate(trows, 1)]
    json.dump(key, open(D / "G14_key.json", "w"))
    print("quote sheet rows", len(rows), [len(rows[p::3]) for p in range(3)], "| truth sheet rows", len(trows))

elif MODE == "unblind":
    from scipy.stats import beta
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
    K = json.load(open(D / "G14_key.json")); dec = load("g14_decisions.json")
    Q = {m: {"witness": [], "decoy": []} for m in MODELS}
    for p in ("1", "2", "3"):
        vs = {}
        for rv in "AB":
            for r in csv.DictReader(open(D / f"G14_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
                vs.setdefault(int(r["row"]), []).append(r["quote_verdict"].strip().casefold())
        for k in K[p]:
            Q[k["m"]][k["kind"]].append(vs[k["row"]])
    T = {m: {"goldwrong": [], "goldright": [], "tdecoy": []} for m in MODELS}; tv = {}
    for rv in "AB":
        for r in csv.DictReader(open(D / f"G14_truth_verdict_{rv}.csv", encoding="utf-8-sig")):
            tv.setdefault(int(r["row"]), []).append(r["true_verdict"].strip().casefold())
    for k in K["truth"]:
        T[k["m"]][k["kind"]].append(tv[k["row"]])
    out = ["# S65 gate G14: the quote check after three other models (2,001 sealed PopQA questions)", "",
           "| model | answered | released (coverage) | quotes reviewed | misleading for both | decoys caught | gold-wrong releases | errors after truth check (unless both 'right') | error upper bound, all questions |", "|---|---|---|---|---|---|---|---|---|"]
    n = len(ITEMS)
    for m in MODELS:
        rel = [i for i, d in dec[m].items() if d["k"] is not None]; ansd = sum(d["answered"] for d in dec[m].values())
        w = Q[m]["witness"]; mis = sum(v == ["not", "not"] for v in w); dc = sum(v == ["not", "not"] for v in Q[m]["decoy"])
        e = sum(v != ["right", "right"] for v in T[m]["goldwrong"])
        tdec = sum("wrong" in v for v in T[m]["tdecoy"]); gr = sum(v == ["wrong", "wrong"] for v in T[m]["goldright"])
        out.append(f"| {m} | {ansd} | {len(rel)} ({100*len(rel)/n:.1f}%) | {len(w)} | {mis} ({100*mis/max(1,len(w)):.1f}%, upper {up(mis, len(w)):.1f}%) | {dc}/{len(Q[m]['decoy'])} | {len(T[m]['goldwrong'])} | {e} | {up(e, n):.2f}% (truth decoys {tdec}/{len(T[m]['tdecoy'])}; gold-right called wrong by both {gr}/{len(T[m]['goldright'])}) |")
    (D / "G14_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
