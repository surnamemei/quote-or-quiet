# AUDIT2: independent audit of S5, S6a, S6b and S2 variant E (2026-11-05)

Scope: docs/S5_PROTOCOL.md, S6A_PROTOCOL.md, S6B_PROTOCOL.md, FREEZE.md (freeze 7), results/S5_probe.md, S6_abstention.md, S6b_abstention.md, open_world_tables.md, SUMMARY.md sections S5/S6a/S6b/S2, code vkg/probe_gen.py, probe_eval.py, s6_run.py, s6b_run.py, retrieval2.py, grade_open.py, analyze_open.py, tasks.py, and the raw files under results/runs/{s5,s6,s6b}.
Method: every table was recomputed from raw jsonl/npy with my own scripts in `results/audit2/` (outputs next to each script as `.txt`). No GPU, no Ollama, no model call; no existing file was edited. The S5 probes were re-fitted on CPU (about 2 min per variant, joblib over layers) with the project's own `cv_pick` logic.

## 0. Bottom line

The arithmetic is right: all published tables reproduce (S5 exactly, S6a and S6b to within bootstrap noise of +-0.007 on CI endpoints, S2 exactly). The problems are in the data and in the framing:

1. **TriviaQA row-sampling leak (new, serious for S6a, minor for S5).** The `rc.nocontext` validation file has 17,944 rows but only 9,960 distinct questions (one row per evidence document). S5, S6a and the "disjoint" claims sample ROWS. Consequences: 38 of the 500 S5 test rows (7.6%) have their question in the S5 train set; 307 of the 3,000 S6a LoRA training rows are the same questions as S5's 2,000, and **67 of the 500 S6a test rows (13.4%) are in the LoRA training set** (with the model's own label as target). The statement "disjoint from S5's 2,000" (S6A_PROTOCOL) is false by question. On the 433 clean test rows the headline S6a advantage over the probe gate shrinks from -5.2 pts (CI -8.2..-2.4) to -3.0 pts (CI -6.2..0.0), and "about equal yield vs the cautious prompt" becomes -4.8 pts (CI -8.3..-1.2), which violates the R1 yield tolerance even in distribution. The S5 results are robust (probe 0.821 -> 0.817 after removing all duplicates).
2. **The "plain" baseline is inflated by regex misses** (UNKNOWN_RE does not catch "The passage does not provide...", "None", "does not contain information", "X did not ..."). With a generous detector, plain SER moves 0.890 -> 0.826 (S6a SimpleQA), 0.303 -> 0.237 (S6b SimpleQA-E), 0.527 -> 0.470 (SQuAD2), 0.960 -> 0.900 (FaithEval). Every "trained minus plain" number in the docs is overstated by 6 to 7 pts on those sets. Cautious/trained are unaffected (0 changes).
3. **A free zero-training gate (mean log-prob of the greedy answer) is as good as the S5 probe gate** at matched coverage in S6a, and the "trained beats probe gate" result is not distinguishable from "trained beats log-prob gate" once the leak is removed (-2.1 pts, CI -5.3..+0.9). The S6a framing treats the probe gate as the representative of "score-based gating".
4. Prediction tallies in SUMMARY are over-generous ("5 of 8 passed outright" for S5 is 4 of 8 as worded; "S6-1..4 pass" ignores that S6-2's SER was outside its predicted range, which the author's own scoring line admits).
5. R4 (S6b) "met as written" rests on a 0.090 point estimate against a 0.10 tolerance whose CI reaches -0.127; the SER match (6.0% vs 6.3%) is at different coverage (0.557 vs 0.650) and against the weakest of three 27B systems (27B VKG_v2 SER is 4.0%).

Nothing found changes the sign of any headline result; several claims are weakened (section 6).

## 1. Mismatches between recomputation and published numbers

