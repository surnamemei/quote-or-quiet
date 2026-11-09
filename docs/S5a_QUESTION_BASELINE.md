# S5a: how much of "correct" / "known" can be predicted from the question text alone? (control for any hidden-state probe)

Date 2026-11-05. Model whose answers define the labels: Qwen3.8-27B Q5_K_M (Ollama), SimpleQA Verified, the 500-question S3 pool (the 300 frozen test ids were never read, embedded or printed; the code asserts disjointness).
No LLM judge. No request was sent to qwen3.8-27b; the only model called was `qwen3-embedding:0.6b` (500 question embeddings, already resident in Ollama). Nothing was started or stopped.

Status labels: **VERIFIED** = computed in this session by the code below; **QUOTED** = copied from `results/S3_signals.md`, not recomputed; **UNVERIFIED** = my reading or interpretation.
Reproduce everything with one command (about 2 minutes, CPU only, embeddings cached):

```
python -B -m vkg.qbaseline all
```
A second full run reproduced `s5a_metrics.json`, `s5a_split_metrics.json` and `s5a_tables.md` bit-for-bit (VERIFIED; hashes below).

## 0. Pre-registration (written and hashed BEFORE the cross-validation run)

The pre-registered text is stored verbatim in `results/runs/s5a_prereg.txt` (sha256 `ed27617133ee53589bb42df6a9ea8c024a3aee7eeaf5cc45fa0ff9e6696a0612`) and reproduced below. Hashes at run time:

