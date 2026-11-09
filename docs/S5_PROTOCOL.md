# S5 protocol: do hidden states encode whether the model knows the answer? (written 2026-11-05 15:04 BEFORE the full run)

Environment (set up with the owner's go-ahead, inside the project folder only): venv_gpu (torch 2.14.1+cu130, transformers 5.22.1, scikit-learn 1.9.1), model models/qwen3-4b-instruct-2507 (Qwen3-4B-Instruct-2507, dense, standard attention, Apache-2.0, 7.6 GB), TriviaQA rc.nocontext validation file (7.3 MB) in data/triviaqa. Nothing was installed into the base Python.
Why this model: it fits the GPU beside nothing else, is the model the S6 plan trains, and probes need labels from the SAME model whose activations are read; labels from Qwen3.8-27B (S3) cannot be reused. It is a different, smaller, dense model: results do not transfer to Qwen3.8-27B or to the hybrid-attention/MoE models without a test.

## Design
- Data: 2,000 TriviaQA validation questions (random.Random(6000)); first 1,500 = train, last 500 = in-distribution (ID) test. Out-of-distribution (OOD): the 500 SimpleQA Verified questions of the S3 pool (all outside the 300 frozen test ids; the test ids are never read). Probes are trained on TriviaQA train only.
- Per question (vkg/probe_gen.py): hidden states at the last prompt token (chat template, before the answer) for 11 layers; a greedy answer with mean token log-probability; 8 sampled answers (T=0.8). Prompt = the project's B0 JSON prompt.
- Labels from the model's own answers. A = greedy answer correct. B = known = at least 1 of the 9 answers correct. TriviaQA correctness: normalised equality with any alias, or token-bounded containment of an alias of at least 3 characters in an answer of at most 12 words. SimpleQA: vkg.grade_open.grade_v3. No LLM judge.
- Probe: L2 logistic regression on standardised activations, class-weight balanced; regularisation C and the layer are chosen by 5-fold CV inside the training set only.
- Controls: TF-IDF of the question (word 1-2-grams); probe on a random-initialised copy of the same architecture (same tokenizer and prompts); shuffled training labels with the full selection pipeline; reference signals: agreement of the 8 samples with the greedy answer, mean log-probability of the greedy answer.
- Metric: AUROC with 2,000-resample bootstrap over questions, paired differences to each control. Primary label for the decision rules: B (more positives).

## Decision rules (fixed now)
- D1 (probe encodes more than question content): on the ID test, label B, probe AUROC >= max(TF-IDF, random-init, shuffled) + 0.05 with paired CI excluding 0.
- D2 (transfer): OOD AUROC lower CI bound above 0.5 AND probe >= TF-IDF OOD + 0.05. If the OOD positives are fewer than 25 or the CI is wider than 0.25, the OOD result is reported as inconclusive, not as pass or fail.
- D3 (beyond sampling): reported only; the probe is called competitive if within 0.03 of sampling agreement (one forward pass vs nine generations).

## Predictions (point guess, range)
- S5-1 base rates: TriviaQA greedy-correct 0.40 (0.28-0.55); SimpleQA greedy-correct 0.02 (0.005-0.05); SimpleQA known 0.06 (0.02-0.11).
- S5-2 ID probe AUROC: label A 0.78 (0.72-0.86); label B 0.80 (0.74-0.88).
- S5-3 TF-IDF ID AUROC label A 0.66 (0.60-0.72).
- S5-4 random-init probe ID AUROC label A 0.62 (0.52-0.70): not above TF-IDF + 0.03.
- S5-5 sampling agreement ID AUROC label A 0.80 (0.74-0.86); probe within 0.04 of it.
- S5-6 selected layer between hidden_states 15 and 27.
- S5-7 OOD (SimpleQA) label B probe AUROC 0.65 (0.55-0.75), lower CI bound above 0.5 with probability about 0.6; sampling agreement OOD higher than the probe.
- S5-8 D1 passes (p about 0.8); D2 is inconclusive or fails (p about 0.7).

## Hashes (before the full run)
```
9c9aa39bacd63c9d810f6417bec64f1a4616dbbf871cf2c91e13533b014bb3fa vkg/probe_gen.py
8f1ac345735292f1005b3c2a56b825dedbbf255a03d93f52260b9e84ab17f0c3 vkg/probe_eval.py
0579f162d7e3e35f0b3f0354a9b4666dd0082403612549b8acebb8777725e790 vkg/grade_open.py
62cb9fb7796e95d936192cb5aca3ac146cd79cc8bcd153d155c94e1f4690e092 vkg/tasks.py
```
Smoke test (16 questions, outputs and labels read by eye, then deleted) found no bug that changes labels; the JSON parser falls back to the first output line when the answer is truncated at 40 tokens.
Known limits: one 4B model, one seed; activations at the prompt's last token only; linear probes; TriviaQA labels are alias-matching (some correct answers will be missed); possible contamination of both datasets; random-init control is one draw.


## Scoring of the pre-registered predictions (written after the run)
- S5-1 base rates: TriviaQA greedy-correct 0.412 train / 0.480 test (predicted 0.28-0.55): pass. SimpleQA greedy-correct 0.064, 32 of 500 (predicted 0.005-0.05): **fail** (above range; I read all 32 positives: one clear false positive, "Artificial Intelligence" vs "Journal of Artificial Intelligence Research", so label noise is about 3%). SimpleQA known 0.096 (predicted 0.02-0.11): pass.
- S5-2 ID probe AUROC: label A 0.821 [0.783, 0.853], label B 0.805 [0.765, 0.840]: pass (both inside the ranges).
- S5-3 TF-IDF ID label A 0.682 (predicted 0.60-0.72): pass.
- S5-4 random-init probe ID label A 0.641 (predicted 0.52-0.70, not above TF-IDF + 0.03): pass.
- S5-5 sampling agreement ID label A 0.803 (predicted 0.74-0.86), probe within 0.04 of it (+0.017, CI -0.026..+0.059): pass.
- S5-6 selected layer between 15 and 27: label A layer 27 pass; label B layer 33 **fail**. The per-layer CV curves are flat from layer 21 to 36 (0.82-0.84), so the choice among them is not meaningful.
- S5-7 OOD label B: probe 0.663 [0.576, 0.746] (predicted 0.55-0.75, lower bound above 0.5): pass. "Sampling agreement OOD higher than the probe": **fail** (agreement 0.585; probe higher by +0.078, CI -0.025..+0.178, not significant).
- S5-8 D1 passes (predicted pass): ID label B probe minus TF-IDF +0.121 [+0.075, +0.166], minus random-init +0.183, minus shuffled +0.292. D2: predicted inconclusive or fail, observed **pass**: OOD label B has 48 positives and CI width 0.17 (conclusive), lower bound 0.576 above 0.5, probe minus TF-IDF OOD +0.131 [+0.035, +0.225]. D3: on label B the probe beats sampling agreement by +0.068 [+0.023, +0.112] on the ID test (one forward pass against nine generations) and is not distinguishable on OOD.
