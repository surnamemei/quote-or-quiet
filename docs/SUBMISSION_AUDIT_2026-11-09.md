# Submission audit of paper/manuscript.md (2026-11-09)
Readiness: not ready to submit; the science is in a stable shape but three items need the authors and one is a design choice.
## Fixed in this pass
- Abstract was about 330 words with seven findings; shortened to a problem, approach, result, transfer, cost, comparison chain.
- Contributions list lacked the closed-evidence benchmark and the larger-veto and Learn-then-Test results; added.
- Section 4 called Sections 5.3 to 5.6 post hoc but did not say how 5.7 was run; added.
- Qualified, Derived were used in 5.7 before being defined; defined at the start of 5.7.
- "Not significant" for 4 against 9 errors had no test; added exact binomial, one-sided p = 0.13.
- Discussion and Conclusion did not reflect the closed-evidence results or the larger-veto and title-retrieval negatives; updated. The Discussion still says synthetic results test machinery only.
- Four claims reworded after the claim-source pass (docs/CLAIM_SOURCE_LOG.md).
## Open
High
1. Data and code availability has a placeholder: no public repository exists (docs/AVAILABILITY_DRAFT.md). Only the authors can create and deposit it.
2. Redistribution terms for the SimpleQA and PopQA items inside the released run records are unchecked.
3. L1 and a second real L2 benchmark are not established; the title and abstract say what is established (one L2 certificate, transfer limits), but a reviewer will ask for the second benchmark. Needs new sealed real questions (docs/POSITIONING_AND_PLAN.md track B).
Medium
4. Comparison with calibrated-cascade methods (BalanceRAG, Judge Retrieve or Abstain) is stated as different regimes; no same-data run (no public code). The Learn-then-Test baseline is our own implementation.
5. PopQA classes and FRESH-5 classes are authors' unblinded readings (stated in the Fig. 3 legend).
6. Adjudicators are language-model agents; the decoy validity bar (62/62, 61/63) is reported; a human subset would calibrate them.
7. Farquhar et al. claim could not be re-quoted today (blocked), supported by an earlier primary read.
Low
8. Draft header comment cites internal file paths; remove at submission. Reference keys are pandoc-style; format for the venue.
9. Figures: Fig. 3 has no panel letters (single panel); Fig. 1 to 3 are print-scale vector PDFs; no figure for the synthetic results (Tables 4 and 5 carry them).
Top remaining risk: a reviewer's objection that the only real-data L2 result is a single run on one benchmark, with an LLM judge, whose gold we also found noisy elsewhere.
Next highest-leverage fix: a sealed second real benchmark with checked, current gold (track B), which also gives power for L1.
