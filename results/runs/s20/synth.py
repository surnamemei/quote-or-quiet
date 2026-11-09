"""S20 Step B (docs/S20_PLAN.md section 3; pre-registration docs/S20_STEPB_PREREG.md): synthetic-page test of C1, C2 and D3.
Items: correct G3 V1-V5 releases on the used sets (cases_v2.json) whose released span is a year or a full date and whose question
falls in one of the relation families of LEX below (question relation from frames.question_relation).
Pages: the item's FineWiki page with k in {1, 2, 4} inserted sentences next to the true sentence, of two kinds:
  rel: same entity (page title), a NEIGHBOURING relation, a fresh value of the same format ("X was baptised in 1851.")
  ent: ANOTHER entity (title of another item's page in the same family), the SAME relation, a fresh value ("Y was born in 1851.")
plus k = 0 (the untouched page). Inserted values differ from gold, from each other and from every string on the page.
The phrase lexicon LEX was written for natural wording, not copied from the D3 trigger lists; the overlap is measured and reported.
usage:  python -B results/runs/s20/synth.py build      (CPU, no model: writes synth_items.json)
        python -B results/runs/s20/synth.py gen        (GPU lock: 4B plain+cautious via podgen :18000, Phi-4 cautious via Ollama :11435)
        python -B results/runs/s20/synth.py parse      (GPU lock: D3 v2 parsers on released contexts, Phi-4)
        python -B results/runs/s20/synth.py score"""
import json
import os
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
ITEMS = HERE / "synth_items.json"
GEN = HERE / "synth_gen.json"
SEED = 2020
N_MAX = 300
KS = (1, 2, 4)

# family: (true-relation phrases, neighbouring-relation phrases). {E} = entity, {V} = "in 1851" / "on 3 May 1851".
LEX = {
    "born": (["{E} was born {V}."],
             ["{E} was baptised {V}.", "{E}'s family settled in the town {V}.", "{E} was first listed in a parish register {V}."]),
    "died": (["{E} died {V}."],
             ["{E} was laid to rest {V}.", "{E} withdrew from public life {V}.", "{E} fell seriously ill {V}."]),
    "founded": (["{E} was founded {V}."],
                ["{E} took its present name {V}.", "{E} moved to new premises {V}.", "{E} was granted a royal charter {V}."]),
    "opened": (["{E} opened to the public {V}."],
               ["Work on {E} began {V}.", "Plans for {E} were first put forward {V}.", "{E} closed for a major renovation {V}."]),
    "construction": (["Construction of {E} was completed {V}."],
                     ["{E} was first proposed {V}.", "{E} was listed as a protected building {V}.", "{E} was restored {V}."]),
    "released": (["{E} was released {V}."],
                 ["{E} was first announced {V}.", "Recording of {E} was finished {V}.", "{E} was reissued {V}."]),
    "award": (["{E} received the award {V}."],
              ["{E} was put forward for the award {V}.", "{E} was named on the shortlist {V}.", "{E} presented the award to a colleague {V}."]),
    "elected": (["{E} was elected {V}."],
                ["{E} first stood as a candidate {V}.", "{E} lost the seat {V}.", "{E} was nominated by the party {V}."]),
    "appointed": (["{E} was appointed to the post {V}."],
                  ["{E} stepped down from the post {V}.", "{E} was considered for the post {V}.", "{E} took up an earlier post {V}."]),
    "married": (["{E} married {V}."],
                ["{E} became engaged {V}.", "{E} separated from their spouse {V}.", "{E} met their future spouse {V}."]),
    "joined": (["{E} joined the organisation {V}."],
               ["{E} left the organisation {V}.", "{E} first applied to the organisation {V}.", "{E} was expelled from the organisation {V}."]),
    "debut": (["{E} made their debut {V}."],
              ["{E} signed a first contract {V}.", "{E} played a final match {V}.", "{E} was first selected for a squad {V}."]),
    "educated": (["{E} graduated {V}."],
                 ["{E} enrolled {V}.", "{E} began teaching at the school {V}.", "{E} was awarded an honorary degree {V}."]),
    "renamed": (["{E} was renamed {V}."],
                ["{E} was founded {V}.", "{E} merged with a neighbour {V}.", "{E} was dissolved {V}."]),
}
MONTHS = "January February March April May June July August September October November December".split()
RE_YEAR = re.compile(r"^\d{4}$")
RE_DMY = re.compile(r"^(\d{1,2}) (" + "|".join(MONTHS) + r") (\d{4})$")
RE_MDY = re.compile(r"^(" + "|".join(MONTHS) + r") (\d{1,2}), (\d{4})$")


