"""S69: cross-family reviewer check (docs/S69_XFAM_PLAN.md). A reviewer of another model family (Gemma 3 12B and Mistral Nemo 12B through Ollama, temperature 0) re-reviews,
with the same instructions and the same blind inputs, a fixed random sample of rows from the review sheets of the gates, and its verdicts are compared with the consensus of the
two Claude reviewers. Not a human check (gate G12 stays open).
  review MODEL : 300 quote rows (G3, G11, G14 sheets; 100 each), 150 attribution rows (S63), 150 claim rows (S60 kept slots).   python -B results/runs/s69/xfam.py review gemma3:12b
  score        : agreement and Cohen kappa per block and model; for rows the Claude pair called misleading, how often the other family agrees.  python -B results/runs/s69/xfam.py score"""
import csv, json, os, random, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; R = ROOT / "results/runs"; D = ROOT / "results/runs/s69"
sys.stdout.reconfigure(encoding="utf-8"); os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
QI = ("You are a careful reviewer. Judge from the quote alone (the page title may serve as the subject); do not use your own knowledge of whether the answer is true.\n"
      "Question: {q}\nAnswer: {a}\nPage title: {t}\nQuote: \"{s}\"\n\n"
      "Verdicts: states = the quote itself says that this answer is the answer to this exact question; incomplete = right subject and relation and agrees with the answer, but part of the question is not in the quote; "
      "not = another subject, relation or time, not said, or something different.\nReply with exactly one word: states, incomplete or not.")
AI = ("You are a careful reviewer. Judge from the sentence alone; do not use your own knowledge.\nStatement: {q}\nSentence (from the page {t}): \"{s}\"\n\n"
      "Verdicts: states = the sentence reports that this same party holds this view; other party = the sentence gives the view to a different party; opposite = the sentence reports the opposite stance "
      "for this party; not = the sentence does not address this party holding this view (including a view stated as plain fact without saying who holds it).\nReply with exactly one of: states, other party, opposite, not.")


def rows_of(sheet, verdict, key, parts, vcol, kinds):
    out = []; K = json.load(open(key, encoding="utf-8"))
    for p in parts:
        S = {int(r["row"]): r for r in csv.DictReader(open(str(sheet).format(p=p), encoding="utf-8-sig"))}; V = {}
        for rv in "AB":
            for r in csv.DictReader(open(str(verdict).format(p=p, rv=rv), encoding="utf-8-sig")):
                V.setdefault(int(r["row"]), []).append(r[vcol].strip().casefold())
        for k in K[p]:
            if k["kind"] in kinds:
                out.append({"row": S[k["row"]], "lm": V[k["row"]], "kind": k["kind"]})
    return out


def sample():
    rng = random.Random(6901)
    g3 = rows_of(R / "s57/G3_sheet_part{p}.csv", R / "s57/G3_verdict_part{p}_{rv}.csv", R / "s57/G3_key.json", "123", "quote_verdict", {"witness", "displayed", "decoy"})
    g11 = rows_of(R / "s61/G11_sheet_part{p}.csv", R / "s61/G11_verdict_part{p}_{rv}.csv", R / "s61/G11_key.json", "123", "quote_verdict", {"witness", "displayed", "decoy"})
    g14 = rows_of(R / "s65/G14_sheet_part{p}.csv", R / "s65/G14_verdict_part{p}_{rv}.csv", R / "s65/G14_key.json", "123", "quote_verdict", {"witness", "decoy"})
    a3 = rows_of(R / "s63/A2_sheet_part{p}.csv", R / "s63/A2_verdict_part{p}_{rv}.csv", R / "s63/A2_key.json", "12", "verdict", {"witness", "displayed", "decoy"})
    c = rows_of(R / "s60/F5_sheet_part{p}.csv", R / "s60/F5_verdict_part{p}_{rv}.csv", R / "s60/F5_key.json", "123", "quote_verdict", {"kept", "decoy_question", "decoy_value"})
    S = []
    for name, rs, n in (("G3", g3, 100), ("G11", g11, 100), ("G14", g14, 100), ("attribution", a3, 150), ("claim", c, 150)):
        for r in rng.sample(rs, min(n, len(rs))):
            x = r["row"]; blk = "attribution" if name == "attribution" else ("claim" if name == "claim" else "quote")
            S.append({"set": name, "block": blk, "q": x.get("statement") or x.get("question"), "a": x.get("answer") or x.get("value", ""), "t": x.get("topic_page") or x.get("page_title"),
                      "s": x.get("sentence") or x.get("quote"), "lm": r["lm"], "kind": r["kind"]})
    return S


def norm(o, block):
    o = str(o or "").strip().lower()
    cats = ["other party", "opposite", "states", "not"] if block == "attribution" else ["incomplete", "states", "not"]
    for c in cats:
        if o.startswith(c) or re.search(r"\b" + c + r"\b", o[:30]):
            return c
    return "unparsed"


if sys.argv[1] == "review":
    import requests
    m = sys.argv[2]; S = sample(); F = D / f"xfam_{re.sub(r'[^a-z0-9]+', '_', m)}.json"
    done = json.load(open(F, encoding="utf-8")) if F.exists() else []
    for x in S[len(done):]:
        p = (AI if x["block"] == "attribution" else QI).format(q=x["q"], a=x["a"], t=x["t"], s=x["s"])
        for t in range(10):
            try:
                o = requests.post(os.environ["OLLAMA_HOST_URL"] + "/api/generate", json={"model": m, "prompt": p, "stream": False, "options": {"temperature": 0, "seed": 0, "num_predict": 8, "num_ctx": 4096}}, timeout=600).json()["response"]; break
            except Exception:
                time.sleep(20)
        done.append(norm(o, x["block"]))
        if len(done) % 50 == 0:
            json.dump(done, open(F, "w")); print(m, len(done), flush=True)
    json.dump(done, open(F, "w")); print("review done", m, len(done))
else:
    S = sample(); out = ["# S69: cross-family reviewers against the two Claude reviewers", ""]
    for f in sorted(D.glob("xfam_*.json")):
        V = json.load(open(f)); m = f.stem[5:]; out.append(f"## {m} (unparsed replies: {sum(v == 'unparsed' for v in V)})")
        for blk, cats in (("quote", ["states", "incomplete", "not"]), ("claim", ["states", "incomplete", "not"]), ("attribution", ["states", "other party", "opposite", "not"])):
            idx = [i for i, x in enumerate(S) if x["block"] == blk and x["lm"][0] == x["lm"][1]]
            if not idx:
                continue
            a = [V[i] for i in idx]; b = [S[i]["lm"][0] for i in idx]; n = len(idx); po = sum(x == y for x, y in zip(a, b)) / n
            pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats); ka = (po - pe) / (1 - pe) if pe < 1 else 1.0
            bad = [i for i in idx if S[i]["lm"][0] not in ("states", "incomplete")]
            out.append(f"- {blk}: rows where the Claude pair agree n={n}; agreement {po:.2f}, kappa {ka:.2f}; rows the pair called {'not/other party/opposite' if blk == 'attribution' else 'not'}: {len(bad)}, the other family also not 'states': {sum(V[i] != 'states' for i in bad)}; decoys judged not 'states': {sum(V[i] != 'states' for i, x in enumerate(S) if x['block'] == blk and x['kind'].startswith('decoy'))}/{sum(1 for x in S if x['block'] == blk and x['kind'].startswith('decoy'))}")
    (D / "XFAM_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
