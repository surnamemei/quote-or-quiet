"""One-off: record the S56 result in the plan document, add Section 5.18 and a framing paragraph to the paper, push material to the release folder."""
import datetime
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations"); tm = datetime.datetime.now().strftime("%H:%M")
p = ROOT / "docs/S56_CONTESTED_QUESTIONS_PLAN.md"; s = p.read_text(encoding="utf-8").rstrip("\n")
s += f"""

## Result ({tm}; results/runs/s56/E12_result.md)

60 topics, 479 statements by Phi-4; 477 had a candidate sentence; rule A kept 207 (43.2%). The first judging run was void (the 27B was called through the raw Ollama interface, returned reasoning text and no YES or NO, so every statement was dropped); it was repeated through the chat
interface with thinking off (the void output is kept as e12_judge_failed_first_run.json). The 27B said YES to 248 of 1,362 candidates and to 8 flipped statements. Blind review of 343 rows (300 statements, 13 differing witnesses, 30 decoys), two reviewers, quote only:

| Sentences | n | misleading for both (opposite or not) | reversed for both (opposite) | 'states' for both |
|---|---|---|---|---|
| Naive display (best-overlap sentence), sampled statements | 300 | 53 (17.7%, 97.5% upper 22.5%) | 1 (0.3%, upper 1.8%) | 230 (76.7%) |
| Naive display, the 135 statements rule A keeps | 135 | 5 (3.7%, upper 8.4%) | 0 (upper 2.7%) | 129 (95.6%) |
| Rule A witness, kept statements | 135 | 0 (0.0%, upper 2.7%) | 0 (upper 2.7%) | 134 (99.3%) |

Against the predictions: naive display misleading in 20 to 45%: just below (17.7%). Naive display reversed in 3 to 15%: FAILED (0.3%; reversals were rare). Rule A keeps 35 to 70%: met (43.2% of all statements). Misleading among kept at most 3%: met (0 of 135, upper bound 2.7%).
Reversed among kept at most 1%: met as a point estimate (0; upper bound 2.7%). The 27B accepting a flipped statement for at most 10% of candidates: met (8 of the candidates of 116 flippable statements).
The decoy check is INVALID: only 16 of 30 flipped-party statements were judged misleading by both reviewers (criterion 27 of 30). The flip changes a generic party word (supporters, critics, in favour of) and many sentences name a person or a body, not the generic party, so a reviewer who sees only the sentence
can accept the flipped statement as well. The reviewers' verdicts on 'opposite' are therefore not validated, and 'no reversal observed' is not evidence of no reversal; what the data show is that reversals were rare in the drafts (1 of 300 for the naive display) and that the common failure was an unsupported or vague statement.
Nonsense, as far as measured here: 272 of the 479 statements (56.8%) have no sentence of the page that the 27B accepts for them, a lower bound on the unsupported content of the draft (the 27B may reject some supported statements; no review of the rejected statements was done).
"""
p.write_text(s + "\n", encoding="utf-8")

m = ROOT / "paper/manuscript.md"; t = m.read_text(encoding="utf-8")
sec = """### 5.18 Contested topics: reporting who holds a view

For most questions there is no single answer and what is said depends on who says it. For these the aim is not a correct answer but two things: nothing is stated that no source supports (nonsense), and a view is not attributed to a party that does not hold it, nor with its stance reversed (calling a deer a horse). This is the quote requirement applied to attribution: the system may report that a party holds a view only when a quoted sentence says so, and it does not assert the view.

We drew 60 English Wikipedia pages on controversies and debates (titles with controversy, debate, criticism of, dispute, opposition to, ethics of and similar words; seed fixed beforehand) and had Phi-4 write 6 to 8 statements per page of the form 'Critics argue that ...' from the first 14,000 characters (479 statements). Rule A kept a statement when, for one of the three page sentences most similar to it, a 27B judge answered YES to 'does this sentence report that this party holds this view' and NO to the same statement with the party flipped (supporters and critics, proponents and opponents). It kept 207 of 479 (43.2%); for 272 (56.8%) no sentence of the page was accepted, a lower bound on the unsupported content of the draft. Two blind reviewers, who saw only the sentence, judged 300 statements. The best-overlap sentence that a citing system would show failed to report the view (opposite or not addressed, for both reviewers) for 53 of 300 (17.7%, 97.5% upper bound 22.5%); for the 135 statements that rule A keeps, its sentence failed for 0 of 135 (upper bound 2.7%) and reported the view for both reviewers in 99.3%. Reversed stances were rare: 1 of 300 for the naive display and 0 for rule A.

The reversal result is not validated. The flipped-party decoys were judged misleading for both reviewers in only 16 of 30 cases, because the generic party word is often not what the sentence reports (a named person or a committee), so a reviewer who sees the sentence alone can accept the flipped statement too; we therefore cannot say that reversals would have been seen if present. The first judging run was void because the judge returned reasoning text and no verdict (an implementation error, repaired and repeated). What the data support is that, on contested pages, a generated summary of who holds which view contains a large share of statements that no sentence of the page supports (57%), that the sentence a citing system would show fails to report the view in about one case in six, and that requiring a sentence that a judge accepts for the stated party removes those at the cost of dropping them. They do not show that the views are the main views of the topic or that the pages are balanced.

"""
k = "## 6. Discussion"; assert t.count(k) == 1
t = t.replace(k, sec + k, 1)
old = "**What the findings establish.**"
assert t.count(old) == 1
t = t.replace(old, "**What this work is for.** For most questions there is no single answer and the answer depends on the stance of the source. The aim we pursued is therefore not the right answer but the removal of two failures: nonsense, a statement that no source supports, and calling a deer a horse, a statement that a source or party is made to say what it does not say. The requirement that a quoted sentence states what is shown is the operational form of both; Sections 5.11 to 5.18 measure how far it holds and where it fails. It does not remove errors that sit in the source, and it does not decide which view is right.\n\n" + old, 1)
m.write_text(t, encoding="utf-8")
print("ok")
