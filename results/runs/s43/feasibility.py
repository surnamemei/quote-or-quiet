import json, os, sys, collections
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations"); os.chdir(ROOT); sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s20"))
import no_retrieval2  # noqa
from vkg import l3_checks2 as C, l3_verify as V, localwiki as LW
N=collections.Counter(); T=collections.defaultdict(collections.Counter)
for b in map(json.loads, open(ROOT/"results/runs/s37/slots2.jsonl", encoding="utf-8")):
    text = LW.page_text(b["name"]); has = bool(text)
    for c in b["claims"]:
        v = str(c["value"]).strip().strip("'\""); t = c.get("type","?")
        N["slots"]+=1; T[t]["n"]+=1
        if not has: continue
        N["page"]+=1; T[t]["page"]+=1
        if v and v in text: N["value_in_page"]+=1; T[t]["in"]+=1
        rel, rec = C.release2(c["question"], v, [b["name"]], LW.page_text)
        if rel: N["gate"]+=1; T[t]["gate"]+=1
print(dict(N))
for t,c in sorted(T.items(), key=lambda x:-x[1]["n"])[:12]: print(t, dict(c))
