"""S63 gates G9/G10, second test (docs/S63_G9_G10_PLAN.md): rule A3 = A2 plus an attribution question for the 27B (YES required); decoys only on sentences that hold all words of the original party. Copy of results/runs/s62/s62_a2.py. Original: rule A2 on contested topics and a review with decoys that a sentence-only reviewer can catch.
Rule A2: for a statement, the three page sentences with the highest content-word overlap (at least 3) are candidates (S56 'cands'); a candidate is the witness when the 27B says
YES to 'does this sentence report that this party holds this view', NO to the party-flipped statement (if the statement has a flippable party word), and NO to the statement with
the view moved to another party of the same topic (the S56 follow-up control; if a replacement party exists and the sentence names none of its content words). Else dropped.
  parties : 27B names the party of every statement (as S56 e12c).            python -B results/runs/s62/s62_a2.py parties
  swap    : 27B rewrites each statement with another party of its topic.       python -B results/runs/s62/s62_a2.py swap
  judge   : 27B judge on candidates (YES, flip, swap).                          python -B results/runs/s62/s62_a2.py judge
  sheet   : decisions and the blind sheet (3 parts).                             python -B results/runs/s62/s62_a2.py sheet
  unblind : counts.                                                            python -B results/runs/s62/s62_a2.py unblind"""
