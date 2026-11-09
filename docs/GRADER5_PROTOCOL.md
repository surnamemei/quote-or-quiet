# Grader 5 protocol: an LLM judge with the public SimpleQA Verified prompt

Written 2026-11-05 at about 22:03 (local clock), before any judge call. The first draft said 2026-11-06 by mistake; that date was corrected after the judge had started, and nothing else changed.

## Why
In S8 and S9, about half of the graded-wrong answers were grader false negatives (10 of 17 for 4B cautious + check, 10 of 22 for certificates). Every SER comparison is limited by this. String rules (grade_v3, v4) keep false credit at zero but miss name variants, number words, and implied parts.

## Reuse
- Prompt: the SimpleQA Verified autorater prompt (Haas et al., arXiv 2509.07968, Appendix A, CC BY 4.0). It was decoded from the paper's embedded text attachment, and only the LaTeX colour markup was removed (`vkg/sqav_grader_prompt.txt`). It revises the original SimpleQA grader (openai/simple-evals `simpleqa_eval.py`, MIT; downloaded copy SHA-256 d61a8f97...). The labels are CORRECT, INCORRECT and NOT_ATTEMPTED; parsing takes the first A/B/C, with C as the default, as in simple-evals.
- Judge: local qwen3.8-27b (Ollama), temperature 0, no thinking.
- **Limitations:**
  - The official setup uses GPT-4.1 as the judge, and a 27B local model may be weaker.
  - The judge is the same family as every graded system, and on 27B outputs it grades its own answers.
  - It sees only the question, gold and answer.

## Validation data (labels fixed before any judge call)
- **V2 (new, primary):** 232 unique answered rows, drawn by `results/grader5/draw.py` (seed 20261106).
  - Pool: FRESH rows of 4B plain, cautious, certificate, 27B B1 and B2, plus DEV SimpleQA-E rows of 4B plain, cautious and certificate. That gives 450 unique rows; the frozen grader calls 112 wrong and 338 correct.
  - Sample: all 112 grader-wrong rows plus 120 random grader-correct rows.
  - Labels: one blind LLM rater (a Claude subagent). It saw only the question, gold and answer, and had no access to grader labels, systems, passages, code or the web.
  - Result: 150 C, 81 W, 1 N, 10 marked borderline (`v2_labels.txt`).
  - Caveat: I (the main session) had read about 40 of these rows during S8 and S9. The rater had not.
- **V1 (old, secondary):** the 240 rows of docs/GRADER_VALIDATION.md (27B outputs; 167 C, 73 W). The v4 rules were designed on V1, so V1 is in-sample for v4 but not for the judge.
- **Frozen graders on V2, computed before the judge:**
  - v3: 0 false credit among the 120 grader-correct rows; 30 misses among the 112 grader-wrong rows.
  - v4: 0 false credit; 23 misses.

## Hashes (SHA-256)
- vkg/grade_judge.py 2e392d6b056eaafbb952205c106ca21aecb5520555b9622db25586d9a5dad390
- vkg/sqav_grader_prompt.txt e8db4b23d91469ce09d5e0a152f381dee894f8042b5590cf3f599573ca38a920
- vkg/judge_run.py fde55a46c50c4b86e536dfbc5f9a0e547c8492b608380637e998f0bb00daac2b
- results/grader5/draw.py 0c44e7bbdf0154651a472c1aa301053ce22c190ae772d0c64b537fc0d956137f
- results/grader5/v2_blind.jsonl 39c52d1195876b77332ffb7ad7e8d47662b16c38f2d7e6136f172bf63429dd90
- results/grader5/v2_labels.txt 3418767c739e70d00e360dc46f234cf7dfb1105504af89e91e172365ab395401
- results/audit/validation/my_labels.txt c43b7f6bfdaa6a818c209b3c0054a3aafb266e8a9fc7ab90e617b8430a330223
- results/audit/validation/sample_blind.jsonl 5e3f8741825ed3e47d5412127f13fce798db51525d52614da9546bd961292025

## Criteria
"False credit" means the judge says CORRECT on a row labelled W or N; this is the dangerous direction, because it hides hallucinations. "Miss" means the judge says anything else on a row labelled C.
- J1 (V2, primary safety): false credit on at most 4 of the 82 W/N rows (about 5%).
- J2 (V2): misses on at most 10 of the 150 C rows (v3 has 30 and v4 has 23).
- J3 (V1): false credit at most 5% of the W rows, and misses at most 10% of the C rows.
- J4 (descriptive): agreement of the judge's NOT_ATTEMPTED with the code non-answer detector, measured on all judged rows.

## Decision rule
- **Adopt:** if J1 and J2 hold, the judge becomes the primary grader for new runs, with v4 reported beside it.
- **Rejected:** if J1 fails, the judge is rejected whatever J2 says, and v4 stays.
- **Past results:** predictions already scored stay scored on their frozen graders. A judge regrade of S6b, S8 and S9 is reported as a sensitivity table only.
- **Error reporting:** pool-level error rates are re-weighted to the full 450-row pool by stratum, since the sample over-weights grader-wrong rows.
