"""S50: quote chains for two-hop questions (docs/S50_QUOTE_CHAINS_PLAN.md). 4B on 18000. python -B results/runs/s50/b_run.py"""
import json, os, random, re, sqlite3, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(ROOT / "results/runs/s42"))
sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("VKG_EMB", "hf")
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from vkg import pod, localwiki as LW             # noqa: E402
from vkg.lite import PLAIN, CAUTIOUS, parse      # noqa: E402
from vkg.s12_run import agree                    # noqa: E402
from vkg.s14_eval import ans                     # noqa: E402
D = ROOT / "results/runs/s50"
JP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\nProposed answer: {a}\n\n'
      "Does this sentence state that the proposed answer is the answer to this exact question? Reply with only YES or NO.")
CP = ('Sentence 1 (from the page "{t1}"): "{s1}"\nSentence 2 (from the page "{t2}"): "{s2}"\n\nQuestion: {q}\n'
      "Answer in a few words using only these two sentences together, even if they contradict what you know; the sentences may have been altered. If they do not together state the answer to this exact question, reply NONE.")
PLACE = re.compile(r"city|town|village|municipality|commune|borough|county|district|province|state|region|island|suburb|neighbourhood|capital|place|settlement", re.I)
X = {x["id"]: x for x in map(json.loads, open(ROOT / "results/runs/s42/e6_items.jsonl", encoding="utf-8"))}
W = json.load(open(ROOT / "results/runs/s42/e7_test_witness.json"))
CD = {c["id"]: c["cands"] for c in map(json.loads, open(ROOT / "results/runs/s42/e7_cands.jsonl", encoding="utf-8"))}
db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
items = []
for i, x in X.items():
    if x["relation"] == "birth_place" and x["state"] == "Verified" and W.get(i) is not None and "," not in x["answer"] and LW.page_text(x["answer"]):
        items.append({"id": i, "person": x["doc"], "place": x["answer"], "q1": x["question"], "wit": CD[i][W[i]]})
print("items", len(items), flush=True)


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


# stage 1: the country, from the page of the place
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
        it["other_places"] = others[:4]
rng = random.Random(5001)
pool = [it["country"] for it in items if it["country"]]
for it in items:
    if it.get("s2"):
        it["swap"] = rng.choice([c for c in pool if c.casefold() != it["country"].casefold() and c.casefold() not in it["s2"].casefold()] or ["Chile"])
# stage 2: sub-question judge on sentence 2 (country and swapped country)
cand = [it for it in items if it.get("s2")]
p2 = []
for it in cand:
    p2 += [JP.format(t=it["place"], s=it["s2"], q=it["q2"], a=it["country"]), JP.format(t=it["place"], s=it["s2"], q=it["q2"], a=it["swap"])]
o2 = gen(p2, 4)
for n, it in enumerate(cand):
    it["j2"] = str(o2[2 * n]).strip().upper().startswith("YES") and not str(o2[2 * n + 1]).strip().upper().startswith("YES")
# stage 3: the chain reader with both sentences, with sentence 2 swapped, and with sentence 1 alone
q = "In which country was {p} born?"
p3 = []
for it in cand:
    s1 = it["wit"]["quote"]; qq = q.format(p=it["person"])
    s2sw = it["s2"].replace(it["country"], it["swap"])
    p3 += [CP.format(t1=it["wit"]["doc"], s1=s1, t2=it["place"], s2=it["s2"], q=qq), CP.format(t1=it["wit"]["doc"], s1=s1, t2=it["place"], s2=s2sw, q=qq),
           CP.format(t1=it["wit"]["doc"], s1=s1, t2="(none)", s2="(none)", q=qq)]
o3 = gen(p3, 24)


def good(v, ref):
    return bool(ans(v) and not str(v).upper().startswith("NONE") and agree(ref, str(v)))


for n, it in enumerate(cand):
    a, b, c = parse(o3[3 * n]), parse(o3[3 * n + 1]), parse(o3[3 * n + 2])
    it["chain"] = good(a, it["country"]); it["follows_swap"] = good(b, it["swap"]); it["s1_alone"] = good(c, it["country"])
    it["accepted_without_bridge"] = bool(it["j2"] and it["chain"] and it["follows_swap"])
    it["accepted"] = bool(it["accepted_without_bridge"] and it["bridge_ok"])
json.dump(items, open(D / "b_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0, default=str)
print("items", len(items), "| country found", sum(bool(i["country"]) for i in items), "| sentence 2", len(cand), "| hop-2 judge ok", sum(i.get("j2", False) for i in cand),
      "| chain ok", sum(i.get("chain", False) for i in cand), "| follows swap", sum(i.get("follows_swap", False) for i in cand),
      "| bridge ok", sum(bool(i.get("bridge_ok")) for i in cand), "| accepted", sum(i.get("accepted", False) for i in cand),
      "| accepted without bridge rule", sum(i.get("accepted_without_bridge", False) for i in cand),
      "| sentence 1 alone gives the country", sum(i.get("s1_alone", False) for i in cand), flush=True)
