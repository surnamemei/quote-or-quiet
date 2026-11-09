"""Coverage of a local Wikipedia index against the pages live retrieval actually used.
Test set: every non-empty, non-redirect article fetched with action=raw in results/cache/wiki (all runs so far).
A title counts as present if page_text(title) is non-empty (exact title, then first letter capitalised, then underscores->spaces).
Run: VKG_LOCALWIKI=fw2025 python -B -m vkg.localwiki_coverage   -> prints coverage and writes results/audit2/localwiki_coverage_<wiki>.txt"""
import json
import re
from urllib.parse import parse_qs, unquote, urlparse

from . import localwiki as L

CACHE = L.ROOT / "results" / "cache" / "wiki"


def titles():
    out = set()
    for f in CACHE.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        if "url" not in d:          # API search responses, not pages
            continue
        q = parse_qs(urlparse(d["url"]).query)
        if q.get("action") != ["raw"] or not d["text"].strip() or re.match(r"\s*#redirect", d["text"], re.I):
            continue
        t = q.get("title", [""])[0] or unquote(urlparse(d["url"]).path.rsplit("/", 1)[-1])
        out.add(t.replace("_", " ").strip())
    return sorted(out)


def main():
    ts = titles()
    present, missing = [], []
    for t in ts:
        (present if L.page_text(t) or L.page_text(t[:1].upper() + t[1:]) else missing).append(t)
    rate = len(present) / max(1, len(ts))
    txt = f"{L.WIKI}: {len(present)}/{len(ts)} present = {rate:.1%}\nmissing:\n" + "\n".join(missing)
    (L.ROOT / "results" / "audit2" / f"localwiki_coverage_{L.WIKI}.txt").write_text(txt, encoding="utf-8")
    print(txt[:1500])


if __name__ == "__main__":
    main()
