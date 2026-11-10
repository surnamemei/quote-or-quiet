# S51: a small quote-sufficiency judge against the 4B prompt judge (held-out questions)

Test rows 939; 'states' for both reviewers 752 (80.1%).

| Judge | AUROC | Acceptance and error |
|---|---|---|
| Small judge (0.6B, LoRA) | 0.988 | at 0.5: accepted 744 (79.2%), not 'states' among accepted 19 (2.6%, upper 4.0%) |
| 4B prompt judge (YES/NO) | 0.798 | accepted 804 (85.6%), not 'states' among accepted 71 (8.8%, upper 11.0%) |
| Small judge at the 4B acceptance rate | | threshold 0.000: accepted 804 (85.6%), not 'states' among accepted 59 (7.3%, upper 9.4%) |
| Small judge, most accepted rows with at most 5% not 'states' | | threshold 0.001: accepted 781 (83.2%), not 'states' among accepted 39 (5.0%, upper 6.8%) |
| Small judge, most accepted rows with at most 3% not 'states' | | threshold 0.059: accepted 756 (80.5%), not 'states' among accepted 22 (2.9%, upper 4.4%) |

By source (small judge at 0.5):

| Source | rows | 'states' share | accepted | not 'states' among accepted |
|---|---|---|---|---|
| e11 | 72 | 61% | 39 | 2 (5.1%) |
| e6 | 153 | 73% | 112 | 3 (2.7%) |
| e7 | 231 | 94% | 218 | 1 (0.5%) |
| e9 | 63 | 90% | 57 | 0 (0.0%) |
| f5 | 80 | 91% | 71 | 0 (0.0%) |
| r4 | 89 | 87% | 77 | 2 (2.6%) |
| s43 | 44 | 73% | 32 | 2 (6.2%) |
| s48 | 75 | 68% | 49 | 0 (0.0%) |
| w4 | 71 | 73% | 54 | 5 (9.3%) |
| web | 61 | 62% | 35 | 4 (11.4%) |

Harder subsets (accepted / not 'states' among accepted):

| Subset | rows | 'states' share | small judge AUROC | small judge at 0.5 | 4B judge |
|---|---|---|---|---|---|
| answer string occurs in the quote | 830 | 85% | 0.988 | 702 / 17 | 739 / 51 |
| answer string does not occur in the quote (includes the decoys) | 109 | 42% | 0.971 | 42 / 2 | 65 / 20 |
| the quote does not occur in the training rows | 713 | 81% | 0.989 | 566 / 10 | 608 / 49 |
| the quote also occurs in the training rows (with another question) | 226 | 78% | 0.984 | 178 / 9 | 196 / 22 |
| answer in the quote and quote unseen in training | 648 | 86% | 0.987 | 548 / 10 | 578 / 38 |
