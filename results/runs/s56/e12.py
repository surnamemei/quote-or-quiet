"""S56: contested topics and attribution fidelity (docs/S56_CONTESTED_QUESTIONS_PLAN.md). Ollama on 11540 (Phi-4 for gen, Qwen3.8-27B for judge).
  gen    : 60 topics, Phi-4 viewpoint statements.        python -B results/runs/s56/e12.py gen
  cands  : CPU, candidate sentences and flipped statements. python -B results/runs/s56/e12.py cands
  judge  : 27B YES/NO on candidates.                      python -B results/runs/s56/e12.py judge
  sheet  : decisions and the blind sheet.                 python -B results/runs/s56/e12.py sheet
  unblind: counts.                                        python -B results/runs/s56/e12.py unblind"""
import csv, json, os, random, re, sqlite3, sys, time, unicodedata
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
D = ROOT / "results/runs/s56"; MODE = sys.argv[1]
STOP = set("a an the of in on at to for from by with and or but is are was were be been being he she it they his her their its this that these those as has have had not no also which who whom whose when where what how into than then there here after before during over under about between argue argues argued say says said claim claims claimed believe believes".split())
FLIP = [("supporters", "critics"), ("proponents", "opponents"), ("advocates", "opponents"), ("defenders", "critics"), ("in favour of", "against"), ("in favor of", "against"), ("supporters", "opponents"), ("backers", "critics")]
JP = ('Topic page: {t}\nSentence from that page: "{s}"\n\nStatement: {a}\n\nDoes this sentence report that the party named in the statement holds this view: the same party and the same stance, '
      "not the opposite stance and not another party's view? Reply with only YES or NO.")


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).casefold()


def cw(s):
    return {w for w in re.findall(r"[a-z0-9]+", fold(s)) if w not in STOP and len(w) > 2}


def flip(stmt):
    low = stmt.lower()
    for a, b in FLIP:
        for x, y in ((a, b), (b, a)):
            m = re.search(r"\b" + re.escape(x) + r"\b", low)
            if m:
                out = stmt[:m.start()] + (y.capitalize() if stmt[m.start()].isupper() else y) + stmt[m.end():]
                return out
    return None


def sentences(text):
    out = []
    for para in text.split("\n"):
        if para.lstrip().startswith(("#", "-", "*", "|", "=", ">")) or not para.strip():
            continue
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", para.strip()):
            if len(s) >= 40:
                out.append(s[:400])
    return out


def ollama(model, prompt, n, ctx=4096, fmt=None):
    for t in range(20):
        try:
            payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0, "seed": 0, "num_predict": n, "num_ctx": ctx}}
            return requests.post(os.environ["OLLAMA_HOST_URL"] + "/api/generate", json=payload, timeout=3600).json()["response"]
        except Exception as e:
            print("retry", t, repr(e)[:100], flush=True); time.sleep(30)
    raise SystemExit("gave up")


if MODE == "gen":
    sys.path.insert(0, str(ROOT))
    import no_retrieval2  # noqa: F401
    from vkg import localwiki as LW
    db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
    rows = db.execute("select title,len from t where qual='' and len>=20000 and len<=120000").fetchall()
    pat = re.compile(r"controvers|debate|criticism of|dispute|opposition to|ethics of|rights movement|gun control|capital punishment|abortion|euthanasia|nuclear power|genetically modified|climate change denial|net neutrality|vaccine", re.I)
    sel = sorted(t for t, l in rows if pat.search(t) and "List of" not in t and "," not in t)
    random.Random(5601).shuffle(sel); topics = sel[:60]
    P = ('Wikipedia article text:\n"""\n{t}\n"""\n\nUsing only the text above, state the main viewpoints that different parties hold on this topic, as 6 to 8 short statements, one per line, each starting with "- ". '
         'Each statement must name the party that holds the view (for example "Critics argue that ...", "Supporters say that ...", "The company states that ...") and must not give your own opinion or add anything that is not in the text.')
    out = []
    for tp in topics:
        text = (LW.page_text(tp) or "")[:14000]
        r = ollama("phi4", P.format(t=text), 500, 8192)
        st = [re.sub(r"^[-*\d.)\s]+", "", l).strip() for l in r.split("\n") if l.strip().startswith(("-", "*")) or re.match(r"^\d+[.)]", l.strip())]
        out += [{"topic": tp, "stmt": s} for s in st if len(s.split()) >= 5]
        print(tp.encode("ascii", "replace").decode(), len(st), flush=True)
    with open(D / "e12_stmts.jsonl", "w", encoding="utf-8") as f:
        for x in out:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print("statements", len(out))

elif MODE == "cands":
    import no_retrieval2  # noqa: F401
    from vkg import localwiki as LW
    S = [json.loads(l) for l in open(D / "e12_stmts.jsonl", encoding="utf-8")]
    cache = {}; n_c = 0
    with open(D / "e12_cands.jsonl", "w", encoding="utf-8") as f:
        for i, x in enumerate(S):
            if x["topic"] not in cache:
                cache[x["topic"]] = sentences(LW.page_text(x["topic"]) or "")
            sw = cw(x["stmt"])
            top = sorted(((len(sw & cw(s)), k) for k, s in enumerate(cache[x["topic"]])), key=lambda t: (-t[0], t[1]))[:3]
            cands = [{"quote": cache[x["topic"]][k], "overlap": ov} for ov, k in top if ov >= 3]
            x.update({"id": f"s{i}", "flipped": flip(x["stmt"]), "cands": cands}); n_c += len(cands)
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print("statements", len(S), "candidates", n_c, "flippable", sum(1 for l in open(D / "e12_cands.jsonl", encoding="utf-8") if json.loads(l)["flipped"]))

