"""S43 part C (E11): apply the sentence-level witness rule (docs/S43_LONGFORM_AND_AMBIGUITY_PLAN.md, part C) and draw the blind sheet.
Witness = first candidate in page order whose quote-only reader returns the value (G) and returns the swapped value when the span is replaced (W).
Sheet: every kept slot, 40 random dropped slots (no quote shown), 30 decoys. Writes E11_sheet_part*.csv, E11_key.json, and prints counts.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s43/s43_sheet.py"""
import csv, json, os, random, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402
from vkg.s12_run import agree     # noqa: E402
from vkg.s14_eval import ans      # noqa: E402
D = ROOT / "results/runs/s43"
slots = [json.loads(l) for l in open(D / "e11_cands.jsonl", encoding="utf-8")]
OUT = json.load(open(D / "e11_out.json", encoding="utf-8"))


def said(o):
    o = str(o or "").strip().strip("'\".")
    return o if ans(o) and not o.upper().startswith("NONE") else None


def yes(o):
    return str(o or "").strip().upper().startswith("YES")


kept, dropped = [], []
ctrl = [0, 0]
for s_ in slots:
    w = None
    for k, c in enumerate(s_["cands"]):
        o = OUT[f"{s_['id']}|{k}"]
        if c["swap"]:
            ctrl[0] += 1; ctrl[1] += yes(o[1])
        if c["N"] and yes(o[0]) and c["swap"] and not yes(o[1]):
            w = k; break
    (kept if w is not None else dropped).append({**s_, "k": w})
print(f"control: judge says YES to the swapped value for {ctrl[1]} of {ctrl[0]} candidates")
n = len(slots)
print(f"slots {n} | kept {len(kept)} ({100*len(kept)/n:.1f}%) | with a candidate {sum(bool(s['cands']) for s in slots)} | witness is the first candidate {sum(s['k']==0 for s in kept)}")
print("kept by type:", {t: f"{v}/{Counter(s['type'] for s in slots)[t]}" for t, v in Counter(s["type"] for s in kept).most_common(12)})
print("biographies with a kept slot:", len({s["person"] for s in kept}), "of 50")
rng = random.Random(4302)
KEPT = kept if len(kept) <= 300 else random.Random(4304).sample(kept, 300)
rows = [dict(kind="kept", s=s, q=s["question"], v=s["value"], quote=s["cands"][s["k"]]["quote"]) for s in KEPT]
for s in rng.sample(dropped, 40):
    rows.append(dict(kind="dropped", s=s, q=s["question"], v=s["value"], quote=""))
for m in range(30):
    while True:
        s = rng.choice(kept); t = [y for y in kept if y["type"] == s["type"] and y["person"] != s["person"] and y["value"].casefold() != s["value"].casefold()]
        if t:
            break
    y = rng.choice(t)
    if m < 15:
        rows.append(dict(kind="decoy_value", s=s, q=s["question"], v=y["value"], quote=s["cands"][s["k"]]["quote"]))
    else:
        rows.append(dict(kind="decoy_question", s=s, q=y["question"], v=s["value"], quote=s["cands"][s["k"]]["quote"]))
rng.shuffle(rows)
P = 2 if len(rows) < 420 else 3; key = {}
for p in range(P):
    part = rows[p::P]
    with open(D / f"E11_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["row", "question", "value", "page_title", "quote"])
        for i, r in enumerate(part, 1):
            w.writerow([i, r["q"], r["v"], r["s"]["person"], r["quote"]])
    key[str(p + 1)] = [{"row": i, "id": r["s"]["id"], "kind": r["kind"], "k": r["s"]["k"]} for i, r in enumerate(part, 1)]
json.dump(key, open(D / "E11_key.json", "w", encoding="utf-8"))
print("sheet rows", len(rows), "| parts", [len(rows[p::P]) for p in range(P)])