| file | sha256 |
|---|---|
| vkg/qbaseline.py (this study's code) | `3ae24484c3d3f276bf084e991e908a2d906dbc544e7537d08e56506dcbf3ecff` (unchanged after the run) |
| vkg/grade_open.py (black box, not edited) | `0579f162d7e3e35f0b3f0354a9b4666dd0082403612549b8acebb8777725e790` |
| vkg/signals.py (black box, not edited) | `69e5068ef9e75999a1c3fd13d36503dc25d27279bca62959c2a7e189b9edd6c6` |
| results/runs/s3_signals_raw.jsonl | `9878df5c923b61dccb375c233c265d01ba2f0f51872588269a149b37a79970d5` |
| results/runs/s3_embeddings.jsonl (answer embeddings) | `da585b1f93a22694fd63ca4749c92efa91c18e568fd68b5b6bcce9164c94dd00` |
| results/runs/s3_pool.json | `c0404f356d5952be5250d4c59f5b88e6901bad41569c19a5fcaa2694da503877` |
| results/runs/s5a_question_embeddings.jsonl (new, 500 questions) | `f374d5f7b72e59ca51aeb1866e773019ca4a903685ccf0807192b4c283b649cc` |
| output s5a_metrics.json (run 1 = run 2) | `14e0d159e5c68835162270895a8604a557ae3ea1d3b80b409f6723633bc84256` |
| output s5a_split_metrics.json (run 1 = run 2) | `45150ff2bb759c0567d56351c552c33ac3cad775f0f2e0b3d0c019ffd5b78126` |
| output s5a_tables.md (run 1 = run 2) | `134d64e8cad20c3d702645ceb989a92229624e19fb5e244a104f422edf6b5df2` |

Done before the text below was frozen: the 500 question embeddings (inputs only), the label counts (A = 31, B = 84, matching docs/S5_S6_FEASIBILITY.md), and a timing smoke test that printed only seconds and array shapes. No AUROC or AP of any question-feature model had been seen.

```
S5a PRE-REGISTRATION (written 2026-11-05 BEFORE the cross-validation run; no AUROC/AP of any question-feature model had been computed or seen)
What had been run before this text: (i) embedding of the 500 questions with qwen3-embedding:0.6b (inputs only, no labels), (ii) label counts (A=31, B=84, matching docs/S5_S6_FEASIBILITY.md),
(iii) a timing smoke test of 5 model/fold combinations that printed elapsed seconds and array shapes only.

DESIGN (fixed)
- Data: the 500 S3 pool questions (results/runs/s3_signals_raw.jsonl). Assertion: disjoint from Random(3000).sample(range(1000),300).
- Labels: A = greedy answer correct under vkg.grade_open.grade_v3 (attempt = non-empty and not UNKNOWN_RE, as in vkg.signals.grade_rec);
  B = at least 1 of the 9 answers (greedy + 8 samples) correct under grade_v3.
- Feature sets (question side only): tfidf (word 1-2 grams, min_df 2, sublinear), lex (18 lexical features), meta (topic + answer_type one-hot; answer_type is
  derived from the gold answer, so it is question-side metadata only in the dataset sense), lex_meta, emb (qwen3-embedding:0.6b question embedding),
  emb_lex_meta. Controls: random16, random1024 (Gaussian features), shuffle_emb, shuffle_lex_meta (labels permuted).
- Classifier: L2 logistic regression, class_weight balanced, standardised columns (not for tfidf); C chosen by 3-fold stratified inner CV (AUROC) inside the training folds only.
  Grids: tfidf {0.1,1,10,100}; dense {1e-3..10}; embedding sets {1e-4..1}; S3 sets {1e-2..10}.
- Evaluation: 20 repeats (seeds 0..19) of stratified 5-fold CV over the 500 questions; AUROC and AP computed on the pooled out-of-fold scores of each repeat, averaged over repeats;
  95% CI = percentile bootstrap (2000 resamples of questions, each resample scores all 20 repeats, mean over repeats). Paired differences use the same resamples.
  Secondary: fit on the 250 S3 calibration questions, score the 250 S3 test questions.
- S3 comparison: 'S3' = LR on [verbal, sc_exact, sc_emb(threshold 0.90, the value S3 chose on its calibration half; fixed), logprob, b1_status];
  'S3+stack_X' = the same plus one extra feature = inner-out-of-fold decision score of the question model X (emb, lex_meta, tfidf), 'S3+lex_meta' = plain concatenation.
  PRIMARY extra comparison = S3+stack_emb minus S3 on label A (paired). Others are exploratory. For label B the sc_* signals are computed from the same 8 samples that define B (circular), so B-with-S3 is shown but not interpreted as an independent predictor.
- 'Question-only control to beat' = the best (highest mean CV AUROC) of the six question-only sets, chosen per label; the choice among six is mildly optimistic and is stated as such.

PREDICTIONS (point guess, range)
 P1  Label counts: A = 31, B = 84.
 P2  Best question-only AUROC, label A: 0.60 (0.50-0.68); its 95% CI lower bound below 0.55.
 P3  Best question-only AUROC, label B: 0.64 (0.56-0.72); its CI lower bound above 0.50. Best set for B is emb or emb_lex_meta (p~0.6).
 P4  tfidf alone: A 0.54 (0.45-0.62), B 0.58 (0.50-0.65). meta alone: A 0.55 (0.45-0.62), B 0.58 (0.50-0.65).
 P5  Controls (random16, random1024, shuffle_emb, shuffle_lex_meta), both labels: mean AUROC in 0.45-0.53 and every 95% CI includes 0.50.
 P6  S3 (LR on the five S3 signals) label A: AUROC 0.76 (0.68-0.83).
 P7  S3+stack_emb minus S3, label A: dAUROC +0.01 (-0.03 to +0.04), paired CI includes 0 (p~0.8): question text adds nothing detectable beyond self-consistency.
 P8  Original cal->test split: emb label A test AUROC 0.58 (0.45-0.70); label B 0.62 (0.52-0.72).
 P9  AP of the best question-only model exceeds the base rate (A 0.062, B 0.168) by a factor of 1.2-2.0 for A and 1.2-1.8 for B.

DECISION RULES (written now)
 D1  'Question text predicts label X' is supported only if the best question-only set has CI lower bound > 0.50 AND its AUROC exceeds both random controls' upper CI bound.
 D2  'Question text adds information beyond the S3 signals' is supported only if the paired dAUROC CI of S3+stack_emb minus S3 on label A excludes 0 (positive).
 D3  A future hidden-state probe is credited with more than question-content only if, under this same protocol and labels, its mean AUROC exceeds the best question-only AUROC by >= 0.05 with a paired bootstrap CI excluding 0.
     It is credited with 'self-knowledge beyond sampling' only if it also beats the S3 signals under the same protocol (the S5 pass rule in docs/S5_S6_FEASIBILITY.md section 5 still applies in full).
```

## 1. What was done

- **Question embeddings.** `results/runs/s3_embeddings.jsonl` holds only answer strings (2638 texts; none of the 500 questions is among them, VERIFIED), so the 500 questions were embedded fresh with `qwen3-embedding:0.6b` via `/api/embed` (no instruction prefix; float32 cached in `results/runs/s5a_question_embeddings.jsonl`).
- **Labels.** A = greedy answer correct (`grade_v3`): 31/500 = 6.2%. B = known = at least one of the 9 answers correct: 84/500 = 16.8%. Count distribution for 0..9 correct answers: 416, 31, 18, 11, 2, 5, 1, 2, 1, 13 (identical to docs/S5_S6_FEASIBILITY.md; VERIFIED).
- **Features, classifier, CV.** As pre-registered. All feature fitting (TF-IDF vocabulary and idf, standardisation, C) happens inside the training folds. Outer CV: 20 repeats of stratified 5-fold. AUROC and AP are computed on the pooled out-of-fold scores of each repeat and averaged over repeats. CI = percentile bootstrap over questions (2000 resamples; each resample scores all 20 repeats). The mean per-fold AUROC is also given in the appendix because pooling scores across folds mixes slightly different score scales.
- **Controls.** Gaussian random features (16 and 1024 columns) and permuted labels (embedding and lex+meta features), through the identical pipeline.
- **S3 comparison.** `S3` = logistic regression on the five S3 signals (verbal, sc_exact, sc_emb at the S3 threshold 0.90, logprob, b1_status), same CV. `S3+stack_X` adds one feature, the out-of-fold score of the question-only model X computed inside the training fold. `S3+lex_meta` is plain concatenation.

## 2. Results (all VERIFIED; full generated tables are in the appendix and in `results/runs/s5a_tables.md`)

Every AUROC is quoted with its positives: label A 31 of 500 (base rate 0.062); label B 84 of 500 (base rate 0.168). A random score has AUROC 0.5 and AP equal to the base rate.

**Headline table: repeated 5-fold CV, 20 repeats, mean AUROC [95% bootstrap CI]**

| model | label A (31 pos, 6.2%) | label B (84 pos, 16.8%) |
|---|---|---|
| tfidf (word 1-2 grams) | **0.620** [0.533, 0.703] | **0.629** [0.570, 0.685] |
| lex (18 lexical features) | 0.594 [0.501, 0.693] | 0.629 [0.568, 0.692] |
| meta (topic + answer_type) | 0.556 [0.468, 0.639] | 0.572 [0.510, 0.632] |
| lex_meta | 0.571 [0.494, 0.649] | 0.612 [0.556, 0.668] |
| question embedding (qwen3-embedding:0.6b) | 0.530 [0.469, 0.591] | 0.558 [0.509, 0.608] |
| embedding + lex_meta | 0.532 [0.472, 0.594] | 0.562 [0.514, 0.611] |
| control: random 16 features | 0.564 [0.465, 0.658] | 0.487 [0.431, 0.542] |
| control: random 1024 features | 0.490 [0.440, 0.536] | 0.486 [0.448, 0.523] |
| control: shuffled labels, embedding | 0.499 [0.477, 0.524] | 0.507 [0.493, 0.522] |
| control: shuffled labels, lex_meta | 0.478 [0.454, 0.501] | 0.497 [0.482, 0.512] |
| S3 signals (LR on the five signals) | 0.821 [0.748, 0.886] | 0.667 [0.606, 0.727] (circular, see section 5) |
| S3 + stack(question embedding) | 0.816 [0.743, 0.881] | 0.662 [0.602, 0.722] |

Seed-to-seed SD of the AUROC over the 20 repeats: about 0.03 for question models on A, 0.02 on B, 0.05-0.06 for the shuffled-label controls (their narrow CIs come from averaging 20 independent permutations; a single shuffled run varies by about +/-0.1 on A).

**Average precision of the best question-only model (tfidf):** A 0.134 [0.079, 0.216] against base rate 0.062 (2.2x); B 0.259 [0.195, 0.333] against 0.168 (1.5x). Embedding: A 0.086, B 0.206.

**Reading.**
1. *Label A (greedy answer correct, 31 positives).* Question text carries at most a weak signal that this sample cannot separate from noise. The best set (tfidf, 0.620) is not above the random-16-feature control (0.564, upper CI 0.658), and the question embedding is at chance (0.530 [0.469, 0.591]; against 1024 random columns the difference is +0.040 [-0.033, +0.120]). Pre-registered rule D1 is **not supported** for A.
2. *Label B (known, 84 positives).* Question text carries a modest real signal: tfidf 0.629 [0.570, 0.685] and lex 0.629 [0.568, 0.692], lower bounds above 0.5 and above both random controls (upper bounds 0.542 and 0.523). D1 is **supported** for B. The embedding is weaker (0.558; +0.072 [+0.010, +0.137] over random 1024 features, but -0.071 [-0.132, -0.007] below tfidf).
3. *Does the question add to the S3 signals?* No detectable gain. Primary comparison, label A: S3+stack_emb minus S3 = **-0.005** [-0.016, +0.004] AUROC. Also S3+stack_lex_meta -0.002 [-0.017, +0.010]; S3+stack_tfidf +0.014 [-0.021, +0.046] (exploratory); plain concatenation S3+lex_meta -0.031 [-0.076, +0.011]. D2 is **not supported**. On B the same stacks give -0.004, +0.015, +0.025, all CIs including 0 (B is circular for the S3 signals, section 5).
4. *Secondary check, original 250/250 split (fit on calibration, score test).* Label A (13 calibration and 18 test positives, test base rate 0.072): tfidf 0.601 [0.479, 0.731], embedding 0.518 [0.369, 0.667], random 16 features 0.572, S3 LR 0.769 [0.649, 0.870], S3+stack_emb 0.772. Label B (41 and 43 positives, test base rate 0.172): tfidf 0.638 [0.539, 0.732], lex 0.658 [0.568, 0.743], embedding 0.584 [0.495, 0.670], S3 0.694. Same ordering as the repeated CV; all intervals wide.
5. *Question text vs the non-circular S3 signals on B (descriptive, unpaired, unfitted, all 500).* b1_status 0.588 [0.533, 0.644], logprob 0.595 [0.529, 0.663], verbal 0.565 [0.504, 0.622], against question-only tfidf/lex 0.629 (CV). The intervals overlap, but the model's own flag and token probabilities are not clearly better than the question text at telling which questions it can answer at least once. sc_exact (0.642) and sc_emb (0.682) are not comparable for B because they are computed from the samples that define B.

**Reference lines for A from S3.** QUOTED from `results/S3_signals.md` (test half, 250 questions, 18 positives): b1_status 0.722 [0.600, 0.837], sc_emb 0.750 [0.642, 0.848], combo_lr 0.795 [0.690, 0.891]; exploratory pooled 500: sc_emb 0.826 [0.758, 0.884], b1 0.715. VERIFIED recomputation here (unfitted, all 500, 31 positives): sc_emb 0.826 [0.759, 0.882], sc_exact 0.771, b1_status 0.715 [0.626, 0.801], logprob 0.714, verbal 0.623. These match the S3 pooled exploratory numbers, so the S3 signal reconstruction is consistent.

**Exploratory, not pre-registered (many looks, descriptive).** Univariate AUROC of length-type features is below 0.5 (n_words 0.42 for A and 0.44 for B; log_chars 0.43 and 0.44; n_commas 0.43 and 0.42; n_cap 0.43 and 0.44): shorter, simpler questions are somewhat more often known. By dataset metadata: answer_type Number is known most often (B 30.2%, A 12.5%; 96 questions), Person least (B 9.9%, A 2.0%; 101 questions); topic Geography A 13.0% (54 questions), Sports A 3.3% (61). Single-sample proportions with small counts.

## 3. Scoring of the pre-registered predictions

| id | prediction | observed | verdict |
|---|---|---|---|
| P1 | counts A = 31, B = 84 | 31, 84 | pass |
| P2 | best question-only A: 0.60 (0.50-0.68), CI lower bound below 0.55 | tfidf 0.620, lower bound 0.533 | pass |
| P3 | best question-only B: 0.64 (0.56-0.72), lower bound above 0.5 | 0.629 [0.570, 0.685] | pass |
| P3b | best set for B is emb or emb_lex_meta (p ~ 0.6) | best is tfidf (0.6290) and lex (0.6287); embedding sets 0.558-0.562 | **fail** |
| P4 | tfidf A 0.54 (0.45-0.62), B 0.58 (0.50-0.65); meta A 0.55 (0.45-0.62), B 0.58 (0.50-0.65) | 0.620 (0.6199, upper edge), 0.629, 0.556, 0.572 | pass, tfidf A on the boundary |
| P5 | four controls, both labels: mean AUROC 0.45-0.53 and every CI includes 0.50 | 7 of 8 means in range; A random 16 features = 0.564 is outside. All 8 CIs include 0.50 (A shuffle_lex_meta upper bound 0.501) | **partial fail** |
| P6 | S3 LR on A: 0.76 (0.68-0.83) | 0.821 | pass (top of range, 0.06 above the point guess) |
| P7 | S3+stack_emb minus S3 on A: +0.01 (-0.03 to +0.04), CI includes 0 | -0.005 [-0.016, +0.004] | pass |
| P8 | split: emb A 0.58 (0.45-0.70), B 0.62 (0.52-0.72) | 0.518, 0.584 | pass (both below the point guesses) |
| P9 | best AP / base rate: A 1.2-2.0x, B 1.2-1.8x | A 2.17x, B 1.54x | A **fail** (marginally above), B pass |

I over-estimated the question embedding (the weakest of the rich feature sets) and under-estimated how well 16 random columns can do at 31 positives (0.564). The second miss is the main message for label A.
Decision rules: D1 supported for B, not for A. D2 not supported. D3 is the bar in section 4.

## 4. What a hidden-state probe has to exceed

**On the same 500 questions, labels and repeated-CV protocol, question text alone reaches AUROC about 0.62 for "greedy answer correct" (best set tfidf, CI up to 0.70, not distinguishable from a random-feature control at 0.56) and about 0.63 for "known" (tfidf and lex, CI [0.57, 0.69]). Under rule D3 a hidden-state probe is credited with more than question content only if its mean AUROC is at least 0.05 higher with a paired bootstrap CI excluding 0, that is roughly 0.67 for A and 0.68 for B; to claim knowledge beyond sampling it must also beat the S3 signals (logistic regression on the five signals: 0.82 for A; sc_emb alone 0.83 pooled and 0.75 on the S3 test half; for B the non-circular b1_status and logprob are 0.59-0.60).**

Two practical consequences. (i) The question *embedding* is a weak control (0.53 for A, 0.56 for B): a probe that only matches it has shown little. The controls to beat are TF-IDF and the lexical features, and for A the S3 signals. (ii) With 31 positives the A label cannot resolve AUROC differences below about 0.1 (CI half-widths 0.06-0.10 for single models), so a probe on A can be shown to beat question text only if it lands near the S3 range; B (84 positives, half-width about 0.06) is the label with usable power.

## 5. Limitations (read before citing)

- **Few positives.** A has 31 positives; every A interval is wide (half-width 0.06-0.10). The A-label question-only results (0.53-0.62) are not separable from noise.
- **Selection among six question-only sets.** The "best of six" (tfidf for A and B) is mildly optimistic. The choice rule was pre-registered, but the maximum of six noisy estimates is biased upward.
- **Bootstrap CI scope.** The CI resamples questions and averages 20 CV repeats; it does not model the dependence among repeats or the variance of the C selection. Pooled out-of-fold AUROC is lower than the mean per-fold AUROC (tfidf on A: 0.620 vs 0.657) because scores from different folds are not on one scale; pooled is primary and both are in the appendix.
- **Circularity for label B with S3 signals.** sc_exact and sc_emb are computed from the 8 samples that also define B, and greedy-correct implies B. The S3 rows for B are shown but are not an independent predictor comparison; the question-only B results are unaffected.
- **S3 reference uses a label-chosen threshold.** sc_emb at 0.90 was chosen by S3 on its calibration half (same A labels). Using it inside a pooled CV that includes those questions leaks one hyperparameter value; the effect looks small (the unfitted pooled numbers match S3's exploratory ones) but is not zero. S3 LR at 0.821 (CV) is above the S3 file's 0.795 (single split) for that reason and because of more training positives.
- **answer_type and topic are dataset metadata**, with answer_type derived from the gold answer; they would not exist at deployment. They add little here (meta 0.556 and 0.572) and are counted as question-side metadata only on the lead's instruction.
- **Labels are model- and grader-specific.** Both labels come from one model (Q5_K_M 27B), one prompt, T=0 plus 8 samples at T=0.8, and `grade_v3` (known false negatives; labels not hand-checked). B depends on 9 answers; another sampling budget changes it. "Question predicts known" is about this model's knowledge, not question difficulty in general; contamination (SimpleQA public since 2025) could make popular questions look known.
- **Embedding choice.** Only the small embedder, no instruction prefix, one setting, standardised columns with strong L2. Another embedder, prompt or non-linear head might do better; not tried (this is the control the lead asked for, not a search for the best text model).
- **One pool.** All 500 questions are one random draw from SimpleQA Verified; nothing here speaks to other datasets or to distribution shift.
- **Process note.** One attempt to delete a temporary hash file was blocked by the sandbox, so a stray 291-byte file `tmp_hash1.txt` exists in the root of the Git Bash filesystem (outside the repository; safe to delete). No repository file was edited; only new files were created (`vkg/qbaseline.py`, `docs/S5a_QUESTION_BASELINE.md`, `results/runs/s5a_*`).

---
## Appendix: generated tables (verbatim from `results/runs/s5a_tables.md`)

### S5a tables (generated by vkg/qbaseline.py; 20 repeats of stratified 5-fold CV, 2000 bootstrap resamples)

Label counts: A (greedy correct, grade_v3) = 31/500, B (any of 9 answers correct) = 84/500.


### Repeated CV, label A: greedy answer correct

| model | positives/n (base rate) | AUROC mean [95% boot CI] | SD over repeats | AP mean [95% boot CI] | mean per-fold AUROC |
|---|---|---|---|---|---|
| tfidf | 31/500 (0.062) | 0.620 [0.533, 0.703] | 0.035 | 0.134 [0.079, 0.216] | 0.657 |
| lex | 31/500 (0.062) | 0.594 [0.501, 0.693] | 0.028 | 0.096 [0.061, 0.157] | 0.599 |
| meta | 31/500 (0.062) | 0.556 [0.468, 0.639] | 0.032 | 0.086 [0.054, 0.128] | 0.572 |
| lex_meta | 31/500 (0.062) | 0.571 [0.494, 0.649] | 0.033 | 0.083 [0.056, 0.126] | 0.586 |
| emb | 31/500 (0.062) | 0.530 [0.469, 0.591] | 0.028 | 0.086 [0.053, 0.138] | 0.561 |
| emb_lex_meta | 31/500 (0.062) | 0.532 [0.472, 0.594] | 0.026 | 0.089 [0.054, 0.144] | 0.569 |
| ctrl_random16 | 31/500 (0.062) | 0.564 [0.465, 0.658] | 0.037 | 0.091 [0.057, 0.143] | 0.572 |
| ctrl_random1024 | 31/500 (0.062) | 0.490 [0.440, 0.536] | 0.025 | 0.066 [0.047, 0.093] | 0.486 |
| ctrl_shuffle_emb | 31/500 (0.062) | 0.499 [0.477, 0.524] | 0.050 | 0.076 [0.069, 0.091] | 0.494 |
| ctrl_shuffle_lex_meta | 31/500 (0.062) | 0.478 [0.454, 0.501] | 0.060 | 0.068 [0.063, 0.082] | 0.476 |
| S3 | 31/500 (0.062) | 0.821 [0.748, 0.886] | 0.013 | 0.257 [0.156, 0.382] | 0.835 |
| S3+lex_meta | 31/500 (0.062) | 0.790 [0.717, 0.858] | 0.025 | 0.218 [0.137, 0.318] | 0.824 |
| S3+stack_emb | 31/500 (0.062) | 0.816 [0.743, 0.881] | 0.012 | 0.235 [0.144, 0.352] | 0.826 |
| S3+stack_lex_meta | 31/500 (0.062) | 0.819 [0.747, 0.882] | 0.013 | 0.238 [0.142, 0.359] | 0.832 |
| S3+stack_tfidf | 31/500 (0.062) | 0.835 [0.770, 0.892] | 0.014 | 0.284 [0.165, 0.427] | 0.848 |

Paired differences, label A (same bootstrap resamples):

| comparison | dAUROC [95% CI] | dAP [95% CI] |
|---|---|---|
| S3+stack_emb - S3 | -0.005 [-0.016, +0.004] | -0.022 [-0.048, +0.002] |
| S3+stack_lex_meta - S3 | -0.002 [-0.017, +0.010] | -0.019 [-0.053, +0.014] |
| S3+stack_tfidf - S3 | +0.014 [-0.021, +0.046] | +0.027 [-0.034, +0.097] |
| S3+lex_meta - S3 | -0.031 [-0.076, +0.011] | -0.039 [-0.108, +0.020] |
| emb - lex_meta | -0.041 [-0.126, +0.043] | +0.002 [-0.033, +0.044] |
| emb - tfidf | -0.090 [-0.174, -0.000] | -0.049 [-0.115, +0.010] |
| emb_lex_meta - emb | +0.002 [-0.008, +0.012] | +0.004 [-0.002, +0.012] |
| emb - ctrl_random1024 | +0.040 [-0.033, +0.120] | +0.020 [-0.009, +0.066] |

Unfitted single S3 signals over all 500 questions, label A:

| signal | AUROC [95% boot CI] | positives/n |
|---|---|---|
| verbal | 0.623 [0.543, 0.693] | 31/500 |
| sc_exact | 0.771 [0.682, 0.852] | 31/500 |
| sc_emb | 0.826 [0.759, 0.882] | 31/500 |
| logprob | 0.714 [0.586, 0.828] | 31/500 |
| b1_status | 0.715 [0.626, 0.801] | 31/500 |

### Repeated CV, label B: known (>=1 of 9 answers correct)

| model | positives/n (base rate) | AUROC mean [95% boot CI] | SD over repeats | AP mean [95% boot CI] | mean per-fold AUROC |
|---|---|---|---|---|---|
| tfidf | 84/500 (0.168) | 0.629 [0.570, 0.685] | 0.021 | 0.259 [0.195, 0.333] | 0.637 |
| lex | 84/500 (0.168) | 0.629 [0.568, 0.692] | 0.017 | 0.259 [0.200, 0.335] | 0.636 |
| meta | 84/500 (0.168) | 0.572 [0.510, 0.632] | 0.024 | 0.220 [0.169, 0.284] | 0.585 |
| lex_meta | 84/500 (0.168) | 0.612 [0.556, 0.668] | 0.022 | 0.248 [0.194, 0.317] | 0.619 |
| emb | 84/500 (0.168) | 0.558 [0.509, 0.608] | 0.023 | 0.206 [0.161, 0.264] | 0.572 |
| emb_lex_meta | 84/500 (0.168) | 0.562 [0.514, 0.611] | 0.026 | 0.208 [0.162, 0.268] | 0.583 |
| ctrl_random16 | 84/500 (0.168) | 0.487 [0.431, 0.542] | 0.028 | 0.168 [0.132, 0.213] | 0.485 |
| ctrl_random1024 | 84/500 (0.168) | 0.486 [0.448, 0.523] | 0.020 | 0.163 [0.132, 0.201] | 0.481 |
| ctrl_shuffle_emb | 84/500 (0.168) | 0.507 [0.493, 0.522] | 0.043 | 0.180 [0.172, 0.195] | 0.505 |
| ctrl_shuffle_lex_meta | 84/500 (0.168) | 0.497 [0.482, 0.512] | 0.031 | 0.179 [0.170, 0.194] | 0.493 |
| S3 | 84/500 (0.168) | 0.667 [0.606, 0.727] | 0.011 | 0.284 [0.220, 0.367] | 0.676 |
| S3+lex_meta | 84/500 (0.168) | 0.679 [0.622, 0.734] | 0.018 | 0.294 [0.230, 0.374] | 0.694 |
| S3+stack_emb | 84/500 (0.168) | 0.662 [0.602, 0.722] | 0.012 | 0.278 [0.217, 0.359] | 0.671 |
| S3+stack_lex_meta | 84/500 (0.168) | 0.681 [0.625, 0.738] | 0.014 | 0.291 [0.225, 0.373] | 0.692 |
| S3+stack_tfidf | 84/500 (0.168) | 0.691 [0.634, 0.748] | 0.015 | 0.313 [0.239, 0.404] | 0.698 |

Paired differences, label B (same bootstrap resamples):

| comparison | dAUROC [95% CI] | dAP [95% CI] |
|---|---|---|
| S3+stack_emb - S3 | -0.004 [-0.019, +0.011] | -0.006 [-0.024, +0.011] |
| S3+stack_lex_meta - S3 | +0.015 [-0.011, +0.042] | +0.007 [-0.019, +0.032] |
| S3+stack_tfidf - S3 | +0.025 [-0.004, +0.053] | +0.029 [-0.009, +0.070] |
| S3+lex_meta - S3 | +0.013 [-0.040, +0.064] | +0.010 [-0.035, +0.054] |
| emb - lex_meta | -0.054 [-0.118, +0.007] | -0.043 [-0.095, +0.005] |
| emb - tfidf | -0.071 [-0.132, -0.007] | -0.053 [-0.108, +0.002] |
| emb_lex_meta - emb | +0.004 [-0.004, +0.012] | +0.002 [-0.003, +0.008] |
| emb - ctrl_random1024 | +0.072 [+0.010, +0.137] | +0.043 [+0.007, +0.091] |

Unfitted single S3 signals over all 500 questions, label B (CIRCULAR for B: sc_exact and sc_emb are computed from the same 8 samples that define B):

| signal | AUROC [95% boot CI] | positives/n |
|---|---|---|
| verbal | 0.565 [0.504, 0.622] | 84/500 |
| sc_exact | 0.642 [0.582, 0.706] | 84/500 |
| sc_emb | 0.682 [0.624, 0.745] | 84/500 |
| logprob | 0.595 [0.529, 0.663] | 84/500 |
| b1_status | 0.588 [0.533, 0.644] | 84/500 |

### Original S3 split: fit on calibration (250), score the test half (250)


Label A: calibration positives 13/250, test positives 18/250 (test base rate 0.072).

| model | test AUROC [95% boot CI] | test AP [95% boot CI] |
|---|---|---|
| tfidf | 0.601 [0.479, 0.731] | 0.173 [0.063, 0.352] |
| lex | 0.553 [0.433, 0.668] | 0.081 [0.047, 0.130] |
| meta | 0.415 [0.279, 0.548] | 0.061 [0.037, 0.096] |
| lex_meta | 0.470 [0.347, 0.593] | 0.068 [0.040, 0.109] |
| emb | 0.518 [0.369, 0.667] | 0.112 [0.047, 0.265] |
| emb_lex_meta | 0.513 [0.365, 0.665] | 0.114 [0.047, 0.274] |
| ctrl_random16 | 0.572 [0.436, 0.699] | 0.088 [0.049, 0.143] |
| ctrl_random1024 | 0.392 [0.270, 0.516] | 0.058 [0.035, 0.088] |
| ctrl_shuffle_emb | 0.479 [0.343, 0.621] | 0.078 [0.044, 0.132] |
| ctrl_shuffle_lex_meta | 0.440 [0.304, 0.576] | 0.075 [0.040, 0.150] |
| S3 | 0.769 [0.649, 0.870] | 0.195 [0.099, 0.351] |
| S3+lex_meta | 0.719 [0.607, 0.821] | 0.137 [0.075, 0.232] |
| S3+stack_emb | 0.772 [0.650, 0.874] | 0.213 [0.107, 0.383] |
| S3+stack_lex_meta | 0.762 [0.635, 0.863] | 0.177 [0.092, 0.305] |
| S3+stack_tfidf | 0.772 [0.649, 0.873] | 0.203 [0.103, 0.367] |

Label B: calibration positives 41/250, test positives 43/250 (test base rate 0.172).

| model | test AUROC [95% boot CI] | test AP [95% boot CI] |
|---|---|---|
| tfidf | 0.638 [0.539, 0.732] | 0.320 [0.199, 0.447] |
| lex | 0.658 [0.568, 0.743] | 0.298 [0.199, 0.434] |
| meta | 0.586 [0.486, 0.682] | 0.232 [0.151, 0.327] |
| lex_meta | 0.631 [0.546, 0.718] | 0.269 [0.178, 0.386] |
| emb | 0.584 [0.495, 0.670] | 0.209 [0.144, 0.299] |
| emb_lex_meta | 0.577 [0.487, 0.664] | 0.206 [0.140, 0.295] |
| ctrl_random16 | 0.475 [0.380, 0.573] | 0.163 [0.114, 0.223] |
| ctrl_random1024 | 0.465 [0.368, 0.562] | 0.173 [0.119, 0.255] |
| ctrl_shuffle_emb | 0.493 [0.405, 0.585] | 0.191 [0.134, 0.267] |
| ctrl_shuffle_lex_meta | 0.522 [0.436, 0.613] | 0.217 [0.153, 0.314] |
| S3 | 0.694 [0.615, 0.765] | 0.330 [0.216, 0.457] |
| S3+lex_meta | 0.710 [0.633, 0.786] | 0.298 [0.204, 0.421] |
| S3+stack_emb | 0.689 [0.609, 0.762] | 0.301 [0.196, 0.425] |
| S3+stack_lex_meta | 0.709 [0.633, 0.777] | 0.298 [0.203, 0.434] |
| S3+stack_tfidf | 0.722 [0.647, 0.794] | 0.343 [0.223, 0.476] |

