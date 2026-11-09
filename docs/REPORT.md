# Silent errors in local LLMs: what reduced them, what did not, and what is left

Consolidated report, 2026-11-05 (drafted by a subagent from the project docs, saved and checked by the main session). Every number is copied from `results/SUMMARY.md` or from the protocol/results doc named next to it, and those documents remain the source of truth. Where SUMMARY has a correction block that overrides an older line, this report uses the corrected value.

## 1. Goal and metrics

The project follows `target.txt` (VKG Research Programme). It has two goals.

- **Goal A:** no silent false claims in the final output. When evidence is insufficient the system should look further, and if that fails it should say "unknown", "disputed" or "conditional" instead of stating a guess as fact.
- **Goal B:** remove the mechanisms that turn missing or wrong knowledge into confident answers, so that the system depends less on external checkers.

`target.txt` sets three success tiers. L1 is an empirical reduction under strict controls. L2 is statistical risk control on a stated task distribution. L3 is a strict guarantee within a formal scope. This report covers L1-type evidence only. No L2 guarantee was attempted (ROADMAP S4 is not done).

| metric | definition |
|---|---|
| SER (silent error rate) | wrong definite answers / all questions. "Strict SER" also counts false conflict claims. |
| yield / correct | correct answers / all questions (or / answerable questions where stated) |
| coverage | answered questions / all questions |
| precision | correct / answered |

A lower SER only counts as progress when it does not come from simply answering less. For that reason, comparisons are made at matched coverage or reported together with the yield cost.

## 2. Method and safeguards against circular evaluation

- **Gold from code or datasets, never from an LLM judge.** The synthetic tasks have programmatic gold. SQuAD 2.0, FaithEval, TriviaQA and SimpleQA Verified use dataset gold. SimpleQA answers are graded by string matchers (strict, then a repaired grader). The repaired grader was validated by hand (`docs/GRADER_VALIDATION.md`): 0 of 120 false positives, and about 8-9% of grader-wrong rows are really correct. Wrong counts are therefore upper bounds.
- **Pre-registration.** Before each held-out run, the code hash and predictions were written in `docs/FREEZE.md` or a protocol doc. Failed predictions are reported as failed. One limit: hashes cover code, not the text of predictions, so the order of predictions and results cannot always be proven from the files.
- **Dev/test separation.** Systems were designed on dev seeds and then frozen. The retrieval variant was chosen on 150 dev questions outside the 300 test questions. Probes chose their layer and regularisation by inner cross-validation on training data only.
- **Two independent audits** (`docs/AUDIT.md`, `docs/AUDIT2.md`) recomputed the numbers from the raw rows. Both found real problems, which are listed in section 4 and corrected in SUMMARY.
- **Controls.** These include matched-coverage prompts (B2_strict), question-only and random-initialised-model controls for probes, shuffled labels, and free baselines such as mean log-probability.

Models: Qwen3.8-27B (dense, UD-Q5_K_M, Ollama) for the main pipeline, and Qwen3-4B-Instruct-2507 (dense) for probe and training experiments. One run per condition.

## 3. Findings, strongest first

### 3.1 Executing code removes errors on computable questions
On generated tasks with programmatic gold, routing computable questions to code execution cut formal-family errors from 63.3% to 0.0% (held-out seed 1001, formal over-abstain 20%). On seed 2001 with the fixed generator, errors fell from 41/60 to 1/60 (7/60 over-abstain). All of VKG_v2's synthetic gain over the cautious prompt (−13.7 pts; the run's own CI is −18.0..−10.0, see AUDIT M1) is in this family.
*Scope:* tool use on computable tasks, not evidence that the model's own arithmetic improved. *Source:* SUMMARY, held-out and second matched-coverage sections.

### 3.2 One cautious prompt does as well as a multi-call same-model verifier

