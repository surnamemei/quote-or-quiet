"""Unblind the S22 adjudication pilot (descriptive; S21's verdict stays final). Joins the blind agent's verdicts with the S21 key."""
import csv, json, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
V = Path(sys.argv[1])
key = {d["row"]: d["kind"] for d in json.load(open(ROOT / "results/runs/s21/S21_adjudication_key.json", encoding="utf-8"))}
sheet = {int(r["row"]): r for r in csv.DictReader(open(ROOT / "results/runs/s21/S21_adjudication_sheet.csv", encoding="utf-8"))}
ver = {int(r["row"]): r for r in csv.DictReader(open(V, encoding="utf-8"))}
RUB = ("gold wrong", "answer wrong", "both acceptable", "ambiguous question", "cannot tell")
by = {k: Counter() for k in ("system", "decoy_baseline_wrong", "decoy_system_correct")}
for r, k in key.items():
    v = (ver.get(r, {}).get("verdict") or "cannot tell").strip().casefold()
    by[k][v if v in RUB else "INVALID:" + v] += 1
lines = ["# S22 adjudication pilot on the S21 Mintaka sheet (blind web check by a fresh agent; descriptive)", "",
         "| kind | n | " + " | ".join(RUB) + " | removed share |", "|---|---|" + "---|" * (len(RUB) + 1)]
for k, c in by.items():
    n = sum(c.values()); rem = c["gold wrong"] + c["both acceptable"]
    lines.append(f"| {k} | {n} | " + " | ".join(str(c[x]) for x in RUB) + f" | {rem / n:.2f} |")
sysk = sum(by["system"].values()); rem = by["system"]["gold wrong"] + by["system"]["both acceptable"]
lines += ["", f"System errors kept after adjudication: {sysk - rem} of {sysk} (would-be adjudicated k; S21 coverage 0.310 fails regardless).",
          f"Missing verdict rows: {sorted(set(key) - set(ver))[:20]}"]
lines += ["", "System rows:", ""] + [f"- {sheet[r]['question']} | gold {sheet[r]['gold']} | ans {sheet[r]['answer']} | **{ver.get(r, {}).get('verdict')}** | {ver.get(r, {}).get('source_url')}"
                                      for r, k in sorted(key.items()) if k == "system"]
lines += ["", "Baseline-wrong decoys judged acceptable:", ""] + [f"- {sheet[r]['question']} | gold {sheet[r]['gold']} | ans {sheet[r]['answer']} | {ver.get(r, {}).get('verdict')} | {ver.get(r, {}).get('reason')}"
        for r, k in sorted(key.items()) if k == "decoy_baseline_wrong" and (ver.get(r, {}).get("verdict") or "").casefold() in ("gold wrong", "both acceptable")]
lines += ["", "System-correct decoys judged answer wrong:", ""] + [f"- {sheet[r]['question']} | gold {sheet[r]['gold']} | ans {sheet[r]['answer']} | {ver.get(r, {}).get('reason')}"
        for r, k in sorted(key.items()) if k == "decoy_system_correct" and (ver.get(r, {}).get("verdict") or "").casefold() == "answer wrong"]
out = ROOT / "results/runs/s22/adj_pilot.md"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
