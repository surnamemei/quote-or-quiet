"""S39: the S23 independent-retrieval variant (results/runs/s23/s23_run.py, unchanged code) on the S39 design questions.
Patches only: output folder results/runs/s39/indep, item loader, web evidence copied from the S39 frozen run, page cache web_fsm.
python -B results/runs/s39/s39_indep.py s39d <gen|phi4|alias>"""
import os, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/runs/s23")); sys.path.insert(0, str(ROOT / "results/runs/s39"))
os.environ["S23_VARIANT"] = "indep"
import s23_run as V
import s39_run as F
from vkg import s17_run as R, websearch as W
V.OUT = ROOT / "results/runs/s39/indep"; V.OUT.mkdir(parents=True, exist_ok=True)
R.items = F.items
W.CACHE = ROOT / "results/cache/web_fsm"
name, stage = sys.argv[1], sys.argv[2]
src = ROOT / "results/runs/s39/run_fsm" / f"{name}_ev_web.json"
if stage == "gen" and not (V.OUT / f"{name}_ev_web.json").exists():
    shutil.copy(src, V.OUT / f"{name}_ev_web.json")
{"gen": V.gen, "phi4": V.phi4, "alias": V.alias}[stage](name)
