"""S57 G4 design: extra withholding rules evaluated on the design releases of Q1c+T (design data only).
E (entity): withhold when the witness page title carries a qualifier, '(...)' or ', X', whose words are not in the question, and the title index holds another page
   with the same core name; or when the title has content words (not in the question) in front of a core name that is itself a page (e.g. 'Australian House of Representatives').
T2 (records): withhold questions about records and superlatives over time (most, all-time, all time, record, leading, longest, highest, largest number).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s57/g4/g4_rules.py"""
import json, os, re, sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path[:0] = [str(ROOT), str(ROOT / "results/runs/s20"), str(ROOT / "results/runs/s22")]
import no_retrieval2  # noqa: F401
from temporal import time_sensitive
from abstain_dev import grade
from scipy.stats import beta
D = ROOT / "results/runs/s57/g4"
db = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True)
STOP = set("the a an of in on at to for and or is was were what who when where which how many much did does do year first".split())
words = lambda s: {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP}
REC = re.compile(r"\b(most|all[- ]time|record|records|leading|longest|highest|largest number)\b", re.I)


def rule_e(q, title):
    m = re.match(r"^(.*?)(?: \(([^)]*)\)|, (.+))$", title)
    qw = words(q)
    if m:
        core, qual = m.group(1), m.group(2) or m.group(3)
        if not (words(qual) <= qw) and db.execute("select count(*) from t where core = ? and title != ?", (core, title)).fetchone()[0] > 0:
            return True
    tw = title.split()
    for k in range(1, len(tw)):
        head, rest = " ".join(tw[:k]), " ".join(tw[k:])
        if not (words(head) <= qw) and words(rest) and words(rest) <= qw and db.execute("select 1 from t where title = ?", (rest,)).fetchone():
            return True
    return False


def run(name, Jf):
    J = json.load(open(D / Jf, encoding="utf-8")); R = [json.loads(l) for l in open(D / f"{name}_cands.jsonl", encoding="utf-8")]
    res = {}
    for var in ("Q1c+T", "Q1c+T+E", "Q1c+T+T2", "Q1c+T+E+T2"):
        rel = wr = 0
        for r in R:
            w = [(ci, [si for si in range(len(c["spans"])) if J.get(f"{r['id']}|{ci}|{si}", {}).get("w")]) for ci, c in enumerate(r["cands"])]
            w = [(ci, s) for ci, s in w if s]
            if len(w) != 1 or time_sensitive(r["question"]):
                continue
            ci, s = w[0]; title = r["cands"][ci]["spans"][s[0]]["doc"]
            if "E" in var.split("+") and rule_e(r["question"], title):
                continue
            if "T2" in var and REC.search(r["question"]):
                continue
            rel += 1; wr += grade(r["question"], r["gold"], r["cands"][ci]["answer"]) is False
        res[var] = (len(R), rel, wr)
    return res


if __name__ == "__main__":
    up = lambda k, n: 100 * beta.ppf(0.975, k + 1, n - k)
    out = ["# S57 G4 design: withholding rules E and T2 (design data; gold-relative)", "", "| set | variant | released | coverage | wrong (gold) | SER | upper |", "|---|---|---|---|---|---|---|"]
    for name in ("mintaka_dev", "mintaka_test"):
        for var, (n, rel, wr) in run(name, "g4_judge.json").items():
            out.append(f"| {name} | {var} | {rel} | {100*rel/n:.1f}% | {wr} | {100*wr/n:.2f}% | {up(wr, n):.2f}% |")
    (D / "G4_rules_result.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
