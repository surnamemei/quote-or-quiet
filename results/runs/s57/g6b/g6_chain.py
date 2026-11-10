"""S57 G6 hop 2: W1 witness for hop 1 (as in results/runs/s46/e9_sheet.py), then the S50 chain rule C2' unchanged (results/runs/s50/b_run.py stages 1 and 2):
the country from the place page (4B, plain and cautious agree), sentence 2 = first sentence of the place page that holds the country, hop-2 judge YES for the country and NO for a
swapped country (seed 5708), bridge check (title equals the place string, no other place of that name in the title index, not a disambiguation page). No chain-level reader.
4B server on 18000. python -B results/runs/s57/g6b/g6_chain.py"""
import json, os, random, re, sqlite3, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import pod, localwiki as LW             # noqa: E402
from vkg.lite import PLAIN, CAUTIOUS, parse      # noqa: E402
from vkg.s12_run import agree                    # noqa: E402
from vkg.s14_eval import ans                     # noqa: E402
D = ROOT / "results/runs/s57/g6b"
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
PLACE = re.compile(r"city|town|village|municipality|commune|borough|county|district|province|state|region|island|suburb|neighbourhood|capital|place|settlement", re.I)
res = json.load(open(D / "e9_out.json", encoding="utf-8"))


def said(o):
    o = str(o or "").strip().strip("'\".")
    return o if ans(o) and not o.upper().startswith("NONE") else None


for r in res:                                     # W1 as in S46
    r["k"] = None
    for k, c in enumerate(r["cands"]):
        g = said(c["out"][0])
        if c["F"] and c["S"] and g and agree(r["answer"], g):
            r["k"] = k; break
json.dump(res, open(D / "g6_witness.json", "w", encoding="utf-8"), ensure_ascii=False)
items = [{"id": r["id"], "person": r["reading"], "place": r["answer"].strip(), "wit": r["cands"][r["k"]]} for r in res
         if r["k"] is not None and "," not in r["answer"] and LW.page_text(r["answer"].strip())]
print("readings", len(res), "| W1 witness", sum(r["k"] is not None for r in res), "| single place with a page", len(items), flush=True)
db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)


def gpu_used():
    import subprocess
    try:
        return int(subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits".split(), capture_output=True, text=True).stdout.strip()) / 1024
    except Exception:
        return 0.0


def gen(batch, n, step=8):
    import requests
    out = []
    for s in range(0, len(batch), step):
        for t in range(40):
            try:
                if gpu_used() > 27:
                    pod.unload_gen(); time.sleep(120)
                out += [o[0] for o in pod.gen(batch[s:s + step], n)]
                break
            except (requests.exceptions.RequestException, RuntimeError) as e:
                print("retry", t, repr(e)[:100], flush=True); time.sleep(45)
        else:
            raise SystemExit("gave up")
    return out


def sent_window(text, i, j):
    a = max(text.rfind("\n", 0, i), max(text.rfind(". ", 0, i), text.rfind("? ", 0, i), text.rfind("! ", 0, i)) + 1)
    ends = [k for k in (text.find("\n", j), text.find(". ", j)) if k != -1]
    b = min(ends) if ends else len(text)
    return text[a:b].strip()[:400]


p1 = []
for it in items:
    text = LW.page_text(it["place"]); q = f"In which country is {it['place']}?"
    p = f"[{it['place']}] " + text[:1500]
    p1 += [PLAIN.format(p=p, q=q), CAUTIOUS.format(p=p, q=q)]
o1 = gen(p1, 40)
for n, it in enumerate(items):
    a, b = parse(o1[2 * n]), parse(o1[2 * n + 1])
    it["country"] = str(a).strip() if ans(a) and ans(b) and agree(str(a), str(b)) else None
    it["q2"] = f"In which country is {it['place']}?"
    if it["country"]:
        text = LW.page_text(it["place"])
        for m in re.finditer(r"(?<![\w])" + re.escape(it["country"]) + r"(?![\w])", text):
            s2 = sent_window(text, m.start(), m.end())
            if len(s2) >= 40 and not s2.lstrip().startswith(("#", "-", "*", "|", "=")):
                it["s2"] = s2
                break
    it["bridge_ok"] = None
    if it.get("s2"):
        rows = db.execute("select qual from t where core = ? and qual != ''", (it["place"],)).fetchall()
        others = [r[0] for r in rows if PLACE.search(r[0])]
        it["bridge_ok"] = len(others) == 0 and "may refer to" not in LW.page_text(it["place"]).lstrip().lower()[:400]
rng = random.Random(5712)
pool = [it["country"] for it in items if it["country"]]
for it in items:
    if it.get("s2"):
        it["swap"] = rng.choice([c for c in pool if c.casefold() != it["country"].casefold() and c.casefold() not in it["s2"].casefold()] or ["Chile"])
cand = [it for it in items if it.get("s2")]
p2 = []
for it in cand:
    p2 += [JP.format(t=it["place"], s=it["s2"], q=it["q2"], a=it["country"]), JP.format(t=it["place"], s=it["s2"], q=it["q2"], a=it["swap"])]
o2 = gen(p2, 4)
for n, it in enumerate(cand):
    it["j2"] = str(o2[2 * n]).strip().upper().startswith("YES") and not str(o2[2 * n + 1]).strip().upper().startswith("YES")
    it["accepted"] = bool(it["j2"] and it["bridge_ok"])
json.dump(items, open(D / "g6_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0, default=str)
print("items", len(items), "| country found", sum(bool(i["country"]) for i in items), "| sentence 2", len(cand), "| hop-2 judge ok", sum(i.get("j2", False) for i in cand),
      "| bridge ok", sum(bool(i.get("bridge_ok")) for i in cand), "| accepted (C2')", sum(i.get("accepted", False) for i in cand), flush=True)