| item | published | recomputed | note |
|---|---|---|---|
| S5 base rates A/B (train, ID test, OOD) | .412/.480/.064; .487/.544/.096 | identical (`s5_basic.py`) | labels recomputed from gen.jsonl with `probe_eval.correct` |
| S5 non-learned AUROCs (agreement, log-prob; A and B, ID and OOD) | e.g. .803/.828, .737/.767, OOD .674/.652, .585/.579 | identical | |
| S5 all probe/control AUROCs, CIs, paired diffs (`s5_refit.py`, REPRO block) | S5_probe.md | identical to the 3rd decimal; 3 CI endpoints differ by 0.001 (lbfgs/bootstrap noise) | selected layers 27 (A), 33 (B), C=1e-3 reproduced |
| S6a tables (coverage, yield, SER, precision, all paired CIs) | S6_tables.md | identical; CI endpoints within +-0.004 | `s6a_recompute.py` (own aggregation, probe refitted at layer 27, C=1e-3) |
| S6b tables | S6b_tables.md | identical; CI endpoints within +-0.007 (e.g. SQuAD2 trained-cautious yield [-0.120,+0.027] vs [-0.113,+0.020]) | `s6b_recompute.py` |
| S6b 27B reference (cov .650, correct .587, SER .063; 4B-27B SER -0.003 [-0.023,+0.017], correct -0.090 [-0.127,-0.053]) | | identical | |
| S2 variant E / baseline tables, paired diffs, evidence coverage 212/300 | open_world_tables.md | identical (`s2_recompute.py`); the 4B S6b passages reproduce coverage 212/300 | |
| SUMMARY S5: "5 of 8 passed outright" | | **4 of 8** as worded (S5-2, 3, 4, 5) | S5-1, 6, 7, 8 each contain a failed clause |
| SUMMARY S6a: "S6-1..4 pass" | | S6-2 SER 0.060 is outside its predicted range 0.08-0.25 (the S6A scoring line says so) | counts as a failed clause |
| S5 protocol/UNKNOWN: "2,000 TriviaQA validation questions" | | 2,000 ROWS = 1,962 distinct questions (38 train/test repeats, 4 repeats inside test) | |
| S6a train "3,000 questions" | | 3,000 rows = 2,786 distinct questions | |

## 2. Data hygiene

Scripts: `hygiene.py` (output `hygiene.txt`), `s6a_recompute.py`, `faith_subsets.py`.

(a) S5.
- TriviaQA train/test: disjoint by row, **not by question**. 38 test rows have the same qid/text as a train row (the greedy label is identical in all 38 pairs), 4 test rows repeat inside test. Effect when re-fitted on CPU (`s5_refit.py`, `s5_refit.txt`):

| variant | probe A ID | TF-IDF A | probe B ID | TF-IDF B | probe-minus-best-control B | OOD probe A / B |
|---|---|---|---|---|---|---|
| published | .821 | .682 | .805 | .683 | +.121 [+.075,+.166] | .706 / .663 |
| drop 38 test dups | .818 | .663 | .797 | .661 | +.136 [+.088,+.187] | .706 / .663 (same fit) |
| dedup train and test | .817 | .667 | .813 | .659 | +.155 [+.108,+.204] | .713 / .648 [.558,.731] |

  The leak mainly flatters TF-IDF (question memorisation), not the probe, so D1 gets stronger when it is removed.
- SimpleQA pool vs the 300 frozen test ids: recomputed `random.Random(3000).sample(range(1000),300)` (qids `sqa-<original_index>`); first 300 of the 500-sample equals the 300-sample; **0 overlap** by id and by question text; the 500 are a subset of the other 700. OK.
- gen.jsonl order equals the seed-6000 draw; 1,500/500/500 split as described.

