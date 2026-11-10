"""S42 E2 and E3 (docs/S42_CLAIM_AUDIT_AND_PLAN.md), S29 sealed set (opened), existing reader outputs only. CPU; loads local wiki pages (idle priority).
E2: claims from three generators through the frozen rule used as a claim verifier (value = only candidate).
E3: rule Q (Qualified = not released, max-support candidate passes the deductive gate) and the paired matrix with Qualified added.
OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s42/claims.py"""
import json, os, re, sys
from collections import Counter
from pathlib import Path
from scipy.stats import beta
ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
import no_retrieval2  # noqa: F401,E402
from abstain_dev import grade  # noqa: E402
from vkg import s17_eval as S, l3_checks2 as C, localwiki as LW  # noqa: E402
from vkg.s12_run import agree  # noqa: E402
from vkg.s14_eval import ans  # noqa: E402
from vkg.s21_judge import aliases  # noqa: E402
D = ROOT / "results/runs/s29/run_fsm"; O = ROOT / "results/runs/s42"
rows = {r["id"]: r for r in map(json.loads, open(D / "wd_outputs.jsonl", encoding="utf-8"))}
phi = {r["id"]: r["answer"] for r in map(json.loads, open(D / "wd_phi4.jsonl", encoding="utf-8"))}
REL = {r["id"]: r for r in map(json.loads, open(D / "wd_releases.jsonl", encoding="utf-8"))}
CB = {r["id"]: r for r in map(json.loads, open(D / "wd_closed.jsonl", encoding="utf-8"))}
txt = (ROOT / "results/runs/s29/review/wd/L2_result.md").read_text(encoding="utf-8")
kept_txt = txt.split("Kept errors:")[1].split("Removed errors:")[0]
kept_q = set(re.findall(r"^- \[\w+\] (.+?) \| gold", kept_txt, re.M))
cleared_q = set(re.findall(r"^- \[\w+\] (.+?) \| gold", txt.split("Removed errors:")[1], re.M))
QUOTES = "'" + '"'


def up(k, n):
    return 100 * beta.ppf(0.975, k + 1, n - k) if n > k else 100.0


def gmatch(r, v):
    g = grade(r["question"], r["gold"], v)
    if g == "?":   # no cached label: plain string agreement with a reference alias (marked with * in the output)
        return "right*" if any(agree(str(v), a) for a in aliases(r["gold"])) else "wrong*"
    return "right" if g else "wrong"


def verify(r, v):
    """Frozen rule with the claim's value as the only candidate."""
    v = str(v).strip().strip(QUOTES).rstrip(".")
    if not ans(v) or S.support(r, v) < 3:
        return False, "support"
    rel, rec = C.release2(r["question"], v, r["wiki_titles"], LW.page_text)
    if not rel:
        return False, "gate"
    p = phi.get(r["id"])
    if not (ans(p) and agree(str(rel), str(p))):
        return False, "phi4"
    text = LW.page_text(rec["doc"])
    assert text[rec["start"]:rec["end"]] == rec["span"], "quote check failed"
    return True, rec["doc"]


out = ["# S42 E2: claims from hostile generators through the verifier (S29 sealed set, opened; existing reader outputs)", ""]
res = {}
# (a) raw model short closed-book answers
A = [(i, CB[i]["b0"]) for i in rows if ans(CB[i]["b0"]) and len(str(CB[i]["b0"]).split()) <= 4]
T = Counter(); leaks = []
for i, v in A:
    k, why = verify(rows[i], v); g = gmatch(rows[i], v)
    T[(g, k)] += 1
    if k and g.startswith("wrong"):
        q = rows[i]["question"]
        leaks.append((q, rows[i]["gold"][:2], v, REL.get(i, {}).get("answer"), "cleared by S29 review" if q in cleared_q else ("not cleared" if q in kept_q else "not reviewed")))
nw = sum(n for (g, k), n in T.items() if g.startswith("wrong")); nr = sum(n for (g, k), n in T.items() if g.startswith("right"))
kw = sum(n for (g, k), n in T.items() if g.startswith("wrong") and k); kr = sum(n for (g, k), n in T.items() if g.startswith("right") and k)
notcl = sum(1 for x in leaks if x[4] != "cleared by S29 review")
out += [f"## (a) Raw model, closed book, answers of 4 words or fewer: {len(A)} claims", "",
        f"Gold-wrong claims {nw}: kept {kw} ({100*kw/nw:.2f}%), of which not cleared by review {notcl} ({100*notcl/nw:.2f}%, one-sided 97.5% upper bound {up(notcl, nw):.2f}%).",
        f"Gold-right claims {nr}: kept {kr} ({100*kr/nr:.1f}%).", f"Labels by string match only (no cached label): {sum(n for (g, k), n in T.items() if g.endswith('*'))}.", "", "Kept gold-wrong claims:", ""]
out += [f"- {q} | gold {g} | claim {v} | system released {a} | {st}" for q, g, v, a, st in leaks] + [""]
res["a"] = {"claims": len(A), "wrong": nw, "wrong_kept": kw, "wrong_kept_not_cleared": notcl, "right": nr, "right_kept": kr}
# (b) decoys: the reference answer of the next question of the same relation whose answer differs
by = {}
for i, r in rows.items():
    by.setdefault(r["stratum"], []).append(i)
kb = 0; nb = 0; lb = []
for st, ids in by.items():
    for n_, i in enumerate(ids):
        for d in range(1, len(ids)):
            j = ids[(n_ + d) % len(ids)]; v = rows[j]["gold"][0]
            if not any(agree(v, a) for a in aliases(rows[i]["gold"])):
                break
        else:
            continue
        nb += 1; k, why = verify(rows[i], v)
        if k:
            kb += 1; lb.append((rows[i]["question"], rows[i]["gold"][:2], v, REL.get(i, {}).get("answer")))
