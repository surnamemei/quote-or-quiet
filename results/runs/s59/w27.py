"""S59 design for G8 (design data only, after the G8 result): rule W4-27 = W4 with the Qwen3.8-27B judge in place of the 4B judge (same prompts: value YES and swapped value NO;
number check and 75% value coverage unchanged). judge: 27B on 11540, all eligible candidates, resumable.  eval: on the reviewed slots of S59.
python -B results/runs/s59/w27.py judge ; OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s59/w27.py eval"""
import csv, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8"); sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20"), str(ROOT / "results/runs/s59")]
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
D = ROOT / "results/runs/s59"
slots = [json.loads(l) for l in open(D / "f5_cands.jsonl", encoding="utf-8")]
yes = lambda o: str(o or "").strip().upper().startswith("YES")
STOPW = None


def eligible(s, c):
    from f5_sheet_rules import cov
    return c["N"] and c["swap"] and cov(s["value"], c["quote"]) >= 0.75


if sys.argv[1] == "judge":
    from vkg.llm import chat
    ask = lambda p: str(chat("qwen3.8-27b", [{"role": "user", "content": p}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))
    PF = D / "w27_judge.json"; J = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    n = 0
    for s in slots:
        for k, c in enumerate(s["cands"]):
            key = f"{s['id']}|{k}"
            if key in J or not eligible(s, c):
                continue
            a = ask(c["j"]); b = ask(c["j_swap"]) if yes(a) else None
            J[key] = [a, b]; n += 1
            if n % 200 == 0:
                json.dump(J, open(PF, "w", encoding="utf-8")); print(n, flush=True)
            if yes(a) and not yes(b):
                break
    json.dump(J, open(PF, "w", encoding="utf-8")); print("w27 judge done", len(J), flush=True)
else:
    from scipy.stats import beta
    J = json.load(open(D / "w27_judge.json", encoding="utf-8")); OUT = json.load(open(D / "f5_out.json", encoding="utf-8"))
    def wit(s, judge):
        for k, c in enumerate(s["cands"]):
            if not eligible(s, c):
                continue
            o = judge.get(f"{s['id']}|{k}")
            if o and yes(o[0]) and not yes(o[1]):
                return k
        return None
    w4 = {s["id"]: wit(s, OUT) for s in slots}; w27 = {s["id"]: wit(s, J) for s in slots}
    K = json.load(open(D / "F5_key.json", encoding="utf-8")); V = {}
    for p, ks in K.items():
        vv = {}
        for rv in "AB":
            for r in csv.DictReader(open(D / f"F5_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
                vv.setdefault(int(r["row"]), []).append((r["quote_verdict"].strip().casefold(), r["true_verdict"].strip().casefold()))
        for k in ks:
            if k["kind"] == "kept":
                V[k["id"]] = vv[k["row"]]
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k)
    rev = [i for i in V]; keep27 = [i for i in rev if w27[i] is not None and w27[i] == w4[i]]
    f = lambda ids: sum(V[i][0][1] == V[i][1][1] == "wrong" for i in ids); m = lambda ids: sum(V[i][0][0] == V[i][1][0] == "not" for i in ids)
    other = [i for i in rev if w27[i] is not None and w27[i] != w4[i]]
    out = ["# S59 design: W4 with the 27B judge (W4-27) on the reviewed G8 slots", "",
           f"All slots: W4 keeps {sum(v is not None for v in w4.values())} of {len(slots)}; W4-27 keeps {sum(v is not None for v in w27.values())}.",
           f"Reviewed kept slots (W4): {len(rev)}; false {f(rev)}, misleading {m(rev)}.",
           f"Of these, W4-27 keeps {len(keep27)} with the same quote: false {f(keep27)} ({100*f(keep27)/max(1,len(keep27)):.1f}%, upper {up(f(keep27), len(keep27)):.1f}%), misleading {m(keep27)} ({100*m(keep27)/max(1,len(keep27)):.1f}%, upper {up(m(keep27), len(keep27)):.1f}%);",
           f"W4-27 keeps {len(other)} more with a different quote (not reviewed); it drops {len(rev)-len(keep27)-len(other)} of the reviewed slots."]
    (D / "W27_design_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
