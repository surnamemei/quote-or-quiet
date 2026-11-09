# S9 protocol: certificate-constrained answering (bold direction 1)

Written 2026-11-05, before any full run. The only output so far is a 4-item SQuAD2 smoke test on CPU (`results/runs/cert/squad2_smoke.jsonl`). All 4 answers were span mode, all certificates verified, and all 4 answers were correct.

## Idea (docs/THEORY.md T4)
The 4B model may only answer in one of three ways:
- **span:** a verbatim substring of the passage, enforced token by token during greedy decoding;
- **compute:** two numbers copied verbatim from the passage, combined by subtraction (absolute value) or addition, evaluated by code;
- **unknown:** abstain.

Every non-abstaining answer carries a certificate, and `verify` re-checks it with plain code. By construction, an answer the passage does not support cannot be produced. What remains wrong is reading errors (wrong span or wrong numbers) and source errors.

Prior work constrains quotes or citations rather than the answer: PEER 2208.11663, ReClaim 2407.01796, FullCite 2606.07130, CopyGen 2610.28393 (checked at snippet level on 2026-11-05). The new part here is narrow: the answer itself is constrained, abstention is allowed, and the outcome is measured as silent errors against prompt baselines on the same items.

## Design
- Model: Qwen3-4B-Instruct-2507, bf16, greedy decoding.
- Mode: chosen from the first-token logits of "span", "compute" and "unknown" after the prefix `{"mode": "`.
- Copying: greedy over the top 64 tokens, with at most 24 tokens per field.
- Suites:
  - FRESH: the 200 S8 fresh questions, the clean test and primary;
  - SimpleQA-E: 300;
  - SQuAD2 held-out: 300;
  - FaithEval held-out: 300.
- Baselines: the 4B plain and cautious prompts on the same items (S6b outputs; `fresh_4b.jsonl` for FRESH), with non-answers counted by the cleaner detector.
- Graders: grade_v3 as in S6b, with grader v4 as a sensitivity; SQuAD2 dataset spans. On FaithEval every answer is an error.
- Runs only when the GPU is free of the user's jobs (`vkg/cert_wait.py`, after the S8 runner), at idle priority.

## Hashes (SHA-256)
- vkg/cert_gen.py 1e2c9343629669f1a49f703f9be82d4203ebaea1e776f0de96aa27883db52cbe
- vkg/cert_eval.py 8ba0900fa89f645341006ddcba72887c3d2e8f0bcd3f81d00398245315377e34
- vkg/cert_wait.py a9afe86665d5c330aa4b4b988eddea437ad84534eeb9279ffa2bc4e2d802b71e (replaced 2f69fc4a... before any run: the waiter no longer imports torch, so it sits at about 25 MB instead of 409 MB while waiting; queue logic unchanged)
- vkg/test_cert_gen.py 0e2f6780b8a6fc231ae080c130ba405b5edfe265954e58af0c7514479be5bbcd (18 constraint checks pass)

## Predictions
- C1: every non-abstaining certificate passes the independent re-check (100%, all suites). Anything less is a bug.
- C2 (FRESH, primary): certificate SER is lower than the cautious prompt's by at least 1 point, and correct answers are within 4 points of cautious.
- C3 (SimpleQA-E): certificate SER ≤ 7.0% (cautious) and correct ≥ 50.0% (cautious 53.0% minus 3).
- C4 (SQuAD2): certificate SER ≤ 18.0% (cautious), and correct among answerable within 5 points of cautious (87.3%).
- C5 (FaithEval): certificate SER within ±10 points of cautious (49.3%). Copying cannot stop a model from quoting a counterfactual passage, so I expect no large gain here.
- C6: compute mode is used on at most 5% of SimpleQA items.

## Decision rule
Certificate answering is called useful if C1 holds and, on FRESH, its SER is below cautious with a CI upper bound ≤ 0 at a correct-answer loss of at most 3 points. If SER is equal and correct is higher, it is reported as "no error gain, yield gain". A failed prediction is reported as failed.
