"""S73: coverage ceiling of G4 on the spent S68 NQ-open questions: share of questions with any gold answer verbatim (case-insensitive, white space collapsed)
on the pages the pipeline retrieves (local retriever's five pages plus the Wikipedia pages named in the web results), and on the local five alone.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s73/ceiling.py"""
import json, os, re, sys
from pathlib import Path
from urllib.parse import unquote
ROOT = Path(__file__).resolve().parents[3]; os.chdir(ROOT); sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20")]
import no_retrieval2  # noqa: F401
from vkg import localwiki as LW
norm = lambda s: re.sub(r"\s+", " ", str(s).replace("\xa0", " ")).strip().casefold()
rows = [json.loads(l) for l in open(ROOT / "results/runs/s68/run_fsm/m68_outputs.jsonl", encoding="utf-8")]
a = b = c = 0
for r in rows:
    gold = [norm(g) for g in (eval(r["gold"]) if isinstance(r["gold"], str) else r["gold"]) if len(norm(g)) >= 2]
    loc = list(eval(r["wiki_titles"]) if isinstance(r["wiki_titles"], str) else r["wiki_titles"])
    urls = eval(r["web_urls"]) if isinstance(r["web_urls"], str) else r["web_urls"]
    web = [unquote(u.split("/wiki/", 1)[1]).replace("_", " ").split("#")[0] for u in urls if "en.wikipedia.org/wiki/" in u]
    tl = {t: norm(LW.page_text(t)) for t in loc}; tw = {t: norm(LW.page_text(t)) for t in web if t not in tl}
    inl = any(g in x for g in gold for x in tl.values()); inw = any(g in x for g in gold for x in tw.values())
    a += inl; b += inl or inw; c += bool(web)
print(f"questions {len(rows)}; gold verbatim on the local five pages {a} ({100*a/len(rows):.1f}%); on local plus web-named Wikipedia pages {b} ({100*b/len(rows):.1f}%); questions with a web-named Wikipedia page {c}")
