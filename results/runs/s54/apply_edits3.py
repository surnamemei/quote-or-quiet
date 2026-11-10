"""One-off: record the MiniCheck comparison in the docs, the paper (5.17) and the release README."""
import datetime
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations"); tm = datetime.datetime.now().strftime("%H:%M")
d = ROOT / "docs/S54_LARGER_JUDGE_RESULT.md"; s = d.read_text(encoding="utf-8").rstrip("\n")
s += f"""

## MiniCheck-Flan-T5-Large as an off-the-shelf checker ({tm}; results/runs/s54/MiniCheck_result.md)

Weights lytang/MiniCheck-Flan-T5-Large (MIT, 3.1 GB, downloaded on 2026-11-10 with the user's permission into models_external/minicheck-ft5-large; only the model files were fetched, none of the repository's scripts was run; the
checkpoint is a pickled PyTorch file read with the default safe loading of the library). Inference reimplemented from the authors' published code (read, not run): 'predict: ' + document + eos + claim, one decoder step from a zero
start token, softmax over token ids 3 and 209. Document = page title and quote; claim = 'The answer to the question "Q" is A.' AlignScore was not run: its checkpoints are Lightning pickles that need the authors' package. No prediction was written.

| Set | Checker | AUROC for 'states' | accepted | measure among accepted |
|---|---|---|---|---|
| held-out (n=939) | MiniCheck, 0.5 | 0.963 | 749 (79.8%) | not 'states' 31 (4.1%, 97.5% upper 5.8%) |
| held-out | small trained judge, 0.5 | 0.988 | 744 (79.2%) | 19 (2.6%, upper 4.0%) |
| held-out | 27B prompt | | 716 (76.3%) | 8 (1.1%, upper 2.2%) |
| Mintaka rows (n=361) | MiniCheck, 0.5 | 0.890 | 190 (52.6%) | misleading 25 (13.2%, upper 18.8%) |
| Mintaka rows | MiniCheck at 154 accepted | | 154 (42.7%) | misleading 7 (4.5%, upper 9.1%) |
| Mintaka rows | small trained judge, 0.5 | 0.897 | 154 (42.7%) | misleading 8 (5.2%, upper 10.0%) |
| Mintaka rows | 27B prompt | | 162 (44.9%) | misleading 3 (1.9%, upper 5.3%) |

Reading: an untrained 770M checker is close to our trained 0.6B judge on the set neither saw (AUROC 0.890 against 0.897; at equal acceptance 4.5% against 5.2% misleading) and somewhat behind it on the in-domain held-out rows (0.963 against 0.988),
which is where training on the reviewers' labels helps. The trained judge is therefore not a large advance over an existing checker; its contribution is the labelled rows. The 27B prompted judge is the best of all.
"""
d.write_text(s + "\n", encoding="utf-8")
m = ROOT / "paper/manuscript.md"; t = m.read_text(encoding="utf-8")
old = "We did not run an off-the-shelf small checker (AlignScore, MiniCheck, HHEM) on the labels, which a reader will want as a baseline."
assert t.count(old) == 1
t = t.replace(old, "An off-the-shelf checker, MiniCheck-Flan-T5-Large (770M, zero-shot), reached an AUROC of 0.963 on the held-out rows and 0.890 on the Mintaka rows, close to the trained judge on the Mintaka rows (0.897; at equal acceptance 4.5% against 5.2% misleading) and behind it on the held-out rows (0.988), where the training data is in domain; the trained judge is therefore not a large advance over an existing checker, and the labelled rows are the main contribution of this section. AlignScore and HHEM were not run.", 1)
m.write_text(t, encoding="utf-8")
r = Path(r"F:\Projects\quote-or-quiet\README.md"); x = r.read_text(encoding="utf-8")
old = "a 27B prompted judge did better still (1.1% on held-out rows, 1.9% on the Mintaka rows) |"
assert old in x
x = x.replace(old, "a 27B prompted judge did better still (1.1% on held-out rows, 1.9% on the Mintaka rows); the off-the-shelf MiniCheck-Flan-T5-Large (0.890 AUROC on Mintaka) is close to the trained judge there |", 1)
r.write_text(x, encoding="utf-8")
print("ok")
