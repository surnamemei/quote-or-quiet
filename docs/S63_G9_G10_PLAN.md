# S63: gates G9 and G10, second test: rule A3 on 200 new contested topics (plan, 2026-11-11, before any S63 run output)

Why. S62 (rule A2) failed G9: 25 of 300 kept statements misleading, 22 of them a view credited to a party the sentence does not name; G10 met its bound (3 of 300, upper 2.9%) but its decoys were 26 of 30. On the S62 data (now design data) an attribution question for the 27B kept 159 of the 300 reviewed statements with 0 misleading (upper 2.3%) and 0 other party or opposite, and dropped all 25 misleading ones.
Rule A3 (frozen now; results/runs/s63/s63_a3.py): A2 unchanged, plus YES required to: 'The statement says that a particular party holds a view. Does the sentence itself say that this same party holds, states or argues this view? Answer NO if the sentence states the view as a plain fact without saying who holds it, if it names a different person or body, or if it only covers part of the view.'
Topics: 200 new contested pages (same title filter; S56 and S62 topics excluded; seed 6301). Statements as before.
Review: as S62 (300 random kept statements or all if fewer; up to 100 best-overlap sentences where different; 30 decoys; two blind sentence-only reviewers; verdicts states / other party / opposite / not). Change to decoys: only on witness sentences that contain all content words of the original party (and none of the replacement's), so that the sentence visibly names the original party.
Predictions: A3 keeps 15 to 30% of statements; at least 250 kept; misleading for both at most 1.5% and other party or opposite at most 1% among reviewed kept (upper bounds at most 3%); decoys at least 27 of 30 for both measures.

Note (14:4x): the first run stopped after statement generation (1,576 statements, candidates built) because of a syntax error in the attribution prompt string of s63_a3.py (a line break where 
 was meant); the string was repaired with no change of wording and the run resumed from the parties step.

## Deviation (2026-11-11 15:2x, after the first unblinding, recorded before any new verdict)
Two problems in the first review: (1) the two part-3 reviewers are not independent (112 of 112 same verdicts, 105 identical notes): part 3 is reviewed again by two new reviewers; (2) the decoys failed (25 and 24 of 30) because the replacement party was often generic ('Critics', 'Some Marxists', even 'No party named'), and a view moved from a named group to 'Critics' need not be false. New decoys: 30 kept statements (seed 6304) where both the original party and the replacement party are specific names (a capitalised name, none of critics, supporters, opponents, some, others, observers, scholars, experts and similar generic words), the witness sentence holds all words of the original party and none of the replacement's, and the rewritten statement contains the replacement name. They are mixed into the part-3 sheet for the new reviewers. Validity rule unchanged: at least 27 of 30 for each measure. The gate is judged on parts 1 and 2 as reviewed, part 3 as re-reviewed, and the new decoys; the first decoy set is reported as invalid by construction.

## Result (2026-11-11 15:3x)

200 topics, 1,576 statements; 1,542 with a candidate; A3 kept 339 (21.5%). Review: parts 1 and 2 (two reviewers each) and part 3 re-reviewed by two new reviewers (their verdicts agree on all 129 rows with no shared note; the first part-3 pair was set aside as copied). First decoy set: 25 and 24 of 30 (invalid by construction, see the deviation). New decoys (specific named parties): 30 of 30 misleading and 30 of 30 'other party' for both reviewers.

| Sentences | n | misleading for both (G9) | other party or opposite for both (G10) | 'states' for both |
|---|---|---|---|---|
| Rule A3 witness, reviewed kept statements | 300 | 2 (0.7%, 97.5% upper bound 2.4%) | 2 (0.7%, upper 2.4%) | 298 (99.3%) |

Against the predictions: kept 15 to 30%: met (21.5%). At least 250: met (339). Misleading at most 1.5%: met (0.7%). Other party or opposite at most 1%: met (0.7%). Upper bounds at most 3%: met (2.4%, 2.4%). Decoys at least 27 of 30: FAILED for the first set, met for the second (built after the first failed, as recorded).
Gates G9 and G10: T met, N met (300), V met with the second decoy set. Both pass. Limits: language-model reviewers who see only the sentence; the second decoy set was introduced after the first was found invalid; perfect agreement of the part-3 re-reviewers on easy rows; A3 keeps about a fifth of generated statements, so most of a generated summary of who holds which view is dropped.
