# S6a protocol: cautious prompt vs probe gate vs fine-tuned abstention on one small model (written 2026-11-05 15:18 BEFORE any S6 output existed)

Prior art (not repeated, reused as recipes): R-Tuning (abstention SFT on a model's own known/unknown split), Gekhman et al. (do not inject unknown facts), reward-based abstention RL (Jha et al. 2601.20126; Chen et al. 2510.17733), semantic-entropy probes (Kossen et al.). What is specific here: one controlled comparison of the three mechanisms on the SAME 4B model, the SAME questions and the SAME grader, at matched coverage, with an out-of-distribution long-tail set.
Model: Qwen3-4B-Instruct-2507 (dense), LoRA r=16 alpha=32 dropout 0.05 on all attention and MLP projections, 2 epochs, batch 16, lr 1e-4 linear decay with 20 warm-up steps, bf16 autocast, LoRA weights in fp32. No hyper-parameter is tuned.
Training data: 3,000 TriviaQA validation questions disjoint from S5's 2,000 (random.Random(7000)). Target = the model's own greedy answer as JSON if it was correct (alias match, vkg/probe_eval.correct), else {"answer": "unknown"}. The training prompt is the plain prompt (no instruction to abstain), so any abstention is learned, not prompted.
Evaluation: S5's in-distribution TriviaQA test (500) and the 500-question SimpleQA Verified pool (outside the 300 frozen test ids). Systems on the same model: plain (S5 greedy answers), cautious prompt (answer only if certain, else "unknown"), trained (LoRA), probe gate (S5's label-A probe on hidden states, applied to the plain answers, answering the top-k questions by probe score with k = the answered count of the system it is matched to).
Abstention = the project's UNKNOWN_RE on the answer string; refusals written as sentences ("X never served as...") are NOT abstentions and count as wrong answers, as in earlier tables. Correctness = TriviaQA alias matching / grade_v3 (known false-negative and false-positive limits; docs/GRADER_VALIDATION.md). SER = wrong answers / all questions; yield = correct / all.

## Decision rules (fixed now)
- R1 trained abstention is credited beyond prompting if, on BOTH test sets, trained minus cautious SER has a paired CI entirely below 0 AND trained yield is not lower than cautious yield by more than 0.03.
- R2 trained is credited beyond the probe gate if trained minus probe-gate SER (same coverage) has a CI entirely below 0 on both sets. If the CI includes 0, the two are reported as tied.
- Any claim stays limited to this 4B model.

## Predictions (point guess, range)
- S6-1 base greedy-correct rate on the 3,000 training questions: 0.43 (0.35-0.52).
- S6-2 trained model on TriviaQA test: coverage 0.55 (0.40-0.70); SER 0.15 (0.08-0.25), at least 0.20 below plain SER.
- S6-3 cautious prompt on TriviaQA test: coverage 0.85 (0.55-0.98), SER 0.30 (0.18-0.42).
- S6-4 R1 on TriviaQA: trained minus cautious SER -0.10 (-0.20 to -0.02), CI excludes 0 (p about 0.7).
- S6-5 R2 on TriviaQA: trained and probe gate tied (difference within +-0.03, CI includes 0) (p about 0.6).
- S6-6 SimpleQA: trained coverage 0.25 (0.05-0.50); cautious coverage 0.70 (0.40-0.95); trained SER at most 0.20; trained minus cautious SER <= -0.10 with CI excluding 0 (p about 0.7).
- S6-7 R1 passes on both sets (p about 0.55).

## Hashes (before the run)
```
f919bfcdcc080e7b0ff6641a77a51323c024cd42fe6a05bda8cc5f472ed87a08 vkg/s6_run.py
9c9aa39bacd63c9d810f6417bec64f1a4616dbbf871cf2c91e13533b014bb3fa vkg/probe_gen.py
8f1ac345735292f1005b3c2a56b825dedbbf255a03d93f52260b9e84ab17f0c3 vkg/probe_eval.py
0579f162d7e3e35f0b3f0354a9b4666dd0082403612549b8acebb8777725e790 vkg/grade_open.py
7f22d4bad5eb1a568f91647df4dfd024479d6e0d2edac1cdadf3763ebe7eb21d vkg/systems.py
```
Known limits: one 4B model, one seed, one training run; labels noisy (alias matching, string grader); TriviaQA and SimpleQA may be in pre-training data; abstention regex is crude; "plain" is penalised when it writes denials as sentences.


## Scoring (written after the run)
- S6-1 base greedy-correct on the 3,000 training questions 0.442 (predicted 0.35-0.52): pass. Training examples: 1,326 answers, 1,674 "unknown" targets. Training loss fell from 0.11 to 0.01 in 374 steps (about 90 s).
- S6-2 trained model, TriviaQA test: coverage 0.424 (predicted 0.40-0.70): pass; SER 0.060 (predicted 0.08-0.25): outside the range, better than predicted; at least 0.20 below plain (plain 0.512, difference -0.452 [-0.496, -0.406]): pass.
- S6-3 cautious prompt, TriviaQA: coverage 0.624 (0.55-0.98) pass, SER 0.246 (0.18-0.42) pass.
- S6-4 trained minus cautious SER on TriviaQA: -0.186 [-0.224, -0.148] (predicted -0.20 to -0.02, CI excluding 0): pass.
- S6-5 trained vs probe gate on TriviaQA predicted a tie: **fail**. Trained has fewer silent errors at the same coverage (-0.052 [-0.082, -0.024]) and more correct answers (+0.052 yield [+0.020, +0.086]).
- S6-6 SimpleQA: trained coverage 0.098 (0.05-0.50) pass; trained SER 0.082 (<= 0.20) pass; cautious coverage 0.106 (predicted 0.40-0.95): **fail** (the cautious prompt already abstains on ~89%); trained minus cautious SER +0.002 [-0.026, +0.028] (predicted <= -0.10): **fail**.
- S6-7 / R1 (trained beats cautious on BOTH sets): **not met**; it holds in distribution only. R2 (trained beats the probe gate on both sets): not met (TriviaQA yes, SimpleQA tied).
