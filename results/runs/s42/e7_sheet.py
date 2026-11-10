"""S42 E7 test sheet (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 9, rule W1 frozen 2026-11-10 11:14 before this ran).
Witness = first candidate in page order that passes F, S and G. Draws the blind sheet: every test Verified item with a witness,
a sample (at most 100) of test Qualified items with a witness, and 60 decoys built from test Verified witnesses as in E6.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/e7_sheet.py"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(Path(__file__).parent))
import no_retrieval2  # noqa: F401,E402
from vkg.s12_run import agree     # noqa: E402
from vkg.s14_eval import ans      # noqa: E402
import e7_lib as L                # noqa: E402
D = ROOT / "results/runs/s42"
X = {x["id"]: x for x in map(json.loads, open(D / "e6_items.jsonl", encoding="utf-8"))}
CD = {c["id"]: c["cands"] for c in map(json.loads, open(D / "e7_cands.jsonl", encoding="utf-8"))}
OUT = json.load(open(D / "e7_test_out.json", encoding="utf-8"))
K = json.load(open(D / "E6_key.json", encoding="utf-8"))
dev = {k["id"] for ks in K.values() for k in ks}
test = [i for i in X if i not in dev]


def said(o):
    o = str(o or "").strip().strip("'\".")
    return o if ans(o) and not o.upper().startswith("NONE") else None


def witness(i):
    x = X[i]
    for k, c in enumerate(CD[i]):
        key = f"{i}|{k}"
        if key not in OUT:
            continue
        a = said(OUT[key][0])
        if c["F"] and L.subject_link(x["question"], c["doc"], c["quote"]) and a and agree(x["answer"], a):
            return k
    return None


W = {i: witness(i) for i in test}
json.dump(W, open(D / "e7_test_witness.json", "w"))
res = {}
for st in ("Verified", "Qualified"):
    ids = [i for i in test if X[i]["state"] == st]
    kept = [i for i in ids if W[i] is not None]
    first = [i for i in kept if W[i] == 0]
    res[st] = (ids, kept, first)
    print(f"{st}: test items {len(ids)} | keep a witness {len(kept)} ({100*len(kept)/len(ids):.1f}%) | witness is the first span {len(first)} | later span {len(kept)-len(first)}")
rng = random.Random(4207)
ver = res["Verified"][1]; qua = rng.sample(res["Qualified"][1], min(100, len(res["Qualified"][1])))
by = {}
for i in ver:
    by.setdefault(X[i]["relation"], []).append(i)


def row(i, kind, **over):
    x = X[i]; c = CD[i][W[i]]
    return {"id": i, "kind": kind, "question": x["question"], "answer": x["answer"], "doc": c["doc"], "quote": c["quote"], "k": W[i], **over}


sheet = [row(i, "verified") for i in ver] + [row(i, "qualified") for i in qua]
for n in range(60):
    i = rng.choice(ver); x = X[i]
    if n < 30:
        j = rng.choice([j for j in by[x["relation"]] if not agree(X[j]["answer"], x["answer"]) and X[j]["answer"].casefold() not in CD[i][W[i]]["quote"].casefold()])
        sheet.append(row(i, "decoy_answer", answer=X[j]["answer"]))
    else:
        j = rng.choice([j for j in by[x["relation"]] if X[j]["doc"] != x["doc"] and not agree(X[j]["answer"], x["answer"])])
        sheet.append(row(i, "decoy_question", question=X[j]["question"]))
rng.shuffle(sheet)
P = max(1, round(len(sheet) / 180)); key = {}
for p in range(P):
    part = sheet[p::P]
    with open(D / f"E7_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "answer", "page_title", "quote"])
        for n, r in enumerate(part, 1):
            w.writerow([n, r["question"], r["answer"], r["doc"], r["quote"]])
    key[str(p + 1)] = [{"row": n, "id": r["id"], "kind": r["kind"], "k": r["k"]} for n, r in enumerate(part, 1)]
json.dump(key, open(D / "E7_key.json", "w"))
print("sheet rows", len(sheet), "| parts", [len(sheet[p::P]) for p in range(P)])
