# S64 gate G13: HHEM-2.1-Open and MiniCheck against the 27B judge and the small judge on our reviewer labels

| Set | Checker | AUROC for 'states' | accepted | measure among accepted |
|---|---|---|---|---|
| heldout (n=939) | HHEM, threshold 0.5 | 0.951 | 734 (78.2%) | not 'states': 34 (4.6%, upper 6.4%) |
| heldout (n=939) | small trained judge, 0.5 | 0.988 | 744 (79.2%) | not 'states': 19 (2.6%, upper 4.0%) |
| heldout (n=939) | HHEM at the small judge's acceptance (744) |  | 744 (79.2%) | not 'states': 37 (5.0%, upper 6.8%) |
| heldout (n=939) | 27B prompted judge (rule R27 prompt) |  | 716 (76.3%) | not 'states': 8 (1.1%, upper 2.2%) |
| heldout (n=939) | HHEM at the 27B judge's acceptance (716) | 0.951 | 716 (76.3%) | not 'states': 31 (4.3%, upper 6.1%) |
| heldout (n=939) | MiniCheck at the 27B judge's acceptance (716) | 0.963 | 716 (76.3%) | not 'states': 22 (3.1%, upper 4.6%) |
| mintaka (n=361) | HHEM, threshold 0.5 | 0.892 | 196 (54.3%) | misleading: 28 (14.3%, upper 20.0%) |
| mintaka (n=361) | HHEM at the small judge's acceptance (154) |  | 154 (42.7%) | misleading: 13 (8.4%, upper 14.0%) |
| mintaka (n=361) | 27B prompted judge (rule R27 prompt) |  | 162 (44.9%) | misleading: 3 (1.9%, upper 5.3%) |
| mintaka (n=361) | HHEM at the 27B judge's acceptance (162) | 0.892 | 162 (44.9%) | misleading: 16 (9.9%, upper 15.5%) |
| mintaka (n=361) | MiniCheck at the 27B judge's acceptance (162) | 0.890 | 162 (44.9%) | misleading: 12 (7.4%, upper 12.6%) |
