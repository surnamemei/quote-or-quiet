# Grader 6 protocol: LLM judge plus a code completeness veto

Written 2026-11-05, before any judge call on V3 and before V3 labels exist.

## Design (vkg/grade6.py)
An answer is correct only if grader 5 (local 27B, SimpleQA Verified prompt) says CORRECT **and** no code veto fires. The vetoes:
- R1, date agreement: when both gold and answer contain a date, their parts must agree.
- R2, date completeness: if the question asks for day, month and year, all three must be present; if it asks for month and year, both must be present.
- R3, two-part place: if the question asks for city and country (or similar) and the gold has a comma, the answer must contain the gold's last part.
- R4, full name: if the question says "full name", every gold name token must appear in the answer.
- R5, qualifier: a kinship or rank qualifier in the gold (maternal, vice, ...) must appear in the answer, unless it already appears in the question.

The vetoes were designed on the judge's failures in V1 and V2. On those design sets, grader 6 has:
- V2: false credit 1/82, misses 1/150 (judge alone: 5 and 1);
- V1: false credit 0/73, misses 2/167.

The one remaining V2 false credit is a missing surname for a question that does not say "full name". I left it unfixed on purpose to avoid fitting the design set further. 20 unit tests pass (`vkg/test_grade6.py`).

## Validation set V3 (new, blind)
- Drawn by `results/grader6/draw3.py` (seed 20261107) from the 27B SimpleQA files: closed-book n500, rag n300, oracle n251, hybrid n300.
  - Rows used: answered rows not already in V1 or V2.
  - Pool: 730 unique rows. The frozen grader calls 181 grounded rows and 431 closed-book rows wrong, and 118 rows correct.
  - Sample: 140 grounded grader-wrong rows, 60 closed-book grader-wrong rows, and 60 random grader-correct rows (260 in all).
- Labels: one blind LLM rater, a new Claude subagent. It sees only the question, gold and answer, with no grader output, system, passage, code or web access. Labels are requested before any V3 judge output is read.
- The judge itself runs on V3 while labelling is in progress. I will not read its output until the labels are saved and hashed.

## Hashes (SHA-256)
- vkg/grade6.py 05b24d6b2628fb5cfc1899d93ae7ca77506e3f8892302b8f1a24a74c622e65d9
- vkg/test_grade6.py 70cd4ca07c42b1b4d118afca30a22063f7d66b8870c97893e3e97614ef342cad
- vkg/judge_file.py 233fdb4837f7baba2f2b1cb9abe58a163bb53cd693621f2fd12d4b7101d525f2
- vkg/grade_judge.py and the prompt are unchanged from grader 5 (2e392d6b..., e8db4b23...).
- results/grader6/draw3.py 57274a56d0cd0a647de531ff048b2ca3a634feb8ba45bac34ace2238d77412f7
- results/grader6/v3_blind.jsonl 17d1e7d6181ed1ddcedd016d3a96fec8f1e70e3232485ecfc4147f6cfad4caab
- vkg/grader6_eval.py ed6ab68a1c97379887cca8f1537c092707bd70db22502da191a118954f4f4d90 (scoring script; written before the labels or any V3 judge output was read)

## Criteria (on V3)
- K1, safety: grader 6 false credit (rows labelled W or N that it grades correct) is at most 3.0% of the W/N rows. The exact 95% upper bound is reported.
- K2: grader 6 misses (rows labelled C that it does not grade correct) are at most 5.0% of the C rows.
- K3, descriptive:
  - the same two rates for v3, v4 and the judge alone;
  - false credit split by stratum (grounded vs closed-book);
  - how many times each veto fires and whether it was right.

## Decision rule
- **Adopt:** if K1 and K2 hold, grader 6 becomes the primary grader for new runs, with v4 reported beside it. Past predictions keep their frozen graders, and a grader-6 regrade is reported as a sensitivity.
- **Reject:** if K1 fails, grader 6 is rejected.
- **Pool-level error:** rates are re-weighted by stratum to the 730-row pool.
- results/grader6/v3_labels.txt 7118bcf9f882c368787bcea921b6b76e6e9863756fc0411455f1aadc98f9ecbe (64 C, 180 W, 16 N; saved before any V3 judge output was read)

## P0.2 error-injection test (added 2026-11-05, before any judge call on these rows)
results/grader6/inject.py builds 330 known-wrong answers from the 289 distinct rater-labelled-correct rows of V1, V2 and V3: 163 swaps (another question's answer), 65 years +3, 61 numbers ×1.37+1, 22 days +9, 19 dropped day of a full date. Criterion: grader 6 credits ≤ 2% (exact 95% upper bound reported, and broken down by kind). Caveat: swaps and scaled numbers are easy corruptions, so this is a floor test. drop_part counts as wrong only where the question asks for a full date. Hashes: inject.py and inject_rows.jsonl are listed in results/grader6/inject_hashes.txt.

## Amendment 6.1 (2026-11-06 04:0x, after the S12 scoring found the fault)
- **Fault:** R1 compared day numbers as strings, so "09 November 2008" vs "November 9, 2008" fired R1 and graded a correct answer wrong.
- **Fix:** day, month and year parts are compared after stripping leading zeros (`num()` in `veto`). Nothing else changed. All 20 unit tests still pass.
- **Reach:** I scanned every judged row on record (results/grader5/judge_grades.jsonl). This was the only row where R1 fired only because of zero padding (S12 DEV sqa-1112). So the V1/V2/V3 validation, the P0.2 injection test, and S8 to S11 are unchanged.
- **Direction:** the fault could only turn correct into wrong, never wrong into correct, so it never caused false credit.
- **Reporting:** S12 is reported under both frozen grader 6 and 6.1. From S13 on, 6.1 is primary, with any row where the two differ listed.
- **Hash:** vkg/grade6.py b74faad218132b83c986bcb52e70044ea995dc9de4863a990b948acad023638e
