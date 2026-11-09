# S6a-clean protocol (written 2026-11-05 17:07 BEFORE any output of this rerun existed)

Why: the independent audit (docs/AUDIT2.md, which I re-checked: 17,944 rows but 9,960 distinct questions in the TriviaQA validation file; 67 of the 500 S6a test rows and 307 of 3,000 S6a training rows duplicate S5 questions) showed S6a's "disjoint" claim was false. This reruns S6a with the same model, LoRA settings and prompts on clean data, and adds the audit's two extra checks. The original S6a numbers are superseded for any claim about trained vs probe gate or yield.
Changes: training pool = distinct questions whose text is not among S5's 2,000 (seed 7100, 3,000 questions); evaluation = S5 test rows whose question text is not in S5's train rows; added untrained mean-log-prob gate; added denial-aware abstention detector shown beside the strict one.
Decision rules (same as S6a): R1 trained beats cautious on both sets with SER CI below 0 and yield not lower by more than 0.03; R2 trained beats the probe gate on both sets.

Predictions (point guess, range):
- C1 In-distribution trained SER 0.07 (0.03-0.12), trained minus cautious SER CI entirely below 0 (p about 0.9).
- C2 Trained minus probe gate SER (strict detector): -0.03 (-0.07 to +0.01); CI excludes 0 with p about 0.4.
- C3 Trained minus log-prob gate SER: CI includes 0 (p about 0.6).
- C4 Trained yield minus cautious yield <= -0.03 (point estimate) in distribution (p about 0.6), so R1's yield clause fails even in distribution.
- C5 SimpleQA: all systems tie within +-0.03 SER (p about 0.8).
- C6 Under the denial-aware detector plain SER falls by 4-8 points on SimpleQA; cautious and trained change by < 1 point (p about 0.8).

Hashes (before the run):
```
d4723fcfa2baf39735664a434de8f40159a86cc9782742bbd47f2aed2f98b605 vkg/s6a_clean.py
f919bfcdcc080e7b0ff6641a77a51323c024cd42fe6a05bda8cc5f472ed87a08 vkg/s6_run.py
8f1ac345735292f1005b3c2a56b825dedbbf255a03d93f52260b9e84ab17f0c3 vkg/probe_eval.py
```
Known limits: same as S6a (one 4B model, one run, one seed, string grading, TriviaQA alias matching with a 12-word cap that gives about 2-3% false negatives per the audit).


## Scoring of the predictions in docs/S6A_CLEAN_PROTOCOL.md (written before the rerun)
Clean data: 3,000 training questions with no text shared with S5 or the evaluation (pool of 8,064 distinct questions; base greedy-correct 40.4% on them); 462 of the 500 in-distribution test rows had no text overlap with S5's training rows.
- C1 pass: in-distribution trained SER 0.052 (predicted 0.03-0.12); trained minus cautious -0.190 [-0.229, -0.152], entirely below 0.
- C2 borderline: trained minus probe gate -0.030 [-0.058, +0.000] with the strict detector (CI touches 0), [-0.058, -0.002] with the denial-aware detector. Point estimate as predicted; "CI excludes 0" depends on the detector.
- C3 pass: trained minus log-prob gate -0.015 [-0.041, +0.011], includes 0.
- C4 pass: trained yield minus cautious yield -0.076 [-0.113, -0.037] (<= -0.03). With this, the yield clause of R1 fails in distribution as well as the SER clause on SimpleQA.
- C5 pass: SimpleQA differences between trained, cautious and the gates are all within +-0.01 (SER +0.002, +0.008, -0.002).
- C6 pass: denial-aware detector moves plain SER on SimpleQA 0.890 -> 0.838 (-5.2 pts) and in distribution 0.506 -> 0.481; cautious and trained SER unchanged.
- R1 (trained beats cautious on both sets with yield loss <= 0.03): not met. R2 (trained beats the probe gate on both sets): not met (in distribution borderline, SimpleQA tied).
