# S55: the student judge (S51 recipe, gold plus 27B silver labels)

Training rows: 3656 labelled + 3368 silver (27B YES share 0.284).

| Set | AUROC for 'states' | accepted at 0.5 | measure among accepted |
|---|---|---|---|
| held-out (n=939) | 0.988 | 745 (79.3%) | not 'states' 16 (2.1%, upper 3.5%) |
| Mintaka rows (n=361) | 0.911 | 163 (45.2%) | misleading 13 (8.0%, upper 13.3%) |
