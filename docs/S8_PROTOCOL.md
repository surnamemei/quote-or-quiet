# S8 protocol: a code-only check of the answer against the passage

Written 2026-11-05, before any fresh-set output existed (the fresh-set build was still running).

## Question
After S7b, the real residual errors were misread passages (wrong day, wrong number, missing day) and the strict grader flagged many correct answers. Can a check written in code, with no LLM and no gold, that tests whether the answer is actually in the passage remove silent errors cheaply? Is that true for a model that answers without an abstain instruction?

## Check (`vkg/support_check.py`)
- A, span support: all answer content tokens occur in one window of the passage; each number sits within 3 tokens of one of the answer's words.
- T, date structure: a date in the answer must appear in the passage with day, month and year next to each other (any format).
- Q, completeness: a "day, month and year" or "month and year" question needs those parts in the answer.
- Unit tests: `vkg/test_support_check.py` (20 hand-written cases, none from the evaluation sets).

## Sets
- DEV: the 300 SimpleQA-E questions. I designed the check after reading 12 residual errors from this set, so DEV is not a clean test. DEV numbers were computed before this protocol and are listed below.
- FRESH (clean test): questions 301–500 of the same seed-3000 SimpleQA Verified sample. Same variant-E retrieval (27B-written queries), same 4B prompts (S6b plain, cautious) and same 27B systems (B1_abstain, B2_strict, frozen `systems.py`). I have never inspected any of these questions. Builder: `vkg/s8_fresh.py`.

## Hashes (SHA-256)
- vkg/support_check.py 368aec291fc40896200c23fb7cd6723ca7a8beb100a5b44efa322d966bca3f43
- vkg/s8_eval.py e62b298f3945c3a0cd8cf279744cef13dda149a2b99b5bb1bd237a7ae1346d6d
- vkg/test_support_check.py 2a960fcb9528005c88e79316e62ade5de68781180a7a2be31f4399d77b004273
- vkg/s8_fresh.py 1d6782aebdaa8e3fe9b370857612a0dd8180ff00ad9de7a132da5d6da9116150; retrieval.py, retrieval2.py, systems.py and llm.py match freeze 7 (results/runs/s8/hashes_before_build.txt).

## DEV numbers (known before writing the predictions)
4B plain: SER 30.3% → 10.0%, correct 59.3% → 58.3%. 4B cautious: 7.0% → 5.0%, correct −0.3. 27B B1: 6.3% → 5.7%, correct −1.0. 27B B2: 5.7% → 5.0%. 27B VKG_v2: unchanged (4.0%).

## Predictions for FRESH (n=200)
- F1: 4B plain + check lowers SER by at least 12 points (CI upper below 0) and loses at most 3 points of correct answers.
- F2: 4B cautious + check lowers SER by 0–4 points and loses at most 2 points of correct answers.
- F3: 27B B1_abstain + check changes SER by between −2 and 0 points and loses at most 2 points of correct answers.
- F4: 4B plain + check vs 4B cautious without the check: correct higher by at least 2 points; SER higher by at most 5 points.
- F5: of the answers the check removes from 4B plain, at least 85% are graded wrong.
- F6 (descriptive, one rater, me): I will read every FRESH answer the check removes that the grader marks correct, and every graded-wrong answer kept by 4B cautious + check. Each is classed as a real error or a grader miss, with whether the passage contains the gold answer.

## Decision rule
The check is called useful if, on FRESH, it lowers 4B plain SER by at least 10 points with the CI upper bound below 0 at a correct-answer loss of at most 3 points, and costs at most 2 points of correct answers on every abstaining system. A failed prediction is reported as failed.

## Amendment 1 (2026-11-05, still before any fresh output exists; only 10 of 200 fresh passages built, no fresh answers generated)
Reading the DEV answers the check removed from 4B plain showed that most were not answers. Of the 300 DEV plain outputs, 28 are parse failures ("```json" or raw "{...", the S6b parser's leftover when the JSON did not parse) and 19 are denials ("The passage does not provide ..."). The strict detector counts these as answers. That inflates both plain's SER and the check's apparent gain, the same problem the second audit found. `vkg/s8_eval.py` now also reports the 4B systems with a cleaner non-answer detector (denial-aware, plus parse failures). The check itself (`support_check.py`) is unchanged.
New hash: vkg/s8_eval.py c7095d70bf001646bcbf3384a82afe29efc6c7574d217ef66a72746e96c80337 (support_check.py unchanged).
DEV with the cleaner detector: 4B plain coverage 74.0%, SER 14.7% → 10.0% (−4.7, CI −7.3..−2.7), correct −1.0; 4B cautious unchanged from before (7.0% → 5.0%).
Revised predictions (they replace F1, F4 and F5; the strict-detector versions are still scored but only as secondary):
- F1': 4B plain (cleaner detector) + check lowers SER by 2–8 points with CI upper below 0, and loses at most 3 points of correct answers.
- F4': 4B plain (cleaner detector) + check vs 4B cautious without the check: correct higher by at least 2 points; SER higher by at most 5 points.
- F5': of the real answers (cleaner detector) the check removes from 4B plain, at least 75% are graded wrong (DEV 14 of 17).
Revised decision rule: the check is useful if, on FRESH, F1' holds and it costs at most 2 points of correct answers on every abstaining system.

## Amendment 2 (2026-11-05, before any fresh answer exists)
- Sensitivity grader: `vkg/grade_v4.py` (SHA-256 a1594f746711b9ccaa6af91ef3d129ab4b2c042975e31a052dadd70fb77ffad2) = the repaired grader plus rules 1, 2 and 3(a) of docs/GRADER_VALIDATION.md section 6, ported unchanged from the prototype. On the 240 hand-labelled rows the port reproduces the prototype: 11 false negatives left (from 47), 0 labelled-wrong answers credited, 0 grader-correct rows lost. Those rows are where the rules were designed; on FRESH they are out of sample. All predictions stay on the frozen graders; v4 is reported beside them, and the F6 manual reading checks it.
- vkg/s8_eval.py now also prints the v4 tables; new hash 7db42572640f162cb164dc10b42b81942e4f42040b1180953689ca0032bb7e72. support_check.py unchanged.
- Incident: the first fresh build crashed at 20/200 because `retrieval2.save_cache()` ran while worker threads were adding embeddings, and the crash truncated `results/cache/emb.pkl` (kept as `emb.pkl.truncated-20261105`). No recorded result depends on that file, since the 300 DEV passages are stored in full in results/runs/s6b/eval_items.json. Rebuilding the old passages from scratch would need re-embedding. `vkg/s8_fresh.py` now saves the cache once, after the threads finish, through a temporary file (new hash appended to results/runs/s8/hashes_before_build.txt). The wiki page cache and the 27B query cache are separate files and were not affected.
