# S59: gate G8, long-form claims on pages that are not about people (plan, 2026-11-11, before any S59 run output)

Gate G8: kept claim false or quote not stating it; threshold 97.5% upper bound at most 3% for both; at least 300 reviewed claims; registered, unseen, valid decoys.
Topics: 50 English Wikipedia pages drawn with seed 5901 (results/runs/s59/g8_topics.py): 17 organisations, 17 events, 16 science topics, classed from the first sentence; no qualifier, 8,000 to 60,000 characters, not people, not S56 pages (drawn; titles not read beyond the counts).
Pipeline: the S47 fresh-test pipeline unchanged except two prompt words: the draft prompt says 'tell me about X' instead of 'tell me a bio of X', and the decomposition prompt says 'Topic' instead of 'Person' (and 'it, its, they, their' instead of 'he, she, his, her'). Phi-4 writes the draft from the first 14,000 characters of the topic's own page; slots are decomposed as in S47; rule W4 (sentence-level 4B judge YES for the value and NO for a swapped value, number check, 75% value content-word coverage) is unchanged. Seeds 5902 to 5904.
Review: a random 400 kept slots (all if fewer), 40 random dropped slots, 30 decoys; two blind reviewers per row; quote verdict (states / incomplete / not) and truth verdict (right / wrong / cannot tell) with a look-up required for every row and a source given; misleading = both 'not', false = both 'wrong'.
Predictions: W4 keeps 40 to 70% of slots (biographies: 61%); among the reviewed kept slots false for both at most 1.5% and misleading for both at most 1.5% (upper bounds at most 3%); decoys at least 27 of 30; among the 40 dropped, false at most 25%.
A failure is reported as failed; no rule change on these data.

## Result (2026-11-11 12:0x; results/runs/s59/F5_result.md)

W4 kept 727 of 1,318 slots (55.2%). Blind review of 470 rows (400 random kept slots, 40 dropped, 30 decoys), two reviewers per row, every row looked up with a source (a few rows rest on a search summary or an older page revision, as the reviewers reported); decoys 30 of 30.

| Rows | n | false for both | misleading for both | 'states' for both |
|---|---|---|---|---|
| Kept slots | 400 | 8 (2.0%, 97.5% upper bound 3.9%; cluster bootstrap by topic 3.3%) | 3 (0.8%, upper 2.2%) | 358 (89.5%) |
| Dropped slots | 40 | 2 (5.0%) | | |

Against the predictions: kept 40 to 70%: met (55.2%). False at most 1.5%: FAILED (2.0%). Misleading at most 1.5%: met (0.8%). Upper bounds at most 3%: FAILED for false (3.9%), met for misleading (2.2%). Decoys: met. Dropped false at most 25%: met (5.0%).
Gate G8: T NOT met (false 3.9% > 3%), N met (400), V met. The gate fails. The 8 false kept claims: 2 where the quote states the claim and the page itself is wrong or inconsistent (a cup's finals 'since 1893' against founding in 1905; an endorsement dated 1803 against a letter of 1802); 2 where the decomposition produced a value that does not answer its question (also judged misleading); 4 where the claim says more or other than its quote (founded in London read as located in London; relegated in 2014 read as 2015; an aim; who formally described a species) and the reviewers rated the quote 'incomplete', not 'states'. A check of reviewer independence (identical non-empty notes 1, 0 and 2 per part) found none copied.
Next (a new design, needs new unseen topics): the 4B judge of W4 accepted the 'incomplete' quotes; the 27B judge did not let an incomplete quote through on natural questions (G3). W4 with the 27B judge is to be designed on these S59 data and tested on 50 fresh topics.