elif MODE == "judge":
    from vkg.llm import chat
    S = [json.loads(l) for l in open(D / "e12_cands.jsonl", encoding="utf-8")]
    PF = D / "e12_judge.json"; res = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    for s in S:
        for k, c in enumerate(s["cands"]):
            for tag, st in (("J", s["stmt"]), ("JS", s["flipped"])):
                key = f"{tag}|{s['id']}|{k}"
                if st and key not in res:
                    res[key] = str(chat("qwen3.8-27b", [{"role": "user", "content": JP.format(t=s["topic"], s=c["quote"], a=st)}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=600))
        if len(res) % 100 < 2:
            json.dump(res, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(res, open(PF, "w", encoding="utf-8"), ensure_ascii=False)
    print("judge done", len(res), "J YES", sum(1 for k, v in res.items() if k.startswith("J|") and v.strip().upper().startswith("YES")),
          "JS YES", sum(1 for k, v in res.items() if k.startswith("JS|") and v.strip().upper().startswith("YES")), flush=True)

elif MODE == "sheet":
    S = [json.loads(l) for l in open(D / "e12_cands.jsonl", encoding="utf-8")]; J = json.load(open(D / "e12_judge.json", encoding="utf-8"))
    yes = lambda o: str(o or "").strip().upper().startswith("YES")
    for s in S:
        s["k"] = None
        for k, c in enumerate(s["cands"]):
            if yes(J.get(f"J|{s['id']}|{k}")) and not (s["flipped"] and yes(J.get(f"JS|{s['id']}|{k}"))):
                s["k"] = k; break
    withc = [s for s in S if s["cands"]]
    kept = [s for s in S if s["k"] is not None]
    print(f"statements {len(S)} | with a candidate sentence {len(withc)} | kept by rule A {len(kept)} ({100*len(kept)/len(S):.1f}%) | no candidate or no YES: {len(S)-len(kept)}")
    json.dump({s["id"]: s["k"] for s in S}, open(D / "e12_decisions.json", "w"))
    rng = random.Random(5602); sample = rng.sample(withc, min(300, len(withc))); rows = []
    for s in sample:
        rows.append(dict(kind="displayed", s=s, stmt=s["stmt"], quote=s["cands"][0]["quote"]))
        if s["k"] not in (None, 0):
            rows.append(dict(kind="ruleA", s=s, stmt=s["stmt"], quote=s["cands"][s["k"]]["quote"]))
    flippable = [s for s in sample if s["flipped"]]
    for s in rng.sample(flippable, min(30, len(flippable))):
        rows.append(dict(kind="decoy", s=s, stmt=s["flipped"], quote=s["cands"][0]["quote"]))
    rng.shuffle(rows); P = 3; key = {}
    for p in range(P):
        part = rows[p::P]
        with open(D / f"E12_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["row", "topic_page", "statement", "sentence"])
            for i, r in enumerate(part, 1):
                w.writerow([i, r["s"]["topic"], r["stmt"], r["quote"]])
        key[str(p + 1)] = [{"row": i, "id": r["s"]["id"], "kind": r["kind"], "quote": r["quote"]} for i, r in enumerate(part, 1)]
    json.dump(key, open(D / "E12_key.json", "w"))
    print("sheet rows", len(rows), [len(rows[p::P]) for p in range(P)])

elif MODE == "unblind":
    from scipy.stats import beta
    K = json.load(open(D / "E12_key.json")); Dn = json.load(open(D / "e12_decisions.json"))
    S = {s["id"]: s for s in map(json.loads, open(D / "e12_cands.jsonl", encoding="utf-8"))}
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
    verdict = {}; decoys = []
    for p, ks in K.items():
        vs = {}
        for rv in "AB":
            for r in csv.DictReader(open(D / f"E12_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
                vs.setdefault(int(r["row"]), []).append(r["verdict"].strip().strip("'\"").casefold())
        for k in ks:
            (decoys.append(vs[k["row"]]) if k["kind"] == "decoy" else verdict.__setitem__((k["id"], k["quote"]), vs[k["row"]]))
    ids = sorted({i for (i, q) in verdict if q == S[i]["cands"][0]["quote"]})
    def vq(i, k):
        return verdict.get((i, S[i]["cands"][k]["quote"]))
    def row(name, vs):
        vs = [v for v in vs if v]; n = len(vs); mis = sum(v[0] != "states" and v[1] != "states" and v[0] == v[1] for v in vs); rev = sum(v == ["opposite", "opposite"] for v in vs); st = sum(v == ["states", "states"] for v in vs)
        return f"| {name} | {n} | {mis} ({100*mis/max(1,n):.1f}%, upper {up(mis,n):.1f}%) | {rev} ({100*rev/max(1,n):.1f}%, upper {up(rev,n):.1f}%) | {st} ({100*st/max(1,n):.1f}%) |"
    kept = [i for i in ids if Dn[i] is not None]
    out = ["# S56: attribution fidelity on contested topics (quote-only blind review)", "", f"Decoys (party flipped) misleading for both reviewers: {sum(v[0] == v[1] and v[0] != 'states' for v in decoys)}/{len(decoys)}.", "",
           "| Sentences | n | misleading for both (opposite or not) | reversed for both (opposite) | 'states' for both |", "|---|---|---|---|---|",
           row("Naive display (best-overlap sentence), sampled statements", [vq(i, 0) for i in ids]), row(f"Naive display, the {len(kept)} statements kept by rule A", [vq(i, 0) for i in kept]),
           row("Rule A witness, kept statements", [vq(i, Dn[i]) for i in kept])]
    (D / "E12_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
