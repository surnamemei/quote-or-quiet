"""S42 E7 development scoring (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 8). Uses only items on the E6 sheet (verdicts already read).
For the first-span quote of each reviewed row it scores every combination of the checks against the review, and for each combination
it reports how many development items would keep a witness among the candidates that were run through the readers.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/e7_dev.py"""
import csv, itertools, json, os, sys
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20")); sys.path.insert(0, str(Path(__file__).parent))
import no_retrieval2  # noqa: F401,E402
from vkg.s12_run import agree     # noqa: E402
from vkg.s14_eval import ans      # noqa: E402
import e7_lib as L                # noqa: E402
D = ROOT / "results/runs/s42"
X = {x["id"]: x for x in (json.loads(l) for l in open(D / "e6_items.jsonl", encoding="utf-8"))}
CD = {c["id"]: c["cands"] for c in (json.loads(l) for l in open(D / "e7_cands.jsonl", encoding="utf-8"))}
OUT = json.load(open(D / "e7_dev_out.json", encoding="utf-8"))
K = json.load(open(D / "E6_key.json", encoding="utf-8"))


def up(k, n):
    return 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0


def said(o):
    o = str(o or "").strip().strip("'\".")
    return o if ans(o) and not o.upper().startswith("NONE") else None


def subj_match(subj, o):
    """Inverse answer names the question's subject: token containment, or all content tokens of the subject present (accents folded)."""
    if agree(subj, o) or agree(L.fold(subj), L.fold(o)):
        return True
    st = [w for w in L.toks(subj) if w not in L.QSTOP]; have = set(L.toks(o))
    return bool(st) and all(w in have for w in st)


def checks(x, k):
    c = CD[x["id"]][k]; o = OUT[f"{x['id']}|{k}"]; subj, _ = L.subject(x["relation"], x["question"])
    a, b, inv, con = (said(v) for v in o)
    return {"F": c["F"], "S": L.subject_link(x["question"], c["doc"], c["quote"]), "P": c["title_in_q"],
            "G": bool(a and agree(x["answer"], a)), "W": bool(b and agree(x["swap"], b)),
            "I": bool(inv and subj_match(subj, inv)), "C": not (con and agree(c["span"], con))}


rows = []
for p, ks in K.items():
    V = {}
    for rv in ("A", "B"):
        for r in csv.DictReader(open(D / f"E6_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            V.setdefault(int(r["row"]), []).append(r["verdict"].strip().strip("'\"").casefold())
    for k in ks:
        if not k["kind"].startswith("decoy"):
            v = V[k["row"]]; x = X[k["id"]]
            rows.append({"kind": k["kind"], "x": x, "v": v, "mis": v == ["not", "not"], "ok": v == ["states", "states"], "ch": checks(x, 0)})
NAMES = ["F", "S", "P", "G", "W", "I", "C"]
out = ["# S42 E7 development scoring (E6 sheet rows; first-span quote against the blind review)", "",
       "F frame check; S subject link; P page is the subject's page; G reader returns the answer; W reader follows the swapped span;",
       "I inverse question returns the subject; C contrasting question does not return the span.", ""]
for kind in ("verified", "qualified"):
    sel = [r for r in rows if r["kind"] == kind]; nm = sum(r["mis"] for r in sel); ns = sum(r["ok"] for r in sel)
    out += [f"## {kind}: n {len(sel)}, misleading {nm}, states for both {ns}", "", "Single checks:", "",
            "| Check | Passes | Misleading left | States kept |", "|---|---|---|---|"]
    for c in NAMES:
        ps = [r for r in sel if r["ch"][c]]
        out.append(f"| {c} | {len(ps)} | {sum(r['mis'] for r in ps)} | {sum(r['ok'] for r in ps)}/{ns} |")
    res = []
    for m in range(1, len(NAMES) + 1):
        for combo in itertools.combinations(NAMES, m):
            ps = [r for r in sel if all(r["ch"][c] for c in combo)]
            res.append((sum(r["mis"] for r in ps), -len(ps), "+".join(combo), len(ps), sum(r["ok"] for r in ps), sum(not r["mis"] and not r["ok"] for r in ps)))
    res.sort()
    out += ["", "Combinations (best 25 by misleading left, then by rows kept):", "",
            "| Checks | Passes | Misleading left | Rate | 97.5% upper | States kept | Other left |", "|---|---|---|---|---|---|---|"]
    out += [f"| {r[2]} | {r[3]} | {r[0]} | {100*r[0]/max(1,r[3]):.2f}% | {up(r[0],r[3]):.2f}% | {r[4]}/{ns} | {r[5]} |" for r in res[:25]]
    out.append("")
(D / "E7_dev.md").write_text("\n".join(out) + "\n", encoding="utf-8")
lst = ["# E7 development listing (not for release)", ""]
for r in rows:
    if r["kind"] == "verified" and (r["mis"] or not r["ok"]):
        x = r["x"]; lst.append(f"- {r['v']} | {''.join(c if r['ch'][c] else '.' for c in NAMES)} | {x['question']} | {x['answer']} | {x['doc']}: {x['quote'][:160]} || {OUT[x['id'] + '|0']}")
lst += ["", "## states for both, some check fails", ""]
for r in rows:
    if r["kind"] == "verified" and r["ok"] and not all(r["ch"][c] for c in ("F", "S", "G", "W", "I", "C")):
        x = r["x"]; lst.append(f"- {''.join(c if r['ch'][c] else '.' for c in NAMES)} | {x['question']} | {x['answer']} | {x['doc']}: {x['quote'][:160]} || {OUT[x['id'] + '|0']}")
(D / "E7_dev_listing.md").write_text("\n".join(lst) + "\n", encoding="utf-8")
print("\n".join(out))
