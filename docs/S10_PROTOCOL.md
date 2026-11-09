# S10 protocol: a code-generated reading curriculum

Written 2026-11-05, before training. No S10 output exists.

## Question
S7b, S8 and S9 left one main error for grounded answering: misreading a passage that contains the answer. Examples are picking a distractor event, the wrong stage of a timeline, or the wrong role, and answering with a distractor's fact when the asked fact is absent. Gating, post-hoc checks and output constraints did not reduce it. Can training on exactly these traps, with exact labels, reduce it on real questions?

## Prior work (checked 2026-11-05, abstracts only)
Distractor-aware fine-tuning already exists: RAFT (2403.10131), PrismRAG (2507.18857; reports +5.4% factuality), and "The Distracting Effect" (2505.06914; up to +7.5% accuracy). Those use LLM-written or edited distractors on real passages. Here, code generates the passages from made-up facts, with exact labels and an explicit "unknown" target when the asked fact is missing. The result is measured as silent errors with abstention. This is a small variant of existing work, not a new method.

## Design
- **Curriculum** (`vkg/reading_curriculum.py`): 2000 items (seed 10), 72% answerable. Item types:
  - biographies of 3 made-up people (birth date and place, three positions with years, an award), asking for one person's fact;
  - several accidents on the same day, asking for one event's count;
  - club timelines, asking for one stage's year;
  - membership numbers written as words for several years;
  - "one of N children" → siblings (a small inference);
  - "miss" variants: the asked fact is removed but distractors keep theirs, and the target is "unknown".
- **Training:** the S6b set (3000 SQuAD2 items, half "unknown") plus the 2000 synthetic items. The recipe is identical to S6b (LoRA r16, 2 epochs, bs 16, lr 1e-4, plain prompt), giving adapter `models/s10_lora_reading`.
- **Comparison:** the S6b adapter (same recipe, SQuAD2 only) is the control, so the curriculum is the only difference. The base model's plain and cautious prompts are reported beside it.
- **Evaluation** (plain prompt, greedy decoding):
  - FRESH (200; S8 items);
  - SimpleQA-E DEV (300);
  - SQuAD2 held-out (300);
  - FaithEval held-out (300);
  - synthetic test (300 new items, seed 11; same templates, so in-distribution).
- **Graders:**
  - SimpleQA: grader 6 (primary since adoption), with v4 as a sensitivity;
  - SQuAD2: dataset spans;
  - FaithEval: every answer counts as an error;
  - synthetic test: normalised exact match against the target;
  - non-answers: the code detector (`s8_eval.non_answer`).
- **Runner:** `vkg/s10_wait.py`, at idle priority, waiting for free VRAM (train ≥ 20 GB, eval ≥ 16 GB). Afterwards the judge runs on the new SimpleQA answers.

## Hashes (SHA-256)
- vkg/reading_curriculum.py b40e1e7b38764d109b83b89dfebc974928242f308ba2caf31afeacf2b58adb9a
- vkg/s10_run.py 7d0d37c62494a70c046ecd025012f6c2161a289ffa19a36858ebe608496c1f99
- vkg/s10_wait.py 15a070070306ebb090a89755635d93840e6779b7792b759267858d62b4690b06
- results/runs/s10/train.json 0f5d0d3df87b19bf11e93a40ae0ebe8ed60a59041efa664be0bb7bfee0864962
- results/runs/s10/synth_test.json bafdc76b2a65c3f2c146c146d28d027c3d2be72956314c0e103e73e522109247

## Predictions
- **R1 (sanity, synthetic test):** S10 SER ≤ 5%, and at least 10 points lower than S6b's.
- **R2 (primary; FRESH + SimpleQA-E pooled, 500 items, grader 6):** S10 SER minus S6b SER ≤ −1.0 point with the paired 95% CI upper bound ≤ 0, and a correct-answer loss of at most 2 points. My prior that this holds is about 35%: the templates are far from Wikipedia text, and S6b is already at about 3% SER on DEV.
- **R3 (SQuAD2):** S10 SER at most S6b's + 2 points, and correct among answerable within 3 points of S6b's.
- **R4 (FaithEval):** S10 SER ≤ S6b SER.
- **R5:** S10 coverage on SimpleQA within 5 points of S6b's.

## Decision rule
- **Useful:** R2 and R3 hold.
- **In-distribution only:** R1 holds but R2 fails; the result is reported as "learned the templates, did not transfer".
- Failed predictions are reported as failed.

## Scoring script
vkg/s10_eval.py b32a92936d1f67bdb2a0d692f7351ee9adb92625479265833a50a44cc5400512 (written while training was running, before any S10 output existed).

## Incident
Training attempt 1 (22:50-23:05) stopped at step 175/624 with CUDA out of memory, probably because another process took GPU memory while it ran (log kept as results/runs/s10/train_attempt1_oom.log). No adapter or output was saved. Restarted unchanged at 23:1x.

## Scoring amendment (2026-11-05, before reading any number)
The frozen s10_eval.py crashed on its first run (KeyError: it requested judge grades for abstentions, which are never judged). It was fixed to compute correctness only for answered items; new hash a67af1590c856d78de0209f97764ac263adf9e7f5a57a3766274affe0519359e. No criterion changed. After the tables were read, a second issue was found: the synthetic matcher does not equate number words with digits ("three thousand" vs "3,000"). This is reported as a correction in results/S10_reading_curriculum.md, not fixed in the script.
