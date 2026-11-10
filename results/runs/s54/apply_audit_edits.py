"""One-off: record the returned audit sheet (filled by an AI assistant, not a person) in the paper as Section 5.21."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
m = ROOT / "paper/manuscript.md"; t = m.read_text(encoding="utf-8")
sec = """### 5.21 A third reviewer on a 180-row audit sheet

A sheet of 180 rows (question, answer, page title and one quote; 40 rows both language-model reviewers called 'not', 40 'states', 30 'incomplete', 30 where they disagreed and 40 decoys made by giving a row the answer of another row of the same source) was prepared for a person. The filled sheet that came back was produced by an AI assistant of another provider, not by a person: its reply names web sources for some rows and cites outside knowledge in its notes, although the instructions said to use neither, so it is a third language-model reviewer that was not blind in the strict sense, and it does not audit the reviewers against a human. It agreed with the first reviewer on 84.4% of rows (Cohen kappa 0.758 over the three verdicts) and with the second on 87.8% (kappa 0.810); on the 150 rows where the two reviewers agreed, agreement was 93.3% (kappa 0.889). Of the 80 rows both reviewers called 'not' (40 genuine, 40 decoys) it called 77 'not' (96.2%); it called all 40 decoys 'not'; of the 40 'states' rows it called 38 'states' and none 'not'. On the 30 rows where the two reviewers disagreed it chose 'incomplete' for 27. Because the filler used the web and outside knowledge for some rows, this is evidence that a different model family reaches the same verdicts on these rows, and the check against a person remains open.

"""
k = "## 6. Discussion"; assert t.count(k) == 1 and "### 5.21" not in t
m.write_text(t.replace(k, sec + k, 1), encoding="utf-8")
print("ok")
