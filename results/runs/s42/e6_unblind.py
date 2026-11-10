"""Unblind S42 E6 (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 7): does the quoted sentence state the released answer to the question?
misleading = both reviewers say 'not'; needs the page = neither says 'states' and the row is not misleading.
Scores the frame check F, the quote-only reader with swap G (4B; Phi-4 secondary) and the strict rule F and G against the review.
Writes E6_result.md (counts only) and E6_verdict_listing.md (per-item, stays out of the release).
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/e6_unblind.py"""
import csv, json, os, sys
from collections import Counter
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa: F401,E402
from vkg.s12_run import agree     # noqa: E402
from vkg.s14_eval import ans      # noqa: E402
D = ROOT / "results/runs/s42"
X = {x["id"]: x for x in (json.loads(l) for l in open(D / "e6_items.jsonl", encoding="utf-8"))}
K = json.load(open(D / "E6_key.json", encoding="utf-8"))
G4 = json.load(open(D / "e6_g4.json", encoding="utf-8")) if (D / "e6_g4.json").exists() else {}   # empty: interim run before the reader step
GPH = json.load(open(D / "e6_gphi.json", encoding="utf-8")) if (D / "e6_gphi.json").exists() else {}


def up(k, n):
    return 100 * beta.ppf(0.975, k + 1, n - k) if n and k < n else 100.0


def said(o):
    o = str(o or "").strip().strip("'\".")
    return o if ans(o) and not o.upper().startswith("NONE") else None


def gpass(x, o):
    a, b = said(o[0]), said(o[1])
    return bool(a and agree(x["answer"], a) and b and agree(x["swap"], b))


def gstep1(x, o):
    a = said(o[0])
    return bool(a and agree(x["answer"], a))


for i, x in X.items():
    x["G"] = gpass(x, G4[i]) if G4 else None; x["G1"] = gstep1(x, G4[i]) if G4 else None; x["strict"] = (x["frame_ok"] and x["G"]) if G4 else None
    x["Gphi"] = gpass(x, GPH[i]) if i in GPH else None
rows = []
for p, ks in K.items():
    V = {}
    for rv in ("A", "B"):
        for r in csv.DictReader(open(D / f"E6_verdict_part{p}_{rv}.csv", encoding="utf-8-sig")):
            v = r["verdict"].strip().strip("'\"").casefold()
            assert v in ("states", "incomplete", "not"), (p, rv, r["row"], v)
            V.setdefault(int(r["row"]), []).append(v)
    for k in ks:
        v = V[k["row"]]; assert len(v) == 2, (p, k["row"])
        rows.append({**k, "v": v, "mis": v == ["not", "not"], "page": "states" not in v and v != ["not", "not"], "either": "not" in v, "x": X[k["id"]]})


def line(name, sel):
    n = len(sel); k = sum(r["mis"] for r in sel); pg = sum(r["page"] for r in sel)
    return f"| {name} | {n} | {k} | {100*k/max(1,n):.1f}% | {up(k,n):.1f}% | {pg} ({100*pg/max(1,n):.1f}%) | {sum(r['either'] for r in sel)} |"


HEAD = ["| Rows | n | Misleading (both 'not') | Rate | 97.5% upper | Needs the page | 'not' for either |", "|---|---|---|---|---|---|---|"]
ver = [r for r in rows if r["kind"] == "verified"]; qua = [r for r in rows if r["kind"] == "qualified"]; tgt = [r for r in rows if r["kind"] == "targeted"]
dec = [r for r in rows if r["kind"].startswith("decoy")]
out = ["# S42 E6: does the quote state the answer? (S29 outputs, blind review of the quote alone)", ""]
if not G4:
    out += ["INTERIM: the quote-only reader has not run yet; only the review and the frame check are scored.", ""]
nd = sum(r["mis"] for r in dec)
out += [f"Decoys misleading for both reviewers: {nd}/{len(dec)} ({'VALID' if nd >= 0.9 * len(dec) else 'INVALID'}); answer decoys {sum(r['mis'] for r in dec if r['kind']=='decoy_answer')}/"
        f"{sum(r['kind']=='decoy_answer' for r in dec)}, question decoys {sum(r['mis'] for r in dec if r['kind']=='decoy_question')}/{sum(r['kind']=='decoy_question' for r in dec)}.",
        f"Reviewers gave the same verdict in {sum(r['v'][0]==r['v'][1] for r in rows)}/{len(rows)} rows; verdict pairs on the Verified sample: "
        f"{dict(Counter(tuple(sorted(r['v'])) for r in ver).most_common())}.", ""]
