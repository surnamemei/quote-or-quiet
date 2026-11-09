"""Run a different READER on the evaluation session's cached evidence (same passages, same frozen prompts; only the reader
changes) and write the shared JSONL format for vkg/score_jsonl.py. DEV and FRESH; and, since the S18 verdict (2026-11-07 04:10),
the used S18 sets FRESH-3 + FRESH-4 as --set s18 (exploratory only; restrict with --ids FILE, one id per line).

  python -B -m vkg.reader_run --reader oai::http://127.0.0.1:3120::<model-id> --evidence s14 --prompt cautious --out OUT.jsonl
  python -B -m vkg.reader_run --reader <ollama-model> --evidence combo --prompt plain --set dev --out OUT.jsonl

--evidence  s14    DuckDuckGo web passages (question + two 4B queries, 1500 words): the S14/S15 "web" condition.
                   4B reference on DEV: web_plain 90.7/82.0/8.7, web_cautious 83.7/78.0/5.7 (coverage/correct/SER %).
                   DEV only (results/runs/s14/outputs.jsonl).
            combo  Serper question-only + local FineWiki, one 1500-word passage (S16/S17, HF embedder).
                   4B on DEV: plain 88.3/81.7/6.7, cautious 80.3/76.7/3.7.  dev: results/runs/s16/dev_combo.json;
                   fresh: results/runs/s17/fresh_ev_combo.json
            web    Serper question-only, 8 pages (S16 k8 / S17 web).  4B DEV: plain 87.0/78.3/8.7, cautious 75.7/71.0/4.7
            wiki   local FineWiki top-5 (S16/S17).                    4B DEV: plain 67.3/56.7/10.7, cautious 56.0/52.3/3.7
--prompt    plain | cautious   (the frozen PLAIN / CAUTIOUS templates of vkg/s6b_run.py, via vkg/lite.py)
Generation settings match the 4B runs as closely as an API allows: greedy (temperature 0, seed 0), at most 40 new tokens,
no thinking, free-form output parsed by the frozen parser (vkg.probe_gen.parse). Items with an empty passage get answer null
(as for the 4B). Responses are cached by vkg/llm.py, keyed by reader and prompt. --workers sets parallel requests (default 4)."""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .lite import CAUTIOUS, PLAIN, parse
from .llm import chat

ROOT = Path(__file__).resolve().parent.parent


def evidence(kind, which):
    R = ROOT / "results" / "runs"
    if kind == "s14":
        if which != "dev":
            sys.exit("--evidence s14 exists for DEV only")
        rows = [json.loads(l) for l in open(R / "s14" / "outputs.jsonl", encoding="utf-8") if '"dev"' in l]
        return [(r["id"], r["question"], r["gold"], r.get("passage") or "", r.get("urls", [])) for r in rows]
    files = {("combo", "dev"): R / "s16" / "dev_combo.json", ("web", "dev"): R / "s16" / "dev_evidence_k8.json",
             ("wiki", "dev"): R / "s16" / "dev_wiki.json", ("combo", "fresh"): R / "s17" / "fresh_ev_combo.json",
             ("web", "fresh"): R / "s17" / "fresh_ev_web.json", ("wiki", "fresh"): R / "s17" / "fresh_ev_wiki.json"}
    if which in ("s19dev", "s19fresh", "fresh5"):   # S19: DuckDuckGo-based evidence from vkg/s17_run.py with VKG_WEB=ddg
        from .s17_run import items as s17_items
        nm = {"s19dev": "dev", "s19fresh": "fresh", "fresh5": "fresh5"}[which]
        ev = json.load(open(R / "s19" / f"{nm}_ev_{kind}.json", encoding="utf-8"))
        return [(e["id"], e["question"], e["gold"], ev[e["id"]]["passage"], ev[e["id"]].get("kept") or ev[e["id"]].get("urls") or [])
                for e in s17_items(nm)]
    if which == "s18":          # used after the S18 verdict; exploratory analysis only
        out = []
        for s in ("fresh3", "fresh4"):
            ev = json.load(open(R / "s17" / f"{s}_ev_{kind}.json", encoding="utf-8"))
            out += [(e["id"], e["question"], e["gold"], ev[e["id"]]["passage"], ev[e["id"]].get("kept") or ev[e["id"]].get("urls") or [])
                    for e in json.load(open(R / s / "items.json", encoding="utf-8"))]
        return out
    ev = json.load(open(files[(kind, which)], encoding="utf-8"))
    if which == "dev":
        items = [e for e in json.load(open(R / "s6b" / "eval_items.json", encoding="utf-8")) if e["suite"] == "simpleqa_E"]
    else:
        items = json.load(open(R / "s8" / "fresh_items.json", encoding="utf-8"))
    return [(e["id"], e["question"], e["gold"], ev[e["id"]]["passage"], ev[e["id"]].get("kept") or ev[e["id"]].get("urls") or []) for e in items]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", required=True)
    ap.add_argument("--evidence", choices=("s14", "combo", "web", "wiki"), required=True)
    ap.add_argument("--prompt", choices=("plain", "cautious"), required=True)
    ap.add_argument("--set", choices=("dev", "fresh", "s18", "s19dev", "s19fresh", "fresh5"), default="dev")
    ap.add_argument("--ids", default=None)
    ap.add_argument("--num-ctx", type=int, default=8192)   # server KV size; larger only avoids slot contention with many workers
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    tmpl = PLAIN if a.prompt == "plain" else CAUTIOUS
    rows = evidence(a.evidence, a.set)
    if a.ids:
        keep = {l.strip() for l in open(a.ids, encoding="utf-8") if l.strip()}
        rows = [r for r in rows if r[0] in keep]

    def one(x):
        i, q, gold, p, urls = x
        rec = {"id": i, "question": q, "gold": gold if isinstance(gold, list) else [gold], "answer": None, "evidence_urls": urls}
        if p:
            raw = chat(a.reader, [{"role": "user", "content": tmpl.format(p=p, q=q)}], temperature=0.0, seed=0, max_tokens=40,
                       think=False, json_mode=False, num_ctx=a.num_ctx)
            rec["answer"] = parse(raw)
            rec["raw"] = raw
        return rec
    with ThreadPoolExecutor(a.workers) as ex:
        out = list(ex.map(one, rows))
    with open(a.out, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} rows to {a.out}; score with: python -B -m vkg.score_jsonl {a.out}")


if __name__ == "__main__":
    main()
