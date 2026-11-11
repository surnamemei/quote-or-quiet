"""S58 G4: mechanical check of the adjudicators' supporting quotes (as S40 L2). For every removing verdict (gold wrong / equally acceptable) the support quote must occur in the named
English Wikipedia page: first the local snapshot (August 2025), else the current page text from the MediaWiki API; comparison after lower-casing, removing wiki markup ([[ ]], '' ''', templates
braces, <ref> tags) and collapsing white space. Writes G4_adj_verdict_{A,B}.csv (row, verdict, quote_found) for s58_q2.py unblind. python -B results/runs/s58/adj_quote_check.py"""
import csv, json, os, re, sys, time
from pathlib import Path
import requests
ROOT = Path(__file__).resolve().parents[3]; D = ROOT / "results/runs/s58"
os.chdir(ROOT); sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20")]; sys.stdout.reconfigure(encoding="utf-8")
import no_retrieval2  # noqa: F401
from vkg import localwiki as LW
def norm(t):
    t = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", " ", t or "", flags=re.S)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t); t = re.sub(r"'{2,}", "", t); t = re.sub(r"[{}\[\]]", " ", t)
    t = t.replace("–", "-").replace("—", "-").replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", t).strip().casefold()
cache = {}
def live(title):
    if title not in cache:
        for t in range(4):
            try:
                r = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "page": title, "prop": "wikitext", "format": "json", "redirects": 1},
                                 headers={"User-Agent": "research-quote-check/1.0"}, timeout=60).json()
                cache[title] = r.get("parse", {}).get("wikitext", {}).get("*", ""); break
            except Exception:
                time.sleep(5)
        else:
            cache[title] = ""
        time.sleep(1)
    return cache[title]
stats = {}
for rv in "AB":
    out = []; n = f = 0
    for r in csv.DictReader(open(D / f"G4_adj_raw_{rv}.csv", encoding="utf-8-sig")):
        v = r["verdict"].strip().casefold(); found = ""
        if v in ("gold wrong", "equally acceptable"):
            n += 1; q = norm(r.get("support_quote", "")); t = (r.get("wiki_title") or "").strip()
            ok = bool(q) and len(q) >= 8 and t and (q in norm(LW.page_text(t) or "") or q in norm(live(t)))
            found = "yes" if ok else "no"; f += ok
        out.append({"row": r["row"], "verdict": v, "quote_found": found})
    with open(D / f"G4_adj_verdict_{rv}.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["row", "verdict", "quote_found"]); w.writeheader(); w.writerows(out)
    stats[rv] = (n, f)
print("removing verdicts with their quote found:", {k: f"{f} of {n}" for k, (n, f) in stats.items()})
