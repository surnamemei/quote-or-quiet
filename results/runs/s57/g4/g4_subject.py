"""S57 G4 design: rule P (page subject). For each Q1c+T release on the design data, the 27B is asked whether the witness page is about the thing the question asks about.
Release only if YES. 27B on 11540: python -B results/runs/s57/g4/g4_subject.py judge ; report: OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s57/g4/g4_subject.py report"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20"), str(ROOT / "results/runs/s22"), str(ROOT / "results/runs/s57/g4")]
os.environ.setdefault("OLLAMA_HOST_URL", "http://127.0.0.1:11540")
D = ROOT / "results/runs/s57/g4"
PP = ('Question: {q}\nWikipedia page title: {t}\nSentence from that page: "{s}"\n\n'
      "Is this page about the same person, thing, place or event that the question asks about, and not about a different one with the same or a similar name? "
      "If the question could mean several different ones, reply NO. Reply with only YES or NO.")


def releases(name, J):
    from temporal import time_sensitive
    for r in map(json.loads, open(D / f"{name}_cands.jsonl", encoding="utf-8")):
        w = [(ci, [si for si in range(len(c["spans"])) if J.get(f"{r['id']}|{ci}|{si}", {}).get("w")]) for ci, c in enumerate(r["cands"])]
        w = [(ci, s) for ci, s in w if s]
        if len(w) == 1 and not time_sensitive(r["question"]):
            ci, s = w[0]; yield r, r["cands"][ci], r["cands"][ci]["spans"][s[0]]


if __name__ == "__main__":
    import no_retrieval2  # noqa: F401
    J = json.load(open(D / "g4_judge.json", encoding="utf-8")); PF = D / "g4_subject.json"
    P = json.load(open(PF, encoding="utf-8")) if PF.exists() else {}
    if sys.argv[1] == "judge":
        from vkg.llm import chat
        for name in ("mintaka_dev", "mintaka_test"):
            for r, c, s in releases(name, J):
                if r["id"] not in P:
                    P[r["id"]] = str(chat("qwen3.8-27b", [{"role": "user", "content": PP.format(q=r["question"], t=s["doc"], s=s["quote"])}], temperature=0.0, seed=0, max_tokens=4, think=False, json_mode=False, num_ctx=4096, timeout=900))
                    if len(P) % 100 == 0:
                        json.dump(P, open(PF, "w", encoding="utf-8")); print(len(P), flush=True)
        json.dump(P, open(PF, "w", encoding="utf-8")); print("subject done", len(P), flush=True)
    else:
        from abstain_dev import grade
        from g4_rules import REC
        from scipy.stats import beta
        up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k)
        out = ["# S57 G4 design: rule P (27B page-subject check) on Q1c+T releases (design data; gold-relative)", "", "| set | variant | released | coverage | wrong (gold) | SER | upper | dropped by P (wrong among them) |", "|---|---|---|---|---|---|---|---|"]
        for name, n in (("mintaka_dev", 200), ("mintaka_test", 2000)):
            for var in ("Q1c+T", "Q1c+T+P", "Q1c+T+P+T2"):
                rel = wr = dp = dw = 0
                for r, c, s in releases(name, J):
                    g = grade(r["question"], r["gold"], c["answer"]) is False
                    if "P" in var.split("+") and not str(P.get(r["id"], "")).strip().upper().startswith("YES"):
                        dp += 1; dw += g; continue
                    if "T2" in var and REC.search(r["question"]):
                        continue
                    rel += 1; wr += g
                out.append(f"| {name} | {var} | {rel} | {100*rel/n:.1f}% | {wr} | {100*wr/n:.2f}% | {up(wr, n):.2f}% | {dp} ({dw}) |")
        (D / "G4_subject_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
