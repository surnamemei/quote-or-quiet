# S23 DEV result: independent retrieval (2026-11-09; design data; rule fixed in docs/S23_DEV_PLAN.md before generation)

Scored with results/runs/s23/score_indep.py (output score_indep.md). Combination rule S19 releases (format gate) U variant releases that are
not time-sensitive and not subject-ambiguous; A = releases added beyond the frozen S19 system, w = graded-wrong among them.

| set | variant | released (coverage) | wrong | added | wrong among added | added from variant |
|---|---|---|---|---|---|---|
| mintaka_dev | indep | 96 (0.480) | 4 | 25 | 2 | 16 |
| mintaka_dev | pin | 108 (0.540) | 6 | 37 | 4 | 28 |
| popqa_dev | indep | 79 (0.263) | 8 | 20 | 1 | 15 |
| popqa_dev | pin | 89 (0.297) | 16 | 30 | 9 | 25 |
| dev (SimpleQA) | indep | 166 (0.553) | 3 | 28 | 2 | 18 |

Pooled: indep A = 73, w = 5 (6.8%); pin (two sets) A = 67, w = 13 (19%). Rule (A >= 40 and w / A <= 3%): **not met, line stopped** (no FRESH-5 run).
Reading: removing the web dependence lowers the error rate of the variant's own additions from 11 of 53 (21%, pin) to 2 of 31 (6.5%, indep) on
the two sets where both ran, so independence of the source matters; it does not reach the 1% to 3% needed to keep the L2 allowance. Of the 5
errors, 2 come from the format gate on the S19 part (Face screenwriter, "Doab"), 3 from the variant (first Mario game 1981 vs 1983; Ark release
date 2015 early access vs 2017; Carrie Underwood date off by one day), the first two being ambiguous questions or gold. Interval for 5 of 73:
95% CP 2.3% to 15.3%, so DEV cannot exclude 3%; the rule was fixed in advance and is followed.
Coverage gain on DEV (frozen S19 -> indep): Mintaka 0.355 -> 0.480, PopQA 0.197 -> 0.263, SimpleQA 0.460 -> 0.553.