| suite | VKG_v2 minus B2_strict |
|---|---|
| SQuAD 2.0 (seed 2000) | strict SER +0.7 pts (CI −2.3..+3.7), yield +2.7 pts (CI −1.4..+7.1) |
| FaithEval (seed 2000) | −1.7 pts (CI −4.7..+1.3); on 252 clean items −1.6 pts (CI −5.2..+2.0) |
| SimpleQA + Wikipedia, variant E | wrong −1.7 pts (CI −3.3..−0.3), correct −5.3 pts (CI −8.0..−3.0) |

On FaithEval the cautious prompt alone cuts B1's strict SER by 9.3 pts (CI −13.0..−6.0).
*Scope:* n=300 per suite (CI about ±3 pts); the checker is the same model. *Source:* SUMMARY, matched-coverage sections and S2.

### 3.3 Retrieval is the main lever for open-world facts
Closed-book on 500 SimpleQA Verified questions, the raw 27B is strict-correct on 4.4% and wrong on 95.6%. With the abstain prompt it attempts 20.2% and is still wrong on 18.4% (strict grader, upper bounds). With variant E retrieval (generator-written queries, BM25 + embedding ranking over up to 10 Wikipedia pages, 1,500-word passage), results on 300 test questions with the repaired grader are:

| system | attempted | correct | wrong | precision |
|---|---|---|---|---|
| B1_abstain | 65.0% | 58.7% | 6.3% | 90.3% |
| B2_strict | 62.0% | 56.3% | 5.7% | 90.9% |
| VKG_v2 | 55.0% | 51.0% | 4.0% | 92.7% |

Compared with baseline retrieval, B1 gains 18.7 pts of correct answers (CI +14.0..+23.7) with wrong +1.3 pts (CI −1.0..+3.7, not significant). The evidence contains the answer for 70.7% of questions (baseline 48.7%). All predictions P19-P23 passed.
*Scope:* one model and one run. Wikipedia content is live. Wrong rates are upper bounds, and about 4-6% of all questions still get a wrong answer. *Source:* SUMMARY S2, `results/open_world_tables.md`.

### 3.4 Closed-book confidence ranks answers but gives no usable threshold
- **S3** (27B, 250 test questions, 18 correct): AUROC ranges from 0.643 (verbalised confidence) to 0.795 (logistic combination; embedding self-consistency 0.750 [0.642, 0.848]). None of the 7 signals met the pre-registered rule of test precision at least 30% at coverage at least 2%. *Source:* `results/S3_signals.md`.
- **S5a:** question text alone gives AUROC about 0.62 and adds nothing to the S3 signals (−0.005, CI −0.016..+0.004).
- **S5** (4B hidden-state probe, TriviaQA): AUROC 0.821 [0.783, 0.853] (0.817 after deduplication), above TF-IDF (0.682), a random-initialised model (0.641) and shuffled labels (0.498). It is tied with free mean log-probability (0.828), and out of distribution it falls to 0.706. *Source:* `results/S5_probe.md` and the second correction block in SUMMARY.

