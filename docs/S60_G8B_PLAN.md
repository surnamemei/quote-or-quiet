# S60: gate G8, second test: rule W4-27 on 50 fresh topic pages (plan, 2026-11-11, before any S60 run output)

Why. S59 failed gate G8 on truth (8 of 400 kept claims false, upper bound 3.9%). On the S59 data (now design data) W4 with the 27B judge in place of the 4B (W4-27) kept 340 of the 400 reviewed slots with the same quote, among them 5 false (1.5%, upper 3.4%) and 0 misleading (upper 1.1%), and 643 of 1,318 slots overall (48.8%). The remaining false claims were 2 errors of the page itself and 3 claims phrased beyond their sentence by the decomposition. No further change was made on these data.
Rule W4-27 (frozen now): the S59 pipeline unchanged (grounded Phi-4 draft, decomposition, three candidate sentences, number check, 75% value coverage), with the YES/NO judge prompts (value YES, swapped value NO) answered by Qwen3.8-27B (chat, thinking off, temperature 0) instead of the 4B; first passing candidate is the witness.
Topics: 50 fresh pages (17 organisations, 17 events, 16 science topics), seed 5911, same criteria as S59, S59 topics and S56 pages excluded (results/runs/s60/g8_topics.py; drawn, titles not read). Seeds 6002 to 6004.
Review: as S59: 400 random kept slots (all if fewer), 40 dropped, 30 decoys; two blind reviewers; quote verdict and truth verdict with a look-up and a source for every row.
Predictions: W4-27 keeps 40 to 60% of slots; false for both at most 1.5% and misleading at most 1% among the reviewed kept slots; upper bounds: false at most 3% (requires at most 5 false of 400) and misleading at most 3%; decoys at least 27 of 30. Probability of meeting the false bound about one half.
Gate G8 T requires both upper bounds at most 3%. Page errors count as false (the gate is not redefined). A failure is reported as failed.

## Result (2026-11-11 12:4x; results/runs/s60/F5_result.md)

W4-27 kept 595 of 1,332 slots (44.7%). Blind review of 470 rows (400 random kept slots, 40 dropped, 30 decoys), two reviewers, every row looked up on Wikipedia with a source; decoys 30 of 30; reviewers agreed on the quote in 424 of 430 and on truth in 466 of 470; identical non-empty notes between paired reviewers 0, 8 and 0 (short stock phrases).

| Rows | n | false for both | misleading for both | 'states' for both |
|---|---|---|---|---|
| Kept slots | 400 | 5 (1.2%, 97.5% upper bound 2.9%; cluster bootstrap by topic 2.8%) | 0 (upper 0.9%) | 389 (97.2%) |
| Dropped slots | 40 | 3 (7.5%) | | |

Against the predictions: kept 40 to 60%: met (44.7%). False at most 1.5%: met (1.25%). Misleading at most 1%: met (0). Upper bounds at most 3%: met (2.9% and 0.9%). Decoys: met.
The 5 false kept claims all have quotes that state them (both reviewers 'states'); each is a difference between the page snapshot (August 2025) and the present page: enrolment figures of a college that have since been updated (2 claims), a re-telecast date since revised (2 claims, one fact), and a disease the snapshot calls fungal and the present page no longer does.
Gate G8: T met (2.9% and 0.9%, both at most 3%), N met (400), V met. The gate passes, with the false bound close to the threshold. Limits: language-model reviewers; the truth check is against the present Wikipedia; grounded drafts only (the draft is written from the page).
