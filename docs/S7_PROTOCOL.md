# S7 protocol: an internal evidence-sufficiency signal in the 4B model (written 2026-11-05 16:48 BEFORE any S7 output existed)

Question: before the 4B model answers, do its hidden states tell whether the passage in front of it contains the answer, and does that transfer from clean SQuAD2 paragraphs to retrieved Wikipedia passages? This targets the failure that remains in the retrieval pipeline: answers given when the evidence lacks the answer. Prior art on evidence-sufficiency judgement exists (GRACE 2601.04525, "sufficient context" work); not repeated, reused as a recipe.
Features: hidden states of the BASE Qwen3-4B-Instruct-2507 at the last prompt token of the plain passage prompt, 11 layers. Probe: L2 logistic regression, layer and C by 5-fold CV inside the training set only (same code as S5). Train: the 3,000 SQuAD2 items of S6b (label = answerable, dataset-provided).
Tests: SQuAD2 held-out (300; label = answerable); SimpleQA-E (the 300 frozen test questions with the variant-E passages; label = the gold answer string is present in the passage by strict OR repaired matching, no model involved: 212 of 300 sufficient); FaithEval unanswerable (150, all insufficient; reported as a rate, not an AUROC).
Controls: fraction of question content tokens found in the passage; TF-IDF of the question; probe on a random-initialised copy of the model; shuffled training labels; the model's own abstentions from S6b (cautious prompt, trained LoRA) as binary detectors (their AUROC equals balanced accuracy).
Metrics: AUROC for "passage is sufficient" with 2,000-resample bootstrap; paired differences to each control.

## Decision rules (fixed now)
- D4 the signal transfers if on SimpleQA-E the probe AUROC has a lower CI bound above 0.5 AND exceeds the best of {token recall, TF-IDF, random-init, shuffled} by >= 0.05 with a paired CI excluding 0.
- D5 the probe is called useful as a second check if its SimpleQA-E AUROC is within 0.03 of, or above, the better of the model's own abstention detectors (cautious, trained).

## Predictions (point guess, range)
- S7-1 SQuAD2 held-out probe AUROC 0.93 (0.85-0.98).
- S7-2 SimpleQA-E probe AUROC 0.75 (0.62-0.86); token-recall control 0.66 (0.55-0.76); random-init 0.55 (0.45-0.65); shuffled 0.50 (0.43-0.57).
- S7-3 own-abstention detectors on SimpleQA-E (balanced accuracy): cautious 0.72 (0.62-0.82), trained 0.74 (0.64-0.84).
- S7-4 D4 holds (p about 0.55); D5 holds (p about 0.45).
- S7-5 FaithEval unanswerable: the probe calls <= 25% of the passages sufficient at the SQuAD2-train median threshold (p about 0.6).

## Hashes (before the run)
```
953eca354ed337c8f5e2082720ccb6fa260c87f24cafe568046bdb4769c8979f vkg/s7_run.py
1d098e18d9905c99a158c3e577d941422b14fabb80c11eb935bb93d2892f9972 vkg/s6b_run.py
8f1ac345735292f1005b3c2a56b825dedbbf255a03d93f52260b9e84ab17f0c3 vkg/probe_eval.py
9c9aa39bacd63c9d810f6417bec64f1a4616dbbf871cf2c91e13533b014bb3fa vkg/probe_gen.py
0579f162d7e3e35f0b3f0354a9b4666dd0082403612549b8acebb8777725e790 vkg/grade_open.py
```
Known limits: one 4B model, one run, linear probes, activations at one position; the SimpleQA-E sufficiency label is a string match (misses paraphrases, so some "insufficient" passages do contain the answer); the 300 SimpleQA-E questions were already used for S6b evaluation (no tuning on them here).


## Confound check run after seeing the results (not pre-registered)
Surface features do not explain the SimpleQA-E result: AUROC for "passage is sufficient" from passage word count 0.463, number of distinct pages 0.446, question length 0.474. Probe score vs passage length correlation -0.13. Probe AUROC within passage-length tertiles: short 0.883, mid 0.870, long 0.921; after regressing out passage length 0.891. Only 1 of the 88 "insufficient" passages contains a lenient token match of the gold answer anyway.
The shuffled-label control scored 0.307 on SimpleQA-E, far below 0.5. Under distribution shift an arbitrary direction in activation space can be strongly (anti-)correlated with the label, so the control's sign is arbitrary; it shows controls near 0.5 are not guaranteed. The real probe's direction was fixed on SQuAD2 and transferred with the correct sign.

## Scoring of the pre-registered predictions
- S7-1 SQuAD2 held-out probe AUROC 0.941 [0.913, 0.965] (predicted 0.85-0.98): pass.
- S7-2 SimpleQA-E: probe 0.893 [0.849, 0.929] (predicted 0.62-0.86): outside the range, better than predicted (fail as worded); token recall 0.590 (0.55-0.76) pass; random-init 0.591 (0.45-0.65) pass; shuffled 0.307 (0.43-0.57) **fail** (see above).
- S7-3 own-abstention detectors on SimpleQA-E: cautious 0.852 (predicted 0.62-0.82) **fail** (higher), trained 0.838 (0.64-0.84) pass.
- S7-4 D4 (transfer: lower CI above 0.5 and >= best control + 0.05): **holds**; the probe beats the best control by +0.300 [+0.213, +0.386]. D5 (within 0.03 of or above the better own-abstention detector): **holds**; probe minus cautious +0.041 [+0.009, +0.073], minus trained +0.056 [+0.022, +0.091].
- S7-5 FaithEval unanswerable: the probe calls 33.3% sufficient at the SQuAD2-train median threshold (predicted <= 25%): **fail**. On SQuAD2 held-out the same threshold calls 13.3% of unanswerable and 90.0% of answerable passages sufficient.