### 3.5 Trained abstention works mostly by abstaining more
**S6a-clean** (4B, LoRA trained on the model's own correct answers, otherwise "unknown"; 462 clean TriviaQA test rows):

| system | coverage | yield | SER |
|---|---|---|---|
| cautious prompt | 62.3% | 38.1% | 24.2% |
| probe gate (coverage of trained) | 35.7% | 27.5% | 8.2% |
| log-prob gate, no training | 35.7% | 29.0% | 6.7% |
| fine-tuned abstention | 35.7% | 30.5% | 5.2% |

Compared with the cautious prompt, fine-tuning lowers SER by 19.0 pts (CI −22.9..−15.2) and lowers yield by 7.6 pts (CI −11.3..−3.7). Against the log-prob gate at equal coverage it is tied (−1.5 pts, CI −4.1..+1.1). On long-tail SimpleQA all mechanisms tie (SER 7.4-8.4%, coverage 9-11%). Rules R1 and R2 were not met. *Source:* `results/S6a_clean.md`.

**S6b** (4B, LoRA trained to answer only from the passage): trained minus cautious SER is −10.7 pts (CI −14.7..−6.7) on SQuAD2 held-out and −16.7 pts (CI −22.3..−11.0) on FaithEval. On SimpleQA with the 27B's passages it is −1.0 pts (CI −3.0..+1.0), with fewer correct answers (49.7% vs 53.0%). SQuAD2 train and eval share all 35 articles, so FaithEval is the only cross-dataset evidence. *Source:* `results/S6b_abstention.md` and the second correction block in SUMMARY.

### 3.6 The hidden state knows whether the passage holds the answer, but gating on it adds little
**S7:** a probe trained on SQuAD2 only reaches AUROC 0.941 [0.913, 0.965] on SQuAD2 held-out and 0.893 [0.849, 0.929] on retrieved Wikipedia passages. Controls score 0.502-0.591. It beats the model's own abstentions (cautious 0.852, fine-tuned 0.838) by +0.041 [+0.009, +0.073] and +0.056 [+0.022, +0.091]. It calls 33.3% of FaithEval counterfactual unanswerable passages sufficient. *Source:* `results/S7_evidence_sufficiency.md`.

**S7b**, the probe used as an answer gate with a threshold fixed in advance:

| system | coverage | correct | SER |
|---|---|---|---|
| 4B cautious prompt | 60.0% | 53.0% | 7.0% |
| 4B gate + cautious | 48.7% | 44.7% | 4.0% |
| 27B B1_abstain | 65.0% | 58.7% | 6.3% |
| 27B B1_abstain gated by the 4B probe | 49.3% | 45.3% | 4.0% |
| 27B VKG_v2 gated by the 4B probe | 44.7% | 42.0% | 2.7% |

The gate lowers SER on every system (4B cautious −3.0 pts, CI −5.0..−1.3; 27B B1 −2.3 pts, CI −4.3..−1.0). The cost is 8-13 pts of correct answers, so by the pre-set rule it is not useful as an add-on. At equal coverage the probe ranks no better than the prompt's own abstention (+1.0 pts SER, CI −1.3..+3.3).
On one rater's manual reading of the 12 errors left after gate+cautious, 7 look like grader false negatives. The 5 real errors all come from passages that contain the gold answer. That gives about 1.7% real silent errors at 48.7% coverage. *Source:* `results/S7b_evidence_gate.md` (the sweep and manual reading were done after seeing results).

## 4. What was withdrawn or corrected, and why

From the first audit:
1. **Graders.** The strict matcher misses correct SimpleQA answers, so SimpleQA "wrong" columns are upper bounds. A repaired grader was added after seeing results.
2. **Retrieval baseline under the repaired grader:** when the evidence lacks the answer, B1 is wrong on 7 (4.5%), not 14%.
3. **"The verifier removes a few more wrong answers" with search retrieval** is withdrawn (wrong −0.3, CI −1.7..+0.7; correct −4.3, CI −6.7..−2.3).
4. **The oracle table** is an upper bound on a self-selected n=251, not a deployable system.
5. **The FaithEval seed-2000 control** reused 48 of 300 items. On the 252 clean items the conclusion is unchanged.
6. **Two test questions were used for cleaner debugging.** Removing them changes no number by more than 0.4 pts.
7. **B0_raw rows are inflated** by a regex abstention detector. Synthetic B0 SER of 49.3% is about 18 points too high.
8. **Wording softened:** "adds nothing measurable" became "not distinguishable at n=300"; "almost no information" became "a 2x lift in precision on a small number of answers".
9. **Prediction notes:** P9 was not blind; P5 passes on SER only; the P12 gain is not significant; P17 and P18 depend on the grader.

From the second audit:
10. **TriviaQA leak.** The file has 17,944 rows but only 9,960 distinct questions. S6a had 67 of 500 test questions in training. The "disjoint" claim was false, and S6a was rerun as S6a-clean. Withdrawn: "beats the probe gate by 5.2 pts with 5.2 pts more correct answers" and "about equal yield". S5 is robust (0.821 to 0.817).
11. **The plain baseline is inflated** by regex misses. "Trained minus plain" figures are overstated by about 6-7 points.
12. **S5 tally:** four of eight predictions pass as worded, not five. The probe is tied with free log-probability.
13. **S6b wording:** "nearly matches the 27B" holds only for SER at different coverage (55.7% vs 65.0%), against the 27B's weakest system, with 9 points fewer correct answers. R4 holds on the point estimate but not the CI.
14. **The S6a out-of-distribution ties** rest on about 50 answered items per system.
15. **S6b's rules** were written after S6a's out-of-distribution result.

Earlier corrections:
16. **Synthetic generator bug** (freeze 4): contradiction items were ill-posed. "10 of 30 contradictory passages answered silently" is withdrawn. The formal result is unaffected.
17. **First pilot** graded with a gold bug: superseded and not cited.

## 5. Relation to prior work

Only references verified in `docs/LITERATURE_CHECK.md` are listed.

- **Abstention training is published.** Gekhman et al. (2405.05904, EMNLP 2024) motivate training only on the model's own answers. Abstain-R1 (2604.17073), TIAR (2605.25850), AWA-RL (2607.10738) and GRACE (2601.04525) cover RL variants. S6a-clean and S6b add a controlled comparison on one model against a cautious prompt and a free log-probability gate, not a new training method.
- **Hidden-state and sampling signals.** Semantic entropy (Farquhar et al., Nature 2024) and semantic entropy probes (Kossen et al., 2406.15927) are the templates for S3 and S5. Farquhar et al. state that consistent errors are not detected, which matches the long-tail failure in S3.
- **Evidence sufficiency.** Sufficient Context (2411.06037), RINSE (2609.37469), SURE-RAG (2605.03534), S2G-RAG (2604.23783) and Sato et al. (2609.01687) study sufficiency judgement. GRAB-RAG (2608.22228, single author, 3.8B-8B) reports that prompted abstention fails under misleading context, which parallels S7's 33.3% on counterfactual FaithEval passages. No 2026 SimpleQA-style retrieval-abstention study with open-weight models was found in four searches.
- **Risk guarantees.** Mohri and Hashimoto (2402.10978), Cherian, Gibbs and Candes (2406.09714), SCoRE (2603.24704), ITCR (2606.08831) and Kotte (2606.29054) are the candidates for L2 work, which is not done here. UniCR (2509.01455) is withdrawn on arXiv and not used.
- **Claim-level checking.** FreeGuard (Wang and Zhao, Discover Computing 29:713, 2026) is a named baseline. It was not run here.

## 6. Open problems and next steps

- **Reading errors.** After retrieval and gating, the real residual errors found by hand are misread passages (wrong day, wrong number, missing day). A code-only check of the answer against its passage (S8) is pre-registered in `docs/S8_PROTOCOL.md` and in progress.
- **Grader.** Name variants (dropped middle names, shortened official names, aliases) still count as wrong. A fix must be validated by hand before use.
- **Not done:** AbstentionBench; risk control with a guarantee (S4); BF16 or other-quantization comparisons for the 27B; Qwen3.8-Flash-Next (MoE); a different-family checker.
- **Long-tail facts without evidence** remain unsolved by every closed-book mechanism tested. The working answer is to retrieve first.

## 7. Limits

- **One seed, one run** per condition; n of 150-500 per suite.
- **4B vs 27B:** the probe and training studies use a 4B model of a different generation from Qwen3.8-27B. No transfer to the 27B, hybrid-attention or MoE models is claimed.
- **Same-family checkers:** VKG_v2's checker is the same model; VKG_v2x and the S7b cross-model gate are smaller same-vendor models. No independent checker was tested.
- **Grader false negatives:** SimpleQA wrong rates are upper bounds (about 8-9% of grader-wrong rows are correct). Manual readings have one rater.
- **Contamination:** all four datasets are public and may be in training data.
- **Scope of "hallucination":** FaithEval counts beyond-passage answers as errors even when true, so its SER measures unsupported answering, not only false claims.
- **Not eliminated:** about 4-6% of open-world questions still get a wrong answer with retrieval (upper bound). The best gated system, on one rater's reading, is about 1.7% at under half coverage.
