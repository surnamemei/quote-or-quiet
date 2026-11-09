"""Question-only features of each benchmark (no system output used): share of time-sensitive questions (rule from S22 DEV) and
share of questions whose first indexed mention has two or more Wikipedia senses. Read-only. python -I -B results/runs/s23/qfeatures.py"""
import sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s22")); sys.path.insert(0, str(ROOT / "results/runs/l3")); sys.path.insert(0, str(ROOT / "results/runs/s23"))
import psutil
psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
from temporal import time_sensitive
import indep_dev as ID
from vkg import s17_run as R
out = ["# Question-only features per benchmark", "", "| set | n | time-sensitive (rule) | first mention has >= 2 senses | no indexed mention |", "|---|---|---|---|---|"]
for n in ("fresh5", "mintaka_test", "popqa_test", "mintaka_dev", "popqa_dev", "dev"):
    it = R.items(n); N = len(it); ts = multi = none = 0
    for e in it:
        q = e["question"]; ts += time_sensitive(q)
        found = False
        for m in ID.mentions(q):
            nm = ID.norm(m); bare = re.sub(r"^the ", "", nm)
            c = ID.T.execute("SELECT count(*) FROM t WHERE ncore IN (?,?)", (bare, "the " + bare)).fetchone()[0]
            if c:
                found = True; multi += c >= 2; break
        none += not found
    out.append(f"| {n} | {N} | {ts} ({ts/N:.3f}) | {multi} ({multi/N:.3f}) | {none} ({none/N:.3f}) |")
    print(out[-1], flush=True)
(ROOT / "results/runs/s23/qfeatures.md").write_text("\n".join(out) + "\n", encoding="utf-8")
