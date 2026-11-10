"""S56 follow-up: reversal control that is valid by construction (no reviewers; cached 27B verdicts of e12_judge.json).
A candidate sentence is usable when it contains the party word X of the statement (word boundary) and not its opposite Y: then the flipped statement (Y for X) is
not reported by this sentence, whatever the sentence says about the view. Counts the share of such flips the 27B accepts (YES) in rule A's use, and the share of original statements accepted for the same sentences.
python -B results/runs/s56/e12_reversal_control.py"""
import json, re, sys
from pathlib import Path
from scipy.stats import beta
D = Path(__file__).resolve().parent; sys.stdout.reconfigure(encoding="utf-8")
FLIP = [("supporters", "critics"), ("proponents", "opponents"), ("advocates", "opponents"), ("defenders", "critics"), ("in favour of", "against"), ("in favor of", "against"), ("supporters", "opponents")]
S = [json.loads(l) for l in open(D / "e12_cands.jsonl", encoding="utf-8")]; J = json.load(open(D / "e12_judge.json", encoding="utf-8"))
yes = lambda o: str(o or "").strip().upper().startswith("YES")
has = lambda w, t: re.search(r"\b" + re.escape(w) + r"\b", t.lower()) is not None
n = fy = oy = 0; stm = set(); stm_fy = set()
for s in S:
    if not s["flipped"]: continue
    for a, b in FLIP:
        for x, y in ((a, b), (b, a)):
            if has(x, s["stmt"]) and not has(y, s["stmt"]):
                for k, c in enumerate(s["cands"]):
                    if has(x, c["quote"]) and not has(y, c["quote"]):
                        n += 1; stm.add(s["id"]); f = yes(J.get(f"JS|{s['id']}|{k}")); o = yes(J.get(f"J|{s['id']}|{k}")); fy += f; oy += o
                        if f: stm_fy.add(s["id"])
                break
up = lambda k, m: 100 * beta.ppf(0.975, k + 1, m - k) if m and k < m else 100.0
out = [f"# S56 reversal control by construction (cached 27B verdicts)\n", f"Usable candidates (sentence has the statement's party word, not its opposite): {n} in {len(stm)} statements.\n",
       f"27B accepts the flipped statement for {fy} of {n} candidates ({100*fy/max(1,n):.1f}%, 97.5% upper bound {up(fy,n):.1f}%); in {len(stm_fy)} of {len(stm)} statements ({100*len(stm_fy)/max(1,len(stm)):.1f}%, upper {up(len(stm_fy),len(stm)):.1f}%).\n",
       f"For the same candidates the 27B accepts the original statement for {oy} of {n} ({100*oy/max(1,n):.1f}%).\n"]
(D / "E12b_result.md").write_text("".join(out), encoding="utf-8"); print("".join(out))
