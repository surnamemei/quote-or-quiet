"""Mechanical source check for adjudication verdicts (docs/S22_ADJUDICATION_DRAFT.md, change 2).
For every verdict that removes an error (gold wrong / both acceptable), fetch source_url and require the quote to appear in the
page text (case, whitespace, quotes and dashes normalised). Failing rows revert to "cannot tell".
usage: python -B quote_check.py verdicts.csv checked.csv"""
import csv, html, re, sys, time, unicodedata
import requests

UA = {"User-Agent": "Mozilla/5.0 (research fact-check script)"}
REMOVE = ("gold wrong", "both acceptable")      # "matches gold" needs no source (same entity as the gold, checked by reading)


def norm(s):
    s = unicodedata.normalize("NFKC", html.unescape(s)).casefold()
    s = re.sub(r"[‘’´`]", "'", s); s = re.sub(r"[“”]", '"', s); s = re.sub(r"[‐-―−]", "-", s)
    return " ".join(re.sub(r"[^\w'\"%.,:;()/-]+", " ", s).split())


def squash(s):
    return re.sub(r"[\W_]+", "", s)


def page_text(url, cache={}):
    if url not in cache:
        try:
            r = requests.get(url, headers=UA, timeout=30)
            t = re.sub(r"(?is)<(script|style).*?</\1>", " ", r.text)
            cache[url] = norm(re.sub(r"(?s)<[^>]+>", " ", t)) if r.ok else ""
        except Exception:
            cache[url] = ""
        time.sleep(1)
    return cache[url]


def main(src, dst):
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    stats = {"checked": 0, "found": 0, "reverted": 0}
    for r in rows:
        r["quote_found"] = ""
        if (r.get("verdict") or "").strip().casefold() in REMOVE:
            stats["checked"] += 1
            q = norm(r.get("quote") or "")
            # compare letters/digits only: tag boundaries in the HTML put spaces before punctuation ("plath ."); word order stays exact
            ok = len(q) >= 15 and squash(q) in squash(page_text((r.get("source_url") or "").strip()))
            r["quote_found"] = "yes" if ok else "no"
            if ok:
                stats["found"] += 1
            else:
                r["verdict_original"] = r["verdict"]; r["verdict"] = "cannot tell"; stats["reverted"] += 1
    fields = list(rows[0].keys()) + [k for k in ("verdict_original",) if k not in rows[0]]
    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(stats)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
