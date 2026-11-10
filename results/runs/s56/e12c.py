"""S56 follow-up 2: party-swap control for kept statements without a flippable word (docs/S56_CONTESTED_QUESTIONS_PLAN.md). Ollama on 11540 (Qwen3.8-27B).
  python -B results/runs/s56/e12c.py parties | swap | judge | report"""
import json, os, random, re, sys, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
D = ROOT / "results/runs/s56"; MODE = sys.argv[1]
S = [json.loads(l) for l in open(D / "e12_cands.jsonl", encoding="utf-8")]; DEC = json.load(open(D / "e12_decisions.json")); J = json.load(open(D / "e12_judge.json", encoding="utf-8"))
K = [s for s in S if DEC[s["id"]] is not None and not s["flipped"]]
STOP = set("the of and for with from that this these those its their his her they who which has have had was were are been being also not but".split())
cw = lambda t: {w for w in re.findall(r"[a-z0-9]+", "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)).casefold()) if len(w) > 3 and w not in STOP}
def llm(p, n):
    from vkg.llm import chat
    return str(chat("qwen3.8-27b", [{"role": "user", "content": p}], temperature=0.0, seed=0, max_tokens=n, think=False, json_mode=False, num_ctx=4096, timeout=900)).strip()
def load(f): return json.load(open(D / f, encoding="utf-8")) if (D / f).exists() else {}
def save(f, o): json.dump(o, open(D / f, "w", encoding="utf-8"), ensure_ascii=False)
JP = ('Topic page: {t}\nSentence from that page: "{s}"\n\nStatement: {a}\n\nDoes this sentence report that the party named in the statement holds this view: the same party and the same stance, '
      "not the opposite stance and not another party's view? Reply with only YES or NO.")
if MODE == "parties":
    P = load("e12c_parties.json")
    for s in S:
        if s["id"] not in P:
            P[s["id"]] = llm(f'Statement: {s["stmt"]}\n\nName the party (person, group or body) that this statement says holds the view, in at most 6 words. Reply with only that name.', 16)
            if len(P) % 50 == 0: save("e12c_parties.json", P)
    save("e12c_parties.json", P); print("parties", len(P))
elif MODE == "swap":
    P = load("e12c_parties.json"); W = load("e12c_swaps.json"); rng = random.Random(5603)
    for s in K:
        if s["id"] in W: continue
        own = cw(P[s["id"]]); pool = [P[o["id"]] for o in S if o["topic"] == s["topic"] and o["id"] != s["id"] and P[o["id"]].strip() and not (cw(P[o["id"]]) & own) and cw(P[o["id"]])]
        if not pool: W[s["id"]] = None; continue
        new = rng.choice(sorted(set(pool)))
        r = llm(f'Statement: {s["stmt"]}\n\nRewrite the statement so that the same view is attributed to {new} instead of {P[s["id"]]}. Change nothing else. Reply with only the rewritten statement.', 120)
        W[s["id"]] = {"party": new, "orig_party": P[s["id"]], "stmt": r}
    save("e12c_swaps.json", W); print("swaps", sum(1 for v in W.values() if v), "of", len(K))
elif MODE == "judge":
    W = load("e12c_swaps.json"); R = load("e12c_judge.json")
    for s in K:
        w = W.get(s["id"])
        if not w or s["id"] in R: continue
        q = s["cands"][DEC[s["id"]]]["quote"]
        usable = not (cw(w["party"]) & cw(q))
        R[s["id"]] = {"usable": usable, "yes": llm(JP.format(t=s["topic"], s=q, a=w["stmt"]), 4) if usable else None}
    save("e12c_judge.json", R); print("judged", sum(1 for v in R.values() if v["usable"]))
elif MODE == "report":
    from scipy.stats import beta
    R = load("e12c_judge.json"); up = lambda k, m: 100 * beta.ppf(0.975, k + 1, m - k) if m and k < m else 100.0
    us = [v for v in R.values() if v["usable"]]; y = sum(str(v["yes"]).upper().startswith("YES") for v in us)
    out = ["# S56 party-swap control (27B, no reviewers)\n", f"Kept statements without a flippable word: {len(K)}; swaps made {sum(1 for k in K if load('e12c_swaps.json').get(k['id']))}; usable (witness sentence names no content word of the replacement party): {len(us)}.\n",
           f"27B accepts the party-swapped statement for {y} of {len(us)} ({100*y/max(1,len(us)):.1f}%, 97.5% upper bound {up(y,len(us)):.1f}%). Rule A2 (also NO to the swap) would drop {y} of the {len(K)} ({100*y/len(K):.1f}%).\n"]
    (D / "E12c_result.md").write_text("".join(out), encoding="utf-8"); print("".join(out))
