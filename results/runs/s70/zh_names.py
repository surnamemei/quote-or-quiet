"""Track C C1: Chinese names for the answer values of the Chinese-question items, so that answers written in Chinese can be scored.
For every distinct expect/forbid value of a zh item: Wikidata wbsearchentities (English label, top hit), then its zh, zh-hans, zh-cn, zh-hant, zh-tw, zh-hk
labels and aliases. Writes zh_names.json {value: {"qid", "en_label", "zh": [...]}}. The top hit can be the wrong entity for an ambiguous value; the rescore
reports how many values got a name and leaves the English match in place. python -B results/runs/s70/zh_names.py"""
import json, sys, time
from pathlib import Path
import requests
D = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "research-esuite-zh-names/1.0"}
API = "https://www.wikidata.org/w/api.php"
LANGS = ["zh", "zh-hans", "zh-cn", "zh-hant", "zh-tw", "zh-hk"]
items = [json.loads(l) for l in open(D / "esuite_v2.jsonl", encoding="utf-8")]
vals = sorted({v for x in items if x["lang"] == "zh" for v in x["expect"] + x.get("forbid", [])})
F = D / "zh_names.json"
out = json.loads(F.read_text(encoding="utf-8")) if F.exists() else {}


def get(params):
    for t in range(4):
        try:
            return requests.get(API, params={**params, "format": "json"}, headers=H, timeout=60).json()
        except Exception:
            time.sleep(5 * (t + 1))
    return {}


for k, v in enumerate(vals):
    if v in out:
        continue
    s = get({"action": "wbsearchentities", "search": v, "language": "en", "type": "item", "limit": 1}).get("search", [])
    rec = {"qid": None, "en_label": None, "zh": []}
    if s:
        q = s[0]["id"]; rec["qid"] = q; rec["en_label"] = s[0].get("label")
        e = get({"action": "wbgetentities", "ids": q, "props": "labels|aliases", "languages": "|".join(LANGS)}).get("entities", {}).get(q, {})
        names = [e.get("labels", {}).get(l, {}).get("value") for l in LANGS] + [a["value"] for l in LANGS for a in e.get("aliases", {}).get(l, [])]
        rec["zh"] = sorted({n for n in names if n})
    out[v] = rec
    if k % 20 == 0:
        F.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    time.sleep(1)
F.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(vals), "values;", sum(bool(r["zh"]) for r in out.values()), "with a Chinese name")