out += HEAD + [line("Verified, random sample", ver), line("Qualified, random sample", qua), line("Targeted (gold-mismatch releases outside the sample)", tgt)]
out += ["", "Verified sample by relation:", ""] + HEAD + [line(rel, [r for r in ver if r["x"]["relation"] == rel]) for rel in sorted({r["x"]["relation"] for r in ver})]
out += ["", "Qualified sample by relation:", ""] + HEAD + [line(rel, [r for r in qua if r["x"]["relation"] == rel]) for rel in sorted({r["x"]["relation"] for r in qua})]
allv = [x for x in X.values() if x["state"] == "Verified"]; allq = [x for x in X.values() if x["state"] == "Qualified"]
CH = [("F frame check", "frame_ok"), ("G quote-only reader with swap (4B)", "G"), ("G step 1 only (no swap)", "G1"), ("Strict rule: F and G", "strict")]
CH = CH if G4 else CH[:1]
for title, sel, pop in (("Verified", ver, allv), ("Qualified", qua, allq)):
    nm = sum(r["mis"] for r in sel)
    out += ["", f"Mechanical checks on the {title} sample (n {len(sel)}, misleading {nm}):", "",
            "| Check | Passes, all items | Passes, sample | Removed from sample | Misleading caught | Misleading left | Rate left | 97.5% upper | Needs the page, left |", "|---|---|---|---|---|---|---|---|---|"]
    for name, f in CH + ([("G with Phi-4 (secondary)", "Gphi")] if GPH else []):
        ps = [r for r in sel if r["x"][f]]; k = sum(r["mis"] for r in ps)
        allp = f"{sum(bool(x[f]) for x in pop)}/{len(pop)} ({100*sum(bool(x[f]) for x in pop)/len(pop):.1f}%)" if f != "Gphi" else "reviewed rows only"
        out.append(f"| {name} | {allp} | {len(ps)} | {len(sel)-len(ps)} ({100*(len(sel)-len(ps))/len(sel):.1f}%) | {nm-k}/{nm} | {k} | {100*k/max(1,len(ps)):.1f}% | {up(k,len(ps)):.1f}% | "
                   f"{sum(r['page'] for r in ps)} ({100*sum(r['page'] for r in ps)/max(1,len(ps)):.1f}%) |")
gm = [r for r in ver if not r["x"]["gold_match"]]
out += ["", f"Verified sample, answer matches the gold: misleading {sum(r['mis'] for r in ver if r['x']['gold_match'])}/{len(ver)-len(gm)}; does not match: {sum(r['mis'] for r in gm)}/{len(gm)}.",
        f"Targeted stratum: strict rule removes {sum(not r['x']['strict'] for r in tgt)}/{len(tgt)}; of its misleading rows it removes {sum(r['mis'] and not r['x']['strict'] for r in tgt)}/{sum(r['mis'] for r in tgt)}."]
dr = [r for r in rows if not r["kind"].startswith("decoy") and "Dominican Republic" in r["x"]["question"] and "2011" in r["x"]["question"]]
out += [f"Dominican Republic 2011: " + ("; ".join(f"{r['kind']} verdicts {r['v']}, F {r['x']['frame_ok']}, G {r['x']['G']}" for r in dr) or
        "; ".join(f"not on the sheet; state {x['state']}, F {x['frame_ok']}, G {x['G']}" for x in X.values() if "Dominican Republic" in x["question"] and "2011" in x["question"]))]
(D / "E6_result.md").write_text("\n".join(out) + "\n", encoding="utf-8")
lst = ["# E6 per-item listing (not for release)", ""]
for title, sel in (("Verified sample, misleading", [r for r in ver if r["mis"]]), ("Verified sample, needs the page", [r for r in ver if r["page"]]),
                   ("Verified sample, split with one 'not'", [r for r in ver if r["either"] and not r["mis"] and not r["page"]]),
                   ("Qualified sample, misleading", [r for r in qua if r["mis"]]), ("Targeted", tgt), ("Decoys not caught", [r for r in dec if not r["mis"]])):
    lst += ["", f"## {title} ({len(sel)})", ""]
    lst += [f"- {r['x']['question']} | {r['x']['answer']} | {r['v']} | F {r['x']['frame_ok']} G {r['x']['G']} gold {r['x']['gold_match']} | {r['x']['doc']}: {r['x']['quote'][:200]} || 4B: {G4.get(r['id'])}" for r in sel]
(D / "E6_verdict_listing.md").write_text("\n".join(lst) + "\n", encoding="utf-8")
print("\n".join(out))
