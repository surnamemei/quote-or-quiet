# S62: gates G9 and G10, attribution on contested topics (plan, 2026-11-11, before any S62 run output)

G9: the shown sentence does not report the view for the stated party (misleading). G10: the view is moved to another party or reversed. Thresholds: 97.5% upper bound at most 3% each; at least 250 reviewed kept statements; registered, unseen; decoys valid (at least 27 of 30).
Before: S56 rule A on 60 topics: 0 of 135 misleading (upper 2.7%) but the flipped-party decoys were invalid (16 of 30), so reversals were not tested; a party-swap control later showed the 27B accepting a moved attribution for 4.4% of candidates (S56 follow-ups).
Topics: 150 new contested pages (same title filter as S56, S56 topics excluded, seed 6201). Statements: Phi-4, as S56 (results/runs/s62/e12.py gen, cands).
Rule A2 (frozen now; results/runs/s62/s62_a2.py): candidate sentences as S56; witness when the 27B says YES for the statement, NO for the party-flipped statement (if flippable), and NO for the statement with the view moved to another party of the same topic (if such a party exists and the sentence names none of its words). Else the statement is dropped.
Review: a random 300 kept statements (all if fewer) with their witness; the best-overlap sentence for up to 100 of them where it differs; 30 decoys: a kept statement with the view moved to another party, shown with a witness sentence that names the original party and none of the replacement's words, so that a reader of the sentence alone can see the party does not match. Two blind reviewers, sentence only, one verdict: states (this party holds this view), other party (the sentence gives the view to another party), opposite (the sentence gives the opposite stance), not (does not address it).
Measures: G9 misleading = both reviewers not 'states'; G10 = both 'other party' or 'opposite'. Decoys valid for G9 when at least 27 are misleading for both, for G10 when at least 27 are 'other party' or 'opposite' for both.
Predictions: A2 keeps 30 to 50% of statements; at least 250 kept; misleading for both at most 1.5% and other party or opposite for both at most 1% (upper bounds at most 3%); decoys at least 27 of 30 for both measures; best-overlap sentence misleading 15 to 35% where it differs.

## Result (2026-11-11 14:2x; results/runs/s62/A2_result.md)

150 topics, 1,184 statements; 1,169 with a candidate; A2 kept 539 (45.5%). Blind review of 337 rows (300 kept statements, 7 differing best-overlap sentences, 30 decoys), two reviewers, sentence only; paired agreement 110/113, 106/112, 108/112; notes refer to their own sheets.

| Sentences | n | misleading for both (G9) | other party or opposite for both (G10) | 'states' for both |
|---|---|---|---|---|
| A2 witness, reviewed kept statements | 300 | 25 (8.3%, upper 12.1%) | 3 (1.0%, upper 2.9%) | 265 (88.3%) |

Decoys: misleading for both 28 of 30 (valid for G9); 'other party' or 'opposite' for both 26 of 30 (criterion 27: INVALID for G10, by one).
Against the predictions: kept 30 to 50%: met. At least 250 kept: met. Misleading at most 1.5%: FAILED (8.3%). Other party or opposite at most 1%: met as a point estimate (1.0%), upper 2.9%. Decoys at least 27 for both measures: FAILED for G10 (26). Best-overlap sentence: only 7 differed (prediction not testable).
Gate G9: T NOT met (12.1%). Gate G10: T met (2.9%) but V NOT met (decoys 26 of 30).
What failed: 22 of the 25 misleading cases were 'not addressed' for both: the sentence states the view as a plain fact, or gives it without a holder, or names a different body, and the statement credits it to a named party ('Critics claim ...', 'The Inspector General found ...'). The 27B accepted these, and neither control (party flip, party swap) catches a missing attribution. This is the failure 'a view credited to a party the source does not name'; S56 had seen none of it in 135 statements.
Design follow-up (on these data, now design data): requiring the party's words in the sentence left 11 of 251 misleading (4.4%); a direct attribution question for the 27B is being tried; any rule chosen needs fresh topics.
