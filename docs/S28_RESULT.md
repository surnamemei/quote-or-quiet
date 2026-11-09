# S28 result: a small trained checker for "does this sentence state that this span answers this question" (2026-11-09; design data; rule in docs/S28_PLAN.md fixed before training)
Training: Qwen3-4B-Instruct-2507 with LoRA on 5,540 examples (1,379 positives, 4,161 hard negatives) built from the SimpleQA design pool only; 15% of the questions held out. Held-out AUROC 0.988 (year 0.927, number 0.897, name 0.997; the name negatives were easy).
Evaluation: 1,871 real releases scored by the checker (sentence of the released span in its release page): Mintaka test combination system (942 correct, 63 wrong, 8 of them clear relation errors), FRESH-5 combination system (713, 14), DEV added releases (121, 18).
| pool | correct | wrong | threshold keeping 95% of correct | wrong flagged | clear relation errors flagged | AUROC correct vs wrong |
|---|---|---|---|---|---|---|
| Mintaka test | 942 | 63 | -0.50 | 10 (16%) | 4 of 8 | 0.603 |
| FRESH-5 | 713 | 14 | -0.30 | 1 (7%) | none among them | 0.677 |
| DEV added | 121 | 18 | 0.75 | 4 (22%) | none among them | 0.571 |
| pooled, one threshold -0.28 | 1,776 | 95 | | 15 (16%) | 4 of 8 | |
Rule (flag at least half of the wrong releases and at least 5 of the 8 clear relation errors at a threshold that keeps 95% of the correct ones): not met (16%, 4 of 8). The learned-checker line stops. Thresholds were chosen on the evaluation data, so the numbers are, if anything, optimistic.
Reading. The checker does what it was built for on about half of the relation errors (4 of 8), but those are 0.4% of releases; across all wrong releases it catches 16% at the price of dropping 5% of the correct ones (about 47 of the 942 correct Mintaka releases for 10 of 63 errors), a bad exchange.
The 27B veto caught 2 of 18 added errors (11%); this checker 4 of 18 on the same pool (22%) and 15 of 95 overall (16%): small differences, same order. The gap between held-out AUROC 0.99 and real AUROC 0.57 to 0.68 shows that the synthetic hard negatives (other typed spans of the same sentence or page)
are not the errors the system makes: the real wrong releases are fluent sentences about the right entity whose relation is close to the asked one. Training on the system's own errors would need far more labelled errors than the 95 available. Statement C4 (a narrow, auditable frame checker) remains untested.