out += [f"## (b) Decoy generator (another question's reference answer, same relation): {nb} claims", "", f"Kept {kb} ({100*kb/nb:.3f}%, one-sided 97.5% upper bound {up(kb, nb):.3f}%).", ""]
out += [f"- {q} | gold {g} | decoy {v} | system released {a}" for q, g, v, a in lb] + [""]
res["b"] = {"claims": nb, "kept": kb}
# (c) reader answers that disagree with the released answer
kc = 0; nc = 0; lc = []
for i, x in REL.items():
    r = rows[i]; seen = []
    for v in [r.get(k_) for k_ in S.ORDER] + [phi.get(i)]:
        if ans(v) and not agree(str(v), x["answer"]) and not any(agree(str(v), s_) for s_ in seen):
            seen.append(str(v)); nc += 1
            k, why = verify(r, v)
            if k:
                kc += 1; lc.append((r["question"], r["gold"][:2], v, x["answer"], gmatch(r, v)))
out += [f"## (c) Reader answers that disagree with the released answer: {nc} claims on {len(REL)} released questions", "", f"Kept {kc} ({100*kc/max(nc,1):.2f}%).", ""]
out += [f"- {q} | gold {g} | claim {v} | system released {a} | claim vs gold: {m}" for q, g, v, a, m in lc] + [""]
res["c"] = {"claims": nc, "kept": kc}
(O / "E2_claims.md").write_text("\n".join(out), encoding="utf-8"); print("\n".join(out)[:6000])
json.dump(res, open(O / "E2_claims.json", "w", encoding="utf-8"), indent=1)
# ---------------- E3: rule Q
Q = {}
for i, r in rows.items():
    if i in REL:
        continue
    a, s = S.cand(r)
    if not ans(a):
        continue
    rel, rec = C.release2(r["question"], a, r["wiki_titles"], LW.page_text)
    if rel:
        text = LW.page_text(rec["doc"]); sent = C.sentence_at(text, rec["start"], rec["end"]).strip()[:300]
        p = phi.get(i)
        Q[i] = {"id": i, "relation": r["stratum"], "question": r["question"], "gold": r["gold"], "answer": str(rel), "doc": rec["doc"], "quote": sent, "support": s,
                "phi4_agrees": bool(ans(p) and agree(str(rel), str(p))), "match": gmatch(r, rel)}
with open(O / "E3_qualified.jsonl", "w", encoding="utf-8") as f:
    for x in Q.values():
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
n = len(rows); nq = len(Q); rq = sum(x["match"].startswith("right") for x in Q.values())
o3 = ["# S42 E3: rule Q on the S29 sealed set (opened; post hoc)", "", f"Verified {len(REL)} ({100*len(REL)/n:.1f}%), Qualified {nq} ({100*nq/n:.1f}%), Unresolved {n-len(REL)-nq} ({100*(n-len(REL)-nq)/n:.1f}%).",
      f"Answer inside the Qualified quote matches gold: {rq} of {nq} ({100*rq/max(nq,1):.1f}%); labels by string match only: {sum(x['match'].endswith('*') for x in Q.values())}.", "",
      "| cell | n | matches gold |", "|---|---|---|"]
cells = Counter(); cr = Counter()
for x in Q.values():
    c = (f"support {x['support']}", "Phi-4 agrees" if x["phi4_agrees"] else "Phi-4 differs or silent"); cells[c] += 1; cr[c] += x["match"].startswith("right")
o3 += [f"| {a}, {b} | {cells[(a, b)]} | {cr[(a, b)]} ({100*cr[(a, b)]/cells[(a, b)]:.1f}%) |" for a, b in sorted(cells)]
o3 += ["", "| relation | Qualified | matches gold |", "|---|---|---|"]
for st in by:
    xs = [x for x in Q.values() if x["relation"] == st]
    if xs:
        o3.append(f"| {st} | {len(xs)} | {sum(x['match'].startswith('right') for x in xs)} ({100*sum(x['match'].startswith('right') for x in xs)/len(xs):.1f}%) |")


def state(i):
    if i in REL:
        return "Verified"
    return "Qualified, quote holds the gold answer" if i in Q and Q[i]["match"].startswith("right") else ("Qualified, quote holds another answer" if i in Q else "Unresolved")


ST = ["Verified", "Qualified, quote holds the gold answer", "Qualified, quote holds another answer", "Unresolved"]
for name, get in (("Raw model, closed book", lambda i: CB[i]["b0"]), ("Standard RAG", lambda i: rows[i].get("combo_plain"))):
    M = Counter()
    for i, r in rows.items():
        a = get(i); g = grade(r["question"], r["gold"], a) if ans(a) else None
        M[("no answer" if g is None else "right" if g is True else "wrong" if g is False else "unlabelled", state(i))] += 1
    o3 += ["", f"## {name} answer against the three states", "", "| baseline outcome | n | " + " | ".join(ST) + " |", "|---|---|---|---|---|---|"]
    for b in ("wrong", "right", "no answer", "unlabelled"):
        t = sum(M[(b, s_)] for s_ in ST)
        if t:
            o3.append(f"| {b} | {t} | " + " | ".join(f"{M[(b, s_)]} ({100*M[(b, s_)]/t:.1f}%)" for s_ in ST) + " |")
(O / "E3_qualified.md").write_text("\n".join(o3), encoding="utf-8"); print("\n".join(o3))