import csv, json, os, random, re, sys, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
D = ROOT / "results/runs/s63"; MODE = sys.argv[1]
S = [json.loads(l) for l in open(D / "e12_cands.jsonl", encoding="utf-8")]
STOP = set("the of and for with from that this these those its their his her they who which has have had was were are been being also not but".split())
cw = lambda t: {w for w in re.findall(r"[a-z0-9]+", "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)).casefold()) if len(w) > 3 and w not in STOP}
yes = lambda o: str(o or "").strip().upper().startswith("YES")
JP = ('Topic page: {t}\nSentence from that page: "{s}"\n\nStatement: {a}\n\nDoes this sentence report that the party named in the statement holds this view: the same party and the same stance, '
      "not the opposite stance and not another party's view? Reply with only YES or NO.")
AP = ('Sentence: "{s}"

Statement: {a}

The statement says that a particular party holds a view. Does the sentence itself say that this same party holds, states or argues this view? '
      "Answer NO if the sentence states the view as a plain fact without saying who holds it, if it names a different person or body, or if it only covers part of the view. Reply with only YES or NO.")
load = lambda f: json.load(open(D / f, encoding="utf-8")) if (D / f).exists() else {}
save = lambda f, o: json.dump(o, open(D / f, "w", encoding="utf-8"), ensure_ascii=False)


def llm(p, n):
    from vkg.llm import chat
    return str(chat("qwen3.8-27b", [{"role": "user", "content": p}], temperature=0.0, seed=0, max_tokens=n, think=False, json_mode=False, num_ctx=4096, timeout=900)).strip()


if MODE == "parties":
    P = load("a2_parties.json")
    for s in S:
        if s["id"] not in P:
            P[s["id"]] = llm(f'Statement: {s["stmt"]}\n\nName the party (person, group or body) that this statement says holds the view, in at most 6 words. Reply with only that name.', 16)
            if len(P) % 50 == 0:
                save("a2_parties.json", P); print("parties", len(P), flush=True)
    save("a2_parties.json", P); print("parties done", len(P))
elif MODE == "swap":
    P = load("a2_parties.json"); W = load("a2_swaps.json"); rng = random.Random(6302)
    for s in S:
        if s["id"] in W or not s["cands"]:
            continue
        own = cw(P[s["id"]]); pool = sorted({P[o["id"]] for o in S if o["topic"] == s["topic"] and o["id"] != s["id"] and P[o["id"]].strip() and cw(P[o["id"]]) and not (cw(P[o["id"]]) & own)})
        if not pool:
            W[s["id"]] = None; continue
        new = rng.choice(pool)
        W[s["id"]] = {"party": new, "orig_party": P[s["id"]], "stmt": llm(f'Statement: {s["stmt"]}\n\nRewrite the statement so that the same view is attributed to {new} instead of {P[s["id"]]}. Change nothing else. Reply with only the rewritten statement.', 120)}
        if len(W) % 50 == 0:
            save("a2_swaps.json", W); print("swaps", len(W), flush=True)
    save("a2_swaps.json", W); print("swaps done", sum(1 for v in W.values() if v))
elif MODE == "judge":
    W = load("a2_swaps.json"); J = load("a2_judge.json"); n = 0
    for s in S:
        for k, c in enumerate(s["cands"]):
            key = f"{s['id']}|{k}"
            if key in J:
                if J[key]["w"]:
                    break
                continue
            a = llm(JP.format(t=s["topic"], s=c["quote"], a=s["stmt"]), 4); f = sw = None; usable = False
            if yes(a) and s["flipped"]:
                f = llm(JP.format(t=s["topic"], s=c["quote"], a=s["flipped"]), 4)
            w = W.get(s["id"])
            if yes(a) and not yes(f) and w and w["stmt"].strip() != s["stmt"].strip():
                usable = not (cw(w["party"]) & cw(c["quote"]))
                if usable:
                    sw = llm(JP.format(t=s["topic"], s=c["quote"], a=w["stmt"]), 4)
            at = llm(AP.format(s=c["quote"], a=s["stmt"]), 4) if (yes(a) and not yes(f) and not yes(sw)) else None   # S63 rule A3: attribution question
            J[key] = {"a": a, "f": f, "sw": sw, "usable": usable, "at": at, "w": yes(a) and not yes(f) and not yes(sw) and yes(at)}
            n += 1
            if n % 200 == 0:
                save("a2_judge.json", J); print("judged", n, flush=True)
            if J[key]["w"]:
                break
    save("a2_judge.json", J); print("judge done", len(J))
elif MODE == "sheet":
    J = load("a2_judge.json"); W = load("a2_swaps.json"); P = load("a2_parties.json"); rng = random.Random(6303)
    for s in S:
        s["k"] = next((k for k in range(len(s["cands"])) if J.get(f"{s['id']}|{k}", {}).get("w")), None)
    kept = [s for s in S if s["k"] is not None]
    json.dump({s["id"]: s["k"] for s in S}, open(D / "a2_decisions.json", "w"))
    rev = kept if len(kept) <= 300 else rng.sample(kept, 300)
    rows = [dict(kind="witness", s=s, stmt=s["stmt"], quote=s["cands"][s["k"]]["quote"]) for s in rev]
    for s in rng.sample(rev, min(100, len(rev))):
        if s["k"] != 0:
            rows.append(dict(kind="displayed", s=s, stmt=s["stmt"], quote=s["cands"][0]["quote"]))
    # decoys: the view moved to another party of the topic, on a witness sentence that names the original party and none of the replacement's words
    dpool = [s for s in kept if W.get(s["id"]) and W[s["id"]]["stmt"].strip() != s["stmt"].strip() and cw(P[s["id"]]) and (cw(P[s["id"]]) <= cw(s["cands"][s["k"]]["quote"])) and not (cw(W[s["id"]]["party"]) & cw(s["cands"][s["k"]]["quote"]))]
    for s in rng.sample(dpool, min(30, len(dpool))):
        rows.append(dict(kind="decoy", s=s, stmt=W[s["id"]]["stmt"], quote=s["cands"][s["k"]]["quote"]))
    rng.shuffle(rows); key = {}
    for p in range(3):
        part = rows[p::3]
        with open(D / f"A2_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["row", "topic_page", "statement", "sentence"])
            for i, r in enumerate(part, 1):
                w.writerow([i, r["s"]["topic"], r["stmt"], r["quote"]])
        key[str(p + 1)] = [{"row": i, "id": r["s"]["id"], "kind": r["kind"]} for i, r in enumerate(part, 1)]
    json.dump(key, open(D / "A2_key.json", "w"))
    print(f"statements {len(S)} | with a candidate {sum(bool(s['cands']) for s in S)} | kept by A2 {len(kept)} ({100*len(kept)/len(S):.1f}%) | reviewed {len(rev)} | decoy pool {len(dpool)} | sheet rows {len(rows)}")
elif MODE == "unblind":
    from scipy.stats import beta
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
    K = json.load(open(D / "A2_key.json")); V = {"witness": [], "displayed": [], "decoy": []}
    for p, ks in K.items():
        vs = {}
        for rv in "AB":
            for r in csv.DictReader(open(D / f"A2_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
                vs.setdefault(int(r["row"]), []).append(r["verdict"].strip().casefold())
        for k in ks:
            assert len(vs[k["row"]]) == 2; V[k["kind"]].append(vs[k["row"]])
    MIS = lambda v: v[0] != "states" and v[1] != "states"; ATT = lambda v: v[0] in ("other party", "opposite") and v[1] in ("other party", "opposite")
    def row(name, vs):
        n = len(vs); m = sum(map(MIS, vs)); a = sum(map(ATT, vs)); s = sum(v == ["states", "states"] for v in vs)
        return f"| {name} | {n} | {m} ({100*m/max(1,n):.1f}%, upper {up(m,n):.1f}%) | {a} ({100*a/max(1,n):.1f}%, upper {up(a,n):.1f}%) | {s} ({100*s/max(1,n):.1f}%) |"
    dm = sum(map(MIS, V["decoy"])); da = sum(map(ATT, V["decoy"]))
    out = ["# S63 gates G9/G10 (second test): rule A3 on 200 new contested topics (sentence-only blind review)", "",
           f"Decoys (view moved to another party): misleading for both {dm}/{len(V['decoy'])}, judged 'other party' or 'opposite' by both {da}/{len(V['decoy'])} (valid when at least 27).", "",
           "| Sentences | n | misleading for both (G9) | other party or opposite for both (G10) | 'states' for both |", "|---|---|---|---|---|",
           row("Rule A3 witness, reviewed kept statements", V["witness"]), row("Best-overlap sentence where it differs", V["displayed"])]
    (D / "A2_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