(b) S6a.
- Train vs S5: recomputed seed-7000 draw equals train_labels.jsonl, and it is disjoint from S5 **by row index only**: 307 train rows are questions that are also in S5's 2,000 and **67 of them are S6a test questions** (the 500 test rows contain 496 distinct questions; 67 of them are in the LoRA training set, see `hygiene.txt`). 214 train rows are repeats of other train rows (1 qid with conflicting labels).
- On those 67 leaked test rows the LoRA model answers exactly where plain was correct (answered-correct 0.552 = plain's 0.552) and says "unknown" less often (0.448 vs 0.596 on clean rows): memorised label.
- S6a OOD set = S5's 500 SimpleQA pool questions, 0 overlap with the 300 test ids.

(c) S6b.
- SQuAD2 training items (3,000; 2,998 distinct (question, context) pairs, 2 exact repeats) vs seed 0/1000/2000 samples: **0 shared ids, 0 shared contexts**; vs the S6b SQuAD2 eval items: 0 shared ids, 0 shared contexts. Checked as claimed.
- But all **35 of 35 SQuAD2-dev articles** occur in both training and evaluation (300/300 eval items have an article seen in training), with the same annotator style for unanswerable questions. The "held-out" SQuAD2 result is same-article, same-distribution, which the docs describe as "looks like the training data" but not as shared articles.
- FaithEval: 2 of 300 eval questions appear verbatim among SQuAD2 training questions and 6 passages share a 12-word shingle with a training passage (the FaithEval SQuAD subset: 31 of the 300 eval items). Answer rates of the 31 SQuAD-derived items equal the rest (trained 0.323 vs 0.327), so no visible effect.
- Eval ids: SQuAD2 and FaithEval held-out ids are identical to the 27B held-out files (300/300 each); SimpleQA-E ids equal the 300 frozen test ids and the 27B hybrid file; no training item shares question text with them (training is SQuAD2 only).
- The SimpleQA-E passages were rebuilt (eval_items.json 15:37:08) rather than loaded from a saved file: evidence coverage recomputed from them is 212/300, equal to the frozen run. No new LLM-cache file was written after 14:57 (only emb.pkl was re-pickled), consistent with cache hits. I cannot prove byte identity (the 27B jsonl does not store passages); 2 of the 300 passages are "(no text was retrieved)".

(d) Tuning on evaluation data / order of events.
- Recorded sha256 values: all hashes in S5, S6A and S6B protocols (probe_gen, probe_eval, grade_open, tasks, s6_run, systems, s6b_run, retrieval, retrieval2) **match the current files**. Freeze 7: systems, tasks, retrieval, retrieval2, run, grade_open, llm match; **vkg/analyze_open.py changed** (recorded a4c1734a..., now b29f6b30...; mtime 13:25:44, i.e. within the freeze minute). The author discloses it; my independent recomputation matches open_world_tables.md exactly, so the change does not affect the numbers. The files under vkg/ modified later than the hashes: only vkg/s7_run.py (16:48, outside scope).
- Timestamps are consistent with the stated order: code 15:02-15:03 -> S5 protocol 15:04 -> gen.jsonl 15:10:53 -> tables 15:14; s6_run.py 15:17:42 -> S6A protocol 15:18 -> train_labels 15:20:13 -> adapter 15:22 -> eval 15:23; s6b_run.py 15:34:52 -> protocol -> train.json 15:35:25 -> eval_items 15:37:08 -> adapter 15:56 -> eval_outputs 16:28:48. All three protocol files and the result files were last written at the same instant as the scoring appended (15:15:36, 15:24:27, 16:29:55), so file times cannot show whether prediction text was edited after results; only code is hashed. Recommendation: hash the prediction text too.
- Sequential adaptivity: S6a's protocol (15:18) was written after the S5 results (15:14); S6b's rules and its choice of SimpleQA-E as a second test were written (15:34) after S6a's OOD failure (15:24). R3 requiring both suites is therefore informed by S6a; the docs do not say so.
- No evidence that any LoRA/probe hyper-parameter was tuned on evaluation data. S5 layer and C are chosen by train-only CV (code read: `fit_layers`, `cv_pick`; scaler, TF-IDF vocabulary and TF-IDF C also train-only). S6a re-fits the probe with the same train-only routine. The cautious-prompt wording and all thresholds are single fixed choices (no prompt search), which is a design limitation (one prompt = the "prompting" arm), not leakage.

## 3. Label and grader issues

TriviaQA `trivia_ok` (`trivia_sample.py`, `trivia_contain.py`, `trivia_fn.py`):
- 60 random rows (seed 11, read by me): 30 judged-correct: 0 clear false positives, 1 borderline ("volcanic cones" for "volcanoes/Active volcano"). 30 judged-wrong: 0 clear false negatives, 2 borderline ("foot" vs "ankle" for tarsus; "Bass oboe" vs bassoon). Many of the judged-wrong are denials/"None" (see below).
- Larger check on all 2,000 rows: 78 judged-correct rows are credited by alias containment only. About 4 are false positives: "James Osterberg is popularly known as Jimmy Buffett" (alias = text echoed from the question), "Maurice Cole was better known as Maurice " (echo, truncated), "Miss Cornelia Blimber does not appear in any novel by Charles Dickens" (echoed alias, a denial), "Scrooge, Huey, Dewey, and Louie". FP rate about 0.5% of 858 judged-correct.
- Candidate false negatives (alias tokens all in the answer or answer inside an alias): 87 of 1,142 judged-wrong rows; by eye about 35-40 are truly correct (e.g. "Herman Munster was played by Fred Gwynne..." and "Hugin and Munin were ravens..." are rejected by the 12-word cap; "Captain Peter Townsend", "King Idris", "coneflower", "Falkland Islands" fail alias matching). FN about 3% of judged-wrong, about 2% of all rows (label A base rate understated by about 2 pts). Verbose answers are systematically penalised by the 12-word cap, which hits the plain/verbose style more than the trained one.
- S5 OOD positives: I read all 48 label-B rows (`s5_ood_pos.txt`): about 2 questionable ("Artificial Intelligence" vs "Journal of Artificial Intelligence Research", already found by the author; "Pioneer did not make its first LaserDisc player ..." credited from a denial that contains LD-700). Noise about 4%, consistent with the author's 3%. 16 of the 48 B-positives are sample-only (greedy wrong), mostly years/numbers where a lucky guess among 9 answers counts as "knows".

Abstention regex UNKNOWN_RE (`regex_audit.py`, `s6a_recompute.py`, `s6b_recompute.py`):
- No false abstentions: 0 outputs flagged by UNKNOWN_RE would otherwise be graded correct (all six system/dataset families).
- Misses (answers the regex treats as answers; all are really abstentions or denials): "None", "none", "No middle name", "The passage does not provide/contain ...", "X did not attend high school in California", "No known cousin ...", "The authors did not specify ...". Counts of plain outputs a generous detector reclassifies as abstentions: S6a TriviaQA 10, S6a SimpleQA 32, S6b SQuAD2 17, FaithEval 18, SimpleQA-E 20. Effect on SER:

| plain SER | UNKNOWN_RE | generous detector |
|---|---|---|
| S6a TriviaQA | .512 | .492 |
| S6a SimpleQA | .890 | .826 |
| S6b SQuAD2 | .527 | .470 |
| S6b FaithEval | .960 | .900 |
| S6b SimpleQA-E | .303 | .237 |

  The author flags this in the "Known limits" line, but the headline tables and "trained minus plain" numbers (-0.452, -0.808, -0.453, -0.633, -0.243) use the uncorrected value. With the generous detector S6b-1's plain SER (.470) still lies above the predicted .18-.45 range, so that failure stands. Some denials ("X never served as...") are arguably wrong answers to a false-presupposition question; the protocol chose to count them as errors, which is defensible for a "silent error" but then the word "penalised unfairly" is the author's own admission.
- The regex is also asymmetric by design: trained/cautious emit the literal token "unknown", so they are never penalised for style.

Same grader for 4B and 27B on SimpleQA-E: `probe_eval.correct` -> `grade_v3` (strict `matches` OR `repaired(gold[0], ans)` with hedge check) and `analyze_open.cor_rep` (same expression) agree on all 900 4B outputs (0 disagreements, `s6b_recompute.py`). Differences that remain: (i) abstention is decided by the status field for the 27B (103 unknown, 2 conflict, 195 answer; no 27B answer text matches UNKNOWN_RE) but by regex for the 4B; (ii) the 27B prompt (B1_abstain) differs from the 4B prompts; (iii) answer length is similar (mean 2.3 words 4B vs 2.3 words 27B), and the two systems' wrong rows are mostly the same questions with the same grader false negatives (Colombia/"The Republic of Colombia", Blodgett, Kielan-Jaworowska, Randolph, "consumption", "White" vs a polluted gold). At least 8 of the 4B's 18 "wrong" are grader false negatives or polluted golds, so both SERs are upper bounds and the comparison is roughly apples to apples on grading. It is not apples to apples on coverage (see 4).

## 4. Statistics and overclaims

Procedure checks.
- Paired bootstraps resample questions/items (S5: 2,000 draws, `probe_eval.boot`; S6: 2,000 draws; seeds fixed). Percentile intervals; draws with a single class skipped (negligible). CIs on S5 are conditional on one fitted probe, one random-init draw, one shuffled-label draw. The shuffled-label control's OOD AUROC varied from .455 to .554 across my three refits (selected layer/train set change), so fit-to-fit variability on the 32/48-positive OOD set is of the same order as the reported CI half-width (0.08-0.09). The D2 margin (+0.131 over TF-IDF, CI lower +0.035) survives all three refits, but the OOD TF-IDF control (a TriviaQA-trained bag of words applied to SimpleQA) is a weak bar by construction.
- Selection of layer and C: inside the training set (confirmed). Folds are not grouped by question, so duplicated questions sit in both CV folds (mild optimism in CV only). The per-layer curve is flat from layer 21 to 36 (.82-.84), so "selected layer 27 vs 33" carries no information; S5-6 is not a meaningful prediction.
- Multiple comparisons: S5 has 20 paired CIs, S6a about 12 per set, S6b about 12 per suite, none adjusted. The pre-registered rules are conjunctions (D1: three controls; R1/R3: both suites), which is conservative for passes. The weakest rejected/borderline items are fragile: S6b trained-minus-cautious SimpleQA-E yield [-0.067,-0.003], S6a clean-test trained-minus-gate [-0.062,0.000].
- Probe-gate fairness (S6a): the gate is applied to the plain answers with k set to the other system's answered count. Not equal conditions: probe trained on 1,500 rows vs LoRA on 3,000 rows (2,786 distinct) that include 67 test questions; the trained model also changes its answers while the gate only filters; only one operating point per comparison and no risk-coverage curve. An untrained gate does as well (`s6a_gates.py`): at trained coverage, SER on TriviaQA test is .112 (probe), .096 (mean log-prob), .114 (sampling agreement); trained-minus-logprob-gate = -0.036 [-0.066,-0.006] on the full test and -0.021 [-0.053,+0.009] on the leak-cleaned test. So the evidence that fine-tuning beats score gating in distribution is thin once the leak is removed.
- S6a OOD ties: about 50 answered items per system, so precision figures (16%-25%) have no power; the "ties" are ties of near-zero coverage.

Overclaims (exact sentences).
1. S6A_PROTOCOL: "3,000 TriviaQA validation questions disjoint from S5's 2,000". False by question (307 shared rows, 67 in the test set).
2. SUMMARY S6a: "In distribution fine-tuning wins: SER 6.0% vs 24.6% for the cautious prompt (-18.6 pts, CI -22.4..-14.8) at about equal yield (-1.4 pts, CI -4.8..+2.2), and vs the probe gate at equal coverage -5.2 pts (CI -8.2..-2.4) with +5.2 pts more correct answers." Clean-test values: SER -18.2 (CI -21.9..-14.3) still holds; yield -4.8 (CI -8.3..-1.2); vs probe gate -3.0 (CI -6.2..0.0), yield +3.0 (CI -0.2..+6.5); vs log-prob gate -2.1 (CI -5.3..+0.9).
3. S6_abstention.md S6-5: "Trained has fewer silent errors at the same coverage (-0.052 [-0.082, -0.024]) and more correct answers (+0.052 yield [+0.020, +0.086])." Same leak. On the clean subset the pre-registered "tie" (difference within +-0.03, CI includes 0) is borderline true (-0.030, CI touches 0.000), so even the "fail" label of S6-5 is not firm.
4. SUMMARY S6a OOD: "plain SER 89.0%", S6_abstention.md "trained minus plain: -0.808 [-0.842, -0.772]". Regex-inflated (82.6% generous; difference about -0.74). Same for S6b: "plain SER 52.7% / 96.0% / 30.3%" and the "trained minus plain" lines.
5. SUMMARY S6a: "S6-1..4 pass". S6-2 predicted SER 0.08-0.25, observed 0.060.
6. SUMMARY S5: "Predictions: 5 of 8 passed outright". Four pass as worded.
7. SUMMARY S5 label B line: "The probe beats every control by at least +0.12 ... and beats sampling agreement by +0.068 [+0.023, +0.112]." True, but it omits that mean log-prob is statistically tied (+0.039 [-0.004,+0.082]) and that on label A the probe is tied with both (+0.017, -0.007). "Sampling agreement" here is exact-match agreement of 8 samples (a weak implementation, and by construction mismatched to label B, which counts any of 9 answers). The D3 statement "the probe beats sampling agreement" is not a statement about "beyond sampling" in general.
8. SUMMARY S6b: "The 4B model nearly matches the 27B on the same questions and passages: SER 6.0% vs 6.3% ..." The 4B abstains more (coverage .557 vs .650), the reference is 27B B1_abstain (the 27B VKG_v2 reaches 4.0%, B2 5.7%), correct is 9 pts lower, and 4B abstention is read from a string while the 27B's comes from a status field. "Nearly matches" is fair only for SER at a different operating point.
9. S6B scoring: "R4 ... met as written" while correct -0.090 [-0.127,-0.053] versus the "within 0.10" tolerance. R4's wording does not say point estimate or CI, so a CI-based reading fails; the author's pre-registered expectation (gap above 0.10) was also not met by 0.01.
10. SUMMARY S6b: "Training helps where the test looks like the training data (clean passages, unanswerable questions) and on FaithEval". The SQuAD2 test uses the same 35 articles as training; the FaithEval gain (-16.7 pts vs cautious) is the only cross-dataset evidence and stays valid, but trained SER there is .327 (far from the predicted .04-.25 range).
11. SUMMARY S5: "the 4B model's hidden states carry a knowledge-boundary signal that is not in the question wording and not in the architecture alone". Supported by D1 against TF-IDF (1,500 training questions), one random-init draw and shuffled labels; the question-only control is weak (S5a found question embeddings at .53-.56); the claim holds, with "question wording" meaning bag-of-words.

## 5. Re-score of pre-registered predictions (exactly as worded)

S5 (rules: D1, D2, D3; primary label B)
| id | wording | observed | verdict |
|---|---|---|---|
| S5-1 | TriviaQA greedy-correct .40 (.28-.55); SimpleQA greedy-correct .02 (.005-.05); SimpleQA known .06 (.02-.11) | .412/.480; .064; .096 | FAIL (SimpleQA greedy-correct above range; the other two pass) |
| S5-2 | ID AUROC A .78 (.72-.86), B .80 (.74-.88) | .821, .805 (dedup .817/.813) | PASS |
| S5-3 | TF-IDF ID A .66 (.60-.72) | .682 | PASS |
| S5-4 | random-init ID A .62 (.52-.70), not above TF-IDF+.03 | .641 | PASS |
| S5-5 | sampling agreement ID A .80 (.74-.86), probe within .04 | .803, diff +.017 | PASS |
| S5-6 | selected layer between 15 and 27 | A: 27, B: 33 | FAIL on the primary label B (A passes); meaningless (flat curves) |
| S5-7 | OOD B probe .65 (.55-.75), CI lower > .5; sampling agreement OOD higher than probe | .663 [.576,.746]; agreement .585 < probe | FAIL (second clause) |
| S5-8 | D1 passes (p .8); D2 inconclusive or fails (p .7) | D1 pass (+.121 [+.075,+.166] over best control); D2 pass (OOD lower bound .576, +.131 over TF-IDF, 48 positives, width .17) | PARTIAL: D1 right, D2 clause FAIL |
| D1 | ID label B, probe >= max(TF-IDF, random, shuffled)+.05 with paired CI excluding 0 | smallest margin +.121 (CI lower +.075) | MET (also after dedup) |
| D2 | OOD lower CI > .5 and probe >= TF-IDF OOD +.05; inconclusive if positives <25 or CI wider than .25 | met on B and on A (32 positives, width .196) | MET |
| D3 | report only; competitive if within .03 of agreement | A +.017 competitive; B +.068 [+.023,+.112] | as reported |
Count: 4 pass, 4 fail/partial (author: "5 of 8").

S6a
| id | wording | observed | verdict |
|---|---|---|---|
| S6-1 | base correct rate .43 (.35-.52) | .442 (recomputed) | PASS |
| S6-2 | trained TriviaQA coverage .55 (.40-.70); SER .15 (.08-.25), >=.20 below plain | cov .424; SER .060; -.452 | PARTIAL: SER outside range -> FAIL as worded (author scored pass) |
| S6-3 | cautious cov .85 (.55-.98), SER .30 (.18-.42) | .624, .246 | PASS |
| S6-4 | trained-cautious SER -.10 (-.20..-.02), CI excludes 0 | -.186 [-.224,-.148] (clean -.182) | PASS |
| S6-5 | trained and probe gate tied (within .03, CI includes 0) | -.052 [-.082,-.024]; clean -.030 [-.062,.000] | FAIL as published; borderline on clean data |
| S6-6 | SimpleQA trained cov .25 (.05-.50); cautious cov .70 (.40-.95); trained SER <= .20; trained-cautious <= -.10 with CI excl. 0 | .098; .106; .082; +.002 [-.026,+.028] | FAIL (two clauses) |
| S6-7 | R1 passes on both sets (p .55) | not met | FAIL |
| R1 | trained-cautious SER CI < 0 on BOTH sets and trained yield not lower by > .03 | SimpleQA CI includes 0; TriviaQA yield -.014 published, -.048 [-.083,-.012] on the clean test | NOT MET (clean data also fails the yield clause in distribution) |
| R2 | trained credited beyond gate if CI < 0 on both sets | TriviaQA yes (published), SimpleQA tied | NOT MET |

S6b
| id | wording | observed | verdict |
|---|---|---|---|
| S6b-1 | SQuAD2 trained SER .06 (.02-.12); cautious .16 (.08-.28); plain .30 (.18-.45); trained yield .82 (.65-.92) | .073; .180; .527 (generous regex .470); .827 | FAIL on plain clause (author: "mostly pass") |
| S6b-2 | FaithEval trained SER .12 (.04-.25), lower than cautious by >= .03 | .327; -.167 [-.223,-.110] | FAIL (SER range), second clause pass |
| S6b-3 | SimpleQA-E trained correct .45 (.30-.58), SER .08 (.03-.16) | .497; .060 | PASS |
| S6b-4 | SimpleQA-E trained-cautious SER <= -.02, CI excludes 0 | -.010 [-.030,+.010] | FAIL |
| S6b-5 | R3 holds (p .45); R4 holds on SER (p .5) and fails on correct (4B > .10 below 27B) (p .7) | R3 not met; R4 SER yes; correct gap -.090 | R3 clause correct (not met); R4-SER clause pass; "fails on correct" clause FAIL |
| R3 | SQuAD2 and SimpleQA-E: trained-cautious SER CI < 0 and yield loss <= .03 | SQuAD2 SER CI < 0 but yield -.047 (point; CI [-.113,+.020]); SimpleQA-E SER CI includes 0, yield -.033 [-.063,-.003] | NOT MET (ambiguous whether yield tolerance applies to point or CI; fails on SimpleQA-E SER either way) |
| R4 | trained SER within +.03 of 27B B1 (CI upper < +.05) AND trained correct within .10 | -.003 [-.023,+.017]; -.090 [-.127,-.053] | MET by point estimate; fails if the CI is used for the second clause (ambiguity in wording) |

Ambiguities flagged: S5-6 does not say which label; S5-7 and S6b-5 combine several clauses; R3/R4 do not say "point estimate" or "CI" for tolerances; "disjoint" is not defined (row vs question). Predictions cannot be verified as pre-dating results (see 2d).

## 6. Verdict per headline claim

| claim | verdict | reason |
|---|---|---|
| S5: probe on hidden states beats question-text, random-init and shuffled-label controls in distribution (D1) | HOLDS | exact reproduction; survives removal of the 38 duplicate questions (margins grow); selection is train-only; caveats: one fit, weak question-only control |
| S5: signal transfers partly to SimpleQA (D2, AUROC .66-.71, 32-48 positives) | HOLDS (weak evidence) | rule met, CI lower .58 (.56 after dedup); label noise about 4%; OOD controls weak; fit-to-fit control variability about 0.05-0.10 |
| S5: probe beats sampling agreement (D3) | WEAKENED | true only on label B ID vs exact-match agreement; tied with sampling and mean log-prob on label A and OOD; log-prob needs a generated answer but is just as good |
| S5: per-layer / layer-choice statements | WEAKENED | curves flat; S5-6 uninformative |
| S6a: fine-tuned abstention beats the cautious prompt in distribution (SER) | HOLDS | -18 pts survives leak removal |
| S6a: ... at about equal yield | WRONG after cleaning | -4.8 pts [-8.3,-1.2] on clean test (published -1.4) |
| S6a: fine-tuned beats the probe gate at equal coverage | WEAKENED | -5.2 -> -3.0 (CI touches 0) after removing the 13% leaked test rows; tied with a log-prob gate |
| S6a: training set disjoint from S5/test | WRONG | 307 shared rows, 67 test questions |
| S6a: OOD all three tie; abstention transfers to SimpleQA | HOLDS | unaffected by the leak; low power (about 50 answers) |
| S6a/S6b: "trained minus plain" magnitudes | WEAKENED | plain is inflated by regex misses (6-7 pts) |
| S6a: R1 not met, R2 not met | HOLDS | conservative; clean data makes R1 fail on yield too |
| S6b: R3 not met (training does not beat prompting on retrieved Wikipedia passages) | HOLDS | independent of the regex issue (cautious/trained only); SQuAD2 test is same-article |
| S6b: trained beats cautious on SQuAD2 and FaithEval | HOLDS for SER (with yield cost -4.7 pts on SQuAD2) | SQuAD2 in-distribution (35/35 articles shared); FaithEval is the only cross-dataset result |
| S6b: 4B "nearly matches" the 27B on SimpleQA-E; R4 met | WEAKENED | SER match at lower coverage and vs the weakest 27B system; correct -9 pts with CI to -12.7; "met" depends on point-vs-CI reading; grading is identical and fair |
| S2 variant E: coverage 70.7%, B1 correct 58.7%, wrong 6.3%, VKG_v2 minus B2 etc. (P19-P23 pass) | HOLDS | reproduced exactly from raw jsonl; hashes match except analyze_open.py (tables only); dev-to-test gain 22.0 vs 26.6 reported; wrong counts are upper bounds (grader FN, the 4B list shows the same); two debug ids sensitivity <0.4 pts (hybrid: B1 .584/.064 without them) |

## 7. Suggested fixes (not applied; no existing file was edited)

1. Sample TriviaQA by `question_id` (dedup rows) and re-run S6a evaluation on the 433 clean rows or retrain without the 67 test questions; report both.
2. Report plain with a stricter abstention detector or label the plain SER as an upper bound everywhere (tables and "trained minus plain" lines).
3. Add a zero-training gate (mean log-prob) and a risk-coverage curve to S6a.
4. State in R3/R4 whether tolerances apply to point estimates or CI bounds; hash the prediction text before runs.
5. Say in S6b that SQuAD2 train/eval share all 35 articles.

## Files

`results/audit2/`: hygiene.py/.txt, s5_basic.py/.txt, s5_refit.py/.txt/.stdout, s6a_recompute.py/.txt, s6a_gates.py/.txt, s6b_recompute.py/.txt, regex_audit.py/.txt, trivia_sample.py/.txt, trivia_contain.py/.txt, trivia_fn.py/.txt, s5_ood_pos.py/.txt, faith_subsets.py/.txt, s2_recompute.py/.txt.
