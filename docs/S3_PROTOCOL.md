# S3 protocol: confidence signals and risk-coverage, closed-book SimpleQA Verified
Written 2026-11-05 about 12:18 (local time), BEFORE any pool question was sent to the model. Only a smoke test on an invented question
("In which year was the Sydney Harbour Bridge opened?", not in the pool) and a synthetic metric self-test were run.

## Question
For closed-book SimpleQA Verified questions, which confidence signal best predicts that the model's greedy answer is correct, and does any
signal give a usable risk-coverage trade-off? Base rate is about 4-5% correct, so positives are few; every number carries an interval.

## Data
- Dataset: HF `google/simpleqa-verified` split `eval` (1000 rows, cache `data/hf`). Row positions are used (as in `vkg/tasks.simpleqa`).
- FORBIDDEN: the 300 frozen test positions = `random.Random(3000).sample(range(1000), 300)`. They are used only to exclude; the code asserts
  disjointness, reads only the 500 pool rows, and never stores or prints the forbidden ids.
- Pool: from the other 700, `random.Random(5000).sample(rest, 500)`. Split: pool shuffled with `random.Random(6000)`, first 250 = calibration,
  last 250 = test. Processing order interleaves cal/test so that the first 300 processed are exactly 150 cal + 150 test.
- Calibration is used only to choose thresholds, the embedding-agreement threshold and the combination weights. Headline results are test only.

## Per question (model `qwen3.8-27b`, Ollama 0.34.4, think off, JSON mode, num_ctx 8192)
- Answer (graded): greedy (T=0, seed 0) with the B0_raw prompt `Question: ...\nReply as JSON: {"answer": "<short answer>"}`.
  It counts as an attempt unless empty or matching `systems.UNKNOWN_RE`. Correct = attempt and (`grade_open.grade` in correct_strict/correct_lenient, or `lenient2`).
  Strict-only counts are reported as a sensitivity check. No LLM judge.
- Signals (all scored as "higher = more likely correct"):
  1. `b1_status`: 1 if the B1 prompt (`systems._b1_prompt`, no passage, greedy) returns status "answer", else 0.
  2. `verbal`: separate greedy call with question + the greedy answer: "confidence 0-100 that the proposed answer is exactly correct", JSON.
  3. Self-consistency, K=8 samples of the B0 prompt at T=0.8, seeds 1001..1008. Agreement = share of samples agreeing with the greedy answer.
     (i) `sc_exact`: normalized equality or token-boundary containment either way (`tasks.norm`, `tasks.matches`); an abstaining sample never agrees.
     (ii) `sc_emb`: cosine of qwen3-embedding:0.6b (`/api/embed`) embeddings of the answer strings >= threshold; the threshold is the grid value
     in {0.70, 0.75, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97} with the best calibration AUROC (ties: stricter).
  4. `logprob`: Ollama 0.34.4 `/api/chat` exposes `logprobs` (checked: tokens with logprob and bytes returned). Signal = mean token log-probability
     of the tokens that spell the answer value inside the greedy JSON output. (Also stored: min, sum, whole-output mean; not headline.)
  5. Combinations fitted on calibration only: `combo_lr` = L2 logistic regression (C=0.1) on standardised [verbal, sc_exact, sc_emb, logprob, b1_status];
     `combo_z` = fit-free mean of the calibration-z-scored four continuous signals. Missing values are filled with the calibration median.
  Seven signals are reported in total (b1_status, verbal, sc_exact, sc_emb, logprob, combo_lr, combo_z). No other signals are tried.
- Embeddings are computed in a separate phase after all generation, so the 27B model is not displaced while generating.

## Metrics (test half only; attempts only for AUROC)
- AUROC for "correct" with 2000-resample percentile bootstrap 95% CI over questions.
- Calibrated operating points: accept if signal >= t. t = lowest threshold at which calibration precision >= target with at least 5 accepted
  (2% of 250). Targets: precision >= 30% (the S3 pass rule), wrong-rate <= 25% ("25% budget"), wrong-rate <= 10% ("10% budget").
  If no such threshold exists on calibration, the signal is recorded as "infeasible" (coverage 0).
  Test result: accepted n, correct k, coverage = n / 250, precision with Clopper-Pearson 95% CI.
- Risk-coverage table on test: top 2%, 5%, 10%, 20%, 50%, all attempts (descriptive; thresholds chosen on test, so optimistic).
- Chance level: 2000 simulations of the whole threshold procedure with iid random scores and the actual labels, giving the probability that a useless signal
  "passes" or meets each budget. This guards against calling a lucky signal a success with so few positives.
- **S3 pass rule (ROADMAP):** a signal passes if, at the calibration-chosen precision>=30% threshold, test coverage >= 2%, test precision >= 30%
  and the Clopper-Pearson lower bound exceeds the test base rate (correct / 250). An optimistic variant with test-selected top-k is reported but does not count.
  S3 is "met" if at least one of the seven signals passes. Seven looks inflate the chance of a pass; the simulated chance level is reported next to it.

