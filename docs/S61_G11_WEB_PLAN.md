# S61: gate G11, rule R27 on pages that are not Wikipedia (plan, 2026-11-11, before any S61 run output)

Gate G11: the shown quote does not state the answer; threshold 97.5% upper bound at most 3%; at least 250 reviewed releases; registered, unseen, valid decoys.
Before: rule R with the 4B judge on non-Wikipedia pages of FRESH-5 releases (S49): 8 of 213 misleading (3.8%, upper 7.3%).
Population: the 705 Mintaka test releases of S57 G3 (only their Wikipedia quotes were reviewed); the pages the system fetched for them from the web, excluding Wikipedia and mirrors (results/runs/s61/g11_cands.py, a copy of S49 part C with seed 6101): 645 releases have such a page holding the answer as a whole word (1,991 pages). No rule has been applied to these pages before.
Rule R27 (as frozen for G3): the first candidate (page order, first occurrences) that is a sentence of at least 40 characters, holds the question's numbers and ordinals, and for which Qwen3.8-27B answers YES for the answer and NO for a swapped answer of the same shape is the witness; otherwise withheld.
Review: every release with a witness; the naive display (first occurrence on the first page) where it differs; 30 decoys (witness with the swapped answer); two blind reviewers, quote only.
Predictions: witnesses for 40 to 70% of the 705; at least 250; misleading among witnesses at most 1.5% (upper at most 3%); naive display misleading 15 to 40% where it differs; decoys at least 27 of 30.

## Result (2026-11-11 13:5x; results/runs/s61/G11_result.md)

R27 found a witness on a non-Wikipedia page for 523 of the 705 releases (74.2%). Blind review of 781 rows (523 witnesses, 228 differing naive displays, 30 decoys), two reviewers, quote only; decoys 30 of 30. Paired reviewers agreed on 238 of 261 (part 1); identical non-empty notes 22, 1 and 0 per part, all short distinct labels.

| Quotes | n | misleading for both | 'states' for both |
|---|---|---|---|
| R27 witness, every release with a witness | 523 | 1 (0.2%, 97.5% upper bound 1.1%) | 469 (89.7%) |
| Naive display where it differs | 228 | 70 (30.7%, upper 37.1%) | 51 (22.4%) |

Against the predictions: witnesses 40 to 70%: FAILED (74.2%, above). At least 250: met. Misleading at most 1.5%: met (0.2%). Upper at most 3%: met (1.1%). Naive display 15 to 40%: met (30.7%). Decoys: met.
Gate G11: T met, N met (523), V met. The gate passes. Limits: language-model reviewers; Mintaka questions only; the pages are those the system's web search returned (not a sample of the web); the truth of the pages is not reviewed.
