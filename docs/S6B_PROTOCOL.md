# S6b protocol: evidence-conditioned abstention on the 4B model (written 2026-11-05 15:34 BEFORE any S6b output existed)

Question: if a small model is trained to answer only from the passage it is given (and say "unknown" otherwise), does that beat prompting for the same, and how does it compare with Qwen3.8-27B on the same retrieved passages? Prior art: reward/SFT abstention (R-Tuning, 2601.20126, 2510.17733, GRACE for evidence sufficiency); not repeated, reused as recipe.
Model: Qwen3-4B-Instruct-2507 + LoRA (same settings as S6a: r=16, alpha=32, 2 epochs, effective batch 16 via 4 micro-batches of 4, gradient checkpointing because the GPU is shared with another job, lr 1e-4, no tuning). Training prompt = plain passage prompt without any instruction to abstain.
Training data (vkg/s6b_run.py build): 3,000 SQuAD 2.0 validation items, 1,500 answerable (target = gold span from the passage) and 1,500 unanswerable (target "unknown"), seed 8000, excluding by id AND by context paragraph every SQuAD2 item used in the seed 0 / 1000 / 2000 evaluation samples. No parametric facts are injected: targets come from the passage.
Evaluation (same 4B model, three systems: plain passage prompt, cautious prompt "use ONLY the passage, else unknown", trained LoRA with the plain prompt):
 (a) SQuAD 2.0 held-out seed 1000 (300 items); (b) FaithEval held-out seed 1000 (300 items; any definite answer to an unanswerable or inconsistent item is a silent error); (c) the 300 SimpleQA test questions with the SAME variant-E Wikipedia passages as the frozen 27B run (graded with the repaired grader; wrong counts are upper bounds).
Reference (not retrained): Qwen3.8-27B B1_abstain on the same 300 questions and passages: correct 58.7%, wrong 6.3%.
Metrics: SER = silent errors / all items; yield = correct / answerable; paired bootstrap CIs over items.

## Decision rules (fixed now)
- R3 evidence-conditioned training is credited beyond prompting if, on SQuAD2 held-out AND on SimpleQA-E, trained minus cautious SER has a CI entirely below 0 and trained yield is not lower than cautious yield by more than 0.03.
- R4 the 4B model is called competitive with the 27B on SimpleQA-E if trained SER is within +0.03 of the 27B B1 SER (paired CI upper bound below +0.05) AND trained correct is within 0.10 of the 27B's.

## Predictions (point guess, range)
- S6b-1 SQuAD2 held-out: trained SER 0.06 (0.02-0.12); cautious SER 0.16 (0.08-0.28); plain SER 0.30 (0.18-0.45); trained yield 0.82 (0.65-0.92).
- S6b-2 FaithEval held-out: trained SER 0.12 (0.04-0.25), lower than cautious by >= 0.03 (p about 0.6).
- S6b-3 SimpleQA-E: trained correct 0.45 (0.30-0.58), SER 0.08 (0.03-0.16).
- S6b-4 SimpleQA-E: trained minus cautious SER <= -0.02 with CI excluding 0 (p about 0.55).
- S6b-5 R3 holds (p about 0.45). R4 holds on SER (p about 0.5) and fails on correct (4B correct more than 0.10 below the 27B) (p about 0.7).

## Hashes (before the run)
```
1d098e18d9905c99a158c3e577d941422b14fabb80c11eb935bb93d2892f9972 vkg/s6b_run.py
f919bfcdcc080e7b0ff6641a77a51323c024cd42fe6a05bda8cc5f472ed87a08 vkg/s6_run.py
8f1ac345735292f1005b3c2a56b825dedbbf255a03d93f52260b9e84ab17f0c3 vkg/probe_eval.py
0579f162d7e3e35f0b3f0354a9b4666dd0082403612549b8acebb8777725e790 vkg/grade_open.py
62cb9fb7796e95d936192cb5aca3ac146cd79cc8bcd153d155c94e1f4690e092 vkg/tasks.py
85bcccd902b3eee821c008ac7cc89cba15b3da0d72b61dc49d263999d10e65f5 vkg/retrieval.py
f2a39fc44b639e71e07fdfe9d15d35815397aab2b22bc2e284b0d0e038181323 vkg/retrieval2.py
```
Known limits: one 4B model, one run; SQuAD2 passages are clean single paragraphs while variant-E passages are multi-article Wikipedia excerpts (a distribution shift by design); string grading with known false negatives; abstention regex crude.


## Scoring (written after the run)
Training: 3,000 examples (1,500 answerable, 1,500 "unknown"), 374 steps, about 18 minutes on the shared GPU; no shared contexts with any earlier SQuAD2 evaluation sample (checked: 0).
- S6b-1 SQuAD2 held-out: trained SER 0.073 (predicted 0.02-0.12) pass; cautious SER 0.180 (0.08-0.28) pass; plain SER 0.527 (0.18-0.45) **fail**, worse than predicted; trained yield 0.827 (0.65-0.92) pass.
- S6b-2 FaithEval held-out: trained SER 0.327 (predicted 0.04-0.25) **fail**; lower than cautious by >= 0.03 (observed -0.167 [-0.223, -0.110]) pass.
- S6b-3 SimpleQA-E: trained correct 0.497 (0.30-0.58) pass, SER 0.060 (0.03-0.16) pass.
- S6b-4 SimpleQA-E trained minus cautious SER <= -0.02 with CI excluding 0: observed -0.010 [-0.030, +0.010] **fail**.
- S6b-5 / R3 (trained beats cautious on SQuAD2 AND SimpleQA-E with yield loss <= 0.03): **not met**. SQuAD2 SER -0.107 [-0.147, -0.067] but yield -0.047 [-0.113, +0.020] (point estimate beyond the 0.03 limit); SimpleQA-E SER difference includes 0 and yield -0.033 [-0.063, -0.003].
- R4 (4B trained competitive with 27B B1 on SimpleQA-E): SER -0.003 [-0.023, +0.017] (within +0.03) and correct -0.090 [-0.127, -0.053] (point estimate within the 0.10 tolerance, the CI's lower end is not): **met as written**. I had predicted the correct-answer gap would exceed 0.10; that part of S6b-5 fails.
