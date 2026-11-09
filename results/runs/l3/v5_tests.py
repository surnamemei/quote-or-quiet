import sys
from collections import Counter
sys.path.insert(0, "results/runs/l3"); sys.path.insert(0, "results/runs/s22"); sys.path.insert(0, ".")
from qualified_dev import releases
import qualified, qualified_v5
from abstain_dev import grade
T = Counter()
for name in ("fresh5", "mintaka_test", "popqa_test"):
    for r, rel, doc, m in releases(name):
        g = grade(r["question"], r["gold"], rel)
        a = qualified.decide(r["question"], rel, doc, strict=True); b = qualified_v5.decide(r["question"], rel, doc, strict=True)
        T[(name, "v4", a[0], g)] += 1; T[(name, "v5", b[0], g)] += 1
        if a[0] != b[0] or a[1] != b[1]: print(name, g, a[0], "->", b[0], "|", r["question"][:70], "|", rel, "|", b[1], "|", b[2].get("why"))
for name in ("fresh5", "mintaka_test", "popqa_test"):
    for v in ("v4", "v5"):
        print(name, v, {s: (T[(name, v, s, True)], T[(name, v, s, False)]) for s in ("Verified", "Qualified", "Unresolved")})
