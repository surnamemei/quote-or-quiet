# S25 result: stronger veto (Qwen3.8-27B) on the added releases (2026-11-09; design data; rule fixed in docs/S25_PLAN.md before running)

997 pre-veto candidates (s19 with format gate, pin, indep on mintaka_dev, popqa_dev, dev); 27B cautious on each variant's combined passage (20 minutes).
Pooled over the two variants, wrong and correct releases added beyond the frozen S19 system:
| policy | wrong added | correct added |
|---|---|---|
| Phi-4 only (current) | 18 | 122 |
| Qwen3.8-27B only | 18 | 133 |
| both must agree | 16 | 121 |
By variant: indep 79/5/74 (27B), 72/5/67 (both), 73/5/68 (Phi-4); pin 72/13/59, 65/11/54, 67/13/54 (A / wrong / correct).
Decision rule (wrong at least halved with at least 75% of correct kept): not met by either policy; line stopped.
Reading. The 27B agrees with the wrong candidates as often as Phi-4 does: switching the veto to a larger model removes 2 of 18 wrong added releases (policy both) and none under 27B alone.
The errors are not veto-detectable. Most are cases where every reader reads the same page the same way (namesakes, ambiguous questions, gold that disagrees with the source), as the error budget
(docs/GENERALITY_STEP1.md) and the correlated-error literature (Denisov-Blanch et al., arXiv 2603.06612) would suggest. The hypothesis "the veto is the weak link" is rejected on DEV.
