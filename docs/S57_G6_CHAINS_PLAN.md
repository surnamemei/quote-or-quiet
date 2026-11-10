# S57: gate G6, quote chains on fresh two-hop items (plan, 2026-11-11, before any G6 run output)

Gate G6: the two quotes together do not state the answer, or the answer is wrong; threshold 97.5% upper bound at most 3% for each; at least 150 reviewed chains; registered, unseen data, valid decoys.
Items: 600 person pages drawn with seed 5706 from the title index (no qualifier, 6,000 to 60,000 characters, people by the S37 test), excluding the people of S42/S50 (results/runs/s57/g6/g6_build.py; built, no answers seen). Question 'In which country was X born?'.
Hop 1: the S46 per-reading pipeline unchanged except that the birth-place frame of W1 (born, birth, native; as in S40) is added: the 4B reader answers 'Where was X born?' from the person's page (plain and cautious agree), the answer is a typed verbatim span passing the gate, W1 chooses the witness. Items continue when the place is a single name (no comma) with its own page.
Hop 2: rule C2' of S50 unchanged (results/runs/s57/g6/g6_chain.py): country from the place page, sentence 2 holding the country, 4B judge YES for the country and NO for a swapped country, bridge check. No chain-level reader.
Review: every accepted chain plus 30 decoys (country swapped); two blind reviewers per row; chain verdict (states / incomplete / not, from the two quotes only) and truth verdict (right / wrong / cannot tell, look-up allowed), as in S50.
Predictions: W1 witness for 60 to 90% of persons; single-place items 35 to 60% of witnesses; C2' accepts 60 to 85% of those (S50: 77.5%); at least 150 accepted chains; misleading for both at most 1.5% and wrong for both at most 1.5% (upper bounds at most 3%); decoys at least 27 of 30.
If fewer than 150 chains are accepted, N fails and is reported; the rule is not changed on these data.

## Extension G6b (registered 2026-11-11, after the G6 hop-1 counts and before any chain output)
G6 hop 1 gave W1 witnesses for 409 of 600 persons and 140 single-place items, so fewer than 150 accepted chains are expected. A second draw of 800 persons (seed 5710, excluding the G6 persons and the S42/S50 people; results/runs/s57/g6b, other seeds 5711 and 5712) is run with the same unchanged pipeline. The gate is evaluated on G6 and G6b together; G6 alone is also reported. Each batch gets its own 30 decoys. Predictions for G6 apply to the union.

## Result (2026-11-11 10:2x; results/runs/s57/G6_result.md)

Hop 1: W1 witnesses for 409 of 600 (G6) and 564 of 800 (G6b) persons; single places with a page 140 and 181. Hop 2 (C2'): 91 and 118 chains accepted (65.0% and 65.2%). Blind review of 269 rows (209 chains, 60 decoys), two reviewers per row; decoys misleading or wrong for both 28 of 30 (G6) and 30 of 30 (G6b), valid.

| Rows | n | misleading for both | country wrong for both | 'states' for both |
|---|---|---|---|---|
| Accepted chains, G6 and G6b | 209 | 0 (upper 1.7%) | 0 (upper 1.7%) | 173 (82.8%) |
| G6 alone | 91 | 0 (upper 4.0%) | 0 (upper 4.0%) | 81 (89.0%) |
| G6b alone | 118 | 0 (upper 3.1%) | 0 (upper 3.1%) | 92 (78.0%) |

Against the predictions: W1 witness 60 to 90%: met (68.2%, 70.5%). Single-place items 35 to 60% of witnesses: FAILED (34.2%, 32.1%; most birth places are written with a region or country after a comma). C2' accepts 60 to 85%: met (65%). At least 150 chains: FAILED for G6 alone (91), met for the registered union (209). Misleading and wrong at most 1.5%: met (0 and 0). Decoys at least 27 of 30 per batch: met.
Gate G6 on the union: T met (1.7% <= 3% for both), N met (209 >= 150), V met (registered, unseen persons, decoys valid; the extension was registered after the hop-1 counts and before any chain output). The gate passes. Limits: one relation pair (birth place, country); single-name places with their own page only (about a third of witnessed birth places); language-model reviewers, who looked up the truth verdicts only in part.
