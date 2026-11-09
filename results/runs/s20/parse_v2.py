"""S20 D3 v2 (docs/S20_PLAN.md section 7): blind LLM parsers into a closed relation vocabulary; the comparison stays in code.
  M_Q v2: the model sees ONLY the question and names the relation it asks for (or "none").
  M_S v2: the model sees ONLY the source context with the released span marked, never the question, and names the relation the
          context states for that span plus the span's role (whole value / part of a larger name / one side of a score / other).
D3 v2 releases only if both relations exist, are equal and the role is "whole" (strict); soft blocks only where both exist and differ
or the role is not whole. Design on DEV; the other sets are used, so everything else is post hoc.
usage:
  python -B results/runs/s20/parse_v2.py cases      (CPU: collect G3 V1-V5 releases on dev/fresh/s18/fresh5 -> cases_v2.json)
  python -B results/runs/s20/parse_v2.py parse [set...]   (GPU: phi4 on Ollama 127.0.0.1:11435, needs the GPU lock)
  python -B results/runs/s20/parse_v2.py eval"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).parent
CASES = HERE / "cases_v2.json"
CACHE = HERE / "parse_v2_cache.jsonl"
OLLAMA = "http://127.0.0.1:11435"
MODEL = "phi4"
KEYTAG = MODEL + "|enum-schema-1"   # cache key: model + constrained JSON-schema decoding

# closed vocabulary: the 42 lexical families of frames.py plus general relations common in SimpleQA question forms
GLOSS = {
    "born": "date or place of birth", "baptised": "baptism", "died": "date, place or cause of death", "buried": "burial place",
    "married": "marriage or spouse", "divorced": "divorce", "engaged": "engagement or betrothal",
    "founded": "founding or establishment", "renamed": "renaming", "relocated": "move to a new location",
    "incorporated": "incorporation", "dissolved": "dissolution or closure", "opened": "opening or inauguration",
    "construction": "construction or building", "released": "release or publication", "announced": "announcement",
    "recorded": "recording", "certified": "sales certification", "award": "award or prize received",
    "nominated": "nomination", "shortlisted": "shortlisting", "elected": "election to a body or office",
    "defeated": "defeat of an opponent", "appointed": "appointment to a position", "resigned": "resignation",
    "educated": "education (school, degree)", "taught": "teaching", "worked": "employment or workplace",
    "invented": "invention or discovery", "joined": "joining an organisation", "left": "leaving an organisation",
    "debut": "first appearance or debut", "children": "children or number of children", "dissertation": "thesis or dissertation",
    "preceded": "predecessor", "succeeded": "successor", "height": "height", "width": "width", "length": "length",
    "elevation": "elevation", "population": "population", "weight": "weight or mass",
    "located_in": "location of a thing", "named_after": "what or who it is named after", "position_held": "position, title or role held",
    "score": "score or match result", "count": "a counted number of things", "creator": "author, creator, designer or composer",
    "owner": "owner", "parent": "parent", "member_of": "membership", "amount": "price, cost or amount of money",
    "duration": "duration", "event_date": "date of some other event",
}
REL = list(GLOSS)
ROLES = ["whole", "part", "score", "other"]
VOCAB = "\n".join(f"- {k}: {v}" for k, v in GLOSS.items())

PQ = ("You classify a question. Which relation does the question ask about, between its subject and the value it asks for?\n"
      "Choose exactly one name from this list, or \"none\" if no listed relation fits exactly:\n" + VOCAB +
      "\n\nQuestion: {q}\n\nAnswer with JSON only: {{\"relation\": \"<name or none>\"}}")
PS = ("You classify a passage. One value in it is marked like this: [[value]]. What relation does the passage state between its "
      "subject and the marked value? Choose exactly one name from this list, or \"none\" if the passage states no listed relation "
      "for exactly this value:\n" + VOCAB +
      "\n\nAlso give the role of the marked value: \"whole\" if it is the complete value of that relation, \"part\" if it is only part "
      "of a larger name or value, \"score\" if it is one side of a score or a pair of numbers, \"other\" otherwise.\n\n"
      "Passage: {p}\n\nAnswer with JSON only: {{\"relation\": \"<name or none>\", \"role\": \"<whole|part|score|other>\"}}")


def context(text, i, j):
    sys.path.insert(0, str(HERE))
    import frames_v1 as F
    t = F._table_header(text, i)
    if t:
        ls = text.rfind("\n", 0, i) + 1
        le = text.find("\n", j)
        le = len(text) if le < 0 else le
        return f"{t[1].strip('# ').strip()} | columns: ...{t[0]}... | row: {text[ls:i]}[[{text[i:j]}]]{text[j:le]}"
    a, b = F.sentence_of(text, i, j)
    pa, _ = F.sentence_of(text, max(0, a - 2), max(0, a - 2))
    pa = pa if pa < a else a
    return (text[pa:i] + "[[" + text[i:j] + "]]" + text[j:b]).replace("\n", " ").strip()[-1200:]


def cases():
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, str(HERE))
    import no_retrieval2  # noqa: F401
    argv, sys.argv = sys.argv, sys.argv[:1]
    import d3_eval as D
    sys.argv = argv
    from vkg import l3_checks2 as C, localwiki as LW, s17_eval as S
    from vkg.s12_run import agree
    from vkg.s14_eval import ans, g6
    out = []
    for name in ("dev", "fresh", "s18", "fresh5"):
        rows, phi = D.load(name)
        for r in rows:
            a, s = S.cand(r)
            if s < 3 or not ans(a):
                continue
            rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
            if not rel:
                continue
            t = LW.page_text(rec["doc"])
            i, j = rec["start"], rec["end"]
            p = phi.get(r["id"])
            import frames_v1 as F
            out.append({"set": name, "n": len(rows), "id": r["id"], "q": r["question"], "gold": r["gold"], "rel": rel,
                        "graded": g6(r["question"], r["gold"], rel), "veto_ok": bool(p is not None and ans(p) and agree(str(rel), str(p))),
                        "ctx": f"(page: {rec['doc']}) " + context(t, i, j), "frame_v1": F.question_relation(r["question"]),
                        "v1_sent": (F.sentence_confirms(F.question_relation(r["question"]), t, i, j) if F.question_relation(r["question"]) else None),
                        "v1_qual": F.qualifiers_ok(r["question"], rel, t, i, j), "v1_role": F.role_ok(r["question"], t, i, j)})
        print(name, sum(x["set"] == name for x in out), flush=True)
    CASES.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")


def _load_cache():
    c = {}
    if CACHE.exists():
        for line in open(CACHE, encoding="utf-8"):
            d = json.loads(line)
            c[d["k"]] = d["out"]
    return c


def _schema(prompt):
    s = {"type": "object", "properties": {"relation": {"type": "string", "enum": REL + ["none"]}}, "required": ["relation"]}
    if prompt.startswith("You classify a passage"):
        s["properties"]["role"] = {"type": "string", "enum": ROLES}
        s["required"].append("role")
    return s


def _ask(prompt):
    for t in range(5):
        try:
            r = requests.post(f"{OLLAMA}/api/chat", json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                                                          "format": _schema(prompt), "stream": False, "keep_alive": "10m",
                                                          "options": {"temperature": 0, "num_predict": 40, "num_ctx": 4096}}, timeout=300)
            r.raise_for_status()
            return json.loads(r.json()["message"]["content"])
        except (requests.RequestException, ValueError, KeyError):
            time.sleep(5 * (t + 1))
    return {}


def parse(sets):
    from concurrent.futures import ThreadPoolExecutor
    X = [x for x in json.loads(CASES.read_text(encoding="utf-8")) if not sets or x["set"] in sets]
    c = _load_cache()
    jobs = {}
    for x in X:
        for p in (PQ.format(q=x["q"]), PS.format(p=x["ctx"])):
            k = hashlib.sha256((MODEL + "\0" + p).encode()).hexdigest()
            if k not in c:
                jobs[k] = p
    print(f"{len(jobs)} prompts to run", flush=True)
    with open(CACHE, "a", encoding="utf-8") as f, ThreadPoolExecutor(4) as ex:
        for done, (k, out) in enumerate(zip(jobs, ex.map(_ask, jobs.values()))):
            f.write(json.dumps({"k": k, "out": out}, ensure_ascii=False) + "\n")
            f.flush()
            if done % 200 == 0:
                print(done, flush=True)


def frames_of(x, c):
    kq = hashlib.sha256((MODEL + "\0" + PQ.format(q=x["q"])).encode()).hexdigest()
    ks = hashlib.sha256((MODEL + "\0" + PS.format(p=x["ctx"])).encode()).hexdigest()
    if kq not in c or ks not in c:
        return None
    fq = str(c[kq].get("relation", "none")).strip().lower()
    fs = str(c[ks].get("relation", "none")).strip().lower()
    role = str(c[ks].get("role", "other")).strip().lower()
    return (fq if fq in GLOSS else None), (fs if fs in GLOSS else None), (role if role in ROLES else "other")


def evaluate():
    X = json.loads(CASES.read_text(encoding="utf-8"))
    c = _load_cache()
    out = ["# D3 v2 (blind LLM parsers, phi4) on used sets (exploratory; DEV is design data)", "",
           "| set | system | released | coverage | wrong | correct | wrong blocked | correct blocked |", "|---|---|---|---|---|---|---|---|"]
    errs = []
    for name in ("dev", "fresh", "s18", "fresh5"):
        S = [x for x in X if x["set"] == name]
        if not S:
            continue
        n = S[0]["n"]
        miss = 0
        for x in S:
            f = frames_of(x, c)
            if f is None:
                miss += 1
                f = (None, None, "other")
            x["fq"], x["fs"], x["role"] = f
        if miss:
            out.append(f"| {name} | {miss} cases not parsed yet | | | | | | |")
            continue
        for veto in (False, True):
            base = [x for x in S if x["veto_ok"] or not veto]
            w0 = sum(x["graded"] is False for x in base)
            c0 = sum(x["graded"] is True for x in base)
            V = {
                "": base,
                " + v2-soft": [x for x in base if not (x["fq"] and x["fs"] and x["fq"] != x["fs"]) and x["role"] == "whole"],
                " + v2-soft + v1-qual": [x for x in base if not (x["fq"] and x["fs"] and x["fq"] != x["fs"]) and x["role"] == "whole" and x["v1_qual"]],
                " + v2-strict": [x for x in base if x["fq"] and x["fq"] == x["fs"] and x["role"] == "whole"],
                " + v2-strict + v1-qual": [x for x in base if x["fq"] and x["fq"] == x["fs"] and x["role"] == "whole" and x["v1_qual"]],
            }
            for lab, L in V.items():
                w = sum(x["graded"] is False for x in L)
                cc = sum(x["graded"] is True for x in L)
                out.append(f"| {name} (n={n}) | G3 V1-V5{' + veto' if veto else ''}{lab} | {len(L)} | {len(L) / n:.3f} | {w} | {cc} | "
                           f"{w0 - w if lab else ''} | {c0 - cc if lab else ''} |")
        cor = [x for x in S if x["graded"] is True]
        out.append(f"| {name} | correct releases: no q-frame {sum(not x['fq'] for x in cor)}, no s-frame {sum(not x['fs'] for x in cor)}, "
                   f"mismatch {sum(bool(x['fq'] and x['fs'] and x['fq'] != x['fs']) for x in cor)}, role not whole "
                   f"{sum(x['role'] != 'whole' for x in cor)} (of {len(cor)}) | | | | | | |")
        errs += [{k: x[k] for k in ("set", "q", "gold", "rel", "veto_ok", "fq", "fs", "role", "v1_qual", "ctx")} for x in S if x["graded"] is False]
    txt = "\n".join(out)
    (HERE / "d3_v2_eval.md").write_text(txt, encoding="utf-8")
    json.dump(errs, open(HERE / "d3_v2_errors.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(txt)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "cases":
        cases()
    elif cmd == "parse":
        parse(sys.argv[2:])
    else:
        evaluate()