def fmt_of(span):
    s = span.strip()
    if RE_YEAR.match(s) and 1000 <= int(s) <= 2030:
        return "year"
    if RE_DMY.match(s):
        return "dmy"
    if RE_MDY.match(s):
        return "mdy"
    return None


def fresh_value(fmt, gold_span, rng, avoid, text):
    y0 = int(re.findall(r"\d{4}", gold_span)[0])
    for _ in range(200):
        y = y0 + rng.choice([-1, 1]) * rng.randint(2, 40)
        if y > 2024:
            continue
        if fmt == "year":
            v, ph = str(y), f"in {y}"
        else:
            d, m = rng.randint(1, 28), rng.choice(MONTHS)
            v = f"{d} {m} {y}" if fmt == "dmy" else f"{m} {d}, {y}"
            ph = f"on {v}"
        if v not in avoid and v not in text and str(y) not in avoid:
            return v, ph
    raise RuntimeError("no fresh value")


def build():
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, str(HERE))
    import no_retrieval2  # noqa: F401
    import frames as F0
    from vkg import l3_checks2 as C, localwiki as LW
    cases = [x for x in json.loads((HERE / "cases_v2.json").read_text(encoding="utf-8")) if x["graded"] is True]
    pool = []
    for x in cases:
        fam = F0.question_relation(x["q"])
        if fam not in LEX:
            continue
        rel, rec = C.release2(x["q"], x["rel"], [x["ctx"].split(") ", 1)[0][len("(page: "):]], LW.page_text)
        if not rel:
            continue
        fmt = fmt_of(rec["span"])
        if not fmt:
            continue
        core = re.sub(r"\s*\(.*?\)$", "", rec["doc"]).split(",")[0].strip().casefold()
        if len(core) < 4 or core not in x["q"].casefold():   # the page must be about the question's entity, so "{E}" = page title is coherent
            continue
        pool.append({"set": x["set"], "id": x["id"], "q": x["q"], "gold": x["gold"], "fam": fam, "fmt": fmt, "doc": rec["doc"],
                     "start": rec["start"], "end": rec["end"], "span": rec["span"]})
    rng = random.Random(SEED)
    rng.shuffle(pool)
    seen, items = set(), []
    for p in pool:                       # one item per page, so an inserted value never leaks into another item's page
        if p["doc"] in seen:
            continue
        seen.add(p["doc"])
        items.append(p)
    items = items[:N_MAX]
    by_fam = {}
    for it in items:
        by_fam.setdefault(it["fam"], []).append(it["doc"])
    out = []
    skipped = 0
    for it in items:
        try:
            out.append(make(it, LW, F0, by_fam, seen, rng))
        except RuntimeError:          # page already holds every nearby year: no clean fresh value, item skipped
            skipped += 1
    print("skipped (no fresh value):", skipped)
    finish(out, F0)


