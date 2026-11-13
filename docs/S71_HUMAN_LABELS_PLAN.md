# S71: the project's reviewers and judge against existing human labels (plan, 2026-11-12, before any S71 output)

Why. No people are available to check the reviewers on our own rows (gate G12 stays open). This measures the same kind of judgment against labels people already made, as a separate, weaker substitute, never counted as G12.
Data: VitaminC test (tals/vitaminc; downloaded 2026-11-12 under the user's download permission; CC BY-SA 3.0): human-written claims about Wikipedia sentences, labelled by people as SUPPORTS, REFUTES or NOT ENOUGH INFO; many come in contrastive pairs. 600 rows, 200 per label, seed 7101 (results/runs/s71/hl.py).
Mapping: our verdict 'states' (or the judge's YES) corresponds to SUPPORTS; 'incomplete' and 'not' (or NO) to REFUTES or NOT ENOUGH INFO.
Reviewers: two Claude reviewers with the quote-only protocol (claim and sentence only, no web, no own knowledge), in two parts; the 27B judge with the project's prompt adapted to a claim.
Reported: agreement with the human labels, Cohen kappa, false accepts (the reviewer says the sentence states the claim, people said it does not; split by REFUTES and NOT ENOUGH INFO) and false rejects.
Expectations (before any output): agreement at least 0.85 for each reviewer and the judge; false accepts at most 5% of the non-SUPPORTS rows for the Claude pair (both 'states') and at most 8% for the judge. VitaminC labels are themselves imperfect; disagreements are reported, not re-labelled.

## Result, Claude reviewers (2026-11-12; results/runs/s71/HL_result.md; the 27B judge row follows after its GPU run)
Four reviewers (two per part) judged all 600 rows; paired agreement 282 of 300 and 291 of 300.

| reviewer | agreement with human labels | kappa | false accepts (non-SUPPORTS called 'states') | false rejects (SUPPORTS not called 'states') |
|---|---|---|---|---|
| A | 0.905 | 0.783 | 23 of 400 (5.8%; REFUTES 5, NEI 18) | 34 of 200 (17.0%) |
| B | 0.912 | 0.799 | 23 of 400 (5.8%; REFUTES 7, NEI 16) | 30 of 200 (15.0%) |
| pair, both 'states' | 0.908 | 0.790 | 21 of 400 (5.2%; REFUTES 5, NEI 16) | 34 of 200 (17.0%) |

Against the expectations: agreement at least 0.85: met. False accepts of the pair at most 5%: FAILED (5.2%).
Reading. The reviewers are stricter than the human labels (15 to 17% of supported claims not called 'states'), and accept about 5% of claims people did not label as supported. Inspection of some of the pair's false accepts after the count (not used to change it): several are claims the sentence implies through an inequality or a paraphrase that VitaminC labels NOT ENOUGH INFO ('another 10 people died' for 'more than 9 people died'; 'a production budget of 80 crore' for 'at least 65 crores'), so part of the 5.2% is a difference of labelling convention; at least one is a plain reviewer error. Consequence for the gates: the measured misleading rates rest on the pair calling a non-stating quote 'not'; if the pair misses about 5% of non-stating quotes in the same way, a measured misleading count k corresponds to about k/0.95, a small upward correction. This holds only to the extent that VitaminC claims resemble our quote rows. Not a human check of our rows; gate G12 stays open.

## 27B judge row (2026-11-13 01:56)
The 27B judge (the project's prompt adapted to a claim, YES = the sentence states it) on the same 600 VitaminC rows: agreement 0.822, kappa 0.552; false accepts 12 of 400 (3.0%; REFUTES 4, not enough information 8); false rejects 95 of 200 (47.5%).
Reading: the 27B is stricter than the Claude reviewers: it accepts fewer claims the humans did not support (3.0% against 5.2% for the pair) and rejects about half of the claims the humans supported. That fits how the project uses it (a release needs a YES; a NO only withholds): its errors cost coverage, not truth. Against human labels on this outside data set its false-accept rate is 3.0% (97.5% upper bound about 5.2%), above the 1 to 2% seen against the Claude reviewers on the project's own rows (S64), so the gate numbers that rest on the 27B judge should be read with that margin in mind.
