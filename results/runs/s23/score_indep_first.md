# S23 DEV scoring (design data)

| set | variant | n | released (cov) | wrong | added vs frozen S19 | wrong among added | added from variant |
|---|---|---|---|---|---|---|---|
| mintaka_dev | indep | 200 | 96 (0.480) | 4 | 25 | 2 | 16 |
| mintaka_dev | pin | 200 | 108 (0.540) | 6 | 37 | 4 | 28 |
| popqa_dev | indep | 300 | 79 (0.263) | 8 | 20 | 1 | 15 |
| popqa_dev | pin | 300 | 89 (0.297) | 16 | 30 | 9 | 25 |
| dev | indep | 300 | 166 (0.553) | 3 | 28 | 2 | 18 |

Pooled over the three DEV sets (added beyond the frozen S19 system):
- indep: A = 73, w = 5, w / A = 0.068
- pin: A = 67, w = 13, w / A = 0.194
Decision rule (A >= 40 and w / A <= 3%) for indep: STOP the independent-retrieval line