def make(it, LW, F0, by_fam, seen, rng):
    if True:
        text = LW.page_text(it["doc"])
        i, j = it["start"], it["end"]
        a, b = F0.sentence_of(text, i, j)
        m = re.match(r"[.!?\"')\]]*", text[b:])          # insert after the sentence's closing punctuation
        b += m.end()
        others = [d for d in by_fam[it["fam"]] if d != it["doc"]] or [d for d in seen if d != it["doc"]]
        conds = [{"kind": "none", "k": 0, "inserted": [], "text": text, "span_at": i}]
        for kind in ("rel", "ent"):
            avoid = {it["span"]}
            sents = []
            for n in range(max(KS)):
                v, ph = fresh_value(it["fmt"], it["span"], rng, avoid, text)
                avoid.add(v)
                if kind == "rel":
                    tpl = LEX[it["fam"]][1][n % len(LEX[it["fam"]][1])]
                    e = it["doc"]
                else:
                    tpl = LEX[it["fam"]][0][0]
                    e = rng.choice(others)
                sents.append({"value": v, "sentence": tpl.format(E=e, V=ph)})
            for k in KS:
                before = [s["sentence"] for n, s in enumerate(sents[:k]) if n % 2 == 1]
                after = [s["sentence"] for n, s in enumerate(sents[:k]) if n % 2 == 0]
                sep = "\n" if text[b:b + 1] == "\n" and not text[a:b].rstrip().endswith(".") else " "   # list/infobox line: own lines
                pre = text[:a] + "".join(s + sep for s in before)
                new = pre + text[a:b] + "".join(sep + s for s in after) + text[b:]
                conds.append({"kind": kind, "k": k, "inserted": sents[:k], "text": new, "span_at": i + len(pre) - a})
        for c in conds:
            t, s = c["text"], c["span_at"]
            lo = max(0, s - 1500)
            lo = t.rfind("\n", 0, lo) + 1 if t.rfind("\n", 0, lo) > 0 else lo
            c["passage"] = f"# {it['doc']}\n" + t[lo:s + 1500]
        return {**it, "conds": conds}


def finish(out, F0):
    ITEMS.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    import collections
    print(len(out), "items;", dict(collections.Counter(x["fam"] for x in out)), dict(collections.Counter(x["fmt"] for x in out)))
    # overlap of the inserted wording with D3 v1's competitor triggers (reported, to show the test is not built from D3's lists)
    import frames_v1 as F1
    hit = tot = 0
    for it in out:
        for c in it["conds"]:
            if c["kind"] == "rel" and c["k"] == max(KS):
                for s in c["inserted"]:
                    tot += 1
                    hit += any(F1.CS[r].search(s["sentence"]) for r in F0.REL[it["fam"]][2])
    print(f"relation-distractor sentences containing a D3 v1 competitor trigger of the asked relation: {hit}/{tot}")


def gen():
    import requests
    from concurrent.futures import ThreadPoolExecutor
    sys.path.insert(0, os.getcwd())
    from vkg.lite import CAUTIOUS, PLAIN, parse
    items = json.loads(ITEMS.read_text(encoding="utf-8"))
    G = json.loads(GEN.read_text(encoding="utf-8")) if GEN.exists() else {}
    jobs = [(f"{it['id']}|{c['kind']}|{c['k']}", it["q"], c["passage"]) for it in items for c in it["conds"]]
    for key, tmpl in (("4b_plain", PLAIN), ("4b_cautious", CAUTIOUS)):
        if key in G:
            continue
        cont = [tmpl.format(p=p, q=q) for _, q, p in jobs]
        outs = []
        for s in range(0, len(cont), 200):
            r = requests.post("http://127.0.0.1:18000/gen", json={"contents": cont[s:s + 200], "max_new": 40}, timeout=7200).json()
            if "error" in r:
                raise RuntimeError(r["error"])
            outs += [o["text"] for o in r["outs"]]
            print(key, s + len(cont[s:s + 200]), flush=True)
        G[key] = {jid: parse(o) for (jid, _, _), o in zip(jobs, outs)}
        GEN.write_text(json.dumps(G, ensure_ascii=False), encoding="utf-8")
    requests.post("http://127.0.0.1:18000/unload", json={}, timeout=120)
    if "phi4_cautious" not in G:
        def one(x):
            jid, q, p = x
            for t in range(5):
                try:
                    r = requests.post("http://127.0.0.1:11435/api/chat", json={
                        "model": "phi4", "messages": [{"role": "user", "content": CAUTIOUS.format(p=p, q=q)}], "stream": False,
                        "keep_alive": "10m", "options": {"temperature": 0, "seed": 0, "num_predict": 40, "num_ctx": 8192}}, timeout=600)
                    return jid, parse(r.json()["message"]["content"])
                except Exception:  # noqa: BLE001
                    import time
                    time.sleep(5 * (t + 1))
            return jid, None
        with ThreadPoolExecutor(4) as ex:
            G["phi4_cautious"] = dict(ex.map(one, jobs))
        GEN.write_text(json.dumps(G, ensure_ascii=False), encoding="utf-8")
    print("gen done", {k: len(v) for k, v in G.items()})


