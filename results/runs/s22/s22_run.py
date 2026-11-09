"""S22 DEV experiment "wiki-pin" (design data only; frozen vkg/ files untouched).
Change vs S19/S21 pipeline: the local-Wikipedia evidence pins first the pages that the kept (contamination-checked) web results
name as en.wikipedia.org articles, if present in the local FineWiki snapshot and not contaminated, in web rank order; the
original localwiki.search top-5 fills the remaining slots (5 titles total). Everything else is vkg.s17_run unchanged; web
evidence and web_* generations are reused from results/runs/s19 (identical inputs, greedy).
Then Phi-4 cautious reader on the new combo passages and alias-aware labels for all six outputs.
Variant (env S22_VARIANT): "tok" = generation limit 40 -> 128 tokens and fence-tolerant parsing, evidence as S19;
"pin" = the same plus wiki pinning. All six 4B outputs and Phi-4 are regenerated in both.
usage: S22_VARIANT=tok|pin VKG_EMB=hf VKG_WEB=ddg VKG_POD_HOST=local python -B results/runs/s22/s22_run.py <set> [gen|phi4|alias]"""
import json, os, re, shutil, sys, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
VARIANT = os.environ.get("S22_VARIANT", "pin")        # "tok": token/parse fix only; "pin": token/parse fix + wiki pinning
OUT = ROOT / "results/runs/s22" / VARIANT
OUT.mkdir(parents=True, exist_ok=True)
K = 5
MAXTOK = 128                                           # S19 used 40: long plain answers were cut before the JSON closed


def parse2(raw):
    """vkg.lite.parse, plus: strip a markdown code fence before matching (the 4B often wraps its JSON in ```json)."""
    from vkg.lite import parse
    m = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    if m:
        return m.group(1)[:200]
    body = re.sub(r"^\s*```(?:json)?\s*", "", raw).strip()
    if body.startswith("{"):
        return ""                                      # JSON cut before the answer closed: treat as no answer
    return parse(body) if body else parse(raw)


def wtitle(u):
    if "en.wikipedia.org/wiki/" not in u:
        return None
    t = urllib.parse.unquote(u.split("/wiki/", 1)[1].split("#")[0].split("?")[0]).replace("_", " ")
    return None if ":" in t else t


def gen(name):
    from vkg import s17_run as R, evidence_fast as E, localwiki as LW, websearch as W
    from concurrent.futures import ThreadPoolExecutor
    from vkg import pod
    R.OUT = OUT
    if not (OUT / f"{name}_ev_web.json").exists():
        shutil.copy(ROOT / "results/runs/s19" / f"{name}_ev_web.json", OUT / f"{name}_ev_web.json")
    if VARIANT == "tok" and not (OUT / f"{name}_ev_wiki.json").exists():
        shutil.copy(ROOT / "results/runs/s19" / f"{name}_ev_wiki.json", OUT / f"{name}_ev_wiki.json")
        shutil.copy(ROOT / "results/runs/s19" / f"{name}_ev_combo.json", OUT / f"{name}_ev_combo.json")
    _gen = pod.gen

    def gen_keep_raw(prompts, n):                      # also keep raw generations, so parser fixes never need the GPU again
        outs = _gen(prompts, max(n, MAXTOK))
        with open(OUT / f"{name}_raw_gen.jsonl", "a", encoding="utf-8") as f:
            for p, o in zip(prompts, outs):
                f.write(json.dumps({"prompt_tail": p[-300:], "raw": o[0]}, ensure_ascii=False) + "\n")
        return outs
    R.pod.gen = gen_keep_raw
    R.parse = parse2
    web = json.load(open(OUT / f"{name}_ev_web.json", encoding="utf-8"))

    def pinned(items, k_pages=K, workers=8):
        def one(e):
            pin = []
            for u in web[e["id"]]["kept"]:
                t = wtitle(u)
                if t and t not in pin:
                    txt = LW.page_text(t)
                    if txt and not W.contaminated(txt, e["question"]):
                        pin.append(t)
            titles = pin[:k_pages]
            for t in LW.search(e["question"], k_pages):
                if len(titles) >= k_pages:
                    break
                if t not in titles:
                    titles.append(t)
            return e["id"], {"titles": titles, "pinned": len(pin[:k_pages]), "passage": E.wiki_passage(e["question"], titles)}
        with ThreadPoolExecutor(workers) as ex:
            return dict(ex.map(one, items))
    if VARIANT == "pin":
        E.wiki_build = pinned
    sys.argv = ["s17_run", name]
    R.main()


def phi4(name):
    os.environ["OLLAMA_HOST_URL"] = os.environ.get("VKG_OLLAMA_URL", "http://127.0.0.1:11435")
    from vkg.lite import CAUTIOUS, parse
    from vkg.llm import chat
    from concurrent.futures import ThreadPoolExecutor
    from vkg import s17_run
    items = s17_run.items(name)                        # s21 sets and fresh3-5 alike
    ev = json.load(open(OUT / f"{name}_ev_combo.json", encoding="utf-8"))

    def one(e):
        p = ev.get(e["id"], {}).get("passage")
        rec = {"id": e["id"], "answer": None}
        if p:
            raw = chat("phi4", [{"role": "user", "content": CAUTIOUS.format(p=p, q=e["question"])}], temperature=0.0, seed=0,
                       max_tokens=MAXTOK, think=False, json_mode=False, num_ctx=24576)
            rec["answer"], rec["raw"] = parse2(raw), raw
        return rec
    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(one, items))
    with open(OUT / f"{name}_phi4.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("phi4", name, len(rows), flush=True)


def alias(name):
    from vkg import pod
    from vkg.s21_judge import needed, J
    keys = [f"{s}_{k}" for s in ("web", "wiki", "combo") for k in ("plain", "cautious")]
    todo = []
    for r in map(json.loads, open(OUT / f"{name}_outputs.jsonl", encoding="utf-8")):
        for k in keys:
            for t in needed(r["question"], r["gold"], r.get(k)):
                if t not in todo:
                    todo.append(t)
    print("alias labels", name, len(todo), flush=True)
    with open(ROOT / "results/grader5/judge_grades.jsonl", "a", encoding="utf-8") as f:
        for s in range(0, len(todo), 64):
            part = todo[s:s + 64]
            for (q, g, a), gr in zip(part, pod.judge_many(part, 4)):
                f.write(json.dumps({"question": q, "gold": g, "answer": a, "grade": gr}, ensure_ascii=False) + "\n")
                J[(q, g, a)] = gr
            f.flush()
    pod.unload_judge()


if __name__ == "__main__":
    {"gen": gen, "phi4": phi4, "alias": alias}[sys.argv[2]](sys.argv[1])
