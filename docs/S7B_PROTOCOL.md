# S7b protocol: the evidence-sufficiency probe as an answer gate

Written 2026-11-05, before running. Code: `vkg/s7b_gate.py`, SHA-256 `dc1c25240d16fd87d20edd0f61cb3585048117e7ce04cee76104e71311552505`.

## Question
S7 showed a linear probe on Qwen3-4B hidden states ranks "the passage contains the answer" at AUROC 0.89 on retrieved Wikipedia passages. Does using it as a gate (answer only when the probe says the passage is sufficient) actually reduce silent errors, compared with the cautious prompt and the evidence-trained LoRA from S6b, and how much correct output does it cost?

## Design (no new generation; all inputs frozen)
- Probe: identical to S7 (layer and C by inner CV on the 3,000 SQuAD2 training items only).
- Threshold T50 = median probe score on the SQuAD2 training items. It is the only threshold; no test item is used to set it.
- Systems per suite: plain, cautious, trained (S6b outputs); gate+plain, gate+cautious, gate+trained (answer kept only if probe > T50); plain@matched (plain answers kept for the top-k probe scores, k = number of items the cautious system answers).
- Suites: SimpleQA-E (300; primary), SQuAD2 held-out (300), FaithEval unanswerable (150; features exist only for this FaithEval half).
- Cross-model: the 4B probe gates the frozen Qwen3.8-27B answers (B1_abstain, B2_strict, VKG_v2) on the same 300 SimpleQA-E questions and passages.
- Graders as in S6b (strict UNKNOWN_RE detector; repaired grader for SimpleQA). Denial-aware detector reported as a sensitivity.
- Paired bootstrap over items, 2,000 draws.

## Predictions (strict detector)
- P1 SimpleQA-E, gate+plain: SER between 0.06 and 0.13 (plain 0.303).
- P2 SimpleQA-E, plain@matched vs cautious (0.070): SER difference within ±0.03 and its CI includes 0 (the probe ranks about as well as the prompt's own abstention).
- P3 SimpleQA-E, gate+cautious vs cautious: SER lower by 0.01–0.04; yield loss ≤ 0.06.
- P4 SQuAD2 held-out, gate+plain: SER between 0.07 and 0.15 (plain 0.527, cautious 0.180).
- P5 FaithEval unanswerable, gate+plain: SER between 0.25 and 0.40 (counterfactual passages written to look supportive fool the probe, S7-5).
- P6 Cross-model: gate+27B B1_abstain SER ≤ 0.045 (from 0.063) with correct loss ≤ 0.05.

## Decision rule
The gate is called useful on top of an abstaining system if, on SimpleQA-E, gate+cautious (or gate+27B B1_abstain) lowers SER with the CI upper bound below 0 and loses at most 0.05 yield. Otherwise it is reported as "a ranking signal that does not add to the model's own abstention".