def _released(it, c, answer):
    sys.path.insert(0, os.getcwd())
    from vkg import l3_checks2 as C
    if not answer:
        return None, None
    rel, rec = C.release2(it["q"], answer, [it["doc"]], lambda d: c["text"] if d == it["doc"] else "")
    return rel, rec


def outcome(rel, it, c, agree):
    if rel is None:
        return "abstain"
    if any(agree(str(rel), g) for g in it["gold"]) or agree(str(rel), it["span"]):
        return "correct"
    if any(agree(str(rel), s["value"]) for s in c["inserted"]):
        return "inserted"
    return "other"


def parse_ctx():
    """D3 v2 parsers on the contexts of 4B-cautious releases (Phi-4, constrained JSON), cached in parse_v2_cache.jsonl."""
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, str(HERE))
    import no_retrieval2  # noqa: F401
    import parse_v2 as P
    from vkg import localwiki  # noqa: F401
    items = json.loads(ITEMS.read_text(encoding="utf-8"))
    G = json.loads(GEN.read_text(encoding="utf-8"))
    X = []
    for it in items:
        for c in it["conds"]:
            a = G["4b_cautious"].get(f"{it['id']}|{c['kind']}|{c['k']}")
            rel, rec = _released(it, c, a)
            if rel:
                X.append({"set": "synth", "q": it["q"], "ctx": f"(page: {it['doc']}) " + P.context(c["text"], rec["start"], rec["end"])})
    P.CASES_OVERRIDE = X
    tmp = HERE / "synth_cases_v2.json"
    tmp.write_text(json.dumps(X, ensure_ascii=False), encoding="utf-8")
    P.CASES = tmp
    P.parse([])


