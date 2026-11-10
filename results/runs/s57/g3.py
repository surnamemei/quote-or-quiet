"""S57 gate G3: rule R27 on 705 unseen Mintaka test releases (docs/S57_G3_NATURAL_QUESTIONS_PLAN.md).
  judge  : 27B through Ollama on 11540 (resumable).   python -B results/runs/s57/g3.py judge
  sheet  : blind quote-only sheets (3 parts) and key.  python -B results/runs/s57/g3.py sheet
  unblind: counts from G3_verdict_part{p}_{A,B}.csv.  python -B results/runs/s57/g3.py unblind"""
import csv, json, os, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
D = ROOT / "results/runs/s57"; MODE = sys.argv[1]
K52 = json.load(open(ROOT / "results/runs/s52/M_key.json")); REV = {k["id"] for p in K52.values() for k in p}
REL = [r for r in map(json.loads, open(ROOT / "results/runs/s52/m_cands.jsonl", encoding="utf-8")) if r["id"] not in REV] + \
      [r for r in map(json.loads, open(D / "pin_cands.jsonl", encoding="utf-8"))]
assert len(REL) == 705, len(REL)
yes = lambda o: str(o or "").strip().upper().startswith("YES")

if MODE == "judge":
    from vkg.llm import chat
    PF = D / "g3_judge.json"; J = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    ask = lambda p: str(chat("qwen3.8-27b", [{"role": "user", "content": p}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))
    for n, r in enumerate(REL):
        if r["id"] in J:
            continue
        w = None; calls = []
        for k, c in enumerate(r["cands"]):
            if not (c["sent"] and c["N"]):
                continue
            a = ask(c["j"]); calls.append((k, "j", a))
            if not yes(a):
                continue
            if c["j_swap"]:
                b = ask(c["j_swap"]); calls.append((k, "swap", b))
                if yes(b):
                    continue
            w = k; break
        J[r["id"]] = {"w": w, "calls": calls}
        if n % 20 == 0:
            json.dump(J, open(PF, "w", encoding="utf-8")); print(n, sum(v["w"] is not None for v in J.values()), flush=True)
    json.dump(J, open(PF, "w", encoding="utf-8"))
    print("judge done", len(J), "witnesses", sum(v["w"] is not None for v in J.values()), flush=True)

elif MODE == "sheet":
    J = json.load(open(D / "g3_judge.json", encoding="utf-8")); rng = random.Random(5702); rows = []
    W = [r for r in REL if J[r["id"]]["w"] is not None]
    for r in W:
        c = r["cands"][J[r["id"]]["w"]]
        rows.append(dict(kind="witness", r=r, a=r["answer"], c=c))
        d = r["cands"][0]
        if d["quote"] != c["quote"]:
            rows.append(dict(kind="displayed", r=r, a=r["answer"], c=d))
    sw = [r for r in W if r["cands"][J[r["id"]]["w"]]["swap"]]
    for r in rng.sample(sw, 30):
        c = r["cands"][J[r["id"]]["w"]]; rows.append(dict(kind="decoy", r=r, a=c["swap"], c=c))
    rng.shuffle(rows); key = {}
    for p in range(3):
        part = rows[p::3]
        with open(D / f"G3_sheet_part{p+1}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f); w.writerow(["row", "question", "answer", "page_title", "quote"])
            for i, x in enumerate(part, 1):
                w.writerow([i, x["r"]["question"], x["a"], x["c"]["doc"], x["c"]["quote"]])
        key[str(p + 1)] = [{"row": i, "id": x["r"]["id"], "kind": x["kind"]} for i, x in enumerate(part, 1)]
    json.dump(key, open(D / "G3_key.json", "w"))
    print("witnesses", len(W), "of", len(REL), "| sheet rows", len(rows), [len(rows[p::3]) for p in range(3)])

elif MODE == "unblind":
    from scipy.stats import beta
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0
    K = json.load(open(D / "G3_key.json")); V = {"witness": [], "displayed": [], "decoy": []}
    for p, ks in K.items():
        vs = {}
        for rv in "AB":
            for r in csv.DictReader(open(D / f"G3_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
                vs.setdefault(int(r["row"]), []).append(r["quote_verdict"].strip().strip("'\"").casefold())
        for k in ks:
            assert len(vs[k["row"]]) == 2, (p, k)
            V[k["kind"]].append(vs[k["row"]])
    J = json.load(open(D / "g3_judge.json", encoding="utf-8")); nw = sum(v["w"] is not None for v in J.values())
    def row(name, vs):
        n = len(vs); m = sum(v == ["not", "not"] for v in vs); s = sum(v == ["states", "states"] for v in vs)
        return f"| {name} | {n} | {m} ({100*m/max(1,n):.1f}%, upper {up(m,n):.1f}%) | {s} ({100*s/max(1,n):.1f}%) |"
    dec = sum(v == ["not", "not"] for v in V["decoy"])
    out = ["# S57 gate G3: rule R27 on 705 unseen Mintaka releases (quote-only blind review)", "",
           f"Witnesses: {nw} of 705 ({100*nw/705:.1f}%). Decoys misleading for both reviewers: {dec}/{len(V['decoy'])} ({'VALID' if dec >= 27 else 'INVALID'}).", "",
           "| Quotes | n | misleading for both | 'states' for both |", "|---|---|---|---|",
           row("R27 witness, all releases with a witness", V["witness"]), row("Displayed quote where it differs from the witness", V["displayed"])]
    (D / "G3_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