## What would convince me the signals are useless
All of: (a) for every signal the test AUROC 95% CI includes 0.5 or its point estimate is < 0.60; (b) no signal passes the pre-registered rule;
(c) the 25%-wrong budget is infeasible on calibration, or missed on test, for every signal. Then closed-book selective prediction on long-tail facts
is not usable for this model (ROADMAP decision rule), and I will say so. Conversely, "usable" would need a calibrated signal meeting the 25%-wrong
budget on test with coverage >= 2% and a CP upper bound on the wrong rate not far above 25%; the 30%-precision pass rule is a much weaker bar
(70% of accepted answers may be wrong).

## Predictions (written before running)
- N1. Correct rate (any of strict/lenient/lenient2) among the 250 test questions: 5% (range 3-8%). Attempts are ~100%.
- N2. Best single-signal test AUROC among {verbal, sc_exact, sc_emb, logprob}: 0.72 (range 0.62-0.82), with the best one most likely a
  self-consistency signal; its bootstrap lower bound will be > 0.5 but < 0.65.
- N3. `b1_status` test AUROC: 0.60 (range 0.52-0.68), as the B1 run showed precision 8.9% vs 4.4% base and ~20% attempted.
- N4. Number of the seven signals that pass the pre-registered S3 rule: 1 (range 0-2); number meeting the 25%-wrong budget on test with
  coverage >= 2%: 0; 10%-wrong budget: 0.

## Execution
- 2 worker threads (one question each, calls sequential), shared Ollama server, I start/stop nothing. Unreachable server: wait and retry with backoff.
  Raw records append to `results/runs/s3_signals_raw.jsonl`; log `results/runs/s3_gen.log`; flag `results/runs/s3_gen_done.flag`.
- Time rule: smoke test cost 14.7 s for the 11 calls of one question (about 2 h for 500 questions if serial). After 15 minutes of generation I extrapolate
  from questions completed; if 500 would exceed ~85 minutes I cut the pool to the first 300 of the interleaved order (150 cal / 150 test) by writing
  `results/runs/s3_limit.txt` and record the cut in the addendum below. This decision uses timing only, not any label or answer.

## Code hashes (sha256, before the run)
```
6a457b582b9f488ba4ca87fee40d97db17d64f451fb3ca5f730b4f78fd6328d6  vkg/signals.py
7f22d4bad5eb1a568f91647df4dfd024479d6e0d2edac1cdadf3763ebe7eb21d  vkg/systems.py
a4753d5710b6f8a2131289a11ece5b52fc951aab62d6e86b523e30ed8454e6cc  vkg/tasks.py
10767d35d1b4e588c1b0a1d8537982ba84828c07d3622857158da87f36aaf680  vkg/llm.py
501bc728d296bc0beb0f75496e516161878adf0221dc81d52f78cb7e725cab94  vkg/grade_open.py
```
(`grade_open.py` differs from freeze 6 because `lenient2` was added afterwards; `grade`/`lenient` are unchanged.)
`vkg/signals.py` uses its own HTTP client (the `llm.chat` cache does not return logprobs), so no files are written to `results/cache`.

## Addenda (written during the run)
- 12:23 Incident (no result looked at): the first launch (12:18) deadlocked after 10 questions because the progress logger re-acquired the
  non-reentrant lock held by the writer thread. I killed that one process of mine (PID 12892; no other process or the Ollama server touched). Fix = a separate lock
  for logging only; no change to prompts, sampling, grading or metrics. The 10 finished records are valid and kept (resume skips them).
  New hash: 555caacbf3e85fa761cb46acf4a5e1129b864491c06d71410683243df8a7c497  vkg/signals.py (the hash in the block above is the superseded 6a457b58...). The 15-minute timing check restarts from the relaunch.
- 12:33 Labelling change (requested by the project lead after an independent audit, docs/AUDIT.md 5.1, found the old graders miss many correct SimpleQA
  answers). Generation was running (about 100 of 500 done); NO labels had been computed or looked at. Primary label is now `vkg.grade_open.grade_v3`
  (status answer + non-empty answer + grade_v3 == "correct"); the old definition (strict/lenient/lenient2) is computed from the same stored answers and reported as a
  secondary column/table. grade_v3 was introduced after the run started. `analyze` fits the calibration-side choices (embedding threshold, LR weights, thresholds)
  separately under each labelling. Nothing else in this protocol changes; predictions N1-N4 refer to the primary (grade_v3) label, and I additionally score them on the old label.
  The running generation process loaded the earlier signals.py; the edits touch only grading/analysis code (generation code, prompts, seeds unchanged).
  Hashes now (analysis-time): 69e5068ef9e75999a1c3fd13d36503dc25d27279bca62959c2a7e189b9edd6c6 vkg/signals.py; 0579f162d7e3e35f0b3f0354a9b4666dd0082403612549b8acebb8777725e790 vkg/grade_open.py (with grade_v3/repaired, not edited by me).