def score():
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, str(HERE))
    import no_retrieval2  # noqa: F401
    import frames_v1 as F1
    import parse_v2 as P
    from vkg.s12_run import agree
    from vkg.s14_eval import ans
    items = json.loads(ITEMS.read_text(encoding="utf-8"))
    G = json.loads(GEN.read_text(encoding="utf-8"))
    cache = P._load_cache()
    R = []
    for it in items:
        for c in it["conds"]:
            jid = f"{it['id']}|{c['kind']}|{c['k']}"
            row = {"id": it["id"], "fam": it["fam"], "kind": c["kind"], "k": c["k"]}
            for rd in ("4b_plain", "4b_cautious", "phi4_cautious"):
                a = G[rd].get(jid)
                a = a if a and ans(a) else None
                rel, rec = _released(it, c, a)
                row[rd] = outcome(rel, it, c, agree)
                row[rd + "_val"] = rel
                if rd == "4b_cautious" and rel:
                    t, i, j = c["text"], rec["start"], rec["end"]
                    fr = F1.question_relation(it["q"])
                    row["v1_soft"] = F1.qualifiers_ok(it["q"], rel, t, i, j) and F1.role_ok(it["q"], t, i, j) and (fr is None or F1.sentence_confirms(fr, t, i, j))
                    row["v1_strict"] = bool(fr) and row["v1_soft"] and F1.sentence_confirms(fr, t, i, j)
                    f = P.frames_of({"q": it["q"], "ctx": f"(page: {it['doc']}) " + P.context(t, i, j)}, cache)
                    row["v2_strict"] = bool(f and f[0] and f[0] == f[1] and f[2] == "whole") if f else None
            p = G["phi4_cautious"].get(jid)
            row["agree"] = bool(row["4b_cautious_val"] and p and ans(p) and agree(str(row["4b_cautious_val"]), str(p)))
            R.append(row)
    (HERE / "synth_rows.json").write_text(json.dumps(R, ensure_ascii=False), encoding="utf-8")
    n_items = len(items)

    def rate(rd, kind, k, what):
        S = [r for r in R if r["kind"] == kind and r["k"] == k]
        return sum(r[rd] == what for r in S) / max(1, len(S)), sum(r[rd] == what for r in S)
    out = [f"# S20 Step B: synthetic-page test (items {n_items}; pre-registration docs/S20_STEPB_PREREG.md)", "",
           "Share of pages on which the gated release (V1-V5, single page) is correct / an inserted value / other / abstain.", "",
           "| reader | kind | k | correct | inserted (A2 by construction) | other | abstain |", "|---|---|---|---|---|---|---|"]
    for rd in ("4b_plain", "4b_cautious", "phi4_cautious"):
        for kind, k in [("none", 0)] + [(kd, k) for kd in ("rel", "ent") for k in KS]:
            vals = [rate(rd, kind, k, w) for w in ("correct", "inserted", "other", "abstain")]
            out.append(f"| {rd} | {kind} | {k} | " + " | ".join(f"{v:.3f} ({c})" for v, c in vals) + " |")
    # P1: slope of the inserted rate in k, relation vs entity (4B cautious and Phi-4)
    out += ["", "## P1 (C1): inserted-value release rate, relation vs entity distractors"]
    p1 = []
    for rd in ("4b_cautious", "phi4_cautious"):
        s_rel = rate(rd, "rel", 4, "inserted")[0] - rate(rd, "none", 0, "inserted")[0]
        s_ent = rate(rd, "ent", 4, "inserted")[0] - rate(rd, "none", 0, "inserted")[0]
        ok = s_rel >= 2 * s_ent and s_rel > 0
        p1.append(ok)
        out.append(f"- {rd}: rise k=0->4 relation {s_rel:+.3f}, entity {s_ent:+.3f} -> {'holds' if ok else 'fails'}")
    out.append(f"**P1 {'holds' if all(p1) else 'fails'}** (must hold for both readers)")
    # P2: shared misreading
    ins = [r for r in R if r["kind"] == "rel" and r["4b_cautious"] == "inserted"]
    shared = sum(r["agree"] for r in ins)
    p2 = len(ins) > 0 and shared / len(ins) >= 0.5
    out += ["", "## P2 (C2): when the 4B releases a relation-distractor value, Phi-4 gives the same value",
            f"- {shared}/{len(ins)} = {shared / max(1, len(ins)):.2f} -> **P2 {'holds' if p2 else 'fails'}** (threshold 0.50)"]
    # P3: D3 on the agreed system (4B cautious released and Phi-4 agrees)
    out += ["", "## P3 (D3): block relation-distractor releases, keep correct ones (system: 4B cautious + Phi-4 agreement)"]
    for d3 in ("v1_soft", "v1_strict", "v2_strict"):
        bad = [r for r in R if r["kind"] == "rel" and r["agree"] and r["4b_cautious"] == "inserted"]
        good0 = [r for r in R if r["kind"] == "none" and r["agree"] and r["4b_cautious"] == "correct"]
        blocked = sum(not r.get(d3) for r in bad)
        kept = sum(bool(r.get(d3)) for r in good0)
        entb = [r for r in R if r["kind"] == "ent" and r["agree"] and r["4b_cautious"] == "inserted"]
        out.append(f"- {d3}: blocks {blocked}/{len(bad)} relation-distractor releases; keeps {kept}/{len(good0)} correct at k=0; "
                   f"blocks {sum(not r.get(d3) for r in entb)}/{len(entb)} entity-distractor releases")
        if d3 == "v1_soft":
            p3 = len(bad) > 0 and blocked / len(bad) >= 0.8 and kept / max(1, len(good0)) >= 0.9
            out.append(f"**P3 (v1_soft) {'holds' if p3 else 'fails'}** (≥ 80% blocked and ≥ 90% kept)")
            p5 = len(entb) == 0 or sum(not r.get(d3) for r in entb) / len(entb) < 0.5
            out.append(f"**P5 (v1_soft blocks < 50% of entity-distractor releases: the blind spot) {'holds' if p5 else 'fails'}**")
    txt = "\n".join(out)
    (HERE / "synth_result.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    {"build": build, "gen": gen, "parse": parse_ctx, "score": score}[sys.argv[1]]()
