# S57: gate G6, quote chains on fresh two-hop items (plan, 2026-11-11, before any G6 run output)

Gate G6: the two quotes together do not state the answer, or the answer is wrong; threshold 97.5% upper bound at most 3% for each; at least 150 reviewed chains; registered, unseen data, valid decoys.
Items: 600 person pages drawn with seed 5706 from the title index (no qualifier, 6,000 to 60,000 characters, people by the S37 test), excluding the people of S42/S50 (results/runs/s57/g6/g6_build.py; built, no answers seen). Question 'In which country was X born?'.
Hop 1: the S46 per-reading pipeline unchanged except that the birth-place frame of W1 (born, birth, native; as in S40) is added: the 4B reader answers 'Where was X born?' from the person's page (plain and cautious agree), the answer is a typed verbatim span passing the gate, W1 chooses the witness. Items continue when the place is a single name (no comma) with its own page.
Hop 2: rule C2' of S50 unchanged (results/runs/s57/g6/g6_chain.py): country from the place page, sentence 2 holding the country, 4B judge YES for the country and NO for a swapped country, bridge check. No chain-level reader.
Review: every accepted chain plus 30 decoys (country swapped); two blind reviewers per row; chain verdict (states / incomplete / not, from the two quotes only) and truth verdict (right / wrong / cannot tell, look-up allowed), as in S50.
Predictions: W1 witness for 60 to 90% of persons; single-place items 35 to 60% of witnesses; C2' accepts 60 to 85% of those (S50: 77.5%); at least 150 accepted chains; misleading for both at most 1.5% and wrong for both at most 1.5% (upper bounds at most 3%); decoys at least 27 of 30.
If fewer than 150 chains are accepted, N fails and is reported; the rule is not changed on these data.
