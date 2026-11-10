"""Progress tracker: reads results/progress.json, prints the bar and writes docs/PROGRESS_TRACKER.md. python -B results/progress.py"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.stdout.reconfigure(encoding="utf-8")
J = json.load(open(ROOT / "results/progress.json", encoding="utf-8")); G = J["gates"]
tot = 3 * len(G); got = sum(sum(g["met"]) for g in G)
bar = lambda a, b, w=30: "[" + "#" * round(w * a / b) + "." * (w - round(w * a / b)) + f"] {a}/{b} ({100*a/b:.0f}%)"
ST = {0: "Done or mostly done", 1: "Stage 1: close the measurement gaps (natural questions, ambiguity, chains)", 2: "Stage 2: new kinds of text and attribution", 3: "Stage 3: independent validity", 4: "Stage 4: apply to existing models"}
out = [f"# Progress tracker ({J['updated']})\n", "```", "Overall " + bar(got, tot, 40), "```\n", J["rule"] + "\n"]
for s in range(5):
    gs = [g for g in G if g["stage"] == s]
    if not gs: continue
    out += [f"\n## {ST[s]}: {bar(sum(sum(g['met']) for g in gs), 3*len(gs), 20)}\n", "| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |", "|---|---|---|---|---|---|---|"]
    for g in gs:
        out.append(f"| {g['id']} | {g['area']} | {g['T']} | {g['N']} | {''.join('Y' if m else '-' for m in g['met'])} | {g['now']} | {g['ref']} |")
(ROOT / "docs/PROGRESS_TRACKER.md").write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out[:4]))
