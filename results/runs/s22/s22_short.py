"""S22 short-answer rewrite (DEV design; user-approved direction "make the checks smarter, not looser").
Every reader output longer than 6 words (and the Phi-4 answer) is rewritten by the 4B into the shortest phrase that answers the
question. Hard constraint, checked in code: the short form must be a contiguous word-for-word substring of the original output
(case/whitespace/punctuation-insensitive); otherwise the original is kept. So the step can only cut, never add content.
Output: a new variant directory with outputs.jsonl and phi4.jsonl in the same format (keys rewritten), plus a log of rewrites.
usage: python -B s22_short.py <src_variant_dir> <dst_variant> <set> [phi4_path]"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import pod                                                  # noqa: E402
from vkg.s14_eval import ans                                         # noqa: E402

KEYS = [f"{s}_{k}" for s in ("web", "wiki", "combo") for k in ("plain", "cautious")]
PROMPT = ("Question: {q}\nAnswer given: {a}\n\nCopy the shortest part of the answer given that answers the question (at most 6 "
          "words), word for word, with nothing added. If the answer given says the answer is unknown or not in the passage, write "
          "unknown.\nShort answer:")


def words(s):
    return re.findall(r"[^\W_]+(?:['’.-][^\W_]+)*", str(s).casefold())


def is_sub(short, orig):
    a, b = words(short), words(orig)
    return bool(a) and len(a) <= 6 and any(b[i:i + len(a)] == a for i in range(len(b) - len(a) + 1))


def clean(raw):
    t = str(raw).strip().split("\n")[0].strip().strip('"').strip("'").rstrip(".").strip()
    return re.sub(r"^(short answer:\s*)", "", t, flags=re.I)


def main(src, dst, name, phi_path=None):
    src, out = Path(src), ROOT / "results/runs/s22" / dst
    out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in open(src / f"{name}_outputs.jsonl", encoding="utf-8")]
    pp = Path(phi_path) if phi_path else src / f"{name}_phi4.jsonl"
    phi = [json.loads(l) for l in open(pp, encoding="utf-8")]
    jobs = []                                    # (kind, index, key, original)
    for i, r in enumerate(rows):
        for k in KEYS:
            v = r.get(k)
            if ans(v) and len(words(v)) > 6:
                jobs.append(("row", i, k, str(v)))
    qmap = {r["id"]: r["question"] for r in rows}
    for i, p in enumerate(phi):
        if ans(p.get("answer")) and len(words(p["answer"])) > 6:
            jobs.append(("phi", i, "answer", str(p["answer"])))
    prompts = [PROMPT.format(q=(rows[i]["question"] if kd == "row" else qmap[phi[i]["id"]]), a=o) for kd, i, k, o in jobs]
    outs = pod.gen(prompts, 24) if prompts else []
    log, kept = [], 0
    for (kd, i, k, o), g in zip(jobs, outs):
        s = clean(g[0])
        ok = s.casefold() == "unknown" or is_sub(s, o)
        new = ("unknown" if s.casefold() == "unknown" else s) if ok else o
        if not ok:
            kept += 1
        (rows[i] if kd == "row" else phi[i])[k] = new
        log.append({"kind": kd, "i": i, "key": k, "orig": o, "short": s, "accepted": ok})
    with open(out / f"{name}_outputs.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / f"{name}_phi4.jsonl", "w", encoding="utf-8") as f:
        for p in phi:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(out / f"{name}_short_log.jsonl", "w", encoding="utf-8") as f:
        for x in log:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(f"{dst} {name}: rewrite jobs {len(jobs)}, rejected (not a substring) {kept}", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
