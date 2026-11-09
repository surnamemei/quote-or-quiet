"""S25: stronger veto on the added releases (docs/S25_PLAN.md). Phases:
  cands : CPU. Pre-veto releases (support, gate with format relaxation) of s19 / pin / indep on the DEV sets -> cands.jsonl (with each variant's combo passage)
  ask   : GPU (Ollama). Qwen3.8-27B cautious on each candidate -> veto27.jsonl   (run through run_veto27.sh)
  score : CPU. Policies Phi-4 / 27B / both; combination rule vs frozen S19; pooled A and w.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s25/veto27.py cands|score ;  VKG_OLLAMA_URL=... python -B results/runs/s25/veto27.py ask"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22"))
OUT = ROOT / "results/runs/s25"
SETS = ("mintaka_dev", "popqa_dev", "dev")
VARS = {"s19": ROOT / "results/runs/s19", "pin": ROOT / "results/runs/s22/pin", "indep": ROOT / "results/runs/s23/indep"}


def outputs(var, N):
    p = VARS[var] / f"{N}_outputs.jsonl"
    return [json.loads(l) for l in open(p, encoding="utf-8")] if p.exists() else None


def phi_file(var, N):
    if var == "s19":
        pre = "s19" if N in ("dev", "fresh", "fresh5") else "s21"
        return ROOT / f"results/shared_eval/readers/{pre}{N}_combo_cautious_phi4.jsonl"
    return VARS[var] / f"{N}_phi4.jsonl"


def cands():
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    from gate_fmt import release_any
    from vkg import localwiki as LW
    out = []
    for var in VARS:
        for N in SETS:
            rows = outputs(var, N)
            if rows is None:
                continue
            ev = json.load(open(VARS[var] / f"{N}_ev_combo.json", encoding="utf-8"))
            for r in rows:
                rel, rec = release_any(r, LW.page_text)
                if rel:
                    out.append({"var": var, "set": N, "id": r["id"], "q": r["question"], "rel": str(rel), "passage": ev[r["id"]]["passage"]})
    with open(OUT / "cands.jsonl", "w", encoding="utf-8") as f:
        for c in out:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print("candidates", len(out))


def ask():
    os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11535")
    import requests
    from vkg.lite import CAUTIOUS
    from vkg.llm import chat
    from concurrent.futures import ThreadPoolExecutor
    from s22_run import parse2
    cs = [json.loads(l) for l in open(OUT / "cands.jsonl", encoding="utf-8")]
    uniq = {}
    for c in cs:
        uniq.setdefault((c["var"], c["set"], c["id"]), c)

    def one(c):
        raw = chat("qwen3.8-27b", [{"role": "user", "content": CAUTIOUS.format(p=c["passage"], q=c["q"])}], temperature=0.0, seed=0,
                   max_tokens=128, think=False, json_mode=False, num_ctx=24576)
        return {"var": c["var"], "set": c["set"], "id": c["id"], "answer": parse2(raw)}
    with ThreadPoolExecutor(2) as ex:
        rows = list(ex.map(one, uniq.values()))
    requests.post(os.environ["OLLAMA_HOST_URL"] + "/api/generate", json={"model": "qwen3.8-27b", "keep_alive": 0}, timeout=120)
    with open(OUT / "veto27.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("asked", len(rows))


def score():
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    from entity_dev import ambiguous
    from temporal import time_sensitive
    from abstain_dev import grade
    from gate_fmt import release_any
    from vkg import localwiki as LW, s17_eval as S, l3_checks2 as C
    from vkg.s12_run import agree
    from vkg.s14_eval import ans
    v27 = {(r["var"], r["set"], r["id"]): r["answer"] for r in map(json.loads, open(OUT / "veto27.jsonl", encoding="utf-8"))}
    lines = ["# S25 stronger veto (design data)", "", "| policy | variant | A (added vs frozen S19) | wrong among added | correct among added |", "|---|---|---|---|---|"]
    pool = {}
    for N in SETS:
        base_rows = outputs("s19", N)
        phi19 = {r["id"]: r["answer"] for r in map(json.loads, open(phi_file("s19", N), encoding="utf-8"))}
        froz = set()                                       # frozen S19 system (frozen gate, Phi-4) = system of record
        for r in base_rows:
            a, s = S.cand(r); a = a if ans(a) else None
            rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text) if s >= 3 else (None, {})
            p = phi19.get(r["id"])
            if rel and ans(p) and agree(str(rel), str(p)):
                froz.add(r["id"])
        pre = {}
        for var in VARS:
            rows = outputs(var, N)
            if rows is None:
                continue
            ph = {r["id"]: r["answer"] for r in map(json.loads, open(phi_file(var, N), encoding="utf-8"))}
            d = {}
            for r in rows:
                rel, rec = release_any(r, LW.page_text)
                d[r["id"]] = (r, rel, rec.get("doc"), ph.get(r["id"]), v27.get((var, N, r["id"])))
            pre[var] = d
        for pol in ("phi4", "27b", "both"):
            def ok(rel, p, q27):
                a = bool(ans(p)) and agree(str(rel), str(p)); b = bool(ans(q27)) and agree(str(rel), str(q27))
                return a if pol == "phi4" else b if pol == "27b" else (a and b)
            for var in ("pin", "indep"):
                if var not in pre:
                    continue
                final = {}
                for i, (r, rel, doc, p, q27) in pre["s19"].items():
                    if rel and ok(rel, p, q27):
                        final[i] = (r, rel, "s19")
                for i, (r, rel, doc, p, q27) in pre[var].items():
                    if i in final or not rel or not ok(rel, p, q27):
                        continue
                    if time_sensitive(r["question"]) or ambiguous(r["question"], r["wiki_titles"], doc)[0]:
                        continue
                    final[i] = (r, rel, var)
                added = [i for i in final if i not in froz]
                g = {i: grade(final[i][0]["question"], final[i][0]["gold"], final[i][1]) for i in added}
                w = sum(x is False for x in g.values()); c = sum(x is True for x in g.values())
                a0 = pool.setdefault((pol, var), [0, 0, 0]); a0[0] += len(added); a0[1] += w; a0[2] += c
    for (pol, var), (a, w, c) in sorted(pool.items()):
        lines.append(f"| {pol} | {var} | {a} | {w} | {c} |")
    lines += ["", "Decision rule (docs/S25_PLAN.md): wrong added releases fall by at least half and at least 75% of the correct added survive, pooled over pin and indep, relative to policy phi4:"]
    base_w = sum(pool[("phi4", v)][1] for v in ("pin", "indep")); base_c = sum(pool[("phi4", v)][2] for v in ("pin", "indep"))
    for pol in ("27b", "both"):
        w = sum(pool[(pol, v)][1] for v in ("pin", "indep")); c = sum(pool[(pol, v)][2] for v in ("pin", "indep"))
        okk = bool(base_w) and w <= base_w / 2 and bool(base_c) and c >= 0.75 * base_c
        lines.append(f"- {pol}: wrong {w} (phi4 {base_w}), correct {c} (phi4 {base_c}) -> {'IMPROVEMENT' if okk else 'not an improvement'}")
    (OUT / "veto27_score.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    {"cands": cands, "ask": ask, "score": score}[sys.argv[1]]()
