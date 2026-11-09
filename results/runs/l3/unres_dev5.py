import sys, json
sys.path.insert(0, "results/runs/l3"); sys.path.insert(0, "results/runs/s22"); sys.path.insert(0, ".")
from qualified_dev import releases
from qualified_v5 import decide, senses, norm
from abstain_dev import grade
for name in ("popqa_dev", "mintaka_dev", "dev", "fresh"):
    for r, rel, doc, m in releases(name):
        st, sense, info = decide(r["question"], rel, doc, strict=True)
        if st == "Unresolved":
            g = grade(r["question"], r["gold"], rel)
            ss = senses(norm(info.get("mention", "")), info.get("mention")) if info.get("mention") else ()
            print(name, g, "|", r["question"][:90], "| A:", rel, "| doc:", doc, "|", info, "| nsenses", len(ss), [t for t,_,_ in ss][:6])
